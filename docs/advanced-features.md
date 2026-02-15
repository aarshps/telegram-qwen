# Advanced Features

Deep-dive into the agent's advanced capabilities.

## Task Checkpoint & Resume

### How It Works

1. Every user message creates a `Task` with a unique ID
2. The task progresses through states: `PENDING → RUNNING → COMPLETED`
3. After each tool call, the full state is saved to `data/tasks/{task_id}.json`
4. If the bot crashes or Qwen fails, the task moves to `CHECKPOINT` or `FAILED`
5. Use `/resume <task_id>` to continue from the last checkpoint

### Task States

| State | Meaning |
|-------|---------|
| `pending` | Created but not yet started |
| `running` | Currently executing |
| `checkpoint` | Paused — can be resumed |
| `completed` | Finished successfully |
| `failed` | Failed after all retries |

### Retry Logic

- Each Qwen call retries up to 3 times on failure
- Exponential backoff: 5s → 15s → 45s
- After all retries fail, the task is checkpointed for manual resume

## Self-Modification

The agent can edit its own source code:

```
You: Add a /ping command that responds with "Pong!"
Bot: [Uses SELF_MODIFY to edit handlers.py, then SELF_RESTART to apply changes]
```

### Safety

- `SELF_MODIFY` is path-restricted to the bot's root directory
- Cannot modify files outside the project (e.g., `/etc/passwd`)
- Changes are only applied after `SELF_RESTART`

## Watchdog Auto-Restart

The `watchdog.py` script supervises the bot process:

```bash
python watchdog.py
```

### Restart Behavior

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| `0` | Clean shutdown | Watchdog stops |
| `42` | Self-restart requested | Immediate restart (1s pause) |
| Other | Crash | Restart after 5s wait |

### Rapid Restart Protection

If the bot crashes 5 times within 60 seconds, the watchdog enters a 2-minute cooldown to prevent CPU thrashing.

## Web Tools

### Web Search

Uses DuckDuckGo (no API key required):
```
You: Search for the latest Python release
Bot: [Searches DuckDuckGo, returns top results with titles and URLs]
```

### Web Read

Fetches and extracts clean text from web pages:
- Uses `httpx` for async HTTP requests
- `BeautifulSoup` for HTML parsing
- Strips navigation, footers, and scripts
- Output is truncated to 5000 characters

## Shell Execution

### Platform-Aware

The `EXEC` tool is platform-aware:
- **Windows** — Wraps commands in `cmd /c` (unless already prefixed with `cmd` or `powershell`)
- **Unix** — Runs commands directly via the default shell

### Timeout

Commands time out after 10 minutes (`Config.QWEN_TIMEOUT`).

## Python Execution

The `PYTHON` tool:
1. Writes code to a temporary file
2. Runs it as a subprocess
3. Captures stdout and stderr
4. Cleans up the temp file

This allows executing multi-line Python scripts without importing them into the bot's process.

## Conversation Memory

### Persistence

- History is stored per-user in `data/conversations/{chat_id}.json`
- Loaded automatically on first message from a user
- Saved after every exchange

### Memory Management

- When history exceeds `MAX_HISTORY_LENGTH`, oldest messages are trimmed
- `/reset` clears all history for the current user
- Memory includes both user messages and bot responses