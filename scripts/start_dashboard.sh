#!/bin/bash

# Kill any existing backend on port 8001
lsof -ti:8001 | xargs kill -9 2>/dev/null

echo "Starting Backend..."
# Run backend in background
python3 llm_brain_api.py > backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend started (PID: $BACKEND_PID). Logs in backend.log"

echo "Starting Frontend..."
cd web-dashboard
npm run dev

# Cleanup on exit
kill $BACKEND_PID
