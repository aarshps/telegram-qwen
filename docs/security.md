# Security

The Telegram-Qwen agent runs with full access to the host system. Understand the security model before deploying.

## Access Control

### Admin Lock

Set `TELEGRAM_ADMIN_ID` in `.env` to restrict the bot to a single Telegram user:

```
TELEGRAM_ADMIN_ID=123456789
```

- **Set** — Only this chat ID can interact with the bot. Others receive "🔒 Access denied"
- **Empty** — Any Telegram user can use the bot (not recommended for production)

### Rate Limiting

Built-in sliding-window rate limiter prevents abuse:
- Default: 5 messages per 10-second window
- Configurable via `RATE_LIMIT_MESSAGES` and `RATE_LIMIT_WINDOW`

## System Access

> ⚠️ **The bot has full admin access to the machine it runs on.**

The following tools execute with the same OS privileges as the Python process:

| Tool | Access Level |
|------|-------------|
| `FILE_READ` | Read any file on the system |
| `FILE_WRITE` | Write/create any file |
| `LIST_FILES` | List any directory |
| `EXEC` | Execute any shell command |
| `PYTHON` | Run arbitrary Python code |
| `SELF_MODIFY` | Edit bot source code (restricted to bot directory) |

### Recommendations

1. **Run under a limited user account** — Don't run as root/Administrator
2. **Use `TELEGRAM_ADMIN_ID`** — Always set this in production
3. **Network isolation** — Consider running in a VM or container
4. **Monitor logs** — The bot logs all tool executions
5. **Review `data/tasks/`** — Task checkpoints record all tool calls and results

## Self-Modification

The `SELF_MODIFY` tool can edit files within the bot's directory:
- Path is restricted to `Config.BOT_ROOT` — can't modify files outside the project
- After modification, `SELF_RESTART` exits with code 42
- The watchdog detects this and restarts the bot with the new code

## Data Storage

| Data | Location | Sensitivity |
|------|----------|-------------|
| Bot token | `.env` | **High** — Never commit to git |
| Chat history | `data/conversations/` | Medium — Contains user messages |
| Task checkpoints | `data/tasks/` | Medium — Contains tool call history |
| Logs | Console output | Low — Diagnostic information |

All data directories are in `.gitignore` by default.