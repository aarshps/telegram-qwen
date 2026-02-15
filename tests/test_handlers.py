"""
Tests for bot.handlers — Telegram command and message handlers.
"""

import asyncio
import time
import pytest
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock

from bot.handlers import (
    _check_auth,
    _check_rate_limit,
    _send_safe,
    cmd_start,
    cmd_help,
    cmd_reset,
    cmd_status,
    cmd_tasks,
    cmd_resume,
    cmd_selfupdate,
    handle_message,
    _rate_limiter,
)
from bot.config import Config
from bot.task_engine import TaskStatus


# ── Helper: create mock Update and Context ────────────────────────────────

def make_update(chat_id=12345, text="Hello"):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_user.id = chat_id
    update.message.text = text
    update.message.reply_text = AsyncMock()
    return update


def make_context(args=None):
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    context.bot.send_message = AsyncMock()
    context.args = args or []
    return context


# ── Auth ─────────────────────────────────────────────────────────────────────

class TestCheckAuth:
    def test_no_admin_id(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        assert _check_auth(99999) is True

    def test_admin_id_placeholder(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "your_chat_id_here")
        assert _check_auth(99999) is True

    def test_authorized_user(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "12345")
        assert _check_auth(12345) is True

    def test_unauthorized_user(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "12345")
        assert _check_auth(99999) is False


# ── Rate Limiting ────────────────────────────────────────────────────────────

class TestRateLimit:
    def setup_method(self):
        _rate_limiter.clear()

    def test_first_message_allowed(self):
        assert _check_rate_limit(100) is True

    def test_within_limit(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.RATE_LIMIT_MESSAGES", 3)
        assert _check_rate_limit(200) is True
        assert _check_rate_limit(200) is True
        assert _check_rate_limit(200) is True

    def test_exceeds_limit(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.RATE_LIMIT_MESSAGES", 2)
        monkeypatch.setattr("bot.config.Config.RATE_LIMIT_WINDOW", 60)
        assert _check_rate_limit(300) is True
        assert _check_rate_limit(300) is True
        assert _check_rate_limit(300) is False

    def test_limit_resets_after_window(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.RATE_LIMIT_MESSAGES", 1)
        monkeypatch.setattr("bot.config.Config.RATE_LIMIT_WINDOW", 0)  # Zero window = always reset
        assert _check_rate_limit(400) is True
        assert _check_rate_limit(400) is True  # Window expired immediately

    def test_different_users_independent(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.RATE_LIMIT_MESSAGES", 1)
        monkeypatch.setattr("bot.config.Config.RATE_LIMIT_WINDOW", 60)
        assert _check_rate_limit(500) is True
        assert _check_rate_limit(501) is True  # Different user


# ── Send Safe ────────────────────────────────────────────────────────────────

class TestSendSafe:
    @pytest.mark.asyncio
    async def test_short_message(self):
        update = make_update()
        await _send_safe(update, "Hello!")
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_message(self):
        update = make_update()
        await _send_safe(update, "")
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "empty" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_long_message_splits(self):
        update = make_update()
        long_text = "x" * 5000
        await _send_safe(update, long_text)
        assert update.message.reply_text.call_count >= 2

    @pytest.mark.asyncio
    async def test_markdown_fallback(self):
        """Should fall back to plain text if Markdown parsing fails."""
        update = make_update()
        call_count = 0

        async def mock_reply(text, parse_mode=None):
            nonlocal call_count
            call_count += 1
            if parse_mode is not None and call_count == 1:
                raise Exception("Bad markup")

        update.message.reply_text = mock_reply
        await _send_safe(update, "test *bold*", parse_mode="Markdown")
        assert call_count == 2  # First fails, second succeeds


# ── Command: /start ──────────────────────────────────────────────────────────

class TestCmdStart:
    @pytest.mark.asyncio
    async def test_authorized(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()
        await cmd_start(update, ctx)
        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "Qwen" in call_text

    @pytest.mark.asyncio
    async def test_unauthorized(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "99999")
        update = make_update(chat_id=11111)
        ctx = make_context()
        await cmd_start(update, ctx)
        call_text = update.message.reply_text.call_args[0][0]
        assert "denied" in call_text.lower()


# ── Command: /help ───────────────────────────────────────────────────────────

class TestCmdHelp:
    @pytest.mark.asyncio
    async def test_authorized(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()
        await cmd_help(update, ctx)
        call_text = update.message.reply_text.call_args[0][0]
        assert "Help" in call_text
        assert "File" in call_text

    @pytest.mark.asyncio
    async def test_unauthorized(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "99999")
        update = make_update(chat_id=11111)
        ctx = make_context()
        await cmd_help(update, ctx)
        call_text = update.message.reply_text.call_args[0][0]
        assert "denied" in call_text.lower()


# ── Command: /reset ──────────────────────────────────────────────────────────

class TestCmdReset:
    @pytest.mark.asyncio
    async def test_reset(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        with patch("bot.handlers.memory") as mock_mem:
            await cmd_reset(update, ctx)
            mock_mem.reset.assert_called_once_with(12345)
            call_text = update.message.reply_text.call_args[0][0]
            assert "cleared" in call_text.lower()

    @pytest.mark.asyncio
    async def test_reset_unauthorized(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "99999")
        update = make_update(chat_id=11111)
        ctx = make_context()
        await cmd_reset(update, ctx)
        call_text = update.message.reply_text.call_args[0][0]
        assert "denied" in call_text.lower()


# ── Command: /status ─────────────────────────────────────────────────────────

class TestCmdStatus:
    @pytest.mark.asyncio
    async def test_status(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        with patch("bot.handlers.memory") as mock_mem:
            mock_mem.get_stats.return_value = {"message_count": 5, "max_length": 50}
            with patch("bot.handlers.engine") as mock_engine:
                mock_engine.get_pending_tasks.return_value = []
                with patch("asyncio.create_subprocess_shell") as mock_proc:
                    mock_p = AsyncMock()
                    mock_p.communicate.return_value = (b"1.0.0", b"")
                    mock_p.returncode = 0
                    mock_proc.return_value = mock_p
                    await cmd_status(update, ctx)

        call_text = update.message.reply_text.call_args[0][0]
        assert "Status" in call_text
        assert "Uptime" in call_text

    @pytest.mark.asyncio
    async def test_status_unauthorized(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "99999")
        update = make_update(chat_id=11111)
        ctx = make_context()
        await cmd_status(update, ctx)
        call_text = update.message.reply_text.call_args[0][0]
        assert "denied" in call_text.lower()


# ── Command: /tasks ──────────────────────────────────────────────────────────

class TestCmdTasks:
    @pytest.mark.asyncio
    async def test_no_tasks(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.get_tasks_for_chat.return_value = []
            await cmd_tasks(update, ctx)

        call_text = update.message.reply_text.call_args[0][0]
        assert "No tasks" in call_text

    @pytest.mark.asyncio
    async def test_with_tasks(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        mock_task = MagicMock()
        mock_task.task_id = "abc123"
        mock_task.status = TaskStatus.COMPLETED
        mock_task.user_request = "Test task"
        mock_task.steps = []
        mock_task.retry_count = 0

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.get_tasks_for_chat.return_value = [mock_task]
            await cmd_tasks(update, ctx)

        call_text = update.message.reply_text.call_args[0][0]
        assert "abc123" in call_text


# ── Command: /resume ─────────────────────────────────────────────────────────

class TestCmdResume:
    @pytest.mark.asyncio
    async def test_no_resumable(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.get_tasks_for_chat.return_value = []
            await cmd_resume(update, ctx)

        call_text = update.message.reply_text.call_args[0][0]
        assert "No resumable" in call_text

    @pytest.mark.asyncio
    async def test_resume_nonexistent_id(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context(args=["nonexistent"])

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.get_task.return_value = None
            await cmd_resume(update, ctx)

        call_text = update.message.reply_text.call_args[0][0]
        assert "not found" in call_text.lower()

    @pytest.mark.asyncio
    async def test_resume_task(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context(args=["t123"])

        mock_task = MagicMock()
        mock_task.task_id = "t123"
        mock_task.user_request = "Test resume"
        mock_task.current_step = 1

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.get_task.return_value = mock_task
            mock_engine.execute_task = AsyncMock(return_value="Resumed!")
            with patch("bot.handlers.memory") as mock_mem:
                mock_mem.get_formatted.return_value = ""
                await cmd_resume(update, ctx)

        # Should have sent at least the "Resuming..." message and the result
        assert update.message.reply_text.call_count >= 1


# ── Command: /selfupdate ────────────────────────────────────────────────────

class TestCmdSelfupdate:
    @pytest.mark.asyncio
    async def test_selfupdate(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        with patch("os._exit") as mock_exit:
            with patch("asyncio.sleep", new=AsyncMock()):
                await cmd_selfupdate(update, ctx)
                mock_exit.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_selfupdate_unauthorized(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "99999")
        update = make_update(chat_id=11111)
        ctx = make_context()
        await cmd_selfupdate(update, ctx)
        call_text = update.message.reply_text.call_args[0][0]
        assert "denied" in call_text.lower()


# ── handle_message ───────────────────────────────────────────────────────────

class TestHandleMessage:
    @pytest.mark.asyncio
    async def test_unauthorized(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "99999")
        update = make_update(chat_id=11111)
        ctx = make_context()
        await handle_message(update, ctx)
        call_text = update.message.reply_text.call_args[0][0]
        assert "denied" in call_text.lower()

    @pytest.mark.asyncio
    async def test_rate_limited(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        monkeypatch.setattr("bot.config.Config.RATE_LIMIT_MESSAGES", 1)
        monkeypatch.setattr("bot.config.Config.RATE_LIMIT_WINDOW", 60)
        _rate_limiter.clear()

        update1 = make_update()
        ctx1 = make_context()

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.create_task.return_value = MagicMock(task_id="t1")
            mock_engine.execute_task = AsyncMock(return_value="ok")
            with patch("bot.handlers.memory"):
                await handle_message(update1, ctx1)

        # Second message should be rate limited
        update2 = make_update()
        ctx2 = make_context()
        await handle_message(update2, ctx2)
        call_text = update2.message.reply_text.call_args[0][0]
        assert "slow down" in call_text.lower() or "rate limit" in call_text.lower()

    @pytest.mark.asyncio
    async def test_empty_text(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update(text=None)
        update.message.text = None
        ctx = make_context()
        _rate_limiter.clear()
        await handle_message(update, ctx)
        # Should return early without error

    @pytest.mark.asyncio
    async def test_successful_message(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        _rate_limiter.clear()
        update = make_update(text="What is 2+2?")
        ctx = make_context()

        mock_task = MagicMock()
        mock_task.task_id = "t1"

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.create_task.return_value = mock_task
            mock_engine.execute_task = AsyncMock(return_value="4")
            with patch("bot.handlers.memory") as mock_mem:
                mock_mem.get_formatted.return_value = ""
                await handle_message(update, ctx)

        # Should have replied with the response
        assert update.message.reply_text.call_count >= 1

    @pytest.mark.asyncio
    async def test_error_handling(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        _rate_limiter.clear()
        update = make_update()
        ctx = make_context()

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.create_task.side_effect = Exception("Unexpected error")
            with patch("bot.handlers.memory"):
                await handle_message(update, ctx)

        # Should have sent an error message
        call_text = update.message.reply_text.call_args[0][0]
        assert "error" in call_text.lower()


# ── Additional coverage tests ────────────────────────────────────────────────

class TestSendSafeFullFailure:
    """Covers handlers.py L70-71: both markdown and plain text send fail."""

    @pytest.mark.asyncio
    async def test_both_sends_fail(self):
        update = make_update()
        update.message.reply_text = AsyncMock(side_effect=Exception("network error"))
        await _send_safe(update, "test message", parse_mode="Markdown")
        # Should not raise; both attempts fail gracefully


class TestSendTypingIndicator:
    """Covers handlers.py L76-85: typing indicator loop and cancellation."""

    @pytest.mark.asyncio
    async def test_typing_indicator_cancelled(self):
        from bot.handlers import send_typing_indicator
        ctx = make_context()
        task = asyncio.create_task(send_typing_indicator(ctx, 12345))
        await asyncio.sleep(0.1)  # Let it run briefly
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        # send_chat_action should have been called at least once
        assert ctx.bot.send_chat_action.call_count >= 1

    @pytest.mark.asyncio
    async def test_typing_cancellation_send_fails(self):
        """If the final send_chat_action in cancellation handler fails, it should still propagate CancelledError."""
        from bot.handlers import send_typing_indicator
        ctx = make_context()

        call_count = 0

        async def mock_action(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise Exception("network error")

        ctx.bot.send_chat_action = mock_action
        task = asyncio.create_task(send_typing_indicator(ctx, 12345))
        await asyncio.sleep(0.1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


class TestCmdStatusPaths:
    """Covers handlers.py L195-197, L212-213: Qwen error and psutil ImportError."""

    @pytest.mark.asyncio
    async def test_status_qwen_error(self, monkeypatch, temp_data_dirs):
        """Qwen returning non-zero exit code shows error status."""
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        with patch("bot.handlers.memory") as mock_mem:
            mock_mem.get_stats.return_value = {"message_count": 0, "max_length": 50}
            with patch("bot.handlers.engine") as mock_engine:
                mock_engine.get_pending_tasks.return_value = []
                with patch("asyncio.create_subprocess_shell") as mock_proc:
                    mock_p = AsyncMock()
                    mock_p.communicate.return_value = (b"", b"error")
                    mock_p.returncode = 1
                    mock_proc.return_value = mock_p
                    await cmd_status(update, ctx)

        call_text = update.message.reply_text.call_args[0][0]
        assert "Status" in call_text

    @pytest.mark.asyncio
    async def test_status_qwen_unavailable(self, monkeypatch, temp_data_dirs):
        """Exception checking Qwen shows unavailable."""
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        with patch("bot.handlers.memory") as mock_mem:
            mock_mem.get_stats.return_value = {"message_count": 0, "max_length": 50}
            with patch("bot.handlers.engine") as mock_engine:
                mock_engine.get_pending_tasks.return_value = []
                with patch("asyncio.create_subprocess_shell", side_effect=Exception("not found")):
                    await cmd_status(update, ctx)

        call_text = update.message.reply_text.call_args[0][0]
        assert "Unavailable" in call_text

    @pytest.mark.asyncio
    async def test_status_without_psutil(self, monkeypatch, temp_data_dirs):
        """Status should show message when psutil not available."""
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        with patch("bot.handlers.memory") as mock_mem:
            mock_mem.get_stats.return_value = {"message_count": 0, "max_length": 50}
            with patch("bot.handlers.engine") as mock_engine:
                mock_engine.get_pending_tasks.return_value = []
                with patch("asyncio.create_subprocess_shell") as mock_proc:
                    mock_p = AsyncMock()
                    mock_p.communicate.return_value = (b"1.0", b"")
                    mock_p.returncode = 0
                    mock_proc.return_value = mock_p
                    # Mock psutil import to fail
                    import builtins
                    real_import = builtins.__import__

                    def mock_import(name, *args, **kwargs):
                        if name == "psutil":
                            raise ImportError("no psutil")
                        return real_import(name, *args, **kwargs)

                    with patch("builtins.__import__", side_effect=mock_import):
                        await cmd_status(update, ctx)

        call_text = update.message.reply_text.call_args[0][0]
        assert "psutil" in call_text.lower() or "Status" in call_text


class TestCmdTasksAuth:
    """Covers handlers.py L235-236: tasks auth denied."""

    @pytest.mark.asyncio
    async def test_tasks_unauthorized(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "99999")
        update = make_update(chat_id=11111)
        ctx = make_context()
        await cmd_tasks(update, ctx)
        call_text = update.message.reply_text.call_args[0][0]
        assert "denied" in call_text.lower()


class TestCmdTasksLongRequest:
    """Covers handlers.py L257-258: truncating long request text."""

    @pytest.mark.asyncio
    async def test_tasks_long_request_truncated(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()

        mock_task = MagicMock()
        mock_task.task_id = "long1"
        mock_task.status = TaskStatus.RUNNING
        mock_task.user_request = "A" * 100  # > 60 chars
        mock_task.steps = []
        mock_task.retry_count = 0

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.get_tasks_for_chat.return_value = [mock_task]
            await cmd_tasks(update, ctx)

        call_text = update.message.reply_text.call_args[0][0]
        assert "..." in call_text


class TestCmdResumeAuth:
    """Covers handlers.py L272-273: resume auth denied."""

    @pytest.mark.asyncio
    async def test_resume_unauthorized(self, monkeypatch):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "99999")
        update = make_update(chat_id=11111)
        ctx = make_context()
        await cmd_resume(update, ctx)
        call_text = update.message.reply_text.call_args[0][0]
        assert "denied" in call_text.lower()


class TestCmdResumeAutoFind:
    """Covers handlers.py L285: auto-finding most recent resumable task."""

    @pytest.mark.asyncio
    async def test_resume_auto_find(self, monkeypatch, temp_data_dirs):
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context()  # No args = auto-find

        mock_task = MagicMock()
        mock_task.task_id = "auto1"
        mock_task.status = TaskStatus.CHECKPOINT
        mock_task.user_request = "Auto-resume this"
        mock_task.current_step = 2

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.get_tasks_for_chat.return_value = [
                MagicMock(status=TaskStatus.COMPLETED),  # Not resumable
                mock_task,  # Resumable
            ]
            mock_engine.execute_task = AsyncMock(return_value="Auto-resumed!")
            with patch("bot.handlers.memory") as mock_mem:
                mock_mem.get_formatted.return_value = ""
                await cmd_resume(update, ctx)

        assert update.message.reply_text.call_count >= 1


class TestProgressCallbacks:
    """Covers handlers.py L307-310, L375-378: progress callbacks inside cmd_resume and handle_message."""

    @pytest.mark.asyncio
    async def test_handle_message_progress_callback(self, monkeypatch, temp_data_dirs):
        """Progress callback in handle_message should call send_message (L375-378)."""
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        _rate_limiter.clear()
        update = make_update(text="Test progress")
        ctx = make_context()

        mock_task = MagicMock()
        mock_task.task_id = "prog1"

        captured_cb = [None]

        async def mock_execute(task, history, progress_callback=None):
            captured_cb[0] = progress_callback
            if progress_callback:
                await progress_callback("Progress update!")
            return "Done!"

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.create_task.return_value = mock_task
            mock_engine.execute_task = mock_execute
            with patch("bot.handlers.memory"):
                await handle_message(update, ctx)

        # Progress callback should have triggered send_message
        ctx.bot.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_handle_message_progress_callback_error(self, monkeypatch, temp_data_dirs):
        """Progress callback error should be silently caught (L377-378)."""
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        _rate_limiter.clear()
        update = make_update(text="Test error cb")
        ctx = make_context()
        ctx.bot.send_message = AsyncMock(side_effect=Exception("send failed"))

        mock_task = MagicMock()
        mock_task.task_id = "prog2"

        async def mock_execute(task, history, progress_callback=None):
            if progress_callback:
                await progress_callback("This will fail silently")
            return "Still works!"

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.create_task.return_value = mock_task
            mock_engine.execute_task = mock_execute
            with patch("bot.handlers.memory"):
                await handle_message(update, ctx)

        # Should not raise, response should still be sent
        assert update.message.reply_text.call_count >= 1

    @pytest.mark.asyncio
    async def test_resume_progress_callback(self, monkeypatch, temp_data_dirs):
        """Progress callback in cmd_resume should call send_message (L307-310)."""
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context(args=["res1"])

        mock_task = MagicMock()
        mock_task.task_id = "res1"
        mock_task.user_request = "Resume test"
        mock_task.current_step = 1

        async def mock_execute(task, history, progress_callback=None):
            if progress_callback:
                await progress_callback("Resuming...")
            return "Resumed!"

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.get_task.return_value = mock_task
            mock_engine.execute_task = mock_execute
            with patch("bot.handlers.memory") as mock_mem:
                mock_mem.get_formatted.return_value = ""
                await cmd_resume(update, ctx)

        ctx.bot.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_resume_progress_callback_error(self, monkeypatch, temp_data_dirs):
        """Progress callback error in cmd_resume should be silently caught (L309-310)."""
        monkeypatch.setattr("bot.config.Config.TELEGRAM_ADMIN_ID", "")
        update = make_update()
        ctx = make_context(args=["res2"])
        ctx.bot.send_message = AsyncMock(side_effect=Exception("cb fail"))

        mock_task = MagicMock()
        mock_task.task_id = "res2"
        mock_task.user_request = "Resume test 2"
        mock_task.current_step = 1

        async def mock_execute(task, history, progress_callback=None):
            if progress_callback:
                await progress_callback("This will fail")
            return "Resumed!"

        with patch("bot.handlers.engine") as mock_engine:
            mock_engine.get_task.return_value = mock_task
            mock_engine.execute_task = mock_execute
            with patch("bot.handlers.memory") as mock_mem:
                mock_mem.get_formatted.return_value = ""
                await cmd_resume(update, ctx)

        # Should not raise, should complete
        assert update.message.reply_text.call_count >= 1


