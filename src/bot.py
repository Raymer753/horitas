"""Bot class — discord.py Bot subclass with auto cog loading."""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from src.config import Config
from src.database import Database

logger = logging.getLogger(__name__)

# Cogs to load automatically on startup
EXTENSIONS = [
    "src.cogs.announcer",
    "src.cogs.commands",
    "src.cogs.health",
]


class HoritasBot(commands.Bot):
    """Custom Bot subclass that manages config, database, and cog loading."""

    def __init__(self, config: Config, db: Database) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        intents.message_content = True

        super().__init__(
            command_prefix=config.bot_prefix,
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
        )

        # Attach config and db to the bot so cogs can access them
        self.config: Config = config  # type: ignore[assignment]
        self.db: Database = db

    async def setup_hook(self) -> None:
        """Called once when the bot starts. Loads all cogs."""
        await self.db.connect()

        for extension in EXTENSIONS:
            try:
                await self.load_extension(extension)
                logger.info("Loaded extension: %s", extension)
            except Exception:
                logger.exception("Failed to load extension: %s", extension)

    async def on_ready(self) -> None:
        """Called when the bot has connected to Discord."""
        logger.info(
            "Bot connected as %s (ID: %d) — %d guild(s)",
            self.user.name if self.user else "Unknown",
            self.user.id if self.user else 0,
            len(self.guilds),
        )

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """Global error handler for commands."""
        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ Solo el propietario del bot puede usar este comando.", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ No tienes permisos para usar este comando.", ephemeral=True)
        elif isinstance(error, commands.CommandNotFound):
            pass  # Silently ignore unknown commands
        else:
            logger.exception("Unhandled command error: %s", error)
            await ctx.send("❌ Ha ocurrido un error inesperado.", ephemeral=True)

    async def close(self) -> None:
        """Cleanup on shutdown."""
        await self.db.close()
        await super().close()
        logger.info("Bot shut down gracefully")
