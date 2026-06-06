"""Tests for src/config.py."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.config import Config


class TestConfig:
    """Tests for Config dataclass."""

    def test_valid_config(self) -> None:
        """Config with a valid token should work."""
        config = Config(discord_token="my-token-123")
        assert config.discord_token == "my-token-123"
        assert config.bot_prefix == "!"
        assert config.default_tz == "Europe/Madrid"
        assert config.log_level == "INFO"

    def test_empty_token_raises(self) -> None:
        """Config without a token should raise ValueError."""
        with pytest.raises(ValueError, match="DISCORD_TOKEN is required"):
            Config(discord_token="")

    def test_invalid_log_level_raises(self) -> None:
        """Config with an invalid log level should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
            Config(discord_token="token", log_level="INVALID")

    def test_valid_log_levels(self) -> None:
        """All standard log levels should be accepted."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = Config(discord_token="token", log_level=level)
            assert config.log_level == level

    def test_default_paths(self) -> None:
        """Default paths should point to /app/."""
        config = Config(discord_token="token")
        assert config.audio_dir == Path("/app/audio")
        assert config.data_dir == Path("/app/data")

    def test_custom_paths(self, tmp_path: Path) -> None:
        """Custom paths should be resolved to absolute."""
        config = Config(
            discord_token="token",
            audio_dir=tmp_path / "audio",
            data_dir=tmp_path / "data",
        )
        assert config.audio_dir.is_absolute()
        assert config.data_dir.is_absolute()

    def test_derived_paths(self, tmp_path: Path) -> None:
        """Derived paths (db, pools, phrases) should be correct."""
        config = Config(
            discord_token="token",
            audio_dir=tmp_path / "audio",
            data_dir=tmp_path / "data",
        )
        assert config.db_path == tmp_path / "data" / "config.db"
        assert config.intro_pool_dir == tmp_path / "audio" / "intro"
        assert config.outro_pool_dir == tmp_path / "audio" / "outro"
        assert config.phrases_path == tmp_path / "audio" / "phrases.json"
        assert config.healthcheck_path == tmp_path / "data" / "healthcheck"

    def test_from_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config.from_env should read from environment variables."""
        monkeypatch.setenv("DISCORD_TOKEN", "env-token")
        monkeypatch.setenv("BOT_PREFIX", "?")
        monkeypatch.setenv("DEFAULT_TZ", "UTC")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("AUDIO_DIR", str(tmp_path / "audio"))
        monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))

        config = Config.from_env()
        assert config.discord_token == "env-token"
        assert config.bot_prefix == "?"
        assert config.default_tz == "UTC"
        assert config.log_level == "DEBUG"

    def test_frozen(self) -> None:
        """Config should be immutable (frozen dataclass)."""
        config = Config(discord_token="token")
        with pytest.raises(AttributeError):
            config.discord_token = "new-token"  # type: ignore[misc]
