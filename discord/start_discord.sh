#!/bin/bash

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create one with DISCORD_BOT_TOKEN."
    exit 1
fi

# Load .env to check if token is set (simple grep)
if ! grep -q "DISCORD_BOT_TOKEN" .env; then
    echo "Error: DISCORD_BOT_TOKEN not found in .env."
    echo "Please add: DISCORD_BOT_TOKEN=your_token_here to .env"
    exit 1
fi

# Determine python path
if [ -f "../venv/bin/python3" ]; then
    PYTHON_CMD="../venv/bin/python3"
elif [ -f "../../venv/bin/python3" ]; then
    PYTHON_CMD="../../venv/bin/python3"
elif [ -f "./venv/bin/python3" ]; then
    PYTHON_CMD="./venv/bin/python3"
elif [ -f "./photo_scanner_tool/backend/venv/bin/python3" ]; then
    PYTHON_CMD="./photo_scanner_tool/backend/venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

echo "Starting OpenClaw Discord Bot with $PYTHON_CMD..."
$PYTHON_CMD discord_bot.py
