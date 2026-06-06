"""TTS generation service — creates audio from text using gTTS."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


async def generate_tts(
    text: str,
    output_dir: Path,
    *,
    lang: str = "es",
    guild_id: int | None = None,
) -> Path | None:
    """Generate a TTS audio file from text using gTTS.

    Runs gTTS in a thread to avoid blocking the event loop.
    Returns None if generation fails (e.g., no internet).

    Args:
        text: Text to convert to speech.
        output_dir: Directory to save the temporary audio file.
        lang: Language code for gTTS.
        guild_id: Optional guild ID for unique temp file naming.

    Returns:
        Path to the generated audio file, or None on failure.
    """
    try:
        output_path = await asyncio.to_thread(
            _generate_tts_sync, text, output_dir, lang, guild_id
        )
        logger.info("TTS generated: '%s' → %s", text, output_path.name)
        return output_path
    except Exception:
        logger.exception("TTS generation failed for text: '%s'", text)
        return None


def _generate_tts_sync(
    text: str,
    output_dir: Path,
    lang: str,
    guild_id: int | None,
) -> Path:
    """Synchronous TTS generation (runs in thread)."""
    from gtts import gTTS

    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a unique temp file per guild to avoid collisions
    suffix = f"_{guild_id}" if guild_id else ""
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=f"horitas_tts{suffix}_",
        suffix=".mp3",
        dir=str(output_dir),
    )
    # Close the file descriptor since gTTS will write to it
    import os
    os.close(fd)

    tmp_path = Path(tmp_path_str)
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(str(tmp_path))
    return tmp_path


def format_hour_text(hour: int) -> str:
    """Format the hour as Spanish text for TTS.

    Args:
        hour: Hour in 12-hour format (1-12).

    Returns:
        Formatted string, e.g. "1" → "la 1", "3" → "las 3".
    """
    if hour == 1:
        return "la 1"
    return f"las {hour}"
