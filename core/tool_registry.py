import abc
import logging
import inspect
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger("tool_registry")

class BaseTool(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        pass

    @abc.abstractmethod
    def execute(self, **kwargs) -> Any:
        pass

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool):
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered. Overwriting.")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        tool = self.get_tool(name)
        if not tool:
            return f"Error: Tool '{name}' not found."
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return f"Error executing tool {name}: {e}"

# --- Concrete Tools ---

class CalendarTool(BaseTool):
    def __init__(self):
        # Lazy import to avoid circular dependencies or top-level failures
        try:
            import calendar_sync
            self._calendar_module = calendar_sync
        except ImportError:
            self._calendar_module = None
            logger.warning("calendar_sync module not found.")

    @property
    def name(self) -> str:
        return "get_calendar_events"

    @property
    def description(self) -> str:
        return "Fetches calendar events for the rest of the day or tomorrow. No arguments needed."

    def execute(self, **kwargs) -> str:
        if not self._calendar_module:
            return "Error: Calendar module not available."
        
        try:
            # Reusing the existing logic from calendar_sync.py
            # get_busy_slots returns a list of dicts with 'start', 'end', 'summary'
            slots = self._calendar_module.get_busy_slots()
            if not slots:
                return "No upcoming events found."
            
            output = ["Upcoming Events:"]
            for slot in slots:
                start_str = slot['start'].strftime('%H:%M')
                end_str = slot['end'].strftime('%H:%M')
                output.append(f"- {start_str} to {end_str}: {slot['summary']}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Failed to fetch calendar: {str(e)}"

class FileSystemTool(BaseTool):
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Reads the content of a file. Args: filepath"

    def execute(self, filepath: str, **kwargs) -> str:
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

# --- Wacli Tools ---

class WhatsAppSendTool(BaseTool):
    @property
    def name(self) -> str:
        return "send_whatsapp"

    @property
    def description(self) -> str:
        return "Sends a WhatsApp message. Args: to (phone number), message (content)"

    def execute(self, to: str, message: str, **kwargs) -> str:
        try:
            from skills.wacli import wacli
            return wacli.send_message(to, message)
        except ImportError:
            return "Error: wacli skill not found."
        except Exception as e:
            return f"Error sending message: {e}"

class WhatsAppReadTool(BaseTool):
    @property
    def name(self) -> str:
        return "read_whatsapp"

    @property
    def description(self) -> str:
        return "Reads WhatsApp chat history. Args: to (phone number), limit (optional int, default 5)"

    def execute(self, to: str, limit: int = 5, **kwargs) -> str:
        try:
            from skills.wacli import wacli
            return wacli.get_history(to, limit)
        except ImportError:
            return "Error: wacli skill not found."
        except Exception as e:
            return f"Error reading history: {e}"

# Helper to initialize default registry
def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register_tool(CalendarTool())
    registry.register_tool(FileSystemTool())
    
    # Register Wacli Tools
    registry.register_tool(WhatsAppSendTool())
    registry.register_tool(WhatsAppReadTool())
    
    return registry
