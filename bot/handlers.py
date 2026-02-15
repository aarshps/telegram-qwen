"""
Telegram command and message handlers.
All commands, message processing, Markdown formatting, and rate limiting.
"""

import asyncio
import logging
import time
import os
import json
from telegram import Update, constants
from telegram.ext import ContextTypes

from bot.config import Config
from bot.memory import memory
from bot.task_engine import engine, TaskStatus
from bot.tools import extract_tool_calls, execute_tool
from bot.qwen import call_qwen_with_context

logger = logging.getLogger("telegram-qwen.handlers")

# Bot startup time for /status
BOT_START_TIME = time.time()

# Rate limiting tracker: {chat_id: [timestamps]}
_rate_limiter: dict[int, list[float]] = {}


def _check_auth(chat_id: int) -> bool:
    """Check if a user is authorized."""
    admin_id = Config.TELEGRAM_ADMIN_ID
    if not admin_id or admin_id == "your_chat_id_here":
        return True  # No admin ID set = allow everyone
    return str(chat_id) == admin_id


def _check_rate_limit(chat_id: int) -> bool:
    """Check rate limit. Returns True if allowed."""
    now = time.time()
    window = Config.RATE_LIMIT_WINDOW
    max_msgs = Config.RATE_LIMIT_MESSAGES

    if chat_id not in _rate_limiter:
        _rate_limiter[chat_id] = []

    # Clean old timestamps
    _rate_limiter[chat_id] = [t for t in _rate_limiter[chat_id] if now - t < window]

    if len(_rate_limiter[chat_id]) >= max_msgs:
        return False

    _rate_limiter[chat_id].append(now)
    return True


async def _send_safe(update: Update, text: str, parse_mode: str = None) -> None:
    """Send a message, splitting if too long. Tries Markdown first, falls back to plain text."""
    if not text:
        text = "_(empty response)_"

    # Try with markdown first, fall back to plain text on parse error
    for chunk_start in range(0, len(text), Config.MAX_MESSAGE_LENGTH):
        chunk = text[chunk_start:chunk_start + Config.MAX_MESSAGE_LENGTH]
        try:
            await update.message.reply_text(chunk, parse_mode=parse_mode)
        except Exception:
            # If markdown parsing fails, send as plain text
            try:
                await update.message.reply_text(chunk)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")


async def send_typing_indicator(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Continuously send typing indicator until cancelled."""
    try:
        while True:
            await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
        except Exception:
            pass
        raise


# ─── Command: /start ────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message with capabilities overview."""
    if not _check_auth(update.effective_chat.id):
        await update.message.reply_text("🔒 Access denied.")
        return

    await update.message.reply_text(
        "🤖 *Qwen Autonomous Agent*\n\n"
        "I'm a powerful AI agent with full system access. I can:\n\n"
        "🔍 *Search & Browse* — web search, read web pages\n"
        "📁 *File Operations* — read/write any file on the system\n"
        "⚡ *Execute Commands* — run any shell command or Python code\n"
        "🔧 *Self-Modify* — edit my own code and restart\n"
        "🔄 *Long Tasks* — handle multi-step tasks with checkpoints\n\n"
        "*Commands:*\n"
        "/help — Detailed help & examples\n"
        "/reset — Clear conversation history\n"
        "/status — Bot status & system info\n"
        "/tasks — View active/pending tasks\n"
        "/resume — Resume a failed task\n"
        "/selfupdate — Force restart\n\n"
        "Just send me a message to get started! 💬",
        parse_mode="Markdown",
    )


# ─── Command: /help ─────────────────────────────────────────────────────────

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detailed help with examples."""
    if not _check_auth(update.effective_chat.id):
        await update.message.reply_text("🔒 Access denied.")
        return

    await update.message.reply_text(
        "📖 *Help — What I Can Do*\n\n"
        "*🔍 Web Search:*\n"
        "• \"Search for the latest Python release\"\n"
        "• \"What's the current Bitcoin price?\"\n\n"
        "*🌐 Web Reading:*\n"
        "• \"Read this article: https://example.com\"\n"
        "• \"Summarize this webpage for me\"\n\n"
        "*📁 File Operations:*\n"
        "• \"Read the file at C:/Users/Aarsh/notes.txt\"\n"
        "• \"Create a Python script that does X\"\n\n"
        "*⚡ System Commands:*\n"
        "• \"What's my IP address?\"\n"
        "• \"Install pandas with pip\"\n"
        "• \"List running processes\"\n\n"
        "*🐍 Python Execution:*\n"
        "• \"Write and run a Python script to analyze CSV data\"\n"
        "• \"Calculate the factorial of 100\"\n\n"
        "*🔧 Self-Modification:*\n"
        "• \"Add a new tool that can XYZ\"\n"
        "• \"Improve your system prompt\"\n\n"
        "*🔄 Long Tasks:*\n"
        "Up to 15 tool turns per request. Tasks checkpoint automatically.\n"
        "If I crash mid-task, use /resume to continue.\n\n"
        "*⚠️ I have full admin access. Use wisely!*",
        parse_mode="Markdown",
    )


# ─── Command: /reset ────────────────────────────────────────────────────────

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear conversation history."""
    if not _check_auth(update.effective_chat.id):
        await update.message.reply_text("🔒 Access denied.")
        return

    chat_id = update.effective_chat.id
    memory.reset(chat_id)
    await update.message.reply_text("🗑️ Conversation history cleared. Fresh start!")


# ─── Command: /status ───────────────────────────────────────────────────────

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot status and system info."""
    if not _check_auth(update.effective_chat.id):
        await update.message.reply_text("🔒 Access denied.")
        return

    chat_id = update.effective_chat.id
    uptime_seconds = int(time.time() - BOT_START_TIME)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    mem_stats = memory.get_stats(chat_id)
    pending_tasks = engine.get_pending_tasks()

    # Check Qwen availability
    qwen_status = "❓ Unknown"
    try:
        proc = await asyncio.create_subprocess_shell(
            "qwen --version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        if proc.returncode == 0:
            version = stdout.decode().strip() if stdout else "unknown"
            qwen_status = f"✅ Available ({version})"
        else:
            qwen_status = "⚠️ Error"
    except Exception:
        qwen_status = "❌ Unavailable"

    # System info
    sys_info = ""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/") if os.name != "nt" else psutil.disk_usage("C:/")
        sys_info = (
            f"\n*System:*\n"
            f"• CPU: {cpu}%\n"
            f"• RAM: {mem.percent}% ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)\n"
            f"• Disk: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)"
        )
    except ImportError:
        sys_info = "\n_(Install psutil for system stats)_"

    await update.message.reply_text(
        f"📊 *Bot Status*\n\n"
        f"*Uptime:* {hours}h {minutes}m {seconds}s\n"
        f"*Qwen:* {qwen_status}\n"
        f"*Memory:* {mem_stats['message_count']}/{mem_stats['max_length']} messages\n"
        f"*Pending Tasks:* {len(pending_tasks)}\n"
        f"*Config:*\n"
        f"• Max tool turns: {Config.MAX_TOOL_TURNS}\n"
        f"• Qwen timeout: {Config.QWEN_TIMEOUT}s\n"
        f"• Max retries: {Config.MAX_RETRIES}"
        f"{sys_info}",
        parse_mode="Markdown",
    )


# ─── Command: /tasks ────────────────────────────────────────────────────────

async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show tasks for this chat."""
    if not _check_auth(update.effective_chat.id):
        await update.message.reply_text("🔒 Access denied.")
        return

    chat_id = update.effective_chat.id
    tasks = engine.get_tasks_for_chat(chat_id)

    if not tasks:
        await update.message.reply_text("📋 No tasks found.")
        return

    status_icons = {
        TaskStatus.PENDING: "⏳",
        TaskStatus.RUNNING: "🔄",
        TaskStatus.CHECKPOINT: "💾",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.FAILED: "❌",
    }

    lines = ["📋 *Your Tasks*\n"]
    for t in tasks:
        icon = status_icons.get(t.status, "❓")
        request_preview = t.user_request[:60]
        if len(t.user_request) > 60:
            request_preview += "..."
        steps = len(t.steps)
        lines.append(f"{icon} `{t.task_id}` — {request_preview}")
        lines.append(f"   Steps: {steps} | Retries: {t.retry_count}")

    lines.append(f"\nUse `/resume <task_id>` to resume a failed/checkpointed task.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─── Command: /resume ───────────────────────────────────────────────────────

async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resume a checkpointed or failed task."""
    if not _check_auth(update.effective_chat.id):
        await update.message.reply_text("🔒 Access denied.")
        return

    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        # Find the most recent resumable task
        tasks = engine.get_tasks_for_chat(chat_id)
        resumable = [t for t in tasks if t.status in (TaskStatus.CHECKPOINT, TaskStatus.FAILED)]
        if not resumable:
            await update.message.reply_text("No resumable tasks found. Use /tasks to see all tasks.")
            return
        task = resumable[0]
    else:
        task_id = args[0]
        task = engine.get_task(task_id)
        if not task:
            await update.message.reply_text(f"Task `{task_id}` not found.", parse_mode="Markdown")
            return

    await update.message.reply_text(
        f"🔄 Resuming task `{task.task_id}`...\n"
        f"Original request: _{task.user_request[:100]}_\n"
        f"Resuming from step {task.current_step + 1}",
        parse_mode="Markdown",
    )

    # Start typing indicator
    typing_task = asyncio.create_task(send_typing_indicator(context, chat_id))

    try:
        history = memory.get_formatted(chat_id)

        async def progress_cb(msg: str):
            try:
                await context.bot.send_message(chat_id=chat_id, text=msg)
            except Exception:
                pass

        response = await engine.execute_task(task, history, progress_callback=progress_cb)
        memory.add(chat_id, "assistant", response)
        await _send_safe(update, response, parse_mode="Markdown")

    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass


# ─── Command: /selfupdate ───────────────────────────────────────────────────

async def cmd_selfupdate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger a bot restart."""
    if not _check_auth(update.effective_chat.id):
        await update.message.reply_text("🔒 Access denied.")
        return

    await update.message.reply_text("🔄 Restarting bot... I'll be back in a moment!")
    logger.info("Self-update triggered by admin command")

    # Schedule exit after a short delay to allow message to send
    await asyncio.sleep(1)
    os._exit(Config.RESTART_EXIT_CODE)


# ─── Message Handler ────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages — the main agent loop."""
    chat_id = update.effective_chat.id

    if not _check_auth(chat_id):
        await update.message.reply_text("🔒 Access denied.")
        return

    if not _check_rate_limit(chat_id):
        await update.message.reply_text("⏱️ Slow down! Rate limit reached. Wait a few seconds.")
        return

    user_message = update.message.text
    if not user_message:
        return

    logger.info(f"Message from {update.effective_user.id}: {user_message[:100]}")

    # Add to memory
    memory.add(chat_id, "user", user_message)

    # Start typing indicator
    typing_task = asyncio.create_task(send_typing_indicator(context, chat_id))

    try:
        # Create a task for tracking
        task = engine.create_task(chat_id, user_message)

        # Get conversation history
        history = memory.get_formatted(chat_id)

        # Progress callback for long tasks
        async def progress_cb(msg: str):
            try:
                await context.bot.send_message(chat_id=chat_id, text=msg)
            except Exception:
                pass

        # Execute the task through the engine
        response = await engine.execute_task(task, history, progress_callback=progress_cb)

        # Save response to memory
        memory.add(chat_id, "assistant", response)

        # Send response
        await _send_safe(update, response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await _send_safe(update, f"❌ An error occurred: {str(e)}")

    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
