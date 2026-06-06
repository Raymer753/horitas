"""Tests for src/services/phrases.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.services.phrases import DEFAULT_PHRASE, get_phrase


class TestGetPhrase:
    """Tests for phrase loading and formatting."""

    def test_specific_hour(self, tmp_path: Path) -> None:
        """Should return the phrase for a specific hour."""
        phrases_file = tmp_path / "phrases.json"
        phrases_file.write_text(json.dumps({
            "12": "¡Mediodía! Son {hora}",
            "default": "Son {hora} en punto",
        }))
        result = get_phrase(phrases_file, 12, "las 12")
        assert result == "¡Mediodía! Son las 12"

    def test_default_fallback(self, tmp_path: Path) -> None:
        """Should use 'default' key when hour is not defined."""
        phrases_file = tmp_path / "phrases.json"
        phrases_file.write_text(json.dumps({
            "default": "Son {hora} en punto",
        }))
        result = get_phrase(phrases_file, 5, "las 5")
        assert result == "Son las 5 en punto"

    def test_missing_file(self, tmp_path: Path) -> None:
        """Should use hardcoded default when file doesn't exist."""
        result = get_phrase(tmp_path / "nonexistent.json", 3, "las 3")
        assert result == "Son las 3 en punto"

    def test_invalid_json(self, tmp_path: Path) -> None:
        """Should use default when JSON is invalid."""
        phrases_file = tmp_path / "phrases.json"
        phrases_file.write_text("{invalid json")
        result = get_phrase(phrases_file, 3, "las 3")
        assert result == "Son las 3 en punto"

    def test_json_not_dict(self, tmp_path: Path) -> None:
        """Should use default when JSON is not a dict."""
        phrases_file = tmp_path / "phrases.json"
        phrases_file.write_text(json.dumps(["not", "a", "dict"]))
        result = get_phrase(phrases_file, 3, "las 3")
        assert result == "Son las 3 en punto"

    def test_hora_variable_replacement(self, tmp_path: Path) -> None:
        """Should replace {hora} in the phrase."""
        phrases_file = tmp_path / "phrases.json"
        phrases_file.write_text(json.dumps({
            "1": "Es {hora} de la mañana",
        }))
        result = get_phrase(phrases_file, 1, "la 1")
        assert result == "Es la 1 de la mañana"

    def test_phrase_without_variable(self, tmp_path: Path) -> None:
        """Phrases without {hora} should work fine."""
        phrases_file = tmp_path / "phrases.json"
        phrases_file.write_text(json.dumps({
            "0": "Medianoche",
        }))
        result = get_phrase(phrases_file, 0, "las 12")
        assert result == "Medianoche"

    def test_hot_reload(self, tmp_path: Path) -> None:
        """Changes to file should be reflected on next call."""
        phrases_file = tmp_path / "phrases.json"
        phrases_file.write_text(json.dumps({"3": "Versión 1: {hora}"}))
        result1 = get_phrase(phrases_file, 3, "las 3")
        assert "Versión 1" in result1

        phrases_file.write_text(json.dumps({"3": "Versión 2: {hora}"}))
        result2 = get_phrase(phrases_file, 3, "las 3")
        assert "Versión 2" in result2
