"""Tests for src/database.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.database import DEFAULTS, Database


class TestDatabase:
    """Tests for the async SQLite database."""

    @pytest.mark.asyncio
    async def test_connect_creates_db(self, tmp_path: Path) -> None:
        """Should create the database file on connect."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)
        await db.connect()
        assert db_path.exists()
        await db.close()

    @pytest.mark.asyncio
    async def test_default_config(self, tmp_path: Path) -> None:
        """Should return defaults for unconfigured guild."""
        db = Database(tmp_path / "test.db")
        await db.connect()
        config = await db.get_guild_config(999)
        assert config["timezone"] == DEFAULTS["timezone"]
        assert config["announce_mode"] == DEFAULTS["announce_mode"]
        assert config["channel_id"] is None
        assert config["enabled"] is True
        await db.close()

    @pytest.mark.asyncio
    async def test_set_and_get_config(self, tmp_path: Path) -> None:
        """Should persist and retrieve guild config."""
        db = Database(tmp_path / "test.db")
        await db.connect()

        await db.set_guild_config(123, timezone="UTC", announce_mode="canal_fijo")
        config = await db.get_guild_config(123)
        assert config["timezone"] == "UTC"
        assert config["announce_mode"] == "canal_fijo"

        await db.close()

    @pytest.mark.asyncio
    async def test_upsert(self, tmp_path: Path) -> None:
        """Should update existing config on second set."""
        db = Database(tmp_path / "test.db")
        await db.connect()

        await db.set_guild_config(123, timezone="UTC")
        await db.set_guild_config(123, timezone="America/New_York")
        config = await db.get_guild_config(123)
        assert config["timezone"] == "America/New_York"

        await db.close()

    @pytest.mark.asyncio
    async def test_partial_update(self, tmp_path: Path) -> None:
        """Should update only specified fields, keeping others."""
        db = Database(tmp_path / "test.db")
        await db.connect()

        await db.set_guild_config(123, timezone="UTC", announce_mode="canal_fijo")
        await db.set_guild_config(123, timezone="Europe/London")
        config = await db.get_guild_config(123)
        assert config["timezone"] == "Europe/London"
        assert config["announce_mode"] == "canal_fijo"  # unchanged

        await db.close()

    @pytest.mark.asyncio
    async def test_get_all_enabled_guilds(self, tmp_path: Path) -> None:
        """Should return only enabled guild IDs."""
        db = Database(tmp_path / "test.db")
        await db.connect()

        await db.set_guild_config(1, enabled=True)
        await db.set_guild_config(2, enabled=False)
        await db.set_guild_config(3, enabled=True)

        enabled = await db.get_all_enabled_guilds()
        assert 1 in enabled
        assert 2 not in enabled
        assert 3 in enabled

        await db.close()

    @pytest.mark.asyncio
    async def test_close_idempotent(self, tmp_path: Path) -> None:
        """Should not crash when closing twice."""
        db = Database(tmp_path / "test.db")
        await db.connect()
        await db.close()
        await db.close()  # Should not raise
