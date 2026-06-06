"""Entry point for Horitas v2 — load config, create bot, run."""

from __future__ import annotations

import logging
import sys

from src.bot import HoritasBot
from src.config import Config
from src.database import Database
from src.utils.logging import setup_logging
from src.utils.paths import ensure_dir


def main() -> None:
    """Application entry point."""
    # Load configuration from environment
    try:
        config = Config.from_env()
    except ValueError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Setup structured logging
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting Horitas v2...")

    # Ensure required directories exist
    ensure_dir(config.data_dir)
    ensure_dir(config.audio_dir / "intro")
    ensure_dir(config.audio_dir / "outro")

    # Create database and bot
    db = Database(config.db_path)
    bot = HoritasBot(config, db)

    # Run the bot
    try:
        bot.run(
            config.discord_token,
            log_handler=None,  # We handle logging ourselves
        )
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt — shutting down")
    except Exception:
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
