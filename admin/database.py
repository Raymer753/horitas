"""Synchronous SQLite database access for the Flask admin panel.

Shares the same database file as the bot (config.db).
Uses stdlib sqlite3 since Flask is synchronous.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


class AdminDatabase:
    """Synchronous SQLite wrapper for the admin panel."""

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Open database connection with WAL mode for concurrent reads."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # WAL mode allows bot to read while admin writes
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._ensure_tables()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _ensure_tables(self) -> None:
        """Ensure required tables exist (same schema as bot)."""
        assert self._conn is not None
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY,
                timezone TEXT DEFAULT 'Europe/Madrid',
                announce_mode TEXT DEFAULT 'mas_usuarios',
                channel_id INTEGER DEFAULT NULL,
                enabled INTEGER DEFAULT 1
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS phrases (
                hour_key TEXT PRIMARY KEY,
                phrase TEXT NOT NULL
            )
        """)
        self._conn.commit()

    # ── Phrases ──────────────────────────────────

    def get_all_phrases(self) -> dict[str, str]:
        """Get all phrases."""
        assert self._conn is not None
        cursor = self._conn.execute("SELECT hour_key, phrase FROM phrases ORDER BY hour_key")
        return {row["hour_key"]: row["phrase"] for row in cursor.fetchall()}

    def set_phrase(self, hour_key: str, phrase: str) -> None:
        """Set or update a phrase."""
        assert self._conn is not None
        self._conn.execute(
            """
            INSERT INTO phrases (hour_key, phrase) VALUES (?, ?)
            ON CONFLICT(hour_key) DO UPDATE SET phrase=excluded.phrase
            """,
            (hour_key, phrase),
        )
        self._conn.commit()

    def delete_phrase(self, hour_key: str) -> bool:
        """Delete a phrase. Returns True if deleted."""
        assert self._conn is not None
        cursor = self._conn.execute(
            "DELETE FROM phrases WHERE hour_key = ?", (hour_key,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # ── Guild Config ─────────────────────────────

    def get_all_guilds(self) -> list[dict]:
        """Get all guild configurations."""
        assert self._conn is not None
        cursor = self._conn.execute(
            "SELECT guild_id, timezone, announce_mode, channel_id, enabled FROM guild_config"
        )
        return [
            {
                "guild_id": row["guild_id"],
                "timezone": row["timezone"],
                "announce_mode": row["announce_mode"],
                "channel_id": row["channel_id"],
                "enabled": bool(row["enabled"]),
            }
            for row in cursor.fetchall()
        ]

    def update_guild_config(self, guild_id: int, **kwargs) -> None:
        """Update specific fields of a guild's config."""
        assert self._conn is not None
        allowed = {"timezone", "announce_mode", "channel_id", "enabled"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return

        # Convert enabled to int for SQLite
        if "enabled" in updates:
            updates["enabled"] = int(updates["enabled"])

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [guild_id]
        self._conn.execute(
            f"UPDATE guild_config SET {set_clause} WHERE guild_id = ?",
            values,
        )
        self._conn.commit()
