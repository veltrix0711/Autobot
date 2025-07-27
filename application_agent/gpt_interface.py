"""
GPT Interface module for Application Agent
Handles communication with OpenRouter/OpenAI API for command interpretation
"""

import json
import requests
from typing import Dict, Any, Optional, List
from openai import OpenAI
from config import config
from logger import agent_logger

class GPTInterface:
    """Interface for communicating with GPT models via OpenRouter or OpenAI"""
    
    def __init__(self):
        self.client = None
        self.api_config = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the API client based on configuration"""
        try:
            self.api_config = config.get_api_config()
            
            self.client = OpenAI(
                api_key=self.api_config['api_key'],
                base_url=self.api_config['base_url']
            )
            
            agent_logger.logger.info(f"GPT client initialized with model: {self.api_config['model']}")
            
        except Exception as e:
            agent_logger.log_error("GPT_INIT", str(e))
            raise
    
    def interpret_command(self, user_command: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Send user command to GPT and get structured response
        Returns parsed action dictionary or None if failed
        """
        try:
            # Prepare the system prompt
            system_prompt = self._get_system_prompt()
            
            # Prepare user message with context
            user_message = self._prepare_user_message(user_command, context)
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.api_config['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=1000,
                timeout=config.GPT_RESPONSE_TIMEOUT
            )
            
            # Parse response
            gpt_response = response.choices[0].message.content
            agent_logger.log_command(user_command, {"raw_response": gpt_response})
            
            return self._parse_gpt_response(gpt_response)
            
        except Exception as e:
            agent_logger.log_error("GPT_INTERPRET", str(e), {"command": user_command})
            return None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for GPT"""
        return """You are an Application Agent that converts natural language commands into structured actions for a desktop automation system.

CRITICAL REQUIREMENTS:
1. Always respond with valid JSON format
2. Include a "reasoning" field explaining your interpretation
3. Only use the allowed action types listed below
4. Be extremely careful with file operations and system commands

ALLOWED ACTION TYPES:
- click: Click at coordinates {"action": "click", "x": 100, "y": 200}
- type: Type text {"action": "type", "text": "hello world"}
- key_press: Press key combinations {"action": "key_press", "key": "enter"}
- open_app: Launch application {"action": "open_app", "app_name": "notepad.exe"}
- close_app: Close application {"action": "close_app", "app_name": "notepad.exe"}
- file_read: Read file content {"action": "file_read", "file_path": "/path/to/file.txt"}
- file_write: Write to file {"action": "file_write", "file_path": "/path/to/file.txt", "content": "text"}
- mouse_move: Move mouse {"action": "mouse_move", "x": 100, "y": 200}
- scroll: Scroll on screen {"action": "scroll", "direction": "up", "clicks": 3}
- wait: Wait for seconds {"action": "wait", "seconds": 2}

RESPONSE FORMAT:
{
    "reasoning": "Explanation of what the user wants to do",
    "action": "action_type",
    "parameters": {
        // action-specific parameters
    },
    "confidence": 0.95,
    "safety_notes": "Any safety considerations"
}

SAFETY RULES:
- Never execute shell commands or scripts
- Only open whitelisted applications
- Be cautious with file operations
- Ask for clarification if command is ambiguous
- Refuse dangerous operations

If you cannot safely interpret the command, respond with:
{
    "reasoning": "Explanation of why command cannot be executed",
    "action": "error",
    "error": "Error message",
    "confidence": 0.0
}"""
    
    def _prepare_user_message(self, command: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare the user message with command and context"""
        message = f"User command: {command}\n"
        
        if context:
            message += f"Context: {json.dumps(context, indent=2)}\n"
        
        message += "\nPlease convert this to a structured action following the specified format."
        
        return message
    
    def _parse_gpt_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse and validate GPT response"""
        try:
            # Try to extract JSON from response
            response = response.strip()
            
            # Handle markdown code blocks
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            parsed = json.loads(response)
            
            # Validate required fields
            if not isinstance(parsed, dict):
                raise ValueError("Response is not a dictionary")
            
            if 'action' not in parsed:
                raise ValueError("Missing 'action' field")
            
            if 'reasoning' not in parsed:
                parsed['reasoning'] = "No reasoning provided"
            
            # Convert to standard format
            action_data = {
                'action': parsed['action'],
                'reasoning': parsed['reasoning'],
                'confidence': parsed.get('confidence', 0.5)
            }
            
            # Add parameters based on action type
            if parsed['action'] != 'error':
                if 'parameters' in parsed:
                    action_data.update(parsed['parameters'])
                else:
                    # Extract parameters from top level
                    for key, value in parsed.items():
                        if key not in ['action', 'reasoning', 'confidence', 'safety_notes']:
                            action_data[key] = value
            else:
                action_data['error'] = parsed.get('error', 'Unknown error')
            
            return action_data
            
        except json.JSONDecodeError as e:
            agent_logger.log_error("GPT_PARSE_JSON", str(e), {"response": response})
            return None
        except Exception as e:
            agent_logger.log_error("GPT_PARSE", str(e), {"response": response})
            return None
    
    def get_clarification(self, original_command: str, error_reason: str) -> Optional[str]:
        """Ask GPT for command clarification"""
        try:
            clarification_prompt = f"""
The user's command "{original_command}" could not be executed because: {error_reason}

Please provide a helpful clarification message to the user explaining:
1. Why the command couldn't be executed
2. What they might try instead
3. Any safety considerations

Respond with a clear, helpful message (not JSON).
"""
            
            response = self.client.chat.completions.create(
                model=self.api_config['model'],
                messages=[
                    {"role": "system", "content": "You are a helpful assistant explaining why commands cannot be executed."},
                    {"role": "user", "content": clarification_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            agent_logger.log_error("GPT_CLARIFICATION", str(e))
            return "Sorry, I couldn't process that command safely."

# Export singleton instance
gpt_interface = GPTInterface()