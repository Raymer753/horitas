"""Tests for src/utils/logging.py."""

from __future__ import annotations

import logging

from src.utils.logging import setup_logging


class TestSetupLogging:
    """Tests for logging configuration."""

    def test_sets_level(self) -> None:
        """Should set the root logger to the specified level."""
        setup_logging("DEBUG")
        assert logging.getLogger().level == logging.DEBUG

    def test_default_info(self) -> None:
        """INFO should be the default level."""
        setup_logging("INFO")
        assert logging.getLogger().level == logging.INFO

    def test_case_insensitive(self) -> None:
        """Should handle lowercase level strings."""
        setup_logging("warning")
        assert logging.getLogger().level == logging.WARNING

    def test_discord_loggers_quieted(self) -> None:
        """Third-party loggers should be set to WARNING."""
        setup_logging("DEBUG")
        assert logging.getLogger("discord").level == logging.WARNING
        assert logging.getLogger("discord.http").level == logging.WARNING
        assert logging.getLogger("asyncio").level == logging.WARNING
