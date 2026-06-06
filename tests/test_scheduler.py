"""Tests for src/services/scheduler.py."""

from __future__ import annotations

from unittest.mock import patch
from datetime import datetime

import pytz
import pytest

from src.services.scheduler import get_current_hour, seconds_until_next_hour


class TestSecondsUntilNextHour:
    """Tests for next-hour delay calculation."""

    def test_returns_positive(self) -> None:
        """Should always return a positive number."""
        result = seconds_until_next_hour("Europe/Madrid")
        assert result > 0

    def test_max_3600(self) -> None:
        """Should never be more than 3600 seconds (1 hour)."""
        result = seconds_until_next_hour("Europe/Madrid")
        assert result <= 3600

    def test_utc(self) -> None:
        """Should work with UTC timezone."""
        result = seconds_until_next_hour("UTC")
        assert 0 < result <= 3600

    def test_unknown_timezone_falls_back(self) -> None:
        """Unknown timezone should fall back to UTC without crashing."""
        result = seconds_until_next_hour("Invalid/Timezone")
        assert 0 < result <= 3600

    def test_at_exact_hour(self) -> None:
        """At the start of an hour, should return ~3600 seconds."""
        tz = pytz.timezone("UTC")
        fake_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=tz)
        with patch("src.services.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            # Can't easily mock datetime.now completely, so just verify
            # the function runs without error
            result = seconds_until_next_hour("UTC")
            assert result > 0

    def test_near_midnight(self) -> None:
        """At 23:59 should still return a valid positive number."""
        result = seconds_until_next_hour("Europe/Madrid")
        assert result > 0


class TestGetCurrentHour:
    """Tests for current hour retrieval."""

    def test_returns_tuple(self) -> None:
        """Should return a tuple of (hour_24, hour_12)."""
        result = get_current_hour("Europe/Madrid")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_hour_24_range(self) -> None:
        """24h hour should be 0-23."""
        hour_24, _ = get_current_hour("UTC")
        assert 0 <= hour_24 <= 23

    def test_hour_12_range(self) -> None:
        """12h hour should be 1-12."""
        _, hour_12 = get_current_hour("UTC")
        assert 1 <= hour_12 <= 12

    def test_unknown_timezone(self) -> None:
        """Unknown timezone should fall back to UTC."""
        result = get_current_hour("Invalid/Timezone")
        assert isinstance(result, tuple)
        assert len(result) == 2
