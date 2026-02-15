# FAQ

Frequently asked questions about the Telegram-Qwen agent.

## General

### What is this project?

A Telegram bot powered by Qwen AI that acts as an autonomous agent. It can search the web, read/write files, execute commands, modify its own code, and run multi-step tasks with checkpoint recovery.

### Is it safe to run?

The bot has full access to the machine it runs on. Only deploy on trusted systems and always set `TELEGRAM_ADMIN_ID` to restrict access. See [Security](security.md) for details.

### What AI model does it use?

It uses the Qwen CLI (`@qwen-code/qwen-code`), which runs locally on your machine. No API keys or cloud services required for the AI model itself.

## Setup

### Do I need a GPU?

No. The Qwen CLI handles model inference. Check the Qwen CLI documentation for hardware requirements.

### Can I run it on a server?

Yes. Use `python watchdog.py` for production. The watchdog handles crash recovery and auto-restart.

### What Python version do I need?

Python 3.10 or higher. Tested on Python 3.14.

## Usage

### How many tools can the bot chain in one request?

Up to 15 tool calls per request (configurable via `MAX_TOOL_TURNS`).

### What happens if the bot crashes mid-task?

The task is checkpointed after each tool call. Use `/resume <task_id>` to continue from the last checkpoint.

### How do I restrict access to my bot?

Set `TELEGRAM_ADMIN_ID` in `.env` to your Telegram chat ID. Only you will be able to interact with the bot.

### Can the bot modify its own code?

Yes, using the `SELF_MODIFY` tool. Changes are applied after `SELF_RESTART`. The watchdog detects exit code 42 and restarts the bot immediately.

### How long can a task run?

There's no hard limit on overall task duration. Individual Qwen calls have a 10-minute timeout, but tasks can chain up to 15 calls. Use `/resume` to continue after the turn limit.

## Troubleshooting

### The bot is slow to respond

Qwen CLI processing time depends on the complexity of the request. Each call has a 10-minute timeout. Check `qwen --help` for tuning options.

### I'm getting rate limited

The bot has a built-in rate limiter (5 messages per 10 seconds by default). Wait a few seconds and try again, or increase `RATE_LIMIT_MESSAGES` in `.env`.

### Web search returns nothing

DuckDuckGo may occasionally rate-limit. Wait a moment and retry.

## Development

### How do I run the tests?

```bash
pytest
```

This runs all 220 tests with 100% coverage. See [Testing](testing.md) for details.

### How do I add a new tool?

1. Add the tool function to `bot/tools.py` (follow the existing pattern)
2. Add the tool description to `TOOL_DESCRIPTIONS`
3. Add the tool to the dispatch logic in `task_engine.py`
4. Add tests in `tests/test_tools.py`
5. Run `pytest` and verify 100% coverage

### How do I add a new command?

1. Create the handler function in `bot/handlers.py`
2. Register it in `telegram_qwen_bridge.py` with `app.add_handler(CommandHandler(...))`
3. Add tests in `tests/test_handlers.py`