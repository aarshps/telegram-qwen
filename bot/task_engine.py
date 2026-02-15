"""
Persistent Task Execution Engine with checkpoint/resume.
Handles long-running multi-step tasks with automatic retry and progress reporting.
"""

import asyncio
import json
import logging
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Awaitable

from bot.config import Config
from bot.tools import extract_tool_calls, execute_tool
from bot.qwen import call_qwen_with_context
from bot.memory import memory

logger = logging.getLogger("telegram-qwen.task_engine")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    CHECKPOINT = "checkpoint"  # Saved mid-task, can be resumed
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStep:
    """A single step in a task's execution."""

    def __init__(self, index: int, tool_name: str = "", tool_params: str = "",
                 tool_result: str = "", qwen_response: str = "", status: str = "pending"):
        self.index = index
        self.tool_name = tool_name
        self.tool_params = tool_params
        self.tool_result = tool_result
        self.qwen_response = qwen_response
        self.status = status

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "tool_result": self.tool_result,
            "qwen_response": self.qwen_response,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskStep":
        return cls(**data)


class Task:
    """A persistent task with checkpoint/resume support."""

    def __init__(self, task_id: str, chat_id: int, user_request: str,
                 status: str = TaskStatus.PENDING, steps: list = None,
                 current_step: int = 0, retry_count: int = 0,
                 created_at: float = None, updated_at: float = None):
        self.task_id = task_id
        self.chat_id = chat_id
        self.user_request = user_request
        self.status = status
        self.steps: list[TaskStep] = steps or []
        self.current_step = current_step
        self.retry_count = retry_count
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or time.time()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "chat_id": self.chat_id,
            "user_request": self.user_request,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
            "current_step": self.current_step,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        steps = [TaskStep.from_dict(s) for s in data.get("steps", [])]
        return cls(
            task_id=data["task_id"],
            chat_id=data["chat_id"],
            user_request=data["user_request"],
            status=data.get("status", TaskStatus.PENDING),
            steps=steps,
            current_step=data.get("current_step", 0),
            retry_count=data.get("retry_count", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def save(self) -> None:
        """Save task state to disk."""
        Config.ensure_dirs()
        self.updated_at = time.time()
        path = Config.TASK_DIR / f"{self.task_id}.json"
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, task_id: str) -> Optional["Task"]:
        """Load a task from disk."""
        path = Config.TASK_DIR / f"{task_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load task {task_id}: {e}")
            return None

    def get_context_summary(self) -> str:
        """Build a context summary of completed steps for prompt injection."""
        if not self.steps:
            return ""

        lines = [f"Original request: {self.user_request}", "Steps completed so far:"]
        for step in self.steps:
            if step.status == "completed":
                lines.append(f"  Step {step.index + 1}: Used {step.tool_name}")
                if step.tool_result:
                    # Truncate long results in context
                    result_preview = step.tool_result[:300]
                    if len(step.tool_result) > 300:
                        result_preview += "..."
                    lines.append(f"    Result: {result_preview}")
        lines.append(f"\nResume from step {self.current_step + 1}. Continue the task.")
        return "\n".join(lines)


# Type for the progress callback
ProgressCallback = Callable[[str], Awaitable[None]]


class TaskEngine:
    """Manages task execution with checkpoint/resume and progress reporting."""

    def __init__(self):
        Config.ensure_dirs()
        self.active_tasks: dict[str, Task] = {}

    def create_task(self, chat_id: int, user_request: str) -> Task:
        """Create a new task."""
        task = Task(
            task_id=str(uuid.uuid4())[:8],
            chat_id=chat_id,
            user_request=user_request,
        )
        task.save()
        self.active_tasks[task.task_id] = task
        return task

    async def execute_task(
        self,
        task: Task,
        conversation_history: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> str:
        """
        Execute a task with full tool loop, checkpointing, and retry logic.
        Returns the final response text.
        """
        task.status = TaskStatus.RUNNING
        task.save()

        current_input = task.user_request
        task_context = ""

        # If resuming, inject checkpoint context
        if task.current_step > 0:
            task_context = task.get_context_summary()
            current_input = f"Continue this task from where it left off."

        last_progress_time = time.time()
        final_response = ""

        for turn in range(task.current_step, Config.MAX_TOOL_TURNS):
            task.current_step = turn

            # Progress reporting
            if progress_callback and (time.time() - last_progress_time) > Config.PROGRESS_INTERVAL:
                total_steps = len(task.steps)
                await progress_callback(
                    f"⏳ Still working... completed step {total_steps}/{Config.MAX_TOOL_TURNS} max"
                )
                last_progress_time = time.time()

            # Call Qwen with retry
            qwen_response = await self._call_with_retry(
                current_input, conversation_history, task_context, task
            )

            if qwen_response.startswith("❌"):
                # All retries failed
                task.status = TaskStatus.FAILED
                task.save()
                return qwen_response

            # Check for tool calls
            tool_name, tool_params = extract_tool_calls(qwen_response)

            if tool_name and turn < Config.MAX_TOOL_TURNS - 1:
                # Execute tool
                step = TaskStep(
                    index=turn,
                    tool_name=tool_name,
                    tool_params=tool_params[0] if tool_params else "",
                    qwen_response=qwen_response,
                )
                task.steps.append(step)

                try:
                    tool_result = await execute_tool(tool_name, tool_params)
                    result_text = json.dumps(tool_result, ensure_ascii=False)
                    step.tool_result = result_text
                    step.status = "completed"

                    # Checkpoint after each successful tool execution
                    task.save()

                    # Feed result back for next turn
                    current_input = f"Tool [{tool_name}] result:\n{result_text}\n\nContinue with the task. If done, provide your final response to the user."
                    # Clear task_context after first resume turn
                    task_context = ""

                except Exception as e:
                    step.tool_result = f"Tool execution error: {e}"
                    step.status = "failed"
                    task.status = TaskStatus.CHECKPOINT
                    task.save()

                    logger.error(f"Tool execution failed at step {turn}: {e}")

                    # Try to recover by telling Qwen about the error
                    current_input = f"Tool [{tool_name}] failed with error: {e}\n\nPlease try an alternative approach or diagnose the issue."
                    task_context = ""

            else:
                # No tool call or final turn — this is the final response
                final_response = qwen_response
                task.status = TaskStatus.COMPLETED
                task.save()
                break

        if not final_response:
            final_response = "Task reached maximum turns without a final response. Use /tasks to check status."
            task.status = TaskStatus.CHECKPOINT
            task.save()

        # Cleanup completed task from active tracking
        self.active_tasks.pop(task.task_id, None)

        return final_response

    async def _call_with_retry(
        self, user_input: str, conversation_history: str,
        task_context: str, task: Task
    ) -> str:
        """Call Qwen with retry logic specific to the task engine."""
        for attempt in range(Config.MAX_RETRIES):
            response = await call_qwen_with_context(
                user_input, conversation_history, task_context
            )

            if response and not response.startswith("❌"):
                return response

            task.retry_count += 1
            logger.warning(f"Task {task.task_id} retry {attempt + 1}")

            if attempt < Config.MAX_RETRIES - 1:
                wait = 5 * (3 ** attempt)
                await asyncio.sleep(wait)

        task.status = TaskStatus.FAILED
        task.save()
        return f"❌ Task failed after {Config.MAX_RETRIES} retry attempts."

    def get_pending_tasks(self) -> list[Task]:
        """Get all tasks that can be resumed (checkpoint or failed)."""
        Config.ensure_dirs()
        tasks = []
        for path in Config.TASK_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                task = Task.from_dict(data)
                if task.status in (TaskStatus.CHECKPOINT, TaskStatus.FAILED, TaskStatus.RUNNING):
                    tasks.append(task)
            except (json.JSONDecodeError, OSError):
                continue
        return tasks

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task."""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        return Task.load(task_id)

    def get_tasks_for_chat(self, chat_id: int) -> list[Task]:
        """Get all tasks for a specific chat."""
        Config.ensure_dirs()
        tasks = []
        for path in Config.TASK_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                task = Task.from_dict(data)
                if task.chat_id == chat_id:
                    tasks.append(task)
            except (json.JSONDecodeError, OSError):
                continue
        # Sort by most recent first
        tasks.sort(key=lambda t: t.updated_at or 0, reverse=True)
        return tasks[:10]  # Last 10 tasks


# Global singleton
engine = TaskEngine()
