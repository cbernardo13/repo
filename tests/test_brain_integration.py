
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path so we can import llm_brain
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import llm_brain

class TestBrainIntegration(unittest.TestCase):
    def test_load_brain_context(self):
        """Test that load_brain_context reads files from the brain directory."""
        context = llm_brain.load_brain_context()
        print(f"Loaded context length: {len(context)}")
        
        # Check for presence of key files in the output
        self.assertIn("--- SOUL.md ---", context)
        self.assertIn("--- USER.md ---", context)
        self.assertIn("--- IDENTITY.md ---", context)
        self.assertIn("--- AGENTS.md ---", context)
        # daily_schedule might be missing if not created, but we saw it in file list
        self.assertIn("--- daily_schedule.md ---", context)

    @patch('llm_brain._call_gemini')
    @patch('llm_brain.get_api_key')
    def test_generate_text_injects_context(self, mock_get_key, mock_call_gemini):
        """Test that generate_text passes the brain context as system_instruction."""
        mock_get_key.return_value = "fake_key"
        mock_call_gemini.return_value = ("Mock response", {})
        
        # We need to force it to use Gemini (or just any provider)
        # Complexity.SIMPLE tries OpenRouter then Gemini then Claude.
        # We can mock OpenRouter to fail or just mock them all.
        
        # Let's mock OpenRouter to fail so it falls back to Gemini
        with patch('llm_brain._call_openrouter', side_effect=Exception("OpenRouter failed")):
             llm_brain.generate_text("Hello", complexity=llm_brain.Complexity.SIMPLE)
             
        # Verify _call_gemini was called
        self.assertTrue(mock_call_gemini.called)
        
        # Get arguments passed to _call_gemini
        args, _ = mock_call_gemini.call_args
        # args: (api_key, prompt, system_instruction, config)
        system_instruction = args[2]
        
        self.assertIn("--- SOUL.md ---", system_instruction)
        self.assertIn("--- USER.md ---", system_instruction)

if __name__ == '__main__':
    unittest.main()
