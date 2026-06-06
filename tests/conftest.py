"""Shared test fixtures and mocks."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import Config
from src.database import Database


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def audio_dir(tmp_path: Path) -> Path:
    """Create a temporary audio directory structure."""
    audio = tmp_path / "audio"
    intro = audio / "intro"
    outro = audio / "outro"
    intro.mkdir(parents=True)
    outro.mkdir(parents=True)
    return audio


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory."""
    data = tmp_path / "data"
    data.mkdir(parents=True)
    return data


@pytest.fixture
def config(audio_dir: Path, data_dir: Path) -> Config:
    """Create a test Config with temporary directories."""
    return Config(
        discord_token="test-token-123",
        bot_prefix="!",
        default_tz="Europe/Madrid",
        log_level="DEBUG",
        audio_dir=audio_dir,
        data_dir=data_dir,
    )


@pytest.fixture
async def db(data_dir: Path) -> Database:
    """Create and connect a test database."""
    database = Database(data_dir / "test.db")
    await database.connect()
    yield database
    await database.close()


@pytest.fixture
def mock_voice_client() -> MagicMock:
    """Create a mock Discord VoiceClient."""
    vc = MagicMock()
    vc.is_connected.return_value = True
    vc.is_playing.return_value = False
    vc.disconnect = AsyncMock()

    def play_side_effect(source, *, after=None):
        """Simulate playback completing immediately."""
        if after:
            after(None)

    vc.play = MagicMock(side_effect=play_side_effect)
    return vc


@pytest.fixture
def mock_guild() -> MagicMock:
    """Create a mock Discord Guild."""
    guild = MagicMock()
    guild.id = 123456789
    guild.name = "Test Guild"
    guild.voice_client = None

    # Create mock voice channels
    channel1 = MagicMock()
    channel1.name = "General"
    channel1.id = 111
    member1 = MagicMock()
    member1.bot = False
    member2 = MagicMock()
    member2.bot = False
    bot_member = MagicMock()
    bot_member.bot = True
    channel1.members = [member1, member2, bot_member]

    channel2 = MagicMock()
    channel2.name = "AFK"
    channel2.id = 222
    channel2.members = []

    guild.voice_channels = [channel1, channel2]
    return guild
