"""Tests for src/services/tts.py."""

from __future__ import annotations

import pytest

from src.services.tts import format_hour_text


class TestFormatHourText:
    """Tests for hour formatting in Spanish."""

    def test_hour_1(self) -> None:
        """Hour 1 should use 'la' (singular)."""
        assert format_hour_text(1) == "la 1"

    def test_hour_other(self) -> None:
        """Other hours should use 'las' (plural)."""
        assert format_hour_text(3) == "las 3"
        assert format_hour_text(12) == "las 12"

    def test_all_hours(self) -> None:
        """All hours 1-12 should produce valid text."""
        for h in range(1, 13):
            result = format_hour_text(h)
            assert isinstance(result, str)
            assert str(h) in result
