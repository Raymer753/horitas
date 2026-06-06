"""Audio playback service — pool selection and playback with timeout."""

from __future__ import annotations

import asyncio
import logging
import random
from pathlib import Path

import discord

logger = logging.getLogger(__name__)

# Supported audio formats
AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav"}

# Maximum time to wait for audio playback before considering it hung
PLAYBACK_TIMEOUT_SECONDS = 60


def get_random_from_pool(pool_dir: Path) -> Path | None:
    """Select a random audio file from a pool directory.

    Args:
        pool_dir: Directory containing audio files.

    Returns:
        Path to a random audio file, or None if pool is empty.
    """
    if not pool_dir.is_dir():
        logger.warning("Audio pool directory does not exist: %s", pool_dir)
        return None

    files = [
        f for f in pool_dir.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    ]

    if not files:
        logger.warning("Audio pool is empty: %s", pool_dir)
        return None

    chosen = random.choice(files)
    logger.debug("Selected from pool %s: %s", pool_dir.name, chosen.name)
    return chosen


async def play_audio(
    voice_client: discord.VoiceClient,
    audio_path: Path,
    *,
    delete_after: bool = False,
    timeout: float = PLAYBACK_TIMEOUT_SECONDS,
) -> bool:
    """Play an audio file on a voice client and wait for completion.

    Args:
        voice_client: Connected Discord voice client.
        audio_path: Path to the audio file.
        delete_after: If True, delete the file after playback.
        timeout: Maximum seconds to wait for playback.

    Returns:
        True if playback completed successfully, False otherwise.
    """
    if not audio_path.exists():
        logger.warning("Audio file not found: %s", audio_path)
        return False

    if not voice_client.is_connected():
        logger.warning("Voice client not connected, cannot play: %s", audio_path.name)
        return False

    done_event = asyncio.Event()
    playback_error: list[Exception | None] = [None]

    def after_playing(error: Exception | None) -> None:
        playback_error[0] = error
        done_event.set()

    try:
        source = discord.FFmpegPCMAudio(str(audio_path))
        voice_client.play(source, after=after_playing)
        logger.debug("Playing: %s", audio_path.name)

        # Wait with timeout to prevent hangs if ffmpeg fails silently
        try:
            await asyncio.wait_for(done_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error("Playback timed out after %ds: %s", timeout, audio_path.name)
            if voice_client.is_playing():
                voice_client.stop()
            return False

        if playback_error[0]:
            logger.error(
                "Playback error for %s: %s", audio_path.name, playback_error[0]
            )
            return False

        logger.debug("Finished playing: %s", audio_path.name)
        return True

    except Exception:
        logger.exception("Unexpected error playing %s", audio_path.name)
        return False

    finally:
        if delete_after:
            try:
                audio_path.unlink(missing_ok=True)
                logger.debug("Deleted temporary file: %s", audio_path.name)
            except OSError:
                logger.exception("Failed to delete: %s", audio_path.name)
