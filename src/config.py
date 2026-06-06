"""Configuration management — reads from environment variables with validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Immutable application configuration loaded from environment variables."""

    discord_token: str
    bot_prefix: str = "!"
    default_tz: str = "Europe/Madrid"
    log_level: str = "INFO"
    audio_dir: Path = field(default_factory=lambda: Path("/app/audio"))
    data_dir: Path = field(default_factory=lambda: Path("/app/data"))

    def __post_init__(self) -> None:
        if not self.discord_token:
            raise ValueError(
                "DISCORD_TOKEN is required. "
                "Set it in your .env file or as an environment variable."
            )
        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid LOG_LEVEL '{self.log_level}'. "
                f"Must be one of: {', '.join(sorted(valid_levels))}"
            )

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> Config:
        """Create Config from environment variables, optionally loading a .env file."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        audio_dir = os.getenv("AUDIO_DIR", "/app/audio")
        data_dir = os.getenv("DATA_DIR", "/app/data")

        return cls(
            discord_token=os.getenv("DISCORD_TOKEN", ""),
            bot_prefix=os.getenv("BOT_PREFIX", "!"),
            default_tz=os.getenv("DEFAULT_TZ", "Europe/Madrid"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            audio_dir=Path(audio_dir).resolve(),
            data_dir=Path(data_dir).resolve(),
        )

    @property
    def db_path(self) -> Path:
        """Path to the SQLite database file."""
        return self.data_dir / "config.db"

    @property
    def intro_pool_dir(self) -> Path:
        """Path to the intro audio pool directory."""
        return self.audio_dir / "intro"

    @property
    def outro_pool_dir(self) -> Path:
        """Path to the outro audio pool directory."""
        return self.audio_dir / "outro"

    @property
    def phrases_path(self) -> Path:
        """Path to the phrases JSON file."""
        return self.audio_dir / "phrases.json"

    @property
    def healthcheck_path(self) -> Path:
        """Path to the healthcheck timestamp file."""
        return self.data_dir / "healthcheck"
