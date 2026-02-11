# ClawBrain Architecture

## System Overview

ClawBrain is a hybrid Python/Node.js system that combines:
- **Python backend** for AI reasoning, scheduling, and tool execution
- **Node.js frontend** for WhatsApp messaging
- **REST API** for communication between components
- **EC2 deployment** for 24/7 availability

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                          │
├─────────────────────┬───────────────────┬───────────────────┤
│   WhatsApp Client   │   CLI Interface   │  Direct Scripts   │
└─────────┬───────────┴──────────┬────────┴────────┬──────────┘
          │                      │                 │
          ▼                      ▼                 ▼
┌─────────────────────┐ ┌─────────────────┐ ┌────────────────┐
│  WhatsApp Bot       │ │  clawbrain CLI  │ │  Python Scripts│
│  (Node.js)          │ │  (Python)       │ │  (Direct exec) │
│  messaging_service/ │ │  ./clawbrain    │ │  scheduler.py  │
└─────────┬───────────┘ └────────┬────────┘ └────────┬───────┘
          │                      │                   │
          └──────────────┬───────┴──────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │    llm_brain.py      │
              │  (Model Router)      │
              │                      │
              │  • Gemini 2.0 Flash  │
              │  • Claude Opus       │
              │  • OpenRouter/Free   │
              └──────────┬───────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
    ┌───────────────┐         ┌──────────────┐
    │  AgentLoop    │         │  Direct LLM  │
    │  (ReAct)      │         │  Generation  │
    └───────┬───────┘         └──────────────┘
            │
            ▼
    ┌───────────────────────┐
    │   Tool Registry       │
    │                       │
    │  • get_calendar       │
    │  • read_file          │
    │  • [future tools]     │
    └───────┬───────────────┘
            │
            ▼
┌──────────────────────────────────────────┐
│         External Integrations            │
├──────────────┬───────────────┬───────────┤
│ Google       │ LLM Providers │ Aryeo API │
│ Calendar API │ (via APIs)    │ (CLI)     │
└──────────────┴───────────────┴───────────┘
```

---

## Component Details

### 1. User Interfaces

#### WhatsApp Bot (`messaging_service/index.js`)
- **Tech**: Node.js, whatsapp-web.js, Puppeteer
- **Function**: Receives messages, forwards to Python brain API
- **Communication**: HTTP POST to `localhost:8000/api/chat`
- **Features**: Message truncation (5k limit), typing indicators

#### CLI (`clawbrain`)
- **Tech**: Python 3, argparse
- **Function**: Command-line access to all ClawBrain features
- **Commands**: status, chat, schedule, deploy, calendar, tools, memory, config

#### Direct Scripts
- **scheduler.py**: Can be run directly for schedule generation
- **calendar_sync.py**: Standalone calendar operations
- **aryeo_cli.py**: Aryeo API interactions

---

### 2. Core Brain (`llm_brain.py`)

#### Model Selection Logic

```python
if Complexity.SIMPLE:
    Try: OpenRouter (Free) → Gemini (Paid) → Claude (Paid)
    
if Complexity.COMPLEX:
    Try: Claude (Paid) → Gemini (Paid) → OpenRouter (Free)
```

#### Providers
- **Gemini 2.0 Flash**: Fast, supports Google Search tool
- **Claude 3 Opus**: Deep reasoning, high quality
- **OpenRouter Free**: Cost-free fallback (Llama 3.3, etc.)

#### Auto-Upgrade to AgentLoop
Detects keywords (`calendar`, `schedule`, `appointment`, `file`) and automatically upgrades to AgentLoop for tool access.

---

### 3. AgentLoop (ReAct-Style Reasoning)

**Flow:**
1. Receive user goal
2. Build system prompt with available tools
3. LLM decides: use tool OR provide answer
4. If tool:
   - Parse JSON tool call: `{"tool": "name", "args": {...}}`
   - Execute via Tool Registry
   - Feed result back to LLM
5. Repeat until `FINAL ANSWER` or max steps

**Safety:**
- Tool outputs truncated to 2000 chars
- Max steps configurable (default: 5)
- History accumulates for context

---

### 4. Tool System

#### Tool Registry (`core/tool_registry.py`)

**Interface:**
```python
class BaseTool:
    @property
    def name(self) -> str
    
    @property
    def description(self) -> str
    
    def execute(self, **kwargs) -> Any
```

**Current Tools:**
1. `get_calendar_events` - Fetch busy slots from Google Calendar
2. `read_file` - Read file contents

**Adding New Tools:**
```python
class MyTool(BaseTool):
    @property
    def name(self):
        return "my_tool"
    
    @property
    def description(self):
        return "Does something useful"
    
    def execute(self, **kwargs):
        # Implementation
        return result

# Register automatically via create_default_registry()
```

---

### 5. Memory System (`core/memory_manager.py`)

#### Storage
- **`memory/user_context.json`**: Name, preferences, bio, facts
- **`memory/interaction_log.json`**: Last 100 interactions

#### Operations
- `get_context()` - Retrieve user info
- `update_preference(key, value)` - Update preferences
- `add_fact(fact)` - Add to knowledge base
- `log_interaction(role, content)` - Log conversation
- `search_memory(query)` - Keyword search

---

### 6. Scheduler (`scheduler.py`)

#### Algorithm
1. Read priorities from `life_priorities.md`
2. Load tasks from `openclaw_tasks.md`
3. Parse: name, priority (High/Med/Low), duration, tags
4. Calculate score = base_score + (priority_keyword_boost × 0.5)
5. Sort by score (descending)
6. Fetch calendar busy slots
7. Allocate time blocks:
   - Start at 9 AM
   - Avoid calendar conflicts
   - Respect lunch break (12-1 PM)
   - Add 5-minute buffers
8. Generate markdown schedule

**LLM Enhancement:**
If `llm_brain` available, passes task data to Gemini for natural language scheduling.

---

### 7. Calendar Integration (`calendar_sync.py`)

#### Google Calendar API Flow
1. Load credentials from `credentials.json`
2. Authenticate (stores token in `token.json`)
3. Query calendar for today/tomorrow
4. Return busy slots: `[{start, end, summary}, ...]`

#### Usage
- Scheduler: Avoid booking over meetings
- AgentLoop: Answer "What's on my calendar?"
- CLI: `clawbrain calendar`

---

### 8. Configuration

#### Files
- **`.env`**: API keys (GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY)
- **`openclaw.json`**: Model config, agent settings, plugin config
- **`brain/*.md`**: Identity, rules, user context

#### Config Loading Priority
1. Environment variables (`.env`) - **highest priority**
2. `openclaw.json` - non-sensitive config only
3. Hardcoded defaults

---

## Data Flow Examples

### Example 1: WhatsApp Message

```
User sends WhatsApp: "What's on my calendar?"
    ↓
WhatsApp Bot (Node.js) receives message
    ↓
POST to localhost:8000/api/chat with {"message": "...", "complexity": "simple"}
    ↓
llm_brain.generate_text() detects keyword "calendar"
    ↓
Auto-upgrades to AgentLoop
    ↓
AgentLoop:
  • Sees "get_calendar_events" tool available
  • LLM outputs: {"tool": "get_calendar_events", "args": {}}
  • Tool executes → returns event list
  • LLM receives tool output
  • LLM outputs: "FINAL ANSWER: You have 2 meetings today..."
    ↓
Response sent back to WhatsApp Bot
    ↓
User receives reply
```

### Example 2: CLI Schedule Command

```
User runs: clawbrain schedule
    ↓
clawbrain CLI calls cmd_schedule()
    ↓
scheduler.read_priorities() → ['growth', 'client', 'health']
    ↓
scheduler.load_tasks() → parses openclaw_tasks.md
    ↓
Calculates scores based on priorities
    ↓
calendar_sync.get_busy_slots() → Google Calendar API
    ↓
scheduler.generate_schedule(tasks) with calendar conflicts
    ↓
llm_brain.generate_schedule() (Gemini) for natural formatting
    ↓
Output to terminal + save to daily_schedule.md
```

---

## Deployment Architecture

### Local Development
```
MacOS (Local)
├── Python scripts
├── Node.js WhatsApp bot
├── clawbrain CLI
└── Git repository
```

### Production (EC2)
```
AWS EC2 (Ubuntu)
├── Same file structure
├── WhatsApp bot (pm2 managed)
├── Cron jobs for scheduled tasks
└── systemd services (optional)
```

### Deployment Process
1. Local edits
2. `clawbrain deploy` or `./sync_to_ec2.sh`
3. Rsync files to EC2
4. SSH to EC2, restart services
5. Test via WhatsApp

---

## Security Model

### Principles
1. **No API keys in code files**
2. **Environment variables only**
3. **Data privacy protocols** (see `brain/IDENTITY.md`)
4. **Sanitized external calls** (strip personal info)
5. **`.env` never committed to git**

### Enforcement
- `.gitignore` includes `.env`
- `clawbrain config` redacts sensitive keys
- Privacy guards in `SOUL.md` and `AGENTS.md`

---

## Technology Stack

### Backend
- **Python 3.9+**
- **google-genai**: Gemini API
- **anthropic**: Claude API  
- **requests**: OpenRouter API
- **google-auth**: Calendar OAuth

### Frontend
- **Node.js 18+**
- **whatsapp-web.js**: WhatsApp integration
- **Puppeteer**: Browser automation for WhatsApp
- **axios**: HTTP client

### Infrastructure
- **AWS EC2**: Ubuntu server
- **pm2**: Process manager (WhatsApp bot)
- **rsync**: Deployment sync
- **systemd/cron**: Optional service management

---

## Future Enhancements

### Planned Tools
- [ ] `send_email` - Gmail API
- [ ] `create_calendar_event` - Write to calendar
- [ ] `get_weather` - For drone flight planning
- [ ] `check_firmware_updates` - Sony/DJI gear
- [ ] `aryeo_schedule` - Unified Aryeo integration

### Planned Features
- [ ] Vector search for memory
- [ ] Conversation compaction
- [ ] Multi-user support
- [ ] Web dashboard
- [ ] Voice interface (ElevenLabs)

---

## Performance Characteristics

### Response Times
- **Direct LLM call**: 2-5 seconds
- **AgentLoop (1 tool)**: 5-10 seconds
- **AgentLoop (multiple tools)**: 10-20 seconds
- **Schedule generation**: 5-15 seconds

### Cost Optimization
- Free tier (OpenRouter) for simple queries
- Gemini Flash for speed + Google Search
- Claude Opus only for complex reasoning
- **Est. cost**: $5-15/month with moderate use

---

## Monitoring & Debugging

### Logs
- Python: `logging` module (INFO level)
- WhatsApp Bot: `console.log` (stdout)
- EC2: `pm2 logs whatsapp-bot`

### Health Checks
- `clawbrain status` - Service health
- `pgrep -f messaging_service` - Bot running?
- Check `.env` variables loaded
- Verify config files present

---

## Contribution Guidelines

This is a personal project, but if extending:

1. Add new tools to `core/tool_registry.py`
2. Follow existing patterns (BaseTool interface)
3. Add tests to `tests/`
4. Update CLI in `clawbrain` if needed
5. Document in this file

---

**Maintained by:** Chris Bernardo  
**Last Updated:** February 2026  
**Version:** 1.0.0
