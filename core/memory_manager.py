import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("memory_manager")

class MemoryManager:
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = memory_dir
        self.user_context_file = os.path.join(memory_dir, "user_context.json")
        self.interaction_log_file = os.path.join(memory_dir, "interaction_log.json")
        
        self._ensure_memory_dir()
        self._load_memory()

    def _ensure_memory_dir(self):
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
            
    def _load_memory(self):
        self.user_context = self._load_json(self.user_context_file, default={
            "name": "Chris",
            "preferences": {},
            "bio": "Entrepreneur and operator of CT Realty Media and R & B Apparel Plus.",
            "facts": []
        })
        self.interaction_log = self._load_json(self.interaction_log_file, default=[])

    def _load_json(self, filepath: str, default: Any) -> Any:
        if not os.path.exists(filepath):
            return default
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode {filepath}, using default.")
            return default

    def _save_json(self, filepath: str, data: Any):
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")

    # --- User Context Methods ---

    def get_context(self) -> Dict[str, Any]:
        """Returns the full user context."""
        return self.user_context

    def update_preference(self, key: str, value: Any):
        """Updates a specific preference."""
        self.user_context["preferences"][key] = value
        self._save_json(self.user_context_file, self.user_context)

    def add_fact(self, fact: str):
        """Adds a fact to the user knowledge base."""
        if fact not in self.user_context["facts"]:
            self.user_context["facts"].append(fact)
            self._save_json(self.user_context_file, self.user_context)

    # --- Interaction Log Methods ---

    def log_interaction(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Logs an interaction."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self.interaction_log.append(entry)
        # Keep log manageable - keep last 100 interactions for now
        if len(self.interaction_log) > 100:
            self.interaction_log = self.interaction_log[-100:]
            
        self._save_json(self.interaction_log_file, self.interaction_log)

    def get_recent_interactions(self, limit: int = 5) -> List[Dict]:
        """Returns the last N interactions."""
        return self.interaction_log[-limit:]

    def search_memory(self, query: str) -> List[str]:
        """
        Simple keyword search implementation. 
        TODO: Upgrade to vector search in future.
        """
        results = []
        query_lower = query.lower()
        
        # Search facts
        for fact in self.user_context["facts"]:
            if query_lower in fact.lower():
                results.append(f"Fact: {fact}")
                
        # Search recent logs
        for entry in self.interaction_log[-20:]: # Search last 20 logs
            if query_lower in entry["content"].lower():
                results.append(f"Log ({entry['timestamp']}): {entry['content'][:100]}...")
                
        return results
