# Architecture

The Telegram-Qwen agent is built as a modular Python application with a watchdog wrapper.

## System Overview

```
watchdog.py                    ← Auto-restart wrapper
  └── telegram_qwen_bridge.py  ← Entry point — initializes bot
        └── bot/               ← Core package
            ├── config.py      ← Centralized configuration
            ├── memory.py      ← Per-user persistent conversation history
            ├── qwen.py        ← Qwen CLI integration with retry logic
            ├── tools.py       ← 9 tools (web, file, exec, self-modify)
            ├── task_engine.py ← Task state machine with checkpoints
            └── handlers.py    ← Telegram command and message handlers
```

## Data Flow

```
User Message → Telegram API → handlers.py → task_engine.py → qwen.py → Qwen CLI
                                                  ↕                        ↓
                                            tools.py ← ← ← ← ← ← Tool Call
                                                  ↓
                                          Result → Next Turn
```

1. **Message arrives** — `handlers.py` receives it, checks auth and rate limits
2. **Task created** — `task_engine.py` creates a `Task` with unique ID
3. **Qwen called** — `qwen.py` sends the prompt to Qwen CLI via subprocess
4. **Tool extraction** — Response is parsed for `[TOOL]...[/TOOL]` tags
5. **Tool execution** — `tools.py` runs the requested tool
6. **Loop continues** — Result feeds back to Qwen for next turn (up to 15 turns)
7. **Checkpoint** — After each tool call, task state is saved to disk
8. **Response sent** — Final text sent back to the user

## Module Details

### `config.py`
Loads all settings from `.env` with defaults. Exposes `Config` class with class-level attributes. Auto-creates `data/` directories on import.

### `memory.py`
- Per-user conversation history stored as JSON in `data/conversations/{chat_id}.json`
- Auto-loads on first message, auto-saves after each exchange
- Configurable max length with LRU-style trimming
- Thread-safe with file-based persistence

### `qwen.py`
- Calls Qwen via `asyncio.create_subprocess_shell`
- Retry logic: 3 attempts with exponential backoff (5s → 15s → 45s)
- 10-minute timeout per call
- Returns clean text response or error message

### `tools.py`
9 tools with structured `{status, output, truncated}` responses:
- **WEB_SEARCH** — DuckDuckGo search
- **WEB_READ** — HTTP fetch + BeautifulSoup HTML extraction
- **FILE_READ** / **FILE_WRITE** — Filesystem access (no restrictions)
- **LIST_FILES** — Directory listing
- **EXEC** — Shell command execution (platform-aware)
- **PYTHON** — Execute Python via temp script
- **SELF_MODIFY** — Edit bot source files (path-restricted to bot root)
- **SELF_RESTART** — Exit with code 42, triggering watchdog restart

### `task_engine.py`
State machine: `PENDING → RUNNING → COMPLETED | CHECKPOINT | FAILED`
- Each task has a unique ID, steps list, retry count, and timestamps
- Checkpoints saved to `data/tasks/{task_id}.json` after each step
- `get_pending_tasks()` scans for incomplete tasks on startup
- Progress callbacks for real-time status updates

### `handlers.py`
Telegram bot handlers:
- Auth check (`_check_auth`) — validates `TELEGRAM_ADMIN_ID`
- Rate limiting (`_check_rate_limit`) — sliding window
- Safe message sending (`_send_safe`) — auto-splits long messages
- 7 command handlers + 1 message handler

### `watchdog.py`
Process supervisor:
- Exit code 0 → clean shutdown
- Exit code 42 → intentional restart (immediate)
- Other exit codes → crash recovery (5s wait)
- Rapid restart detection (5 restarts in 60s → 2min cooldown)
