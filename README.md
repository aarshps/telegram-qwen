# Telegram-Qwen Autonomous Agent

A powerful autonomous AI agent that connects Telegram with the Qwen AI model. Features persistent task execution, self-modification, auto-restart, web search, and full system access.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Web Search** | Search the web via DuckDuckGo |
| 🌐 **Web Reading** | Fetch and extract text from any URL |
| 📁 **File Operations** | Read/write any file on the system |
| ⚡ **Command Execution** | Run any shell command |
| 🐍 **Python Execution** | Execute Python code directly |
| 🔧 **Self-Modification** | Edit its own source code |
| 🔄 **Auto-Restart** | Watchdog with crash recovery |
| 💾 **Task Checkpoints** | Resume long tasks after failures |
| 🧠 **Persistent Memory** | Per-user conversation history |
| 🔒 **Admin Lock** | Restrict access to authorized users |

## Prerequisites

- Python 3.10+
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- Qwen CLI (`npm install -g @qwen-code/qwen-code`)

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone https://github.com/aarshps/telegram-qwen.git
   cd telegram-qwen
   pip install -r requirements.txt
   ```

2. **Configure `.env`:**
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_ADMIN_ID=your_chat_id
   ```

3. **Run with auto-restart (recommended):**
   ```bash
   python watchdog.py
   ```

   Or run directly:
   ```bash
   python telegram_qwen_bridge.py
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Detailed help with examples |
| `/reset` | Clear conversation history |
| `/status` | Bot uptime, Qwen health, system stats |
| `/tasks` | View active/pending/failed tasks |
| `/resume [id]` | Resume a failed or checkpointed task |
| `/selfupdate` | Force restart the bot |

## Architecture

```
telegram-qwen/
├── telegram_qwen_bridge.py  # Entry point
├── watchdog.py              # Auto-restart wrapper
├── bot/
│   ├── __init__.py
│   ├── config.py            # Centralized configuration
│   ├── memory.py            # Persistent conversation memory
│   ├── tools.py             # 9 tools (web, file, exec, self-modify...)
│   ├── qwen.py              # Qwen CLI with retry logic
│   ├── task_engine.py       # Checkpoint/resume task engine
│   └── handlers.py          # Telegram command handlers
├── data/
│   ├── conversations/       # Per-user chat history (auto-created)
│   └── tasks/               # Task checkpoints (auto-created)
├── requirements.txt
└── .env
```

## Configuration

All settings in `.env` (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | — | Bot token from BotFather |
| `TELEGRAM_ADMIN_ID` | — | Your Telegram chat ID |
| `MAX_TOOL_TURNS` | 15 | Max tool calls per request |
| `QWEN_TIMEOUT` | 600 | Seconds per Qwen call |
| `MAX_RETRIES` | 3 | Retry attempts on failure |
| `MAX_HISTORY_LENGTH` | 50 | Messages per user before compression |
| `RATE_LIMIT_MESSAGES` | 5 | Max messages per window |
| `RATE_LIMIT_WINDOW` | 10 | Rate limit window (seconds) |

## How Long Tasks Work

1. Every message creates a **Task** tracked with a unique ID
2. The agent can chain up to **15 tool calls** per request
3. After each tool call, state is **checkpointed** to disk
4. If Qwen fails, it **retries 3 times** with exponential backoff
5. If the bot crashes, use `/resume` to **continue from checkpoint**
6. Progress updates sent every **60 seconds** during long operations

## Self-Modification

The agent can edit its own source files using the `SELF_MODIFY` tool and restart itself with `SELF_RESTART`. The watchdog detects the restart signal (exit code 42) and immediately relaunches the bot.

## Testing

220 tests with **100% code coverage** across all modules.

```bash
# Run all tests
pytest

# Quick run without coverage
pytest --no-cov -q
```

See [docs/testing.md](docs/testing.md) for details.

## Documentation

Full documentation is in the [`docs/`](docs/) directory:

- [Getting Started](docs/getting-started.md)
- [Installation Guide](docs/installation-guide.md)
- [Configuration](docs/configuration.md)
- [Usage Guide](docs/usage-guide.md)
- [Architecture](docs/architecture.md)
- [Testing](docs/testing.md)
- [Security](docs/security.md)
- [Advanced Features](docs/advanced-features.md)
- [Troubleshooting](docs/troubleshooting.md)
- [FAQ](docs/faq.md)
- [Contributing](docs/contributing.md)

## License

MIT License — see [LICENSE](LICENSE).

## Disclaimer

This bot has full admin access to the machine it runs on. Only run it on trusted systems and restrict access via `TELEGRAM_ADMIN_ID`.