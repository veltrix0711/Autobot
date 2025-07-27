"""
Logging module for Application Agent
Tracks all actions, safety checks, and system interactions
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
from config import config

class AgentLogger:
    """Logger for tracking all agent actions and safety events"""
    
    def __init__(self, log_file: str = "agent_log.txt"):
        self.log_file = log_file
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        self.log_file = os.path.join("logs", self.log_file)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('ApplicationAgent')
        
        # Log startup
        self.logger.info("Application Agent Logger initialized")
    
    def log_command(self, command: str, gpt_response: Optional[Dict[str, Any]] = None):
        """Log user command and GPT response"""
        self.logger.info(f"USER COMMAND: {command}")
        if gpt_response:
            self.logger.info(f"GPT RESPONSE: {gpt_response}")
    
    def log_action(self, action_type: str, details: Dict[str, Any], success: bool = True):
        """Log executed action with details"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"ACTION {status}: {action_type} - {details}")
    
    def log_safety_check(self, check_type: str, passed: bool, details: str = ""):
        """Log safety check results"""
        status = "PASSED" if passed else "FAILED"
        self.logger.warning(f"SAFETY CHECK {status}: {check_type} - {details}")
    
    def log_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """Log errors with context"""
        self.logger.error(f"ERROR: {error_type} - {error_message}")
        if context:
            self.logger.error(f"CONTEXT: {context}")
    
    def log_file_operation(self, operation: str, file_path: str, success: bool = True):
        """Log file operations"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"FILE {status}: {operation} on {file_path}")
    
    def log_app_control(self, operation: str, app_name: str, success: bool = True):
        """Log application control operations"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"APP {status}: {operation} on {app_name}")
    
    def log_user_confirmation(self, action: str, confirmed: bool):
        """Log user confirmation results"""
        status = "CONFIRMED" if confirmed else "DENIED"
        self.logger.info(f"USER CONFIRMATION {status}: {action}")
    
    def get_recent_logs(self, lines: int = 50) -> str:
        """Get recent log entries"""
        try:
            with open(self.log_file, 'r') as f:
                log_lines = f.readlines()
                return ''.join(log_lines[-lines:])
        except FileNotFoundError:
            return "No log file found"
        except Exception as e:
            return f"Error reading logs: {str(e)}"
    
    def export_session_log(self, session_start: datetime) -> str:
        """Export logs from current session"""
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            session_lines = []
            for line in lines:
                try:
                    # Extract timestamp from log line
                    timestamp_str = line.split(' - ')[0]
                    log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    if log_time >= session_start:
                        session_lines.append(line)
                except (ValueError, IndexError):
                    continue
            
            return ''.join(session_lines)
        except Exception as e:
            self.log_error("LOG_EXPORT", str(e))
            return ""

# Export singleton instance
agent_logger = AgentLogger()