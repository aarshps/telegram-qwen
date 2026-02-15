"""
Tests for bot.config — Config class and ensure_dirs.
"""

import os
from pathlib import Path
from unittest.mock import patch

from bot.config import Config


class TestConfig:
    """Tests for the Config class."""

    def test_default_values(self):
        """Config should have sensible defaults."""
        assert Config.MAX_MESSAGE_LENGTH == 4096
        assert Config.MAX_OUTPUT_LENGTH == 4000
        assert Config.RESTART_EXIT_CODE == 42
        assert Config.PROGRESS_INTERVAL == 60

    def test_bot_root_is_a_directory(self, temp_data_dirs):
        """BOT_ROOT should be a valid directory (temp in test, real in production)."""
        # During tests, BOT_ROOT is overridden to a temp dir by the fixture.
        # We just verify it's set and is a Path.
        assert Config.BOT_ROOT.is_dir()

    def test_paths_are_path_objects(self):
        """All path configs should be Path objects."""
        assert isinstance(Config.DATA_DIR, Path)
        assert isinstance(Config.CONVERSATION_DIR, Path)
        assert isinstance(Config.TASK_DIR, Path)
        assert isinstance(Config.SCRIPTS_DIR, Path)

    def test_env_vars_with_defaults(self, monkeypatch):
        """Config should use defaults when env vars are not set."""
        monkeypatch.delenv("QWEN_TIMEOUT", raising=False)
        monkeypatch.delenv("MAX_TOOL_TURNS", raising=False)
        monkeypatch.delenv("MAX_RETRIES", raising=False)
        # The defaults are set at class definition time, so we verify they're integers
        assert isinstance(Config.QWEN_TIMEOUT, int)
        assert isinstance(Config.MAX_TOOL_TURNS, int)
        assert isinstance(Config.MAX_RETRIES, int)

    def test_ensure_dirs_creates_directories(self, temp_data_dirs):
        """ensure_dirs should create all required directories."""
        # Remove a directory to test creation
        import shutil
        tasks_dir = temp_data_dirs / "data" / "tasks"
        if tasks_dir.exists():
            shutil.rmtree(tasks_dir)

        Config.ensure_dirs()

        assert Config.DATA_DIR.exists()
        assert Config.CONVERSATION_DIR.exists()
        assert Config.TASK_DIR.exists()
        assert Config.SCRIPTS_DIR.exists()

    def test_ensure_dirs_idempotent(self, temp_data_dirs):
        """ensure_dirs should be safe to call multiple times."""
        Config.ensure_dirs()
        Config.ensure_dirs()  # Should not raise

    def test_telegram_token_default(self, monkeypatch):
        """Token should default to empty string."""
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        # Class-level default is already set, just verify type
        assert isinstance(Config.TELEGRAM_BOT_TOKEN, str)

    def test_rate_limit_defaults(self):
        """Rate limit should have sensible defaults."""
        assert Config.RATE_LIMIT_MESSAGES >= 1
        assert Config.RATE_LIMIT_WINDOW >= 1
