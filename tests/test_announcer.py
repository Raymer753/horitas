"""Tests for src/cogs/announcer.py — channel selection and announcement logic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cogs.announcer import AnnouncerCog
from src.config import Config
from src.database import Database


@pytest.fixture
def announcer_cog(config: Config, db) -> AnnouncerCog:
    """Create an AnnouncerCog with mock bot."""
    mock_bot = MagicMock()
    mock_bot.guilds = []
    mock_bot.wait_until_ready = AsyncMock()
    return AnnouncerCog(mock_bot, config, db)


class TestFindTargetChannel:
    """Tests for channel selection logic."""

    def test_most_users_mode(self, announcer_cog: AnnouncerCog, mock_guild: MagicMock) -> None:
        """Should pick the channel with most human users."""
        guild_config = {
            "announce_mode": "mas_usuarios",
            "channel_id": None,
            "enabled": True,
            "timezone": "Europe/Madrid",
        }
        channel = announcer_cog._find_target_channel(mock_guild, guild_config)
        assert channel is not None
        assert channel.name == "General"  # Has 2 humans

    def test_no_users(self, announcer_cog: AnnouncerCog, mock_guild: MagicMock) -> None:
        """Should return None when no users in any channel."""
        # Empty all channels
        for ch in mock_guild.voice_channels:
            ch.members = []

        guild_config = {
            "announce_mode": "mas_usuarios",
            "channel_id": None,
            "enabled": True,
            "timezone": "Europe/Madrid",
        }
        channel = announcer_cog._find_target_channel(mock_guild, guild_config)
        assert channel is None

    def test_ignores_bots(self, announcer_cog: AnnouncerCog, mock_guild: MagicMock) -> None:
        """Should not count bots when finding the best channel."""
        # Make channel with only bots
        for ch in mock_guild.voice_channels:
            for member in ch.members:
                member.bot = True

        guild_config = {
            "announce_mode": "mas_usuarios",
            "channel_id": None,
            "enabled": True,
            "timezone": "Europe/Madrid",
        }
        channel = announcer_cog._find_target_channel(mock_guild, guild_config)
        assert channel is None

    def test_fixed_channel_mode(self, announcer_cog: AnnouncerCog, mock_guild: MagicMock) -> None:
        """Fixed channel mode should return the configured channel."""
        target_channel = MagicMock()
        target_channel.name = "Fixed Channel"
        mock_guild.get_channel = MagicMock(return_value=target_channel)

        # Need to make it look like a VoiceChannel
        import discord
        target_channel.__class__ = discord.VoiceChannel

        guild_config = {
            "announce_mode": "canal_fijo",
            "channel_id": 999,
            "enabled": True,
            "timezone": "Europe/Madrid",
        }
        channel = announcer_cog._find_target_channel(mock_guild, guild_config)
        assert channel is not None
        mock_guild.get_channel.assert_called_with(999)


class TestAnnounceGuild:
    """Tests for the announcement sequence."""

    @pytest.mark.asyncio
    async def test_disabled_guild(self, announcer_cog: AnnouncerCog, mock_guild: MagicMock, db: Database) -> None:
        """Should skip announcement for disabled guilds."""
        await db.set_guild_config(mock_guild.id, enabled=False)
        result = await announcer_cog._announce_guild(mock_guild)
        assert "desactivados" in result.lower()

    @pytest.mark.asyncio
    async def test_already_connected(self, announcer_cog: AnnouncerCog, mock_guild: MagicMock) -> None:
        """Should skip if already connected to voice in this guild."""
        mock_guild.voice_client = MagicMock()
        mock_guild.voice_client.is_connected.return_value = True
        result = await announcer_cog._announce_guild(mock_guild)
        assert "ya conectado" in result.lower()

    @pytest.mark.asyncio
    async def test_no_users_in_voice(self, announcer_cog: AnnouncerCog, mock_guild: MagicMock) -> None:
        """Should report no users when channels are empty."""
        for ch in mock_guild.voice_channels:
            ch.members = []
        result = await announcer_cog._announce_guild(mock_guild)
        assert "no hay usuarios" in result.lower()
