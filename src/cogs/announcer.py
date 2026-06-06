"""Announcer cog — hourly voice announcement with multi-guild support."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import discord
import pytz
from discord.ext import commands, tasks

from src.config import Config
from src.database import Database
from src.services import audio as audio_service
from src.services import phrases as phrase_service
from src.services import scheduler
from src.services import tts as tts_service

logger = logging.getLogger(__name__)


class AnnouncerCog(commands.Cog, name="Announcer"):
    """Cog that handles the hourly voice announcement loop."""

    def __init__(self, bot: commands.Bot, config: Config, db: Database) -> None:
        self.bot = bot
        self.config = config
        self.db = db
        self._started = False

    async def cog_load(self) -> None:
        """Called when the cog is loaded. Starts the announcement loop."""
        logger.info("AnnouncerCog loaded")

    async def cog_unload(self) -> None:
        """Called when the cog is unloaded. Stops the loop."""
        if self.announcement_loop.is_running():
            self.announcement_loop.cancel()
            logger.info("Announcement loop stopped")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Start the announcement loop once the bot is ready."""
        if not self._started:
            self._started = True
            self.announcement_loop.start()
            logger.info("Announcement loop started")

    @tasks.loop(minutes=60)
    async def announcement_loop(self) -> None:
        """Execute announcements for all guilds every hour."""
        if not self.bot.guilds:
            logger.warning("No guilds connected — skipping announcement")
            return

        # Run announcements in parallel for all guilds
        guild_tasks = [
            self._announce_guild(guild)
            for guild in self.bot.guilds
        ]
        results = await asyncio.gather(*guild_tasks, return_exceptions=True)

        for guild, result in zip(self.bot.guilds, results):
            if isinstance(result, Exception):
                logger.error(
                    "Announcement failed for guild '%s' (%d): %s",
                    guild.name, guild.id, result,
                )

    @announcement_loop.before_loop
    async def before_announcement_loop(self) -> None:
        """Wait until the next exact hour before starting."""
        await self.bot.wait_until_ready()

        delay = scheduler.seconds_until_next_hour(self.config.default_tz)
        logger.info(
            "Syncing to next hour — waiting %.0f seconds (%.1f minutes)",
            delay, delay / 60,
        )
        await asyncio.sleep(delay)

    async def announce_for_guild(self, guild: discord.Guild) -> str:
        """Public method to force an announcement for a specific guild.

        Used by the /forzar command.

        Returns:
            Status message describing the result.
        """
        return await self._announce_guild(guild)

    async def _announce_guild(self, guild: discord.Guild) -> str:
        """Core announcement logic for a single guild.

        1. Get guild config (timezone, mode)
        2. Find the target voice channel
        3. Connect and play the audio sequence
        4. Disconnect

        Returns:
            Status message.
        """
        # Guard: don't announce if already in a voice channel for this guild
        if guild.voice_client and guild.voice_client.is_connected():
            logger.warning(
                "Already connected to voice in guild '%s' — skipping", guild.name
            )
            return f"Ya conectado en '{guild.name}', anuncio omitido."

        # Get per-guild config
        guild_config = await self.db.get_guild_config(guild.id)
        if not guild_config["enabled"]:
            logger.debug("Announcements disabled for guild '%s'", guild.name)
            return f"Anuncios desactivados en '{guild.name}'."

        timezone_str = guild_config["timezone"]

        # Find target channel
        channel = self._find_target_channel(guild, guild_config)
        if not channel:
            logger.info(
                "No users in voice channels for guild '%s' — skipping", guild.name
            )
            return f"No hay usuarios en canales de voz en '{guild.name}'."

        # Get current hour info for TTS
        hour_24, hour_12 = scheduler.get_current_hour(timezone_str)
        hour_text = tts_service.format_hour_text(hour_12)

        # Get the phrase for this hour (DB → JSON → hardcoded)
        phrase = await phrase_service.get_phrase_with_db(
            self.db, self.config.phrases_path, hour_24, hour_text
        )

        logger.info(
            "Announcing in guild '%s', channel '%s': %s",
            guild.name, channel.name, phrase,
        )

        # Connect and play sequence
        vc: discord.VoiceClient | None = None
        try:
            vc = await channel.connect(timeout=10.0)

            # Step 1: Intro (random from pool)
            intro_file = audio_service.get_random_from_pool(self.config.intro_pool_dir)
            if intro_file:
                await audio_service.play_audio(vc, intro_file)

            # Step 2: TTS announcement
            tts_file = await tts_service.generate_tts(
                phrase,
                self.config.data_dir,
                guild_id=guild.id,
            )
            if tts_file:
                await audio_service.play_audio(vc, tts_file, delete_after=True)

            # Step 3: Outro (random from pool)
            outro_file = audio_service.get_random_from_pool(self.config.outro_pool_dir)
            if outro_file:
                await audio_service.play_audio(vc, outro_file)

            logger.info(
                "Announcement completed in guild '%s', channel '%s'",
                guild.name, channel.name,
            )
            return f"Anuncio realizado en '{channel.name}' de '{guild.name}'."

        except discord.ClientException as e:
            logger.error("Voice connection error in guild '%s': %s", guild.name, e)
            return f"Error de conexión de voz en '{guild.name}': {e}"
        except Exception:
            logger.exception("Unexpected error during announcement in guild '%s'", guild.name)
            return f"Error inesperado en '{guild.name}'."
        finally:
            if vc and vc.is_connected():
                await vc.disconnect(force=True)
                logger.debug("Disconnected from voice in guild '%s'", guild.name)

    def _find_target_channel(
        self,
        guild: discord.Guild,
        guild_config: dict,
    ) -> discord.VoiceChannel | None:
        """Find the voice channel to announce in based on guild config.

        Args:
            guild: The Discord guild.
            guild_config: Guild configuration dict.

        Returns:
            Target voice channel, or None if no suitable channel found.
        """
        mode = guild_config["announce_mode"]

        if mode == "canal_fijo" and guild_config["channel_id"]:
            # Fixed channel mode
            channel = guild.get_channel(guild_config["channel_id"])
            if isinstance(channel, discord.VoiceChannel):
                return channel
            logger.warning(
                "Fixed channel %d not found in guild '%s' — falling back to most users",
                guild_config["channel_id"], guild.name,
            )

        # Default: find channel with most human users
        best_channel = None
        max_humans = 0

        for channel in guild.voice_channels:
            humans = [m for m in channel.members if not m.bot]
            if len(humans) > max_humans:
                max_humans = len(humans)
                best_channel = channel

        return best_channel if max_humans > 0 else None


async def setup(bot: commands.Bot) -> None:
    """Setup function called by bot.load_extension()."""
    config: Config = bot.config  # type: ignore[attr-defined]
    db: Database = bot.db  # type: ignore[attr-defined]
    await bot.add_cog(AnnouncerCog(bot, config, db))
