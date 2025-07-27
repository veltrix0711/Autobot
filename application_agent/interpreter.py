"""
Interpreter module for Application Agent
Processes GPT responses and coordinates action execution with safety checks
"""

from typing import Dict, Any, Optional, Tuple
from gpt_interface import gpt_interface
from safety import safety_checker
from logger import agent_logger

class CommandInterpreter:
    """Interprets user commands and coordinates safe execution"""
    
    def __init__(self):
        self.conversation_context = []
        self.last_action = None
    
    def process_command(self, user_command: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process user command through the full pipeline
        Returns (success, message, action_data)
        """
        try:
            # Step 1: Get GPT interpretation
            agent_logger.logger.info(f"Processing command: {user_command}")
            
            context = self._build_context()
            action_data = gpt_interface.interpret_command(user_command, context)
            
            if not action_data:
                return False, "Failed to interpret command", None
            
            # Step 2: Handle error responses from GPT
            if action_data.get('action') == 'error':
                error_msg = action_data.get('error', 'Unknown error')
                clarification = gpt_interface.get_clarification(user_command, error_msg)
                return False, clarification or error_msg, action_data
            
            # Step 3: Safety validation
            is_safe, safety_reason = safety_checker.validate_action(action_data)
            agent_logger.log_safety_check("ACTION_VALIDATION", is_safe, safety_reason)
            
            if not is_safe:
                clarification = gpt_interface.get_clarification(user_command, safety_reason)
                return False, clarification or f"Safety check failed: {safety_reason}", action_data
            
            # Step 4: User confirmation if required
            if safety_checker.requires_confirmation(action_data):
                confirmed = safety_checker.show_confirmation_dialog(action_data)
                if not confirmed:
                    return False, "Action cancelled by user", action_data
            
            # Step 5: Store context for future commands
            self._update_context(user_command, action_data)
            
            return True, f"Command interpreted successfully: {action_data.get('reasoning', 'No reasoning provided')}", action_data
            
        except Exception as e:
            agent_logger.log_error("COMMAND_PROCESSING", str(e), {"command": user_command})
            return False, f"Error processing command: {str(e)}", None
    
    def _build_context(self) -> Dict[str, Any]:
        """Build context from recent conversation"""
        context = {
            "recent_commands": self.conversation_context[-3:],  # Last 3 commands
            "last_action": self.last_action
        }
        
        # Add system information that might be useful
        try:
            import platform
            import os
            
            context.update({
                "platform": platform.system(),
                "current_directory": os.getcwd(),
                "user_home": os.path.expanduser("~")
            })
        except Exception:
            pass
        
        return context
    
    def _update_context(self, command: str, action_data: Dict[str, Any]):
        """Update conversation context"""
        self.conversation_context.append({
            "command": command,
            "action": action_data.get('action'),
            "reasoning": action_data.get('reasoning'),
            "timestamp": agent_logger.logger.handlers[0].format(agent_logger.logger.makeRecord(
                'context', 20, '', 0, '', (), None
            )).split(' - ')[0]
        })
        
        # Keep only recent context
        if len(self.conversation_context) > 10:
            self.conversation_context = self.conversation_context[-10:]
        
        self.last_action = action_data
    
    def get_conversation_history(self) -> str:
        """Get formatted conversation history"""
        if not self.conversation_context:
            return "No recent commands"
        
        history = "Recent Commands:\n"
        for i, item in enumerate(self.conversation_context[-5:], 1):
            history += f"{i}. {item['command']} -> {item['action']} ({item.get('reasoning', 'No reasoning')})\n"
        
        return history
    
    def validate_action_format(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate that action data has required format"""
        if not isinstance(action_data, dict):
            return False, "Action data must be a dictionary"
        
        if 'action' not in action_data:
            return False, "Missing 'action' field"
        
        action_type = action_data['action']
        
        # Validate action-specific required fields
        required_fields = {
            'click': ['x', 'y'],
            'type': ['text'],
            'key_press': ['key'],
            'open_app': ['app_name'],
            'close_app': ['app_name'],
            'file_read': ['file_path'],
            'file_write': ['file_path', 'content'],
            'mouse_move': ['x', 'y'],
            'scroll': ['direction'],
            'wait': ['seconds']
        }
        
        if action_type in required_fields:
            for field in required_fields[action_type]:
                if field not in action_data:
                    return False, f"Missing required field '{field}' for action '{action_type}'"
        
        return True, "Action format valid"
    
    def suggest_commands(self) -> list[str]:
        """Suggest example commands based on context"""
        suggestions = [
            "Open Chrome and go to YouTube",
            "Write a note that says 'Meeting at 3 PM' in Notepad",
            "Move the mouse to the top left and click",
            "Type 'Hello world' and hit enter",
            "Read me the contents of desktop.txt",
            "Click at coordinates 500, 300",
            "Press the enter key",
            "Wait for 2 seconds",
            "Scroll down 3 times"
        ]
        
        # Add context-specific suggestions if available
        if self.last_action:
            last_action_type = self.last_action.get('action')
            if last_action_type == 'open_app':
                suggestions.insert(0, f"Close {self.last_action.get('app_name', 'the application')}")
            elif last_action_type == 'file_read':
                suggestions.insert(0, f"Write to {self.last_action.get('file_path', 'that file')}")
        
        return suggestions[:5]  # Return top 5 suggestions

# Export singleton instance
command_interpreter = CommandInterpreter()