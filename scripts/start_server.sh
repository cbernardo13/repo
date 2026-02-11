#!/bin/bash

# Kill any existing backend on port 8001
lsof -ti:8001 | xargs kill -9 2>/dev/null

echo "Starting OpenClaw Server + Dashboard..."
echo "Access Dashboard at http://localhost:8001"

# Run backend (which now serves frontend)
python3 llm_brain_api.py
