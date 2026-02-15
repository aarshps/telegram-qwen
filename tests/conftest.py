"""
Shared fixtures for all tests.
"""

import os
import sys
import json
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the project root is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def temp_data_dirs(tmp_path, monkeypatch):
    """Redirect all data directories to a temp location for test isolation."""
    data_dir = tmp_path / "data"
    conv_dir = data_dir / "conversations"
    task_dir = data_dir / "tasks"
    scripts_dir = tmp_path / "scripts"

    for d in [data_dir, conv_dir, task_dir, scripts_dir]:
        d.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("bot.config.Config.DATA_DIR", data_dir)
    monkeypatch.setattr("bot.config.Config.CONVERSATION_DIR", conv_dir)
    monkeypatch.setattr("bot.config.Config.TASK_DIR", task_dir)
    monkeypatch.setattr("bot.config.Config.SCRIPTS_DIR", scripts_dir)
    monkeypatch.setattr("bot.config.Config.BOT_ROOT", tmp_path)

    return tmp_path


@pytest.fixture
def sample_conversation_file(temp_data_dirs):
    """Create a sample conversation JSON file."""
    conv_dir = temp_data_dirs / "data" / "conversations"
    chat_id = 12345
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    path = conv_dir / f"{chat_id}.json"
    path.write_text(json.dumps(history), encoding="utf-8")
    return chat_id, path


@pytest.fixture
def sample_task_file(temp_data_dirs):
    """Create a sample task JSON file."""
    task_dir = temp_data_dirs / "data" / "tasks"
    task_data = {
        "task_id": "abc12345",
        "chat_id": 12345,
        "user_request": "Test task",
        "status": "checkpoint",
        "steps": [
            {
                "index": 0,
                "tool_name": "EXEC",
                "tool_params": "echo hello",
                "tool_result": '{"status": "success", "output": "hello"}',
                "qwen_response": "Let me run that [EXEC]echo hello[/EXEC]",
                "status": "completed",
            }
        ],
        "current_step": 1,
        "retry_count": 0,
        "created_at": 1000000.0,
        "updated_at": 1000001.0,
    }
    path = task_dir / "abc12345.json"
    path.write_text(json.dumps(task_data), encoding="utf-8")
    return task_data, path


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object."""
    update = MagicMock()
    update.effective_chat.id = 12345
    update.effective_user.id = 12345
    update.message.text = "Hello"
    update.message.reply_text = MagicMock(return_value=asyncio.coroutine(lambda: None)())
    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram context."""
    context = MagicMock()
    context.bot.send_chat_action = MagicMock(return_value=asyncio.coroutine(lambda: None)())
    context.bot.send_message = MagicMock(return_value=asyncio.coroutine(lambda: None)())
    context.args = []
    return context


import asyncio
