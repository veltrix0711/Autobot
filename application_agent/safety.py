"""
Safety module for Application Agent
Provides security checks, confirmations, and safe execution controls
"""

import os
import re
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from config import config
from logger import agent_logger

class SafetyChecker:
    """Safety validation and confirmation system"""
    
    def __init__(self):
        self.dangerous_patterns = self._compile_dangerous_patterns()
    
    def _compile_dangerous_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for dangerous commands"""
        patterns = []
        for keyword in config.DANGEROUS_KEYWORDS:
            # Escape special regex characters and create pattern
            escaped = re.escape(keyword)
            patterns.append(re.compile(escaped, re.IGNORECASE))
        return patterns
    
    def validate_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate if an action is safe to execute
        Returns (is_safe, reason)
        """
        action_type = action.get('action', '').lower()
        
        # Check for dangerous action types
        if action_type in ['shell', 'execute', 'run_command']:
            return False, "Shell command execution is not allowed"
        
        # Check specific action types
        if action_type == 'click':
            return self._validate_click_action(action)
        elif action_type == 'type':
            return self._validate_type_action(action)
        elif action_type == 'open_app':
            return self._validate_app_action(action)
        elif action_type == 'file_read':
            return self._validate_file_read(action)
        elif action_type == 'file_write':
            return self._validate_file_write(action)
        elif action_type == 'key_press':
            return self._validate_key_action(action)
        else:
            return True, "Action type validated"
    
    def _validate_click_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate mouse click actions"""
        try:
            x = action.get('x')
            y = action.get('y')
            if x is None or y is None:
                return False, "Click coordinates not specified"
            
            # Basic coordinate validation
            if not (0 <= x <= 3840 and 0 <= y <= 2160):  # Max reasonable screen size
                return False, "Click coordinates out of reasonable range"
            
            return True, "Click action validated"
        except Exception as e:
            return False, f"Click validation error: {str(e)}"
    
    def _validate_type_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate keyboard typing actions"""
        text = action.get('text', '')
        
        # Check for dangerous text patterns
        for pattern in self.dangerous_patterns:
            if pattern.search(text):
                return False, f"Dangerous text pattern detected: {pattern.pattern}"
        
        # Check for excessive length
        if len(text) > 10000:
            return False, "Text too long for safety"
        
        return True, "Type action validated"
    
    def _validate_app_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate application control actions"""
        app_name = action.get('app_name', '').lower()
        
        # Check if app is whitelisted
        if not any(allowed.lower() in app_name for allowed in config.WHITELISTED_APPLICATIONS):
            return False, f"Application '{app_name}' not in whitelist"
        
        return True, "App action validated"
    
    def _validate_file_read(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate file read operations"""
        file_path = action.get('file_path', '')
        
        try:
            path = Path(file_path).resolve()
            
            # Check if in restricted directory
            for restricted in config.RESTRICTED_DIRECTORIES:
                if str(path).startswith(restricted):
                    return False, f"Access to restricted directory: {restricted}"
            
            # Check if file exists
            if not path.exists():
                return False, "File does not exist"
            
            # Check file size (prevent reading huge files)
            if path.stat().st_size > 50 * 1024 * 1024:  # 50MB limit
                return False, "File too large for safety"
            
            return True, "File read validated"
        except Exception as e:
            return False, f"File validation error: {str(e)}"
    
    def _validate_file_write(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate file write operations"""
        file_path = action.get('file_path', '')
        content = action.get('content', '')
        
        try:
            path = Path(file_path).resolve()
            
            # Check if in restricted directory
            for restricted in config.RESTRICTED_DIRECTORIES:
                if str(path).startswith(restricted):
                    return False, f"Write to restricted directory: {restricted}"
            
            # Check file extension
            if path.suffix.lower() not in config.SAFE_FILE_EXTENSIONS:
                return False, f"Unsafe file extension: {path.suffix}"
            
            # Check content for dangerous patterns
            for pattern in self.dangerous_patterns:
                if pattern.search(content):
                    return False, f"Dangerous content pattern detected"
            
            # Check content size
            if len(content) > 10 * 1024 * 1024:  # 10MB limit
                return False, "Content too large for safety"
            
            return True, "File write validated"
        except Exception as e:
            return False, f"File write validation error: {str(e)}"
    
    def _validate_key_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate keyboard key press actions"""
        key = action.get('key', '').lower()
        
        # Block dangerous key combinations
        dangerous_keys = ['alt+f4', 'ctrl+alt+del', 'cmd+q', 'win+r']
        if key in dangerous_keys:
            return False, f"Dangerous key combination: {key}"
        
        return True, "Key action validated"
    
    def requires_confirmation(self, action: Dict[str, Any]) -> bool:
        """Check if action requires user confirmation"""
        if not config.CONFIRMATION_REQUIRED:
            return False
        
        action_type = action.get('action', '').lower()
        
        # Always confirm file writes and app launches
        confirmation_actions = ['file_write', 'open_app', 'close_app']
        if action_type in confirmation_actions:
            return True
        
        # Confirm if file path contains certain keywords
        file_path = action.get('file_path', '')
        if file_path and any(keyword in file_path.lower() for keyword in ['system', 'program', 'windows']):
            return True
        
        return False
    
    def show_confirmation_dialog(self, action: Dict[str, Any]) -> bool:
        """Show confirmation dialog to user"""
        try:
            root = tk.Tk()
            root.withdraw()  # Hide main window
            
            action_type = action.get('action', 'Unknown')
            action_details = self._format_action_details(action)
            
            message = f"Confirm action execution:\n\nAction: {action_type}\nDetails: {action_details}\n\nProceed?"
            
            result = messagebox.askyesno("Confirm Action", message)
            root.destroy()
            
            agent_logger.log_user_confirmation(f"{action_type}: {action_details}", result)
            return result
            
        except Exception as e:
            agent_logger.log_error("CONFIRMATION_DIALOG", str(e))
            return False
    
    def _format_action_details(self, action: Dict[str, Any]) -> str:
        """Format action details for confirmation dialog"""
        action_type = action.get('action', '')
        
        if action_type == 'click':
            return f"Click at ({action.get('x')}, {action.get('y')})"
        elif action_type == 'type':
            text = action.get('text', '')
            if len(text) > 50:
                text = text[:47] + "..."
            return f"Type: '{text}'"
        elif action_type == 'open_app':
            return f"Open application: {action.get('app_name')}"
        elif action_type == 'file_read':
            return f"Read file: {action.get('file_path')}"
        elif action_type == 'file_write':
            return f"Write to file: {action.get('file_path')}"
        elif action_type == 'key_press':
            return f"Press key: {action.get('key')}"
        else:
            return str(action)

# Export singleton instance
safety_checker = SafetyChecker()