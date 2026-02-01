# Telegram-Qwen CLI Bridge

[![GitHub Repo](https://img.shields.io/badge/GitHub-telegram--qwen-blue?logo=github)](https://github.com/aarshps/telegram-qwen)

A simple bridge to connect Telegram chat with your local Qwen CLI.

## Setup

1. Create a Telegram bot with [BotFather](https://core.telegram.org/bots#botfather) and get your bot token.

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set your Telegram bot token. You can copy `.env.example` to `.env` and fill in your token:
   ```bash
   cp .env.example .env
   ```
   *Note: Ensure you have a way to load these environment variables (like `python-dotenv`) or export them manually.*


4. Make sure your Qwen CLI is installed and accessible from your command line.

## Usage

Run the bridge:
```bash
python telegram_qwen_bridge.py
```

Then, send a message to your Telegram bot and it will forward it to Qwen CLI and return the response.

## Configuration

The script assumes that your Qwen CLI can be called with the command `qwen chat`. If your CLI uses a different command, modify the subprocess.run call in the script.

## Notes

- The bot has a timeout of 30 seconds for each CLI call.
- Messages are limited to 4096 characters due to Telegram's limitations.
- Error messages from the CLI will be returned to the user.