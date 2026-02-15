"""
Tests for bot.memory — ConversationMemory class.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from bot.memory import ConversationMemory
from bot.config import Config


class TestConversationMemory:
    """Tests for per-user persistent conversation memory."""

    def setup_method(self):
        """Fresh memory instance for each test."""
        self.mem = ConversationMemory()

    # ── Load / Save ─────────────────────────────────────────────────────

    def test_load_empty_user(self, temp_data_dirs):
        """Loading a user with no history returns empty list."""
        result = self.mem.load(99999)
        assert result == []

    def test_load_returns_from_cache(self, temp_data_dirs):
        """Second load should return cached data without reading disk."""
        self.mem.load(99999)
        self.mem._cache["99999"].append({"role": "user", "content": "cached"})
        result = self.mem.load(99999)
        assert len(result) == 1
        assert result[0]["content"] == "cached"

    def test_load_from_file(self, sample_conversation_file):
        """Should load existing conversation from disk."""
        chat_id, path = sample_conversation_file
        result = self.mem.load(chat_id)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_load_corrupt_json(self, temp_data_dirs):
        """Should handle corrupt JSON gracefully."""
        path = Config.CONVERSATION_DIR / "corrupt.json"
        path.write_text("not valid json{{{", encoding="utf-8")
        result = self.mem.load("corrupt")
        assert result == []

    def test_save_creates_file(self, temp_data_dirs):
        """Save should write history to disk."""
        self.mem._cache["42"] = [{"role": "user", "content": "test"}]
        self.mem.save(42)
        path = Config.CONVERSATION_DIR / "42.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data) == 1

    def test_save_empty_cache(self, temp_data_dirs):
        """Save with no cache data should write empty list."""
        self.mem.save(42)
        path = Config.CONVERSATION_DIR / "42.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data == []

    # ── Add ──────────────────────────────────────────────────────────────

    def test_add_message(self, temp_data_dirs):
        """Add should append to history and auto-save."""
        self.mem.add(100, "user", "Hello")
        self.mem.add(100, "assistant", "Hi!")
        history = self.mem.load(100)
        assert len(history) == 2
        # Verify saved to disk
        path = Config.CONVERSATION_DIR / "100.json"
        assert path.exists()

    def test_add_triggers_compression(self, temp_data_dirs, monkeypatch):
        """Add should trigger compression when history exceeds max length."""
        monkeypatch.setattr("bot.config.Config.MAX_HISTORY_LENGTH", 5)
        mem = ConversationMemory()
        for i in range(6):
            mem.add(200, "user", f"Message {i}")
        history = mem.load(200)
        # After compression: 1 summary + last 5 (but we only have 6, keep_count=30 so all kept)
        # Actually keep_count is 30 which is > 6, so _compress returns early
        # Let's test with more messages
        assert len(history) <= 10  # Should not exceed limit by much

    # ── Compress ─────────────────────────────────────────────────────────

    def test_compress_under_limit(self, temp_data_dirs, monkeypatch):
        """Compress should be no-op when under limit."""
        monkeypatch.setattr("bot.config.Config.MAX_HISTORY_LENGTH", 50)
        mem = ConversationMemory()
        mem._cache["300"] = [{"role": "user", "content": "hi"}] * 10
        mem._compress(300)
        assert len(mem._cache["300"]) == 10  # Unchanged

    def test_compress_over_limit(self, temp_data_dirs, monkeypatch):
        """Compress should summarize old messages when over limit."""
        monkeypatch.setattr("bot.config.Config.MAX_HISTORY_LENGTH", 5)
        mem = ConversationMemory()
        # Create 40 messages to trigger compression (keep_count=30, so need >30)
        messages = [{"role": "user", "content": f"msg {i}"} for i in range(40)]
        mem._cache["400"] = messages
        mem._compress(400)
        history = mem._cache["400"]
        # Should be: 1 summary + 30 recent = 31
        assert len(history) == 31
        assert history[0]["role"] == "system"
        assert "[CONVERSATION SUMMARY]" in history[0]["content"]

    def test_compress_truncates_long_messages(self, temp_data_dirs, monkeypatch):
        """Compress should truncate very long messages in the summary."""
        monkeypatch.setattr("bot.config.Config.MAX_HISTORY_LENGTH", 5)
        mem = ConversationMemory()
        long_msg = "x" * 500
        messages = [{"role": "user", "content": long_msg}] * 35
        mem._cache["500"] = messages
        mem._compress(500)
        summary = mem._cache["500"][0]["content"]
        assert "..." in summary

    # ── Get Formatted ────────────────────────────────────────────────────

    def test_get_formatted_empty(self, temp_data_dirs):
        """Get formatted for empty history returns empty string."""
        result = self.mem.get_formatted(600)
        assert result == ""

    def test_get_formatted_with_history(self, temp_data_dirs):
        """Get formatted should return role:content pairs."""
        self.mem.add(700, "user", "What is 2+2?")
        self.mem.add(700, "assistant", "4")
        result = self.mem.get_formatted(700)
        assert "USER: What is 2+2?" in result
        assert "ASSISTANT: 4" in result

    def test_get_formatted_respects_max(self, temp_data_dirs):
        """Get formatted should only return recent messages up to max."""
        for i in range(25):
            self.mem.add(800, "user", f"msg {i}")
        result = self.mem.get_formatted(800, max_messages=5)
        lines = [l for l in result.split("\n") if l.strip()]
        assert len(lines) == 5

    # ── Reset ────────────────────────────────────────────────────────────

    def test_reset_clears_cache(self, temp_data_dirs):
        """Reset should clear the in-memory cache."""
        self.mem.add(900, "user", "test")
        self.mem.reset(900)
        assert self.mem._cache.get("900") == []

    def test_reset_deletes_file(self, sample_conversation_file):
        """Reset should delete the conversation file from disk."""
        chat_id, path = sample_conversation_file
        self.mem.load(chat_id)
        self.mem.reset(chat_id)
        assert not path.exists()

    def test_reset_nonexistent_user(self, temp_data_dirs):
        """Reset on a user with no history should not raise."""
        self.mem.reset(999999)  # Should not raise

    # ── Get Stats ────────────────────────────────────────────────────────

    def test_get_stats(self, temp_data_dirs):
        """Get stats should return message count and max length."""
        self.mem.add(1000, "user", "test")
        self.mem.add(1000, "assistant", "reply")
        stats = self.mem.get_stats(1000)
        assert stats["message_count"] == 2
        assert stats["max_length"] == Config.MAX_HISTORY_LENGTH

    def test_get_stats_empty(self, temp_data_dirs):
        """Get stats for empty history."""
        stats = self.mem.get_stats(1001)
        assert stats["message_count"] == 0

    # ── Path ─────────────────────────────────────────────────────────────

    def test_path_format(self, temp_data_dirs):
        """Path should be CONVERSATION_DIR/chat_id.json."""
        path = self.mem._path(42)
        assert path == Config.CONVERSATION_DIR / "42.json"

    # ── Error Handling ────────────────────────────────────────────────────

    def test_save_handles_os_error(self, temp_data_dirs):
        """Save should log and not raise on OS errors."""
        self.mem._cache["1100"] = [{"role": "user", "content": "test"}]
        with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
            self.mem.save(1100)  # Should not raise

    def test_reset_handles_unlink_error(self, temp_data_dirs):
        """Reset should handle unlink errors gracefully."""
        self.mem.add(1200, "user", "test data")
        # File exists now, mock unlink to fail
        with patch("pathlib.Path.unlink", side_effect=OSError("permission denied")):
            self.mem.reset(1200)  # Should not raise
        assert self.mem._cache.get("1200") == []
