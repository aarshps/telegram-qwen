#!/bin/bash
# Setup script for Telegram-Qwen Bridge

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Creating .env file if it doesn't exist..."
if [ ! -f .env ]; then
    cp .env.example .env
fi

echo ""
echo "Setup complete!"
echo "Please edit the .env file to add your Telegram bot token and admin ID."
echo "Then run the bot with: python telegram_qwen_bridge.py"