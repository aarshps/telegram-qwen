# Installation Guide

Detailed platform-specific installation instructions.

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.10 | 3.12+ |
| Node.js | 18 | 20+ (for Qwen CLI) |
| RAM | 512 MB | 2 GB |
| Disk | 100 MB | 500 MB |

## Step 1: Install Qwen CLI

The agent uses Qwen via its CLI. Install it globally:

```bash
npm install -g @qwen-code/qwen-code
```

Verify installation:

```bash
qwen --help
```

## Step 2: Clone the Repository

```bash
git clone https://github.com/aarshps/telegram-qwen.git
cd telegram-qwen
```

## Step 3: Python Environment

### Using the Setup Script

**Windows:**
```cmd
setup.bat
```

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
.\venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## Step 4: Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the bot token (format: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)

## Step 5: Get Your Chat ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your numeric chat ID

## Step 6: Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_ID=your_chat_id_here
```

## Step 7: Start the Bot

**With auto-restart (recommended for production):**
```bash
python watchdog.py
```

**Direct start (for development):**
```bash
python telegram_qwen_bridge.py
```

## Verifying the Installation

1. The console should show: `Bot started successfully`
2. Message your bot on Telegram with `/start`
3. You should receive a welcome message with the feature list

## Dependencies

All dependencies are in `requirements.txt`:

| Package | Purpose |
|---------|---------|
| `python-telegram-bot` | Telegram Bot API |
| `python-dotenv` | Environment variable loading |
| `beautifulsoup4` | HTML content extraction |
| `duckduckgo-search` | Web search tool |
| `psutil` | System status information |
| `httpx` | Async HTTP client |

### Test Dependencies

| Package | Purpose |
|---------|---------|
| `pytest` | Test framework |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Coverage reporting |