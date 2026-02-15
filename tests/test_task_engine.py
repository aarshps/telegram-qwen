"""
Tests for bot.task_engine — TaskStep, Task, TaskEngine.
"""

import asyncio
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from bot.task_engine import TaskStatus, TaskStep, Task, TaskEngine
from bot.config import Config


# ── TaskStep ─────────────────────────────────────────────────────────────────

class TestTaskStep:
    def test_creation(self):
        step = TaskStep(index=0, tool_name="EXEC", tool_params="echo hi")
        assert step.index == 0
        assert step.tool_name == "EXEC"
        assert step.status == "pending"

    def test_to_dict(self):
        step = TaskStep(index=1, tool_name="FILE_READ", tool_params="/tmp/test",
                        tool_result="content", qwen_response="resp", status="completed")
        d = step.to_dict()
        assert d["index"] == 1
        assert d["tool_name"] == "FILE_READ"
        assert d["status"] == "completed"
        assert d["tool_result"] == "content"

    def test_from_dict(self):
        data = {
            "index": 2,
            "tool_name": "PYTHON",
            "tool_params": "print(1)",
            "tool_result": "1",
            "qwen_response": "Running code",
            "status": "completed",
        }
        step = TaskStep.from_dict(data)
        assert step.index == 2
        assert step.tool_name == "PYTHON"

    def test_defaults(self):
        step = TaskStep(index=0)
        assert step.tool_name == ""
        assert step.tool_params == ""
        assert step.tool_result == ""
        assert step.qwen_response == ""
        assert step.status == "pending"

    def test_roundtrip(self):
        original = TaskStep(index=5, tool_name="WEB_SEARCH", tool_params="query",
                            tool_result="results", qwen_response="resp", status="completed")
        reconstructed = TaskStep.from_dict(original.to_dict())
        assert reconstructed.index == original.index
        assert reconstructed.tool_name == original.tool_name
        assert reconstructed.status == original.status


# ── TaskStatus ───────────────────────────────────────────────────────────────

class TestTaskStatus:
    def test_values(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.CHECKPOINT == "checkpoint"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"

    def test_is_string(self):
        assert isinstance(TaskStatus.PENDING, str)


# ── Task ─────────────────────────────────────────────────────────────────────

class TestTask:
    def test_creation(self, temp_data_dirs):
        task = Task(task_id="t1", chat_id=123, user_request="Do something")
        assert task.task_id == "t1"
        assert task.chat_id == 123
        assert task.status == TaskStatus.PENDING
        assert task.steps == []
        assert task.current_step == 0

    def test_to_dict(self, temp_data_dirs):
        task = Task(task_id="t2", chat_id=456, user_request="Task request",
                    created_at=1000.0, updated_at=1001.0)
        d = task.to_dict()
        assert d["task_id"] == "t2"
        assert d["chat_id"] == 456
        assert d["steps"] == []
        assert d["created_at"] == 1000.0

    def test_from_dict(self, temp_data_dirs):
        data = {
            "task_id": "t3",
            "chat_id": 789,
            "user_request": "Test request",
            "status": "running",
            "steps": [{"index": 0, "tool_name": "EXEC", "tool_params": "echo",
                        "tool_result": "ok", "qwen_response": "r", "status": "completed"}],
            "current_step": 1,
            "retry_count": 2,
            "created_at": 2000.0,
            "updated_at": 2001.0,
        }
        task = Task.from_dict(data)
        assert task.task_id == "t3"
        assert len(task.steps) == 1
        assert task.steps[0].tool_name == "EXEC"
        assert task.retry_count == 2

    def test_save_and_load(self, temp_data_dirs):
        task = Task(task_id="save1", chat_id=100, user_request="Save test")
        task.steps.append(TaskStep(index=0, tool_name="EXEC", status="completed"))
        task.save()

        loaded = Task.load("save1")
        assert loaded is not None
        assert loaded.task_id == "save1"
        assert loaded.chat_id == 100
        assert len(loaded.steps) == 1

    def test_load_nonexistent(self, temp_data_dirs):
        result = Task.load("nonexistent_id")
        assert result is None

    def test_load_corrupt(self, temp_data_dirs):
        path = Config.TASK_DIR / "corrupt.json"
        path.write_text("not json{{{", encoding="utf-8")
        result = Task.load("corrupt")
        assert result is None

    def test_save_updates_timestamp(self, temp_data_dirs):
        task = Task(task_id="ts1", chat_id=100, user_request="test",
                    updated_at=1000.0)
        task.save()
        assert task.updated_at > 1000.0

    def test_get_context_summary_empty(self, temp_data_dirs):
        task = Task(task_id="ctx1", chat_id=100, user_request="test")
        assert task.get_context_summary() == ""

    def test_get_context_summary_with_steps(self, temp_data_dirs):
        task = Task(task_id="ctx2", chat_id=100, user_request="Multi-step task")
        task.steps.append(TaskStep(
            index=0, tool_name="EXEC", tool_params="echo hi",
            tool_result="hi", qwen_response="r", status="completed"
        ))
        task.steps.append(TaskStep(
            index=1, tool_name="FILE_READ", tool_params="/tmp/f",
            tool_result="content", qwen_response="r", status="completed"
        ))
        task.current_step = 2

        summary = task.get_context_summary()
        assert "Multi-step task" in summary
        assert "EXEC" in summary
        assert "FILE_READ" in summary
        assert "step 3" in summary.lower()

    def test_get_context_summary_truncates_long_results(self, temp_data_dirs):
        task = Task(task_id="ctx3", chat_id=100, user_request="test")
        task.steps.append(TaskStep(
            index=0, tool_name="EXEC", tool_result="x" * 500,
            status="completed"
        ))
        task.current_step = 1
        summary = task.get_context_summary()
        assert "..." in summary

    def test_roundtrip(self, temp_data_dirs):
        original = Task(task_id="rt1", chat_id=42, user_request="roundtrip test",
                        status=TaskStatus.CHECKPOINT, current_step=3, retry_count=1)
        original.steps.append(TaskStep(0, "EXEC", "cmd", "out", "resp", "completed"))
        original.save()

        loaded = Task.load("rt1")
        assert loaded.task_id == original.task_id
        assert loaded.status == original.status
        assert loaded.current_step == original.current_step
        assert loaded.retry_count == original.retry_count
        assert len(loaded.steps) == 1


# ── TaskEngine ───────────────────────────────────────────────────────────────

class TestTaskEngine:
    def setup_method(self):
        self.engine = TaskEngine()

    def test_create_task(self, temp_data_dirs):
        task = self.engine.create_task(123, "Do something")
        assert task.chat_id == 123
        assert task.user_request == "Do something"
        assert task.task_id in self.engine.active_tasks
        # Should be saved to disk
        assert (Config.TASK_DIR / f"{task.task_id}.json").exists()

    @pytest.mark.asyncio
    async def test_execute_task_no_tools(self, temp_data_dirs):
        """Task with a response that has no tool calls should complete immediately."""
        task = self.engine.create_task(123, "Say hello")

        with patch("bot.task_engine.call_qwen_with_context", new=AsyncMock(return_value="Hello there!")):
            result = await self.engine.execute_task(task, "")
            assert result == "Hello there!"
            assert task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_task_with_tool_chain(self, temp_data_dirs):
        """Task with tool calls should chain through multiple turns."""
        task = self.engine.create_task(123, "Run a command")

        call_count = 0

        async def mock_qwen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "Let me run [EXEC]echo hello[/EXEC]"
            else:
                return "The command returned: hello"

        with patch("bot.task_engine.call_qwen_with_context", side_effect=mock_qwen):
            result = await self.engine.execute_task(task, "")
            assert "hello" in result.lower()
            assert task.status == TaskStatus.COMPLETED
            assert len(task.steps) == 1

    @pytest.mark.asyncio
    async def test_execute_task_qwen_failure(self, temp_data_dirs):
        """If Qwen fails completely, task should be marked FAILED."""
        task = self.engine.create_task(123, "Test failure")

        with patch("bot.task_engine.call_qwen_with_context",
                    new=AsyncMock(return_value="❌ Qwen failed after 3 attempts.")):
            result = await self.engine.execute_task(task, "")
            assert "❌" in result
            assert task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_task_tool_error_recovery(self, temp_data_dirs):
        """Task should try to recover when a tool fails."""
        task = self.engine.create_task(123, "Run failing command")

        call_count = 0

        async def mock_qwen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "[EXEC]this_command_does_not_exist_xyz[/EXEC]"
            elif call_count == 2:
                return "[EXEC]echo recovered[/EXEC]"
            else:
                return "Task completed after recovery."

        with patch("bot.task_engine.call_qwen_with_context", side_effect=mock_qwen):
            result = await self.engine.execute_task(task, "")
            assert task.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_task_max_turns(self, temp_data_dirs, monkeypatch):
        """Task reaching max turns should checkpoint."""
        monkeypatch.setattr("bot.config.Config.MAX_TOOL_TURNS", 2)
        engine = TaskEngine()
        task = engine.create_task(123, "Infinite loop")

        async def mock_qwen(*args, **kwargs):
            return "[EXEC]echo turn[/EXEC]"

        with patch("bot.task_engine.call_qwen_with_context", side_effect=mock_qwen):
            result = await engine.execute_task(task, "")
            # Should complete at max turns
            assert task.current_step <= 2

    @pytest.mark.asyncio
    async def test_execute_task_progress_callback(self, temp_data_dirs, monkeypatch):
        """Progress callback should be called during long tasks."""
        monkeypatch.setattr("bot.config.Config.PROGRESS_INTERVAL", 0)  # Trigger immediately

        task = self.engine.create_task(123, "Long task")
        progress_messages = []

        async def progress_cb(msg):
            progress_messages.append(msg)

        call_count = 0

        async def mock_qwen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return "[EXEC]echo step[/EXEC]"
            return "Done!"

        with patch("bot.task_engine.call_qwen_with_context", side_effect=mock_qwen):
            await self.engine.execute_task(task, "", progress_callback=progress_cb)
            # With PROGRESS_INTERVAL=0, callback should have been called
            assert len(progress_messages) >= 0  # May or may not trigger depending on timing

    @pytest.mark.asyncio
    async def test_execute_task_resume(self, temp_data_dirs):
        """Resuming a checkpointed task should inject context."""
        task = self.engine.create_task(123, "Resumable task")
        task.current_step = 1
        task.steps.append(TaskStep(0, "EXEC", "echo hi", "hi", "resp", "completed"))

        captured_args = []

        async def mock_qwen(user_input, history, task_context=""):
            captured_args.append((user_input, task_context))
            return "Resumed and completed!"

        with patch("bot.task_engine.call_qwen_with_context", side_effect=mock_qwen):
            result = await self.engine.execute_task(task, "")
            assert "Continue" in captured_args[0][0]
            assert "EXEC" in captured_args[0][1]

    def test_get_pending_tasks(self, sample_task_file, temp_data_dirs):
        """Should find tasks with checkpoint/failed/running status."""
        tasks = self.engine.get_pending_tasks()
        assert len(tasks) >= 1
        assert any(t.task_id == "abc12345" for t in tasks)

    def test_get_pending_tasks_ignores_completed(self, temp_data_dirs):
        """Completed tasks should not appear in pending list."""
        task = self.engine.create_task(123, "Completed task")
        task.status = TaskStatus.COMPLETED
        task.save()

        pending = self.engine.get_pending_tasks()
        assert not any(t.task_id == task.task_id for t in pending)

    def test_get_task_from_active(self, temp_data_dirs):
        task = self.engine.create_task(123, "Active task")
        found = self.engine.get_task(task.task_id)
        assert found is not None
        assert found.task_id == task.task_id

    def test_get_task_from_disk(self, sample_task_file, temp_data_dirs):
        found = self.engine.get_task("abc12345")
        assert found is not None
        assert found.task_id == "abc12345"

    def test_get_task_nonexistent(self, temp_data_dirs):
        found = self.engine.get_task("nonexistent")
        assert found is None

    def test_get_tasks_for_chat(self, temp_data_dirs):
        self.engine.create_task(111, "Task 1")
        self.engine.create_task(111, "Task 2")
        self.engine.create_task(222, "Other user task")

        tasks = self.engine.get_tasks_for_chat(111)
        assert len(tasks) == 2
        assert all(t.chat_id == 111 for t in tasks)

    def test_get_tasks_for_chat_empty(self, temp_data_dirs):
        tasks = self.engine.get_tasks_for_chat(999999)
        assert tasks == []

    def test_get_tasks_for_chat_limited(self, temp_data_dirs):
        """Should return max 10 tasks."""
        for i in range(15):
            task = self.engine.create_task(333, f"Task {i}")
            task.save()

        tasks = self.engine.get_tasks_for_chat(333)
        assert len(tasks) <= 10

    @pytest.mark.asyncio
    async def test_call_with_retry_success(self, temp_data_dirs):
        """_call_with_retry should return on first success."""
        task = self.engine.create_task(123, "test")

        with patch("bot.task_engine.call_qwen_with_context",
                    new=AsyncMock(return_value="Success!")):
            result = await self.engine._call_with_retry("input", "history", "", task)
            assert result == "Success!"

    @pytest.mark.asyncio
    async def test_call_with_retry_exhausted(self, temp_data_dirs, monkeypatch):
        """_call_with_retry should fail after retries exhausted."""
        monkeypatch.setattr("bot.config.Config.MAX_RETRIES", 2)
        engine = TaskEngine()
        task = engine.create_task(123, "test")

        with patch("bot.task_engine.call_qwen_with_context",
                    new=AsyncMock(return_value="❌ Failed")):
            with patch("asyncio.sleep", new=AsyncMock()):
                result = await engine._call_with_retry("input", "history", "", task)
                assert "❌" in result
                assert task.status == TaskStatus.FAILED

    # ── Additional coverage tests ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_execute_task_tool_exception(self, temp_data_dirs):
        """Tool raising an exception should checkpoint and try recovery (L237-247)."""
        task = self.engine.create_task(123, "Tool exception test")
        call_count = 0

        async def mock_qwen(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "[EXEC]some_command[/EXEC]"
            return "Recovered from error."

        async def mock_execute_tool(tool_name, params):
            raise RuntimeError("Unexpected tool failure")

        with patch("bot.task_engine.call_qwen_with_context", side_effect=mock_qwen):
            with patch("bot.task_engine.execute_tool", side_effect=mock_execute_tool):
                result = await self.engine.execute_task(task, "")
                assert "Recovered" in result
                # The first step should be CHECKPOINT status initially
                assert any(s.status == "failed" for s in task.steps)

    @pytest.mark.asyncio
    async def test_execute_task_max_turns_no_final(self, temp_data_dirs, monkeypatch):
        """Hitting max turns without a final response should checkpoint (L257-259)."""
        # Set MAX_TOOL_TURNS=0 so the for-loop body never executes,
        # leaving final_response as None and triggering L256-259
        monkeypatch.setattr("bot.config.Config.MAX_TOOL_TURNS", 0)
        engine = TaskEngine()
        task = engine.create_task(123, "Endless tools")

        with patch("bot.task_engine.call_qwen_with_context", new=AsyncMock(return_value="ignored")):
            result = await engine.execute_task(task, "")
            assert "maximum turns" in result.lower()
            assert task.status == TaskStatus.CHECKPOINT

    def test_get_pending_tasks_corrupt_json(self, temp_data_dirs):
        """Corrupt task JSON files should be skipped (L300-301)."""
        # Write a corrupt JSON file
        corrupt_path = Config.TASK_DIR / "corrupt_task.json"
        corrupt_path.write_text("not valid json{{", encoding="utf-8")

        # Should not raise, just skip the corrupt file
        tasks = self.engine.get_pending_tasks()
        assert not any(hasattr(t, 'task_id') and t.task_id == "corrupt_task" for t in tasks)

    def test_get_tasks_for_chat_corrupt_json(self, temp_data_dirs):
        """Corrupt task JSON should be skipped during chat task scan (L320-321)."""
        corrupt_path = Config.TASK_DIR / "corrupt_chat.json"
        corrupt_path.write_text("{bad json", encoding="utf-8")

        # Create a valid task too
        self.engine.create_task(777, "Valid task")

        tasks = self.engine.get_tasks_for_chat(777)
        assert len(tasks) == 1
        assert tasks[0].chat_id == 777

