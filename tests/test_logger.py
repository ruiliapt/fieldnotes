"""Tests for logger.py - logging configuration."""
import os
import time
import logging
import pytest
from logger import setup_logger, _cleanup_old_logs


class TestSetupLogger:
    """Test logger initialization."""

    def test_setup_returns_logger(self):
        logger = setup_logger()
        assert logger is not None
        assert logger.name == "fieldnote"

    def test_logger_has_handlers(self):
        logger = setup_logger()
        assert len(logger.handlers) >= 1

    def test_logger_level_is_debug(self):
        logger = setup_logger()
        assert logger.level == logging.DEBUG


class TestCleanupOldLogs:
    """Test log cleanup."""

    def test_cleanup_removes_old_files(self, tmp_path):
        # Create a fake old log file
        old_log = tmp_path / "fieldnote_2020-01-01.log"
        old_log.write_text("old log content")
        # Set modification time to 60 days ago
        old_time = time.time() - (60 * 24 * 60 * 60)
        os.utime(str(old_log), (old_time, old_time))

        _cleanup_old_logs(str(tmp_path), max_days=30)
        assert not old_log.exists()

    def test_cleanup_keeps_recent_files(self, tmp_path):
        recent_log = tmp_path / "fieldnote_2026-03-07.log"
        recent_log.write_text("recent log content")

        _cleanup_old_logs(str(tmp_path), max_days=30)
        assert recent_log.exists()
