# Configuration

All settings are managed through environment variables in the `.env` file.

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) | `123456789:ABC...` |
| `TELEGRAM_ADMIN_ID` | Your Telegram chat ID (leave empty for open access) | `123456789` |

### Optional — Tuning

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_TOOL_TURNS` | `15` | Max consecutive tool calls per request |
| `QWEN_TIMEOUT` | `600` | Seconds per Qwen CLI call |
| `MAX_RETRIES` | `3` | Retry attempts on Qwen failure |
| `MAX_HISTORY_LENGTH` | `50` | Messages per user before summarization |
| `RATE_LIMIT_MESSAGES` | `5` | Max messages per rate window |
| `RATE_LIMIT_WINDOW` | `10` | Rate limit window in seconds |
| `RESTART_EXIT_CODE` | `42` | Exit code for self-restart signal |

## Configuration Module

All configuration is centralized in `bot/config.py`. The `Config` class loads from `.env` with sensible defaults:

```python
from bot.config import Config

Config.TELEGRAM_BOT_TOKEN   # Bot token
Config.MAX_TOOL_TURNS       # 15
Config.QWEN_TIMEOUT         # 600
Config.BOT_ROOT             # Absolute path to project root
Config.TASK_DIR             # data/tasks/
Config.CONVERSATION_DIR     # data/conversations/
```

## Data Directories

These are auto-created on first run and should **not** be committed to git:

| Directory | Purpose |
|-----------|---------|
| `data/conversations/` | Per-user chat history JSON files |
| `data/tasks/` | Task checkpoint JSON files |

## Security Configuration

### Admin Lock

Set `TELEGRAM_ADMIN_ID` to restrict the bot to a single user. Leave empty to allow all users (not recommended for production).

### Rate Limiting

Built-in rate limiting prevents abuse:
- Default: 5 messages per 10-second window
- Configure via `RATE_LIMIT_MESSAGES` and `RATE_LIMIT_WINDOW`