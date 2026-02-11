import subprocess
import json
import os

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CLI_PATH = os.path.join(SKILL_DIR, 'cli.js')

def _run_cli(args):
    """Runs the wacli Node.js script with given arguments."""
    cmd = ['node', CLI_PATH] + args
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=SKILL_DIR,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def send_message(to: str, message: str) -> str:
    """
    Sends a WhatsApp message via wacli.
    
    Args:
        to (str): The phone number to send to.
        message (str): The message content.
        
    Returns:
        str: Output from the CLI (e.g., success message or error).
    """
    return _run_cli(['send', '--to', to, '--msg', message])

def get_history(to: str, limit: int = 10) -> str:
    """
    Retrieves chat history via wacli.
    
    Args:
        to (str): The phone number to get history for.
        limit (int): Number of messages to retrieve.
        
    Returns:
        str: JSON string of chat history.
    """
    return _run_cli(['history', '--to', to, '--limit', str(limit)])

def check_status() -> str:
    """Checks the connection status of the WhatsApp bot."""
    return _run_cli(['status'])
