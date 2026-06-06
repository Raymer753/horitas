"""Tests for src/services/audio.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.audio import get_random_from_pool, play_audio


class TestGetRandomFromPool:
    """Tests for pool selection."""

    def test_empty_pool(self, tmp_path: Path) -> None:
        """Empty pool should return None."""
        pool = tmp_path / "empty_pool"
        pool.mkdir()
        assert get_random_from_pool(pool) is None

    def test_nonexistent_pool(self, tmp_path: Path) -> None:
        """Non-existent pool dir should return None."""
        assert get_random_from_pool(tmp_path / "nonexistent") is None

    def test_pool_with_mp3(self, tmp_path: Path) -> None:
        """Pool with mp3 files should return one."""
        pool = tmp_path / "pool"
        pool.mkdir()
        (pool / "test.mp3").write_bytes(b"fake audio")
        result = get_random_from_pool(pool)
        assert result is not None
        assert result.suffix == ".mp3"

    def test_pool_with_multiple_formats(self, tmp_path: Path) -> None:
        """Pool should accept mp3, ogg, and wav."""
        pool = tmp_path / "pool"
        pool.mkdir()
        for ext in [".mp3", ".ogg", ".wav"]:
            (pool / f"test{ext}").write_bytes(b"fake audio")

        results = set()
        for _ in range(50):
            result = get_random_from_pool(pool)
            assert result is not None
            results.add(result.name)
        # Should have picked at least 2 different files in 50 tries
        assert len(results) >= 2

    def test_pool_ignores_non_audio(self, tmp_path: Path) -> None:
        """Pool should ignore non-audio files."""
        pool = tmp_path / "pool"
        pool.mkdir()
        (pool / ".gitkeep").touch()
        (pool / "readme.txt").write_text("not audio")
        assert get_random_from_pool(pool) is None

    def test_pool_with_gitkeep_and_audio(self, tmp_path: Path) -> None:
        """Pool should find audio even with .gitkeep present."""
        pool = tmp_path / "pool"
        pool.mkdir()
        (pool / ".gitkeep").touch()
        (pool / "bells.mp3").write_bytes(b"fake audio")
        result = get_random_from_pool(pool)
        assert result is not None
        assert result.name == "bells.mp3"


class TestPlayAudio:
    """Tests for audio playback."""

    @pytest.mark.asyncio
    async def test_missing_file(self, mock_voice_client: MagicMock, tmp_path: Path) -> None:
        """Playing a missing file should return False."""
        result = await play_audio(
            mock_voice_client, tmp_path / "nonexistent.mp3"
        )
        assert result is False
        mock_voice_client.play.assert_not_called()

    @pytest.mark.asyncio
    async def test_disconnected_client(self, mock_voice_client: MagicMock, tmp_path: Path) -> None:
        """Playing on a disconnected client should return False."""
        mock_voice_client.is_connected.return_value = False
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")
        result = await play_audio(mock_voice_client, audio_file)
        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.audio.discord.FFmpegPCMAudio")
    async def test_successful_playback(
        self, mock_ffmpeg: MagicMock, mock_voice_client: MagicMock, tmp_path: Path
    ) -> None:
        """Successful playback should return True."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")
        result = await play_audio(mock_voice_client, audio_file)
        assert result is True
        mock_voice_client.play.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.services.audio.discord.FFmpegPCMAudio")
    async def test_delete_after(
        self, mock_ffmpeg: MagicMock, mock_voice_client: MagicMock, tmp_path: Path
    ) -> None:
        """delete_after=True should remove the file after playback."""
        audio_file = tmp_path / "temp.mp3"
        audio_file.write_bytes(b"fake audio")
        assert audio_file.exists()

        await play_audio(mock_voice_client, audio_file, delete_after=True)
        assert not audio_file.exists()

