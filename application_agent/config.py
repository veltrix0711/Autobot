"""
Configuration module for Application Agent
Contains safety settings, whitelists, and environment configuration
"""

import os
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Application Agent"""
    
    # API Configuration
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GPT_MODEL = os.getenv('GPT_MODEL', 'openai/gpt-4-turbo-preview')
    
    # Agent Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    SAFETY_MODE = os.getenv('SAFETY_MODE', 'true').lower() == 'true'
    CONFIRMATION_REQUIRED = os.getenv('CONFIRMATION_REQUIRED', 'true').lower() == 'true'
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    
    # Hotkey Configuration
    ACTIVATION_HOTKEY = os.getenv('ACTIVATION_HOTKEY', 'ctrl+shift+a')
    
    # Safety Configuration
    WHITELISTED_APPLICATIONS = [
        'notepad.exe', 'notepad++.exe', 'code.exe', 'chrome.exe', 
        'firefox.exe', 'calculator.exe', 'mspaint.exe', 'explorer.exe',
        'cmd.exe', 'powershell.exe', 'wordpad.exe', 'write.exe',
        'gedit', 'kate', 'nano', 'vim', 'emacs', 'firefox', 'chromium',
        'nautilus', 'dolphin', 'thunar', 'pcmanfm', 'calc', 'gnome-calculator'
    ]
    
    DANGEROUS_KEYWORDS = [
        'format', 'delete', 'remove', 'rm -rf', 'del /f', 'shutdown', 
        'restart', 'reboot', 'kill', 'taskkill', 'sudo rm', 'rmdir',
        'fdisk', 'mkfs', 'dd if=', 'wget', 'curl', 'powershell -c',
        'cmd /c', 'bash -c', 'eval', 'exec'
    ]
    
    SAFE_FILE_EXTENSIONS = [
        '.txt', '.md', '.json', '.csv', '.xml', '.html', '.css', '.js',
        '.py', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.php', '.rb'
    ]
    
    RESTRICTED_DIRECTORIES = [
        '/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/root',
        'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
        '/System', '/Library', '/usr/lib', '/lib'
    ]
    
    # Action timeouts (seconds)
    ACTION_TIMEOUT = 10
    GPT_RESPONSE_TIMEOUT = 30
    
    # GUI Configuration
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 300
    TRAY_ICON_SIZE = (16, 16)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.OPENROUTER_API_KEY and not cls.OPENAI_API_KEY:
            return False
        return True
    
    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        """Get API configuration for GPT interface"""
        if cls.OPENROUTER_API_KEY:
            return {
                'api_key': cls.OPENROUTER_API_KEY,
                'base_url': cls.OPENROUTER_BASE_URL,
                'model': cls.GPT_MODEL
            }
        elif cls.OPENAI_API_KEY:
            return {
                'api_key': cls.OPENAI_API_KEY,
                'base_url': 'https://api.openai.com/v1',
                'model': cls.GPT_MODEL.replace('openai/', '')
            }
        else:
            raise ValueError("No valid API key configured")

# Export singleton instance
config = Config()