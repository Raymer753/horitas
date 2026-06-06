"""Dynamic phrase service — loads per-hour phrases from JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default phrase when no custom phrase is defined for an hour
DEFAULT_PHRASE = "Son las {hora} en punto"


def get_phrase(phrases_path: Path, hour_24: int, hour_text: str) -> str:
    """Get the announcement phrase for a specific hour.

    Loads phrases from JSON on each call (hot-reload support).
    Falls back to DEFAULT_PHRASE if the file is missing or the hour has no entry.

    Args:
        phrases_path: Path to the phrases.json file.
        hour_24: Hour in 24-hour format (0-23), used as JSON key.
        hour_text: Formatted hour text (e.g. "las 3") for {hora} replacement.

    Returns:
        The phrase with {hora} replaced by the actual hour text.
    """
    phrases = _load_phrases(phrases_path)
    hour_key = str(hour_24)

    # Try specific hour, then fallback to "default" key, then hardcoded default
    raw_phrase = phrases.get(hour_key, phrases.get("default", DEFAULT_PHRASE))

    try:
        return raw_phrase.format(hora=hour_text)
    except (KeyError, ValueError):
        logger.warning("Invalid placeholder in phrase for hour %d: '%s'", hour_24, raw_phrase)
        return DEFAULT_PHRASE.format(hora=hour_text)


def _load_phrases(phrases_path: Path) -> dict[str, str]:
    """Load phrases from a JSON file. Returns empty dict on failure."""
    if not phrases_path.exists():
        logger.debug("Phrases file not found: %s — using defaults", phrases_path)
        return {}

    try:
        with open(phrases_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning("phrases.json is not a dict — using defaults")
            return {}
        return data
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in %s — using defaults", phrases_path)
        return {}
    except OSError:
        logger.exception("Error reading %s", phrases_path)
        return {}
