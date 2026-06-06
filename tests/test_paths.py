"""Tests for src/utils/paths.py."""

from __future__ import annotations

from pathlib import Path

from src.utils.paths import ensure_dir


class TestEnsureDir:
    """Tests for directory creation utility."""

    def test_creates_dir(self, tmp_path: Path) -> None:
        """Should create a directory that doesn't exist."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        assert not new_dir.exists()
        result = ensure_dir(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_existing_dir(self, tmp_path: Path) -> None:
        """Should not fail on existing directory."""
        existing = tmp_path / "existing"
        existing.mkdir()
        result = ensure_dir(existing)
        assert existing.exists()
        assert result == existing

    def test_returns_path(self, tmp_path: Path) -> None:
        """Should return the same path passed in."""
        target = tmp_path / "test"
        result = ensure_dir(target)
        assert result == target
