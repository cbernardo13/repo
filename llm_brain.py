import os
import logging
import time
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_brain")

# Initialize Traffic Logger
try:
    from core.traffic_logger import TrafficLogger
    traffic_logger = TrafficLogger()
    TRAFFIC_LOGGING_AVAILABLE = True
except ImportError:
    TRAFFIC_LOGGING_AVAILABLE = False
    logger.warning("TrafficLogger not found. Traffic logging disabled.")

class Complexity(Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"
    HEARTBEAT = "heartbeat"

# --- Cost Rates (approximate per 1M tokens) ---
# Format: model_name_fragment: (input_rate, output_rate)
COST_RATES = {
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-3-pro": (1.25, 5.00),
    "claude-3-opus": (15.0, 75.0),
    "claude-3-sonnet": (3.0, 15.0),
    "claude-opus-4.6": (15.0, 75.0),
    "free": (0.0, 0.0), # OpenRouter free
    "llama": (0.7, 0.9), # General fallback for paid open models
    "default": (1.0, 3.0)
}

# --- Provider Availability Checks ---
try:
    from google import genai
    from google.genai import types
    GEMINI_LIB_AVAILABLE = True
except ImportError:
    GEMINI_LIB_AVAILABLE = False
    logger.warning("google-genai lib missing.")

try:
    import anthropic
    ANTHROPIC_LIB_AVAILABLE = True
except ImportError:
    ANTHROPIC_LIB_AVAILABLE = False
    logger.warning("anthropic lib missing.")

# Check for requests (used for OpenRouter)
try:
    import requests
    REQUESTS_LIB_AVAILABLE = True
except ImportError:
    REQUESTS_LIB_AVAILABLE = False
    logger.warning("requests lib missing.")


def get_api_key(name):
    key = os.environ.get(name)
    if not key or key.strip() == "":
        return None
    return key


# --- Context Loading ---

def load_brain_context():
    """Reads and combines the brain markdown files."""
    brain_dir = os.path.join(os.path.dirname(__file__), "brain")
    
    # Priority order for context
    # SOUL -> USER -> IDENTITY -> AGENTS -> daily_schedule -> memory
    files_to_read = [
        "SOUL.md",
        "USER.md",
        "IDENTITY.md",
        "AGENTS.md",
        "daily_schedule.md"
    ]
    
    context_parts = []
    
    for filename in files_to_read:
        filepath = os.path.join(brain_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        context_parts.append(f"\n\n--- {filename} ---\n{content}")
            except Exception as e:
                logger.error(f"Failed to read brain file {filename}: {e}")

    # Load today's memory if available
    import datetime
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    memory_file = os.path.join(brain_dir, "memory", f"{today_str}.md")
    
    if os.path.exists(memory_file):
         try:
            with open(memory_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    context_parts.append(f"\n\n--- memory/{today_str}.md ---\n{content}")
         except Exception as e:
            logger.error(f"Failed to read daily memory: {e}")
            
    return "\n".join(context_parts)

def generate_text(prompt, complexity=Complexity.SIMPLE, system_instruction=None, channel="unknown"):
    gemini_key = get_api_key("GEMINI_API_KEY")
    claude_key = get_api_key("ANTHROPIC_API_KEY")
    openrouter_key = get_api_key("OPENROUTER_API_KEY")

    # --- Load & Inject Brain Context ---
    brain_context = load_brain_context()
    
    # If a specific system instruction is provided (e.g. by a tool like generate_schedule), 
    # we append the brain context to it (or prepend, depending on importance).
    # Generally, the Persona (Brain) should be the base, and specific instructions add to it.
    
    final_system_instruction = brain_context
    if system_instruction:
        final_system_instruction = f"{brain_context}\n\n--- TASK INSTRUCTION ---\n{system_instruction}"
        
    # Override the local variable to be used in calls
    # We will pass final_system_instruction instead of system_instruction to the providers
    
    # --- Tool Routing (Auto-Upgrade to AgentLoop) ---
    # If the user asks about calendar, schedule, or files, try to use the AgentLoop automatically.
    # This ensures "dumb" callers (like the legacy WhatsApp bot) get "smart" behavior.
    
    # Simple check for keywords
    tool_keywords = ["calendar", "schedule", "appointment", "busy", "free", "project", "file"]
    should_use_agent = any(keyword in prompt.lower() for keyword in tool_keywords)
    
    # NOTE: AgentLoop internally uses memory/tools which is "Agentic". 
    # The brain files we just loaded are "Persona/Context". 
    # We should ideally pass this brain context to the AgentLoop too, 
    # but AgentLoop constructs its own system prompt. 
    # For now, we will leave AgentLoop as is, or we would need to modify AgentLoop to accept extra context.
    # Given the implementation of AgentLoop below, it constructs a prompt. 
    # Let's Modify AgentLoop later if needed to respect this context. 
    # For now, let's focus on non-agent text generation (the bulk of chat).

    if should_use_agent and CORE_AVAILABLE and not system_instruction: 
         # Only hijack if no specific system instruction (to avoid breaking specific workflows like generate_schedule)
         try:
             logger.info(f"Auto-upgrading prompt to AgentLoop: {prompt}")
             agent = AgentLoop(prompt)
             # Run for a few steps and return the result
             result = agent.run(max_steps=3)
             return result
         except Exception as e:
             logger.error(f"AgentLoop failed, falling back to simple text: {e}")

    # Log incoming prompt length for debugging
    logger.info(f"Incoming prompt length: {len(prompt)} chars")

    # --- Standard Text Generation ---

    # Define providers with fallbacks
    # Format: (name, api_key, lib_available, model_config)
    
    providers = []
    
    # OpenRouter Free Models (Good for simple tasks)
    openrouter_free_config = {
        "model": "openrouter/free", # Recommended for guaranteed free access
        "site_url": "https://openclaw.ai", 
        "app_name": "OpenClaw"
    }
    
    # Direct Paid Models
    gemini_paid_config = {"model": "gemini-2.0-flash"}
    claude_paid_config = {"model": "claude-3-opus-20240229"}

    # Premium Models (for complex tasks)
    gemini_3_pro_config = {"model": "gemini-3-pro"}
    claude_opus_46_config = {"model": "claude-opus-4.6"}


    if complexity == Complexity.HEARTBEAT:
        # Strategy: Cheapest only — minimize cost
        providers.append(("openrouter", openrouter_key, REQUESTS_LIB_AVAILABLE, openrouter_free_config))

    elif complexity == Complexity.SIMPLE:
        # Strategy: Free -> Cheap Paid -> Expensive Paid
        providers.append(("openrouter", openrouter_key, REQUESTS_LIB_AVAILABLE, openrouter_free_config))
        providers.append(("gemini", gemini_key, GEMINI_LIB_AVAILABLE, gemini_paid_config))
        providers.append(("claude", claude_key, ANTHROPIC_LIB_AVAILABLE, claude_paid_config))
        
    else: # COMPLEX
        # Strategy: Premium -> Standard Paid -> Free fallback
        providers.append(("gemini", gemini_key, GEMINI_LIB_AVAILABLE, gemini_3_pro_config))
        providers.append(("claude", claude_key, ANTHROPIC_LIB_AVAILABLE, claude_opus_46_config))
        providers.append(("gemini", gemini_key, GEMINI_LIB_AVAILABLE, gemini_paid_config))
        providers.append(("openrouter", openrouter_key, REQUESTS_LIB_AVAILABLE, openrouter_free_config))

    
    errors = []

    for name, key, lib_ok, config in providers:
        if not lib_ok:
            # errors.append(f"{name}: lib missing") # don't clutter logs with missing libs unless critical
            continue
        if not key:
            # errors.append(f"{name}: key missing")
            continue
            
        # Attempt generation
        try:
            logger.info(f"Attempting generation with {name}...")
            start_time = time.time()
            content = None
            usage = {}
            
            if name == "gemini":
                content, usage = _call_gemini(key, prompt, final_system_instruction, config)
            elif name == "claude":
                content, usage = _call_claude(key, prompt, final_system_instruction, config)
            elif name == "openrouter":
                content, usage = _call_openrouter(key, prompt, final_system_instruction, config)
            
            end_time = time.time()
            latency = end_time - start_time
            
            # --- Traffic Logging ---
            if TRAFFIC_LOGGING_AVAILABLE:
                try:
                    # usage keys vary by provider, normalize them
                    t_in = usage.get("prompt_tokens", 0)
                    t_out = usage.get("completion_tokens", 0)
                    
                    # Estimate cost
                    model_id = config.get("model", "default")
                    rates = COST_RATES.get("default")
                    
                    # specific matches
                    for k, v in COST_RATES.items():
                        if k in model_id:
                            rates = v
                            break
                            
                    cost = (t_in * rates[0] + t_out * rates[1]) / 1_000_000
                    
                    traffic_logger.log_traffic(
                        prompt=prompt[:500], # Log truncated prompt
                        response=content[:500] if content else "", # Log truncated response
                        provider=name,
                        model=model_id,
                        latency=latency,
                        status="success",
                        tokens_in=t_in,
                        tokens_out=t_out,
                        cost=cost,
                        channel=channel or "unknown"
                    )
                except Exception as log_err:
                    logger.error(f"Traffic logging failed (non-blocking): {log_err}")

            return content
                
        except Exception as e:
            # Log failure
            if TRAFFIC_LOGGING_AVAILABLE:
                traffic_logger.log_traffic(
                    prompt=prompt[:500],
                    response="",
                    provider=name,
                    model=config.get("model", "unknown"),
                    latency=0,
                    status=f"error: {str(e)}",
                    cost=0,
                    channel=channel or "unknown"
                )

            logger.error(f"{name} failed: {e}")
            errors.append(f"{name} error: {str(e)}")
            continue # Try next provider

    return f"Brain Failure. All models failed. Errors: {'; '.join(errors)}"


def _call_openrouter(api_key, prompt, system_instruction=None, config=None):
    """Calls OpenRouter API."""
    model = config.get("model", "meta-llama/llama-3.3-70b-instruct:free")
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": config.get("site_url", "https://openclaw.ai"),
        "X-Title": config.get("app_name", "OpenClaw")
    }
    
    payload = {
        "model": model,
        "messages": messages
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return content, usage
        else:
             raise Exception(f"OpenRouter returned empty choices: {data}")
    else:
        raise Exception(f"OpenRouter API Error: {response.status_code} - {response.text}")


def _call_gemini(api_key, prompt, system_instruction=None, config=None):
    """Calls Gemini (using gemini-2.0-flash with search tool)."""
    
    client = genai.Client(api_key=api_key)
    
    # Using Gemini 2.0 Flash (Recommended for speed/tools)
    model_name = config.get("model", "gemini-2.0-flash")
    
    # Configure Google Search Tool
    # Note: Only attach tools if it's the flash model that supports them well, or if requested.
    # For simplicity, we keep it enabled for 2.0 Flash.
    
    tools = []
    if "flash" in model_name:
         tools=[types.Tool(google_search=types.GoogleSearch())]

    gen_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=tools,
        response_modalities=["TEXT"]
    )
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=gen_config
    )
    
    if response.candidates and response.candidates[0].content.parts:
         content = response.text
         # Extract usage if available
         usage = {}
         if response.usage_metadata:
             usage = {
                 "prompt_tokens": response.usage_metadata.prompt_token_count,
                 "completion_tokens": response.usage_metadata.candidates_token_count
             }
         return content, usage
    return "Error: No content generated.", {}

def _call_claude(api_key, prompt, system_instruction=None, config=None):
    """Calls Claude 3.5 Sonnet / Opus."""
    client = anthropic.Anthropic(api_key=api_key)
    
    messages = [{"role": "user", "content": prompt}]
    
    # Using Claude 3 Opus (Fallback to known stable)
    model_name = config.get("model", "claude-3-opus-20240229")
    
    response = client.messages.create(
        model=model_name,
        max_tokens=4096,
        system=system_instruction if system_instruction else "",
        messages=messages
    )
    
    content = response.content[0].text
    usage = {}
    if response.usage:
        usage = {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens
        }
    
    return content, usage


# --- Core Integration ---
try:
    from core.memory_manager import MemoryManager
    from core.tool_registry import ToolRegistry, create_default_registry
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    logger.warning("Core modules (memory, tools) not found. Advanced agent features disabled.")

# --- Specific workflow functions ---

def generate_schedule(tasks_data):
    """
    Generates a daily schedule.
    Defined as SIMPLE to prefer Gemini (speed), but will fallback to Claude (intelligence) if Gemini missing.
    """
    system_instruction = (
        "You are an expert scheduler. "
        "Create a markdown daily schedule based on the provided JSON task list. "
        "Prioritize high impact tasks. "
        "Format as a clean markdown list with times. "
        "Include emojis. "
    )
    
    prompt = f"Here are my tasks for today: {tasks_data}. Create a schedule starting at 9 AM."
    
    return generate_text(prompt, complexity=Complexity.SIMPLE, system_instruction=system_instruction)

class AgentLoop:
    """
    A simple ReAct-style loop that uses Memory and Tools.
    """
    def __init__(self, goal: str):
        self.goal = goal
        self.memory = MemoryManager() if CORE_AVAILABLE else None
        self.registry = create_default_registry() if CORE_AVAILABLE else None
        self.history = []

    def run(self, max_steps=5):
        if not CORE_AVAILABLE:
            return "Error: Core modules missing."

        print(f"Agent Goal: {self.goal}")
        
        # 1. Retrieve Context
        context = self.memory.get_context()
        user_name = context.get("name", "User")
        
        # 2. Build Tools Context
        tools_desc = "\n".join([f"- {t['name']}: {t['description']}" for t in self.registry.list_tools()])
        
        system_prompt = (
            f"You are OpenClaw, an assistant for {user_name}. "
            f"You have access to the following tools:\n{tools_desc}\n\n"
            "CRITICAL INFLUENCE:\n"
            "You DO have access to the user's calendar and files via these tools.\n"
            "Do NOT say you cannot access them. Use the tool instead.\n\n"
            "To use a tool, output a JSON block ONLY: {\"tool\": \"tool_name\", \"args\": {...}}\n"
            "If you have enough info to finish, output: FINAL ANSWER: [your answer]"
        )
        
        current_prompt = f"Goal: {self.goal}"
        
        for i in range(max_steps):
            print(f"--- Step {i+1} ---")
            # Call LLM (using simple complexity for generic planning)
            # merging history
            # merging history
            full_prompt = "\n".join(self.history + [current_prompt])
            logger.info(f"Agent Step {i+1} Prompt Length: {len(full_prompt)} chars")
            
            response = generate_text(full_prompt, complexity=Complexity.COMPLEX, system_instruction=system_prompt)
            print(f"LLM Response: {response}")
            self.history.append(f"Assistant: {response}")
            
            # Check for tool use
            # Very naive parsing for this MVP
            import json
            if "{" in response and "}" in response:
                try:
                    # Find first JSON-like block
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_str = response[start:end]
                    tool_call = json.loads(json_str)
                    
                    tool_name = tool_call.get("tool")
                    tool_args = tool_call.get("args", {})
                    
                    if tool_name:
                        print(f"Executing {tool_name} with {tool_args}...")
                        result = str(self.registry.execute_tool(tool_name, **tool_args))
                        
                        # Safety Truncation for Tool Outputs
                        original_len = len(result)
                        if original_len > 2000:
                            result = result[:2000] + f"\n...(truncated {original_len - 2000} chars)..."
                            logger.warning(f"Tool output truncated from {original_len} to 2000 chars.")

                        print(f"Tool Output: {result}")
                        self.history.append(f"System: Tool {tool_name} returned: {result}")
                        current_prompt = f"Tool output: {result}. Continue."
                        continue
                        
                except Exception as e:
                    print(f"Failed to parse tool call: {e}")
            
            if "FINAL ANSWER:" in response:
                return response.split("FINAL ANSWER:")[1].strip()
            
            # If no tool and no final answer, just let it continue or stop
            # For this simple loop, we'll assume it's chatting or asking.
            # But let's stop if it didn't use a tool to avoid loops.
            if i > 0 and "Tool" not in self.history[-1]:
                 return response
                 
        return "Max steps reached."

