# Troubleshooting

Common issues and their solutions.

## Bot Won't Start

### "TELEGRAM_BOT_TOKEN not set"

```
Ensure .env exists and contains:
TELEGRAM_BOT_TOKEN=your_token_here
```

### "Module not found" errors

```bash
pip install -r requirements.txt
```

### Qwen CLI not found

```bash
npm install -g @qwen-code/qwen-code
qwen --help  # Verify installation
```

## Bot Doesn't Respond

### Check admin lock

If `TELEGRAM_ADMIN_ID` is set, only that user can interact. Check the value matches your Telegram chat ID.

### Check rate limiting

If you send too many messages quickly, the rate limiter will silently drop them. Wait 10 seconds and try again.

### Check the console

The bot logs all activity to the console. Look for error messages.

## Tool Execution Issues

### EXEC commands fail on Windows

Windows commands are automatically wrapped in `cmd /c`. If a command fails, try prefixing it explicitly:

```
Run: cmd /c dir
```

### PYTHON tool fails

The PYTHON tool writes to a temp file in the project directory. Ensure the bot has write permissions.

### WEB_SEARCH returns empty

DuckDuckGo may rate-limit searches. Wait a few seconds and try again.

## Task Issues

### Task stuck in "running" state

If the bot crashed during a task, it may be stuck. Use `/tasks` to see all tasks and `/resume <id>` to retry.

### "Maximum turns reached"

The agent hit the 15-turn limit. The task is checkpointed. Use `/resume` to continue from where it left off, or rephrase your request to be more specific.

## Memory Issues

### Bot doesn't remember previous messages

Check that `data/conversations/` exists and is writable. The bot auto-creates this directory on startup.

### History seems corrupted

Use `/reset` to clear your conversation history and start fresh.

## Watchdog Issues

### Bot keeps restarting

Check the console for crash errors. If the bot crashes 5 times in 60 seconds, the watchdog enters a 2-minute cooldown.

### Watchdog won't stop

Press `Ctrl+C` to stop the watchdog. If that doesn't work, kill the Python process.

## Getting Help

1. Check the console output for error messages
2. Review `data/tasks/` for task checkpoint files (they contain error details)
3. Open an issue on [GitHub](https://github.com/aarshps/telegram-qwen/issues)