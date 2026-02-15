"""
Per-user persistent conversation memory.
Stores conversation history as JSON files in data/conversations/.
Supports auto-summarization of old messages to keep context manageable.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from bot.config import Config

logger = logging.getLogger("telegram-qwen.memory")


class ConversationMemory:
    """Manages persistent per-user conversation history."""

    def __init__(self):
        Config.ensure_dirs()
        self._cache: dict[str, list[dict]] = {}

    def _path(self, chat_id: int | str) -> Path:
        return Config.CONVERSATION_DIR / f"{chat_id}.json"

    def load(self, chat_id: int | str) -> list[dict]:
        """Load conversation history for a user. Returns from cache if available."""
        key = str(chat_id)
        if key in self._cache:
            return self._cache[key]

        path = self._path(chat_id)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._cache[key] = data
                return data
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to load history for {chat_id}: {e}")

        self._cache[key] = []
        return self._cache[key]

    def save(self, chat_id: int | str) -> None:
        """Persist conversation history to disk."""
        key = str(chat_id)
        history = self._cache.get(key, [])
        path = self._path(chat_id)
        try:
            path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            logger.error(f"Failed to save history for {chat_id}: {e}")

    def add(self, chat_id: int | str, role: str, content: str) -> None:
        """Add a message to the conversation history and auto-save."""
        history = self.load(chat_id)
        history.append({"role": role, "content": content})

        # Trim if over limit — keep a summary of old messages + recent ones
        if len(history) > Config.MAX_HISTORY_LENGTH:
            self._compress(chat_id)

        self.save(chat_id)

    def _compress(self, chat_id: int | str) -> None:
        """Compress old messages into a summary block to save context space."""
        key = str(chat_id)
        history = self._cache.get(key, [])
        if len(history) <= Config.MAX_HISTORY_LENGTH:
            return

        # Keep the last 30 messages, summarize the rest
        keep_count = 30
        old_messages = history[:-keep_count]
        recent_messages = history[-keep_count:]

        # Build a simple summary of old messages
        summary_parts = []
        for msg in old_messages:
            role = msg["role"].upper()
            content = msg["content"]
            # Truncate very long messages in summary
            if len(content) > 200:
                content = content[:200] + "..."
            summary_parts.append(f"{role}: {content}")

        summary = "[CONVERSATION SUMMARY]\n" + "\n".join(summary_parts) + "\n[END SUMMARY]"

        # Replace history with summary + recent
        self._cache[key] = [{"role": "system", "content": summary}] + recent_messages

    def get_formatted(self, chat_id: int | str, max_messages: int = 20) -> str:
        """Get formatted conversation history string for injection into prompts."""
        history = self.load(chat_id)
        recent = history[-max_messages:]
        if not recent:
            return ""
        lines = []
        for msg in recent:
            role = msg["role"].upper()
            content = msg["content"]
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def reset(self, chat_id: int | str) -> None:
        """Clear all conversation history for a user."""
        key = str(chat_id)
        self._cache[key] = []
        path = self._path(chat_id)
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        logger.info(f"Reset conversation history for {chat_id}")

    def get_stats(self, chat_id: int | str) -> dict:
        """Get memory stats for a user."""
        history = self.load(chat_id)
        return {
            "message_count": len(history),
            "max_length": Config.MAX_HISTORY_LENGTH,
        }


# Global singleton
memory = ConversationMemory()
