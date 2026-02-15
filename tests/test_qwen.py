"""
Tests for bot.qwen — Qwen CLI integration with retry logic.
"""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from bot.qwen import build_system_prompt, call_qwen, call_qwen_with_context
from bot.config import Config


class TestBuildSystemPrompt:
    def test_returns_string(self):
        prompt = build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_contains_tool_descriptions(self):
        prompt = build_system_prompt()
        assert "WEB_SEARCH" in prompt
        assert "SELF_RESTART" in prompt

    def test_contains_agent_identity(self):
        prompt = build_system_prompt()
        assert "Qwen" in prompt
        assert "admin" in prompt.lower()


class TestCallQwen:
    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Should return response on first attempt."""
        def make_mock_proc(stdout_bytes):
            proc = MagicMock()
            async def communicate(input=None):
                return (stdout_bytes, b"")
            proc.communicate = communicate
            return proc

        mock_proc = make_mock_proc(b"Hello, I'm Qwen!")

        with patch("asyncio.create_subprocess_shell", return_value=mock_proc):
            result = await call_qwen("test prompt")
            assert result == "Hello, I'm Qwen!"

    @pytest.mark.asyncio
    async def test_empty_response_retries(self, monkeypatch):
        """Should retry on empty response."""
        monkeypatch.setattr("bot.config.Config.MAX_RETRIES", 2)

        call_count = 0

        def make_mock_proc(stdout_bytes):
            proc = MagicMock()
            async def communicate(input=None):
                return (stdout_bytes, b"")
            proc.communicate = communicate
            return proc

        async def mock_create_subprocess(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return make_mock_proc(b"")
            else:
                return make_mock_proc(b"Success on retry!")

        with patch("asyncio.create_subprocess_shell", side_effect=mock_create_subprocess):
            with patch("asyncio.sleep", new=AsyncMock()):
                result = await call_qwen("test")
                assert "Success on retry!" in result

    @pytest.mark.asyncio
    async def test_timeout_retries(self, monkeypatch):
        """Should retry on timeout."""
        monkeypatch.setattr("bot.config.Config.MAX_RETRIES", 2)

        async def mock_wait_for(coro, timeout):
            # Await coro to prevent "never awaited" warning
            try:
                await coro
            except Exception:
                pass
            raise asyncio.TimeoutError()

        proc = MagicMock()
        async def mock_communicate(input=None):
            return (b"", b"")
        proc.communicate = mock_communicate

        with patch("asyncio.create_subprocess_shell", return_value=proc):
            with patch("asyncio.wait_for", side_effect=mock_wait_for):
                with patch("asyncio.sleep", new=AsyncMock()):
                    result = await call_qwen("test")
                    assert "❌" in result
                    assert "failed" in result.lower()

    @pytest.mark.asyncio
    async def test_exception_retries(self, monkeypatch):
        """Should retry on general exceptions."""
        monkeypatch.setattr("bot.config.Config.MAX_RETRIES", 2)

        with patch("asyncio.create_subprocess_shell", side_effect=OSError("process failed")):
            with patch("asyncio.sleep", new=AsyncMock()):
                result = await call_qwen("test")
                assert "❌" in result

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self, monkeypatch):
        """Should return error after all retries fail."""
        monkeypatch.setattr("bot.config.Config.MAX_RETRIES", 1)

        proc = MagicMock()
        # Use a regular function since wait_for is mocked and communicate() is never awaited
        proc.communicate = MagicMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_shell", return_value=proc):
            with patch("asyncio.wait_for", return_value=(b"", b"")):
                with patch("asyncio.sleep", new=AsyncMock()):
                    result = await call_qwen("test")
                    assert "❌" in result
                    assert "failed" in result.lower()

    @pytest.mark.asyncio
    async def test_stderr_logged(self):
        """Should log stderr but still return stdout."""
        proc = MagicMock()
        async def mock_communicate(input=None):
            return (b"response", b"some warning")
        proc.communicate = mock_communicate

        with patch("asyncio.create_subprocess_shell", return_value=proc):
            result = await call_qwen("test")
            assert result == "response"

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, monkeypatch):
        """Retries should use exponential backoff: 5s, 15s, 45s..."""
        monkeypatch.setattr("bot.config.Config.MAX_RETRIES", 3)
        sleep_times = []

        async def mock_sleep(seconds):
            sleep_times.append(seconds)

        proc = MagicMock()
        # Use a regular function since wait_for is mocked and communicate() is never awaited
        proc.communicate = MagicMock(return_value=(b"", b""))

        with patch("asyncio.create_subprocess_shell", return_value=proc):
            with patch("asyncio.wait_for", return_value=(b"", b"")):
                with patch("asyncio.sleep", side_effect=mock_sleep):
                    await call_qwen("test")
                    assert len(sleep_times) == 2  # 3 attempts = 2 waits
                    assert sleep_times[0] == 5
                    assert sleep_times[1] == 15


class TestCallQwenWithContext:
    @pytest.mark.asyncio
    async def test_includes_user_input(self):
        """Prompt should contain the user input."""
        captured_prompt = []

        async def mock_call_qwen(prompt):
            captured_prompt.append(prompt)
            return "response"

        with patch("bot.qwen.call_qwen", side_effect=mock_call_qwen):
            await call_qwen_with_context("What is 2+2?", "")
            assert "What is 2+2?" in captured_prompt[0]

    @pytest.mark.asyncio
    async def test_includes_history(self):
        """Prompt should contain conversation history."""
        captured_prompt = []

        async def mock_call_qwen(prompt):
            captured_prompt.append(prompt)
            return "response"

        with patch("bot.qwen.call_qwen", side_effect=mock_call_qwen):
            await call_qwen_with_context("test", "USER: Hello\nASSISTANT: Hi")
            assert "CONVERSATION HISTORY" in captured_prompt[0]
            assert "USER: Hello" in captured_prompt[0]

    @pytest.mark.asyncio
    async def test_includes_task_context(self):
        """Prompt should contain task context when provided."""
        captured_prompt = []

        async def mock_call_qwen(prompt):
            captured_prompt.append(prompt)
            return "response"

        with patch("bot.qwen.call_qwen", side_effect=mock_call_qwen):
            await call_qwen_with_context("test", "", task_context="Resuming step 3")
            assert "TASK CONTEXT" in captured_prompt[0]
            assert "Resuming step 3" in captured_prompt[0]

    @pytest.mark.asyncio
    async def test_no_history_no_context(self):
        """Prompt should work without history or context."""
        captured_prompt = []

        async def mock_call_qwen(prompt):
            captured_prompt.append(prompt)
            return "response"

        with patch("bot.qwen.call_qwen", side_effect=mock_call_qwen):
            result = await call_qwen_with_context("test", "")
            assert result == "response"
            assert "CONVERSATION HISTORY" not in captured_prompt[0]
            assert "TASK CONTEXT" not in captured_prompt[0]
