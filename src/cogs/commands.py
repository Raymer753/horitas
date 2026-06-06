"""Commands cog — hybrid slash/prefix commands for bot control."""

from __future__ import annotations

import logging
import time
from datetime import datetime

import discord
import pytz
from discord import app_commands
from discord.ext import commands

from src.config import Config
from src.database import Database
from src.services import scheduler

logger = logging.getLogger(__name__)


class CommandsCog(commands.Cog, name="Commands"):
    """Cog providing slash and prefix commands for bot management."""

    def __init__(self, bot: commands.Bot, config: Config, db: Database) -> None:
        self.bot = bot
        self.config = config
        self.db = db
        self._start_time = time.monotonic()

    @commands.hybrid_command(name="forzar", description="Fuerza un anuncio inmediato")
    @commands.is_owner()
    async def force_announce(self, ctx: commands.Context) -> None:
        """Force an immediate announcement in the current guild (owner only)."""
        if not ctx.guild:
            await ctx.send("❌ Este comando solo funciona en un servidor.", ephemeral=True)
            return

        await ctx.defer()
        logger.info("Forced announcement by %s in guild '%s'", ctx.author.name, ctx.guild.name)

        announcer = self.bot.get_cog("Announcer")
        if not announcer:
            await ctx.send("❌ El cog de anuncios no está cargado.", ephemeral=True)
            return

        result = await announcer.announce_for_guild(ctx.guild)  # type: ignore[union-attr]
        await ctx.send(f"✅ {result}")

    @commands.hybrid_command(name="estado", description="Muestra el estado del bot")
    async def status(self, ctx: commands.Context) -> None:
        """Show bot status: uptime, guilds, next announcement."""
        uptime_seconds = time.monotonic() - self._start_time
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)

        next_delay = scheduler.seconds_until_next_hour(self.config.default_tz)
        next_mins = int(next_delay // 60)

        embed = discord.Embed(
            title="🕐 Estado de Horitas",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="⏱️ Uptime",
            value=f"{hours}h {minutes}m {seconds}s",
            inline=True,
        )
        embed.add_field(
            name="🌐 Servidores",
            value=str(len(self.bot.guilds)),
            inline=True,
        )
        embed.add_field(
            name="⏰ Próximo anuncio",
            value=f"~{next_mins} minutos",
            inline=True,
        )
        embed.add_field(
            name="🕑 Timezone por defecto",
            value=self.config.default_tz,
            inline=True,
        )

        if ctx.guild:
            guild_config = await self.db.get_guild_config(ctx.guild.id)
            embed.add_field(
                name="⚙️ Config de este servidor",
                value=(
                    f"Timezone: `{guild_config['timezone']}`\n"
                    f"Modo: `{guild_config['announce_mode']}`\n"
                    f"Activado: {'✅' if guild_config['enabled'] else '❌'}"
                ),
                inline=False,
            )

        embed.set_footer(text="Horitas v2")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="sync", description="Sincroniza los slash commands")
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context) -> None:
        """Manually sync slash commands with Discord (owner only)."""
        await ctx.defer(ephemeral=True)
        synced = await self.bot.tree.sync()
        logger.info("Synced %d commands by %s", len(synced), ctx.author.name)
        await ctx.send(f"✅ Sincronizados {len(synced)} comandos.", ephemeral=True)

    # ── Config subcommands ───────────────────────────────────

    @commands.hybrid_group(name="config", description="Configuración del servidor")
    @commands.has_permissions(administrator=True)
    async def config_group(self, ctx: commands.Context) -> None:
        """Server configuration command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @config_group.command(name="timezone", description="Configura la timezone del servidor")
    @app_commands.describe(zona="Timezone IANA, por ejemplo: Europe/Madrid, America/New_York")
    async def config_timezone(self, ctx: commands.Context, zona: str) -> None:
        """Set the timezone for this server."""
        if not ctx.guild:
            await ctx.send("❌ Solo funciona en un servidor.", ephemeral=True)
            return

        # Validate timezone
        try:
            pytz.timezone(zona)
        except pytz.UnknownTimeZoneError:
            await ctx.send(
                f"❌ Timezone desconocida: `{zona}`\n"
                f"Ejemplos válidos: `Europe/Madrid`, `America/New_York`, `UTC`",
                ephemeral=True,
            )
            return

        await self.db.set_guild_config(ctx.guild.id, timezone=zona)
        await ctx.send(f"✅ Timezone del servidor actualizada a `{zona}`.")
        logger.info("Guild %d timezone set to %s by %s", ctx.guild.id, zona, ctx.author.name)

    @config_group.command(name="canal", description="Configura el modo de anuncio")
    @app_commands.describe(modo="Modo de canal: mas_usuarios o canal_fijo")
    @app_commands.choices(modo=[
        app_commands.Choice(name="Canal con más usuarios", value="mas_usuarios"),
        app_commands.Choice(name="Canal fijo", value="canal_fijo"),
    ])
    async def config_channel(self, ctx: commands.Context, modo: str) -> None:
        """Set the announcement channel mode for this server."""
        if not ctx.guild:
            await ctx.send("❌ Solo funciona en un servidor.", ephemeral=True)
            return

        update = {"announce_mode": modo}

        if modo == "canal_fijo":
            # Use the voice channel the user is currently in
            if not isinstance(ctx.author, discord.Member) or not ctx.author.voice:
                await ctx.send(
                    "❌ Para usar modo `canal_fijo`, "
                    "conectate a un canal de voz primero.",
                    ephemeral=True,
                )
                return
            update["channel_id"] = ctx.author.voice.channel.id
            await self.db.set_guild_config(ctx.guild.id, **update)
            await ctx.send(
                f"✅ Modo cambiado a `canal_fijo`: "
                f"anunciaré en **{ctx.author.voice.channel.name}**."
            )
        else:
            update["channel_id"] = None
            await self.db.set_guild_config(ctx.guild.id, **update)
            await ctx.send("✅ Modo cambiado a `mas_usuarios`: anunciaré donde haya más gente.")

        logger.info(
            "Guild %d channel mode set to %s by %s",
            ctx.guild.id, modo, ctx.author.name,
        )

    @config_group.command(name="activar", description="Activa/desactiva los anuncios")
    @app_commands.describe(estado="Activar o desactivar anuncios")
    @app_commands.choices(estado=[
        app_commands.Choice(name="Activar", value="on"),
        app_commands.Choice(name="Desactivar", value="off"),
    ])
    async def config_toggle(self, ctx: commands.Context, estado: str) -> None:
        """Enable or disable announcements for this server."""
        if not ctx.guild:
            await ctx.send("❌ Solo funciona en un servidor.", ephemeral=True)
            return

        enabled = estado == "on"
        await self.db.set_guild_config(ctx.guild.id, enabled=enabled)
        emoji = "✅" if enabled else "🔇"
        word = "activados" if enabled else "desactivados"
        await ctx.send(f"{emoji} Anuncios {word} en este servidor.")
        logger.info(
            "Guild %d announcements %s by %s",
            ctx.guild.id, word, ctx.author.name,
        )


async def setup(bot: commands.Bot) -> None:
    """Setup function called by bot.load_extension()."""
    config: Config = bot.config  # type: ignore[attr-defined]
    db: Database = bot.db  # type: ignore[attr-defined]
    await bot.add_cog(CommandsCog(bot, config, db))
