"""
Actions module for Application Agent
Safe wrappers for mouse, keyboard, application control, and file operations
"""

import os
import time
import subprocess
import signal
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Import automation libraries with error handling
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Enable failsafe
    pyautogui.PAUSE = 0.1  # Small pause between actions
except ImportError:
    pyautogui = None

try:
    import keyboard
except ImportError:
    keyboard = None

try:
    import psutil
except ImportError:
    psutil = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

from config import config
from logger import agent_logger

class ActionExecutor:
    """Executes validated actions safely"""
    
    def __init__(self):
        self.running_processes = {}
        self._validate_dependencies()
    
    def _validate_dependencies(self):
        """Check if required dependencies are available"""
        missing = []
        if not pyautogui:
            missing.append("pyautogui")
        if not keyboard:
            missing.append("keyboard")
        if not psutil:
            missing.append("psutil")
        
        if missing:
            agent_logger.log_error("DEPENDENCIES", f"Missing dependencies: {', '.join(missing)}")
    
    def execute_action(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Execute a validated action
        Returns (success, result_message)
        """
        action_type = action_data.get('action', '').lower()
        
        try:
            if action_type == 'click':
                return self._execute_click(action_data)
            elif action_type == 'type':
                return self._execute_type(action_data)
            elif action_type == 'key_press':
                return self._execute_key_press(action_data)
            elif action_type == 'open_app':
                return self._execute_open_app(action_data)
            elif action_type == 'close_app':
                return self._execute_close_app(action_data)
            elif action_type == 'file_read':
                return self._execute_file_read(action_data)
            elif action_type == 'file_write':
                return self._execute_file_write(action_data)
            elif action_type == 'mouse_move':
                return self._execute_mouse_move(action_data)
            elif action_type == 'scroll':
                return self._execute_scroll(action_data)
            elif action_type == 'wait':
                return self._execute_wait(action_data)
            else:
                return False, f"Unknown action type: {action_type}"
                
        except Exception as e:
            agent_logger.log_error("ACTION_EXECUTION", str(e), action_data)
            return False, f"Action execution failed: {str(e)}"
    
    def _execute_click(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute mouse click"""
        if not pyautogui:
            return False, "pyautogui not available"
        
        try:
            x = int(action_data['x'])
            y = int(action_data['y'])
            button = action_data.get('button', 'left')
            clicks = action_data.get('clicks', 1)
            
            # Validate coordinates are on screen
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                return False, f"Coordinates ({x}, {y}) are outside screen bounds"
            
            pyautogui.click(x, y, clicks=clicks, button=button)
            
            agent_logger.log_action("CLICK", {"x": x, "y": y, "button": button, "clicks": clicks})
            return True, f"Clicked at ({x}, {y})"
            
        except Exception as e:
            return False, f"Click failed: {str(e)}"
    
    def _execute_type(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute text typing"""
        if not pyautogui:
            return False, "pyautogui not available"
        
        try:
            text = action_data['text']
            interval = action_data.get('interval', 0.01)
            
            pyautogui.typewrite(text, interval=interval)
            
            agent_logger.log_action("TYPE", {"text_length": len(text), "interval": interval})
            return True, f"Typed {len(text)} characters"
            
        except Exception as e:
            return False, f"Type failed: {str(e)}"
    
    def _execute_key_press(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute key press"""
        if not pyautogui:
            return False, "pyautogui not available"
        
        try:
            key = action_data['key']
            
            # Handle special key combinations
            if '+' in key:
                keys = [k.strip() for k in key.split('+')]
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(key)
            
            agent_logger.log_action("KEY_PRESS", {"key": key})
            return True, f"Pressed key: {key}"
            
        except Exception as e:
            return False, f"Key press failed: {str(e)}"
    
    def _execute_open_app(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute application launch"""
        try:
            app_name = action_data['app_name']
            
            # Platform-specific application launching
            if os.name == 'nt':  # Windows
                success, message = self._launch_windows_app(app_name)
            else:  # Linux/macOS
                success, message = self._launch_unix_app(app_name)
            
            if success:
                agent_logger.log_app_control("OPEN", app_name, True)
            else:
                agent_logger.log_app_control("OPEN", app_name, False)
            
            return success, message
            
        except Exception as e:
            return False, f"App launch failed: {str(e)}"
    
    def _launch_windows_app(self, app_name: str) -> Tuple[bool, str]:
        """Launch application on Windows"""
        try:
            # Try common Windows paths
            common_paths = [
                app_name,  # If full path or in PATH
                f"C:\\Program Files\\{app_name}",
                f"C:\\Program Files (x86)\\{app_name}",
                f"C:\\Windows\\System32\\{app_name}"
            ]
            
            for path in common_paths:
                try:
                    process = subprocess.Popen(path, shell=True)
                    self.running_processes[app_name] = process.pid
                    return True, f"Launched {app_name}"
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            
            return False, f"Could not find application: {app_name}"
            
        except Exception as e:
            return False, f"Windows app launch error: {str(e)}"
    
    def _launch_unix_app(self, app_name: str) -> Tuple[bool, str]:
        """Launch application on Unix-like systems"""
        try:
            # Remove .exe extension if present (for cross-platform compatibility)
            app_name = app_name.replace('.exe', '')
            
            # Try to launch the application
            process = subprocess.Popen([app_name], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            self.running_processes[app_name] = process.pid
            return True, f"Launched {app_name}"
            
        except FileNotFoundError:
            return False, f"Application not found: {app_name}"
        except Exception as e:
            return False, f"Unix app launch error: {str(e)}"
    
    def _execute_close_app(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute application close"""
        try:
            app_name = action_data['app_name']
            
            if not psutil:
                return False, "psutil not available for app management"
            
            # Find and terminate processes
            terminated = 0
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    if app_name.lower() in process.info['name'].lower():
                        process.terminate()
                        terminated += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if terminated > 0:
                agent_logger.log_app_control("CLOSE", app_name, True)
                return True, f"Terminated {terminated} instance(s) of {app_name}"
            else:
                agent_logger.log_app_control("CLOSE", app_name, False)
                return False, f"No running instances of {app_name} found"
                
        except Exception as e:
            return False, f"App close failed: {str(e)}"
    
    def _execute_file_read(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute file read operation"""
        try:
            file_path = action_data['file_path']
            path = Path(file_path)
            
            if not path.exists():
                return False, f"File does not exist: {file_path}"
            
            # Read file content
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            agent_logger.log_file_operation("READ", file_path, True)
            
            # Limit output for safety
            if len(content) > 1000:
                display_content = content[:1000] + "... (truncated)"
            else:
                display_content = content
            
            return True, f"File content:\n{display_content}"
            
        except Exception as e:
            agent_logger.log_file_operation("READ", action_data.get('file_path', 'unknown'), False)
            return False, f"File read failed: {str(e)}"
    
    def _execute_file_write(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute file write operation"""
        try:
            file_path = action_data['file_path']
            content = action_data['content']
            mode = action_data.get('mode', 'w')  # 'w' for write, 'a' for append
            
            path = Path(file_path)
            
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
            
            agent_logger.log_file_operation("WRITE", file_path, True)
            return True, f"Successfully wrote {len(content)} characters to {file_path}"
            
        except Exception as e:
            agent_logger.log_file_operation("WRITE", action_data.get('file_path', 'unknown'), False)
            return False, f"File write failed: {str(e)}"
    
    def _execute_mouse_move(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute mouse movement"""
        if not pyautogui:
            return False, "pyautogui not available"
        
        try:
            x = int(action_data['x'])
            y = int(action_data['y'])
            duration = action_data.get('duration', 0.25)
            
            pyautogui.moveTo(x, y, duration=duration)
            
            agent_logger.log_action("MOUSE_MOVE", {"x": x, "y": y, "duration": duration})
            return True, f"Moved mouse to ({x}, {y})"
            
        except Exception as e:
            return False, f"Mouse move failed: {str(e)}"
    
    def _execute_scroll(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute scroll action"""
        if not pyautogui:
            return False, "pyautogui not available"
        
        try:
            direction = action_data['direction'].lower()
            clicks = action_data.get('clicks', 3)
            x = action_data.get('x')
            y = action_data.get('y')
            
            # Determine scroll amount
            scroll_amount = clicks if direction == 'up' else -clicks
            
            if x is not None and y is not None:
                pyautogui.scroll(scroll_amount, x=x, y=y)
            else:
                pyautogui.scroll(scroll_amount)
            
            agent_logger.log_action("SCROLL", {"direction": direction, "clicks": clicks})
            return True, f"Scrolled {direction} {clicks} clicks"
            
        except Exception as e:
            return False, f"Scroll failed: {str(e)}"
    
    def _execute_wait(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute wait action"""
        try:
            seconds = float(action_data['seconds'])
            
            if seconds > 60:  # Limit wait time
                return False, "Wait time too long (max 60 seconds)"
            
            time.sleep(seconds)
            
            agent_logger.log_action("WAIT", {"seconds": seconds})
            return True, f"Waited for {seconds} seconds"
            
        except Exception as e:
            return False, f"Wait failed: {str(e)}"
    
    def get_screen_info(self) -> Dict[str, Any]:
        """Get screen information for context"""
        info = {}
        
        if pyautogui:
            try:
                info['screen_size'] = pyautogui.size()
                info['mouse_position'] = pyautogui.position()
            except Exception:
                pass
        
        return info
    
    def cleanup(self):
        """Cleanup running processes"""
        for app_name, pid in self.running_processes.items():
            try:
                if psutil and psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    process.terminate()
                    agent_logger.log_app_control("CLEANUP_TERMINATE", app_name, True)
            except Exception as e:
                agent_logger.log_error("CLEANUP", str(e), {"app": app_name, "pid": pid})

# Export singleton instance
action_executor = ActionExecutor()