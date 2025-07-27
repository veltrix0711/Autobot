"""
CLI interface for Application Agent
Provides command-line interaction for headless operation
"""

import sys
import signal
import readline
from typing import Optional
from datetime import datetime

from config import config
from logger import agent_logger
from interpreter import command_interpreter
from actions import action_executor

class ApplicationAgentCLI:
    """Command-line interface for the Application Agent"""
    
    def __init__(self):
        self.running = True
        self.session_start = datetime.now()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Setup readline for command history
        try:
            readline.read_history_file(".agent_history")
        except FileNotFoundError:
            pass
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n\nShutting down Application Agent...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """Run the CLI interface"""
        try:
            self._print_banner()
            self._check_configuration()
            
            print("Application Agent CLI started. Type 'help' for commands or 'quit' to exit.")
            print("Use Ctrl+C to exit at any time.\n")
            
            while self.running:
                try:
                    command = input("agent> ").strip()
                    
                    if not command:
                        continue
                    
                    # Add to history
                    readline.add_history(command)
                    
                    # Handle built-in commands
                    if self._handle_builtin_command(command):
                        continue
                    
                    # Process agent command
                    self._process_command(command)
                    
                except EOFError:
                    print("\nGoodbye!")
                    break
                except KeyboardInterrupt:
                    print("\nUse 'quit' or Ctrl+C to exit.")
                    continue
                    
        except Exception as e:
            agent_logger.log_error("CLI_MAIN", str(e))
            print(f"Fatal error: {e}")
        finally:
            self.cleanup()
    
    def _print_banner(self):
        """Print application banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                            Application Agent CLI                             ║
║                     Secure Local Desktop Automation                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
        print(f"Version: 1.0.0")
        print(f"Safety Mode: {'ON' if config.SAFETY_MODE else 'OFF'}")
        print(f"Confirmations: {'REQUIRED' if config.CONFIRMATION_REQUIRED else 'DISABLED'}")
        print(f"Model: {config.GPT_MODEL}")
        print()
    
    def _check_configuration(self):
        """Check and display configuration status"""
        if not config.validate_config():
            print("⚠️  WARNING: No API key configured!")
            print("   Please set OPENROUTER_API_KEY or OPENAI_API_KEY in your .env file.")
            print()
    
    def _handle_builtin_command(self, command: str) -> bool:
        """
        Handle built-in CLI commands
        Returns True if command was handled, False otherwise
        """
        cmd_parts = command.lower().split()
        cmd = cmd_parts[0] if cmd_parts else ""
        
        if cmd in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            self.running = False
            return True
        
        elif cmd == 'help':
            self._show_help()
            return True
        
        elif cmd == 'status':
            self._show_status()
            return True
        
        elif cmd == 'history':
            self._show_history()
            return True
        
        elif cmd == 'logs':
            lines = int(cmd_parts[1]) if len(cmd_parts) > 1 and cmd_parts[1].isdigit() else 20
            self._show_logs(lines)
            return True
        
        elif cmd == 'clear':
            self._clear_screen()
            return True
        
        elif cmd == 'config':
            self._show_config()
            return True
        
        elif cmd == 'suggestions':
            self._show_suggestions()
            return True
        
        elif cmd == 'export':
            self._export_session()
            return True
        
        return False
    
    def _process_command(self, command: str):
        """Process a user command"""
        print(f"\n> {command}")
        
        try:
            # Step 1: Interpret command
            success, message, action_data = command_interpreter.process_command(command)
            
            if not success:
                print(f"❌ {message}")
                return
            
            # Step 2: Execute action if interpretation was successful
            if action_data:
                print(f"💭 {action_data.get('reasoning', 'No reasoning provided')}")
                
                # Confirm if CLI mode and confirmations are enabled
                if config.CONFIRMATION_REQUIRED and self._requires_cli_confirmation(action_data):
                    if not self._get_user_confirmation(action_data):
                        print("❌ Action cancelled by user")
                        return
                
                exec_success, exec_message = action_executor.execute_action(action_data)
                
                if exec_success:
                    print(f"✅ {exec_message}")
                else:
                    print(f"❌ Execution failed: {exec_message}")
            else:
                print(f"✅ {message}")
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            agent_logger.log_error("CLI_COMMAND_EXECUTION", str(e), {"command": command})
            print(f"❌ {error_msg}")
        
        print()  # Add spacing
    
    def _requires_cli_confirmation(self, action_data) -> bool:
        """Check if action requires confirmation in CLI mode"""
        action_type = action_data.get('action', '').lower()
        
        # Always confirm these actions in CLI
        high_risk_actions = ['file_write', 'open_app', 'close_app']
        return action_type in high_risk_actions
    
    def _get_user_confirmation(self, action_data) -> bool:
        """Get user confirmation for action"""
        action_type = action_data.get('action', 'Unknown')
        
        details = self._format_action_details(action_data)
        print(f"\n⚠️  Confirm action execution:")
        print(f"   Action: {action_type}")
        print(f"   Details: {details}")
        
        while True:
            response = input("   Proceed? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                agent_logger.log_user_confirmation(f"{action_type}: {details}", True)
                return True
            elif response in ['n', 'no']:
                agent_logger.log_user_confirmation(f"{action_type}: {details}", False)
                return False
            else:
                print("   Please enter 'y' or 'n'")
    
    def _format_action_details(self, action_data) -> str:
        """Format action details for display"""
        action_type = action_data.get('action', '')
        
        if action_type == 'click':
            return f"Click at ({action_data.get('x')}, {action_data.get('y')})"
        elif action_type == 'type':
            text = action_data.get('text', '')
            if len(text) > 50:
                text = text[:47] + "..."
            return f"Type: '{text}'"
        elif action_type == 'open_app':
            return f"Open application: {action_data.get('app_name')}"
        elif action_type == 'file_read':
            return f"Read file: {action_data.get('file_path')}"
        elif action_type == 'file_write':
            return f"Write to file: {action_data.get('file_path')}"
        elif action_type == 'key_press':
            return f"Press key: {action_data.get('key')}"
        else:
            return str(action_data)
    
    def _show_help(self):
        """Show help information"""
        help_text = """
Available Commands:

Built-in Commands:
  help              Show this help message
  quit/exit/bye     Exit the application
  status            Show agent status
  history           Show command history
  logs [n]          Show recent log entries (default: 20)
  clear             Clear the screen
  config            Show configuration
  suggestions       Show example commands
  export            Export session logs

Agent Commands:
  Any natural language command for automation, such as:
  - "Open Chrome and go to YouTube"
  - "Click at coordinates 100, 200"
  - "Type 'Hello World'"
  - "Read the file desktop.txt"
  - "Write 'Meeting notes' to file notes.txt"

Tips:
  - Use quotes for text that contains spaces
  - Commands are logged for your security
  - Dangerous actions require confirmation
  - Use Ctrl+C to interrupt at any time
        """
        print(help_text)
    
    def _show_status(self):
        """Show current agent status"""
        screen_info = action_executor.get_screen_info()
        
        print("\nAgent Status:")
        print(f"  Session started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Safety mode: {'Enabled' if config.SAFETY_MODE else 'Disabled'}")
        print(f"  Confirmations: {'Required' if config.CONFIRMATION_REQUIRED else 'Disabled'}")
        print(f"  API model: {config.GPT_MODEL}")
        
        if screen_info:
            if 'screen_size' in screen_info:
                print(f"  Screen size: {screen_info['screen_size']}")
            if 'mouse_position' in screen_info:
                print(f"  Mouse position: {screen_info['mouse_position']}")
        
        print()
    
    def _show_history(self):
        """Show command history"""
        history = command_interpreter.get_conversation_history()
        print(f"\n{history}")
    
    def _show_logs(self, lines: int = 20):
        """Show recent log entries"""
        logs = agent_logger.get_recent_logs(lines)
        print(f"\nRecent logs ({lines} lines):")
        print("=" * 60)
        print(logs)
        print("=" * 60)
    
    def _clear_screen(self):
        """Clear the terminal screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        self._print_banner()
    
    def _show_config(self):
        """Show current configuration"""
        print("\nConfiguration:")
        print(f"  API Key: {'Set' if config.OPENROUTER_API_KEY or config.OPENAI_API_KEY else 'Not set'}")
        print(f"  Model: {config.GPT_MODEL}")
        print(f"  Safety mode: {config.SAFETY_MODE}")
        print(f"  Confirmations: {config.CONFIRMATION_REQUIRED}")
        print(f"  Log level: {config.LOG_LEVEL}")
        print(f"  Max retries: {config.MAX_RETRY_ATTEMPTS}")
        
        print(f"\nWhitelisted applications ({len(config.WHITELISTED_APPLICATIONS)}):")
        for app in config.WHITELISTED_APPLICATIONS[:10]:  # Show first 10
            print(f"  - {app}")
        if len(config.WHITELISTED_APPLICATIONS) > 10:
            print(f"  ... and {len(config.WHITELISTED_APPLICATIONS) - 10} more")
        
        print()
    
    def _show_suggestions(self):
        """Show command suggestions"""
        suggestions = command_interpreter.suggest_commands()
        
        print("\nSuggested commands:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
        print()
    
    def _export_session(self):
        """Export current session logs"""
        session_logs = agent_logger.export_session_log(self.session_start)
        
        if session_logs:
            filename = f"session_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            try:
                with open(filename, 'w') as f:
                    f.write(session_logs)
                print(f"✅ Session logs exported to {filename}")
            except Exception as e:
                print(f"❌ Failed to export logs: {str(e)}")
        else:
            print("ℹ️  No session data to export")
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Save command history
            readline.write_history_file(".agent_history")
        except Exception:
            pass
        
        # Cleanup action executor
        action_executor.cleanup()
        agent_logger.logger.info("Application Agent CLI shut down")

def run_cli():
    """Entry point for CLI mode"""
    cli = ApplicationAgentCLI()
    cli.run()

if __name__ == "__main__":
    run_cli()