# Getting Started with Telegram-Qwen Bridge

This guide will help you get up and running with the Telegram-Qwen Bridge quickly.

## Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher
- A Telegram account
- Access to create a Telegram bot
- Qwen CLI installed (`pip install qwen`)
- Basic command-line knowledge

## Quick Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/aarshps/telegram-qwen.git
   cd telegram-qwen
   ```

2. Run the setup script:
   - On Windows: `setup.bat`
   - On macOS/Linux: `chmod +x setup.sh && ./setup.sh`

3. Configure your environment variables in the `.env` file:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - `TELEGRAM_ADMIN_ID`: Your Telegram chat ID (for security)

4. Start the bot:
   ```bash
   python telegram_qwen_bridge.py
   ```

## First Steps

Once your bot is running:

1. Open Telegram and find your bot
2. Send `/start` to receive a welcome message
3. Send `/id` to get your chat ID (useful for the `.env` configuration)
4. Try sending a simple message to test the Qwen integration

## Understanding the Architecture

The Telegram-Qwen Bridge operates in a few key steps:

1. **Message Reception**: The bot receives a message from Telegram
2. **Authorization Check**: Verifies the sender is authorized (based on `TELEGRAM_ADMIN_ID`)
3. **Qwen Processing**: Sends the message to Qwen with conversation history
4. **Action Execution**: If Qwen responds with `[EXEC]...[/EXEC]` blocks, executes those commands
5. **Response Delivery**: Sends Qwen's response back to Telegram

## Next Steps

- Read the [Installation Guide](installation-guide.md) for detailed setup instructions
- Learn about [Configuration Options](configuration.md)
- Explore the [Usage Guide](usage-guide.md) for advanced features