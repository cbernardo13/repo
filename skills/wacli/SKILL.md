# wacli Skill

**wacli** (WhatsApp CLI) provides a robust, daemon-based interface for interacting with WhatsApp from the command line and AI agents.

## Architecture

- **Daemon (`server.js`)**: Runs in the background (pm2), maintains the WhatsApp session using `whatsapp-web.js` + valid browser profile.
- **CLI (`cli.js`)**: Lightweight client that sends commands to the daemon via HTTP (localhost only).
- **Python Wrapper (`wacli.py`)**: Integration layer for ClawBrain to use wacli as a tool.

## Installation

1.  **Dependencies**:
    ```bash
    cd skills/wacli
    npm install
    pip install -r requirements.txt
    ```

2.  **Start Daemon**:
    ```bash
    pm2 start server.js --name wacli-server
    ```

3.  **Login**:
    ```bash
    node cli.js login
    ```

## Commands

### CLI Usage
```bash
# Check status
node cli.js status

# Send message
node cli.js send --to 1234567890 --msg "Hello world"

# Get history
node cli.js history --to 1234567890 --limit 5
```

### Python Usage
```python
from skills.wacli import wacli
wacli.send_message("1234567890", "Hello from Python")
```
