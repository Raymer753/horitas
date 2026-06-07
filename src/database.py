"""SQLite data layer for per-guild configuration and phrases."""

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
    """Async SQLite database for guild configuration and phrases.

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
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS phrases (
                hour_key TEXT PRIMARY KEY,
                phrase TEXT NOT NULL
            )
        """)
        await self._conn.commit()
        logger.debug("Database migration complete")

    # ── Guild Config ─────────────────────────────

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

    # ── Phrases ──────────────────────────────────

    async def get_all_phrases(self) -> dict[str, str]:
        """Get all phrases from the database.

        Returns:
            Dict mapping hour_key (str) to phrase text.
            Keys are "0"-"23" for specific hours, "default" for fallback.
        """
        assert self._conn is not None
        cursor = await self._conn.execute("SELECT hour_key, phrase FROM phrases")
        rows = await cursor.fetchall()
        return {row["hour_key"]: row["phrase"] for row in rows}

    async def get_phrase(self, hour_key: str) -> str | None:
        """Get a single phrase by hour key.

        Args:
            hour_key: "0"-"23" or "default".

        Returns:
            Phrase text, or None if not set.
        """
        assert self._conn is not None
        cursor = await self._conn.execute(
            "SELECT phrase FROM phrases WHERE hour_key = ?",
            (hour_key,),
        )
        row = await cursor.fetchone()
        return row["phrase"] if row else None

    async def set_phrase(self, hour_key: str, phrase: str) -> None:
        """Set or update a phrase for a specific hour (upsert).

        Args:
            hour_key: "0"-"23" or "default".
            phrase: The phrase text (may contain {hora} placeholder).
        """
        assert self._conn is not None
        await self._conn.execute(
            """
            INSERT INTO phrases (hour_key, phrase) VALUES (?, ?)
            ON CONFLICT(hour_key) DO UPDATE SET phrase=excluded.phrase
            """,
            (hour_key, phrase),
        )
        await self._conn.commit()
        logger.info("Phrase for hour '%s' updated: '%s'", hour_key, phrase)

    async def delete_phrase(self, hour_key: str) -> bool:
        """Delete a phrase for a specific hour.

        Args:
            hour_key: "0"-"23" or "default".

        Returns:
            True if a phrase was deleted, False if it didn't exist.
        """
        assert self._conn is not None
        cursor = await self._conn.execute(
            "DELETE FROM phrases WHERE hour_key = ?",
            (hour_key,),
        )
        await self._conn.commit()
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Phrase for hour '%s' deleted", hour_key)
        return deleted

