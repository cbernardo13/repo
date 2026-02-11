import os
import logging
import re

logger = logging.getLogger("settings_manager")

class SettingsManager:
    def __init__(self, env_path=".env"):
        # Ensure we're using the absolute path or relative to CWD
        self.env_path = os.path.abspath(env_path) if env_path else ".env"

    def get_api_keys(self):
        """
        Reads the .env file and returns a list of API keys with masked values.
        """
        keys = []
        target_keys = ["GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"]
        
        # If env file doesn't exist, we can't read keys
        if not os.path.exists(self.env_path):
            logger.warning(f".env file not found at {self.env_path}")
            return []

        try:
            with open(self.env_path, 'r') as f:
                content = f.read()
            
            for key_name in target_keys:
                # Simple regex to find the key value
                # Using multiline matching to find "KEY=VALUE"
                match = re.search(f"^{key_name}=(.*)$", content, re.MULTILINE)
                value = match.group(1).strip() if match else ""
                
                # Mask the key
                masked_value = ""
                if value and len(value) > 8:
                    masked_value = f"{value[:4]}...{value[-4:]}"
                elif value:
                    masked_value = "****"
                
                keys.append({
                    "name": key_name,
                    "value": masked_value, 
                    "is_set": bool(value)
                })
        except Exception as e:
            logger.error(f"Failed to read .env file: {e}")
            
        return keys

    def update_api_key(self, key_name, new_value):
        """
        Updates a specific API key in the .env file.
        """
        try:
            # Create file if it doesn't exist
            if not os.path.exists(self.env_path):
                with open(self.env_path, 'w') as f:
                    f.write("")
            
            with open(self.env_path, 'r') as f:
                lines = f.readlines()
            
            key_found = False
            new_lines = []
            
            for line in lines:
                if line.strip().startswith(f"{key_name}="):
                    new_lines.append(f"{key_name}={new_value}\n")
                    key_found = True
                else:
                    new_lines.append(line)
            
            if not key_found:
                # Ensure we add a newline if the last line doesn't have one
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines[-1] += '\n'
                new_lines.append(f"{key_name}={new_value}\n")
            
            with open(self.env_path, 'w') as f:
                f.writelines(new_lines)
            
            logger.info(f"Updated {key_name} in {self.env_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update .env file: {e}")
            return False
