# Getting Started

Get the Telegram-Qwen Agent running in under 5 minutes.

## Prerequisites

- **Python 3.10+** (3.14 tested)
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
- **Qwen CLI** installed globally: `npm install -g @qwen-code/qwen-code`
- **Git** (to clone the repo)

## Quick Setup

```bash
# 1. Clone
git clone https://github.com/aarshps/telegram-qwen.git
cd telegram-qwen

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
.\venv\Scripts\activate    # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_ID

# 5. Run with auto-restart (recommended)
python watchdog.py
```

## First Steps

1. Open Telegram and message your bot
2. Send `/start` — you'll see a welcome message listing capabilities
3. Send `/help` — detailed usage examples
4. Try a message like "What files are in my home directory?" to verify tool execution
5. Send `/status` to check system health

## What's Next

- [Configuration](configuration.md) — Tune timeouts, retry counts, rate limits
- [Usage Guide](usage-guide.md) — Full command and tool reference
- [Architecture](architecture.md) — Understand the module design