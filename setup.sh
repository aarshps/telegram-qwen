#!/bin/bash
# Setup script for Telegram-Qwen Bridge

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

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
echo "Then run the bot with: "
echo "1. source venv/bin/activate"
echo "2. python telegram_qwen_bridge.py"