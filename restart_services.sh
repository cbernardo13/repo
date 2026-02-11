#!/bin/bash
# Stop existing services
pkill -f 'node index.js' || true
pkill -f 'uvicorn main:app' || true
pkill -f 'chrome' || true
pkill -f 'chromium' || true
pkill -f 'discord_bot.py' || true

# Force fresh session
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
rm -rf "$DIR/messaging_service/session_store"

# Wait a moment
sleep 2

# Start backend
cd "$DIR"
nohup ./scripts/start_server.sh > server.log 2>&1 &
echo "Backend started."

# Start bot
if [ -d "$DIR/skills/wacli" ]; then
    cd "$DIR/skills/wacli"
    nohup node server.js > bot.log 2>&1 &
    echo "WhatsApp bot started."
else
    echo "Warning: WhatsApp bot (skills/wacli) directory not found."
fi

# Start Discord bot
if [ -d "$DIR/discord" ]; then
    cd "$DIR/discord"
    nohup ./start_discord.sh > ../discord.log 2>&1 &
    echo "Discord bot started from $DIR/discord."
else
    echo "Warning: discord directory not found."
fi
