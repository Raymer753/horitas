"""Health cog — file-based healthcheck for Docker monitoring."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from discord.ext import commands, tasks

from src.config import Config

logger = logging.getLogger(__name__)


class HealthCog(commands.Cog, name="Health"):
    """Cog that writes a heartbeat timestamp for Docker HEALTHCHECK."""

    def __init__(self, bot: commands.Bot, config: Config) -> None:
        self.bot = bot
        self.config = config
        self._healthcheck_path: Path = config.healthcheck_path

    async def cog_load(self) -> None:
        """Start the heartbeat loop when the cog is loaded."""
        self.heartbeat_loop.start()
        logger.info("Health heartbeat started → %s", self._healthcheck_path)

    async def cog_unload(self) -> None:
        """Stop the heartbeat loop when the cog is unloaded."""
        self.heartbeat_loop.cancel()

    @tasks.loop(seconds=30)
    async def heartbeat_loop(self) -> None:
        """Write current timestamp to the healthcheck file every 30 seconds."""
        try:
            self._healthcheck_path.parent.mkdir(parents=True, exist_ok=True)
            self._healthcheck_path.write_text(str(time.time()))
        except OSError:
            logger.exception("Failed to write healthcheck file")

    @heartbeat_loop.before_loop
    async def before_heartbeat(self) -> None:
        """Wait until the bot is ready before starting heartbeats."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """Setup function called by bot.load_extension()."""
    config: Config = bot.config  # type: ignore[attr-defined]
    await bot.add_cog(HealthCog(bot, config))
