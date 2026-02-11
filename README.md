# 🧠 ClawBrain

**Chris Bernardo's Custom AI Assistant**

ClawBrain is a personal AI assistant designed to streamline business operations for CT Realty Media and R&B Apparel Plus. It provides intelligent scheduling, calendar integration, multi-model AI reasoning, and WhatsApp-based interaction.

## Features

- **🤖 Multi-Model AI Brain**: Cost-optimized routing across Gemini, Claude, and OpenRouter
- **📅 Smart Scheduling**: Priority-based task scheduling with Google Calendar integration
- **💬 WhatsApp Bot**: 24/7 availability via WhatsApp messaging
- **🛠️ Extensible Tools**: Calendar access, file operations, and custom integrations (Aryeo API)
- **🧠 Memory System**: Persistent context and interaction logging
- **⚡ CLI Interface**: Unified command-line access to all functionality

## Quick Start

### Installation

```bash
# Clone or navigate to ClawBrain directory
cd /path/to/OpenClaw

# Make CLI executable
chmod +x clawbrain

# Optional: Add to PATH
sudo ln -s $(pwd)/clawbrain /usr/local/bin/clawbrain

# Install Python dependencies
pip3 install -r requirements.txt

# Install Node.js dependencies (for WhatsApp bot)
cd messaging_service && npm install && cd ..
```

### Configuration

1. **Set up environment variables** (`.env`):
```bash
GEMINI_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key
OPENROUTER_API_KEY=your_openrouter_key
```

2. **Configure Google Calendar** (via `credentials.json` and `token.json`)

3. **Optional**: Update `openclaw.json` for custom settings

## CLI Commands

```bash
# Check system status
clawbrain status

# Chat with ClawBrain
clawbrain chat "What's on my schedule today?"

# Generate daily schedule
clawbrain schedule

# View calendar events
clawbrain calendar

# List available tools
clawbrain tools

# Search memory
clawbrain memory "client meetings"

# Deploy to EC2
clawbrain deploy

# Show version info
clawbrain version

# View configuration (sanitized)
clawbrain config
```

## Architecture

### Core Components

1. **`clawbrain`** - Unified CLI interface
2. **`llm_brain.py`** - Multi-model AI routing and text generation
3. **`scheduler.py`** - Smart task scheduling with priority management
4. **`calendar_sync.py`** - Google Calendar integration
5. **`messaging_service/`** - WhatsApp bot (Node.js)
6. **`core/`** - Tool registry and memory management
7. **`brain/`** - Identity, rules, and operational guidelines

### Data Flow

```
User Input (WhatsApp/CLI)
    ↓
llm_brain (Model Router)
    ↓
AgentLoop (if tools needed)
    ↓
Tool Registry (Calendar, Files, etc.)
    ↓
Response
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

## Business Context

ClawBrain is optimized for:

### CT Realty Media
- Real estate photography, videography, drone services
- 3D tours and floor plans
- Client communication and scheduling

### R&B Apparel Plus
- Marketing and SEO
- Website health monitoring
- Social media management (1-2 posts/week)

## Development

### Project Structure

```
OpenClaw/
├── clawbrain              # Main CLI
├── llm_brain.py           # AI brain
├── scheduler.py           # Smart scheduling
├── calendar_sync.py       # Calendar integration
├── messaging_service/     # WhatsApp bot
│   └── index.js
├── core/                  # Tools & memory
│   ├── tool_registry.py
│   └── memory_manager.py
├── brain/                 # Identity & rules
│   ├── SOUL.md
│   ├── AGENTS.md
│   ├── USER.md
│   └── IDENTITY.md
├── skills/                # Custom skills
└── tests/                 # Test suite
```

### Running Tests

```bash
# Unit tests
pytest tests/ -v

# Integration tests
./test_integration.sh

# Manual testing
clawbrain status
clawbrain chat "test message"
```

## Deployment

### EC2 Deployment

```bash
# Deploy all files to EC2
clawbrain deploy

# Or manually sync
./sync_to_ec2.sh

# SSH to EC2
ssh -i openclaw_key.pem ubuntu@44.203.209.163

# Start WhatsApp bot on EC2
cd OpenClaw/messaging_service
pm2 start index.js --name whatsapp-bot
```

### WhatsApp Bot Setup

```bash
cd messaging_service
npm install
node index.js  # Scan QR code with WhatsApp
# Or use pm2 for production: pm2 start index.js
```

## Security

- ✅ All API keys stored in `.env` (never in config files)
- ✅ Data privacy protocols enforced
- ✅ Sanitized external API calls
- ✅ Environment variable validation

## Troubleshooting

### WhatsApp Bot Won't Start
```bash
# Check if Chromium is installed (EC2/ARM)
which chromium-browser
# If not: sudo apt-get install chromium-browser

# Clear WhatsApp session
rm -rf messaging_service/.wwebjs_auth
```

### Missing API Keys
```bash
# Verify .env is loaded
clawbrain config
# Check environment
echo $GEMINI_API_KEY
```

### Calendar Sync Issues
```bash
# Re-authenticate Google Calendar
python3 setup_calendar.py
```

## Version History

- **v1.0.0** (Feb 2026) - Initial ClawBrain release with unified CLI
- Rebranded from custom OpenClaw implementation
- Multi-model brain with cost optimization
- WhatsApp integration
- Smart scheduling with calendar sync

## Credits

Built by Chris Bernardo for CT Realty Media and R&B Apparel Plus.

Inspired by the OpenClaw platform but implemented as a fully custom solution.

## License

Proprietary - For personal use by Chris Bernardo
