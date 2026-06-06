"""SQLite data layer for per-guild configuration."""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

# Default values for guild config
DEFAULTS = {
    "timezone": "Europe/Madrid",
    "announce_mode": "mas_usuarios",
    "channel_id": None,
    "enabled": True,
}


class Database:
    """Async SQLite database for guild configuration.

    Usage:
        db = Database(path)
        await db.connect()
        ...
        await db.close()
    """

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open the database connection and run migrations."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._migrate()
        logger.info("Database connected: %s", self._path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("Database closed")

    async def _migrate(self) -> None:
        """Create tables if they don't exist."""
        assert self._conn is not None
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY,
                timezone TEXT DEFAULT 'Europe/Madrid',
                announce_mode TEXT DEFAULT 'mas_usuarios',
                channel_id INTEGER DEFAULT NULL,
                enabled INTEGER DEFAULT 1
            )
        """)
        await self._conn.commit()
        logger.debug("Database migration complete")

    async def get_guild_config(self, guild_id: int) -> dict:
        """Get configuration for a guild. Returns defaults if not configured.

        Args:
            guild_id: Discord guild (server) ID.

        Returns:
            Dict with keys: timezone, announce_mode, channel_id, enabled.
        """
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT timezone, announce_mode, channel_id, enabled "
            "FROM guild_config WHERE guild_id = ?",
            (guild_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return dict(DEFAULTS)
        return {
            "timezone": row["timezone"],
            "announce_mode": row["announce_mode"],
            "channel_id": row["channel_id"],
            "enabled": bool(row["enabled"]),
        }

    async def set_guild_config(self, guild_id: int, **kwargs) -> None:
        """Update configuration for a guild (upsert).

        Args:
            guild_id: Discord guild (server) ID.
            **kwargs: Config fields to update (timezone, announce_mode, channel_id, enabled).
        """
        assert self._conn is not None
        # Ensure guild exists
        current = await self.get_guild_config(guild_id)
        current.update(kwargs)

        await self._conn.execute(
            """
            INSERT INTO guild_config (guild_id, timezone, announce_mode, channel_id, enabled)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET timezone=excluded.timezone,
                          announce_mode=excluded.announce_mode,
                          channel_id=excluded.channel_id,
                          enabled=excluded.enabled
            """,
            (
                guild_id,
                current["timezone"],
                current["announce_mode"],
                current["channel_id"],
                int(current["enabled"]),
            ),
        )
        await self._conn.commit()
        logger.info("Guild %d config updated: %s", guild_id, kwargs)

    async def get_all_enabled_guilds(self) -> list[int]:
        """Get all guild IDs that have announcements enabled."""
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT guild_id FROM guild_config WHERE enabled = 1"
        )
        rows = await cursor.fetchall()
        return [row["guild_id"] for row in rows]
