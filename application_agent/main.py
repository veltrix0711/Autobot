#!/usr/bin/env python3
"""
Main entry point for Application Agent
Provides GUI interface, hotkey activation, and system tray functionality
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from typing import Optional
import atexit

# Import automation libraries with error handling
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# Import agent modules
from config import config
from logger import agent_logger
from interpreter import command_interpreter
from actions import action_executor
from gpt_interface import gpt_interface

class ApplicationAgentGUI:
    """Main GUI for the Application Agent"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.tray_icon = None
        self.session_start = datetime.now()
        self.hotkey_thread = None
        self.is_running = True
        
        self._setup_gui()
        self._setup_hotkey()
        self._setup_tray()
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
    
    def _setup_gui(self):
        """Setup the main GUI window"""
        self.root.title("Application Agent")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Application Agent", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, text="Status:")
        status_label.grid(row=1, column=0, sticky=tk.W)
        status_value = ttk.Label(main_frame, textvariable=self.status_var, 
                                foreground="green")
        status_value.grid(row=1, column=1, sticky=tk.W)
        
        # Command input
        ttk.Label(main_frame, text="Command:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(main_frame, textvariable=self.command_var, width=40)
        self.command_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(10, 0), padx=(5, 0))
        self.command_entry.bind('<Return>', self._on_command_enter)
        
        # Execute button
        self.execute_btn = ttk.Button(main_frame, text="Execute", command=self._execute_command)
        self.execute_btn.grid(row=2, column=2, pady=(10, 0), padx=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Button(button_frame, text="Show Suggestions", 
                  command=self._show_suggestions).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Show History", 
                  command=self._show_history).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Logs", 
                  command=self._clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Settings", 
                  command=self._show_settings).pack(side=tk.LEFT, padx=(0, 5))
        
        # Output area
        ttk.Label(main_frame, text="Output:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=(10, 0))
        self.output_text = scrolledtext.ScrolledText(main_frame, width=50, height=15, 
                                                    wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                             pady=(10, 0), padx=(5, 0))
        
        # Hotkey info
        hotkey_info = f"Global hotkey: {config.ACTIVATION_HOTKEY}" if KEYBOARD_AVAILABLE else "Global hotkeys not available"
        ttk.Label(main_frame, text=hotkey_info, font=('Arial', 8), 
                 foreground="gray").grid(row=5, column=0, columnspan=3, pady=(5, 0))
        
        # Initial message
        self._append_output("Application Agent started successfully!")
        self._append_output(f"Safety mode: {'ON' if config.SAFETY_MODE else 'OFF'}")
        self._append_output(f"Confirmations: {'REQUIRED' if config.CONFIRMATION_REQUIRED else 'DISABLED'}")
        
        if not config.validate_config():
            self._append_output("WARNING: No API key configured! Please check your .env file.")
            self.status_var.set("Configuration Error")
    
    def _setup_hotkey(self):
        """Setup global hotkey for activation"""
        if not KEYBOARD_AVAILABLE:
            agent_logger.logger.warning("Keyboard library not available - hotkeys disabled")
            return
        
        def hotkey_handler():
            """Handle hotkey activation"""
            try:
                self.root.after(0, self._show_quick_input)
            except Exception as e:
                agent_logger.log_error("HOTKEY", str(e))
        
        def hotkey_thread():
            """Thread for hotkey monitoring"""
            try:
                keyboard.add_hotkey(config.ACTIVATION_HOTKEY, hotkey_handler)
                while self.is_running:
                    keyboard.wait(0.1)
            except Exception as e:
                agent_logger.log_error("HOTKEY_THREAD", str(e))
        
        self.hotkey_thread = threading.Thread(target=hotkey_thread, daemon=True)
        self.hotkey_thread.start()
        
        agent_logger.logger.info(f"Global hotkey registered: {config.ACTIVATION_HOTKEY}")
    
    def _setup_tray(self):
        """Setup system tray icon"""
        if not TRAY_AVAILABLE:
            agent_logger.logger.warning("Tray functionality not available")
            return
        
        try:
            # Create a simple icon
            image = Image.new('RGB', (64, 64), color='blue')
            draw = ImageDraw.Draw(image)
            draw.rectangle([16, 16, 48, 48], fill='white')
            draw.text((20, 25), "AI", fill='blue')
            
            # Create tray menu
            menu = pystray.Menu(
                pystray.MenuItem("Show", self._show_window),
                pystray.MenuItem("Quick Command", self._show_quick_input),
                pystray.MenuItem("Settings", self._show_settings),
                pystray.MenuItem("Quit", self._quit_application)
            )
            
            self.tray_icon = pystray.Icon("ApplicationAgent", image, 
                                         "Application Agent", menu)
            
            # Start tray in separate thread
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            tray_thread.start()
            
            agent_logger.logger.info("System tray icon created")
            
        except Exception as e:
            agent_logger.log_error("TRAY_SETUP", str(e))
    
    def _on_command_enter(self, event):
        """Handle Enter key in command entry"""
        self._execute_command()
    
    def _execute_command(self):
        """Execute the entered command"""
        command = self.command_var.get().strip()
        if not command:
            return
        
        self.command_var.set("")  # Clear input
        self._append_output(f"\n> {command}")
        self.status_var.set("Processing...")
        self.execute_btn.config(state=tk.DISABLED)
        
        # Execute in separate thread to prevent GUI freezing
        thread = threading.Thread(target=self._execute_command_thread, args=(command,))
        thread.daemon = True
        thread.start()
    
    def _execute_command_thread(self, command: str):
        """Execute command in separate thread"""
        try:
            # Step 1: Interpret command
            success, message, action_data = command_interpreter.process_command(command)
            
            if not success:
                self.root.after(0, lambda: self._append_output(f"❌ {message}"))
                self.root.after(0, lambda: self.status_var.set("Error"))
                return
            
            # Step 2: Execute action if interpretation was successful
            if action_data:
                exec_success, exec_message = action_executor.execute_action(action_data)
                
                if exec_success:
                    self.root.after(0, lambda: self._append_output(f"✅ {exec_message}"))
                    self.root.after(0, lambda: self.status_var.set("Success"))
                else:
                    self.root.after(0, lambda: self._append_output(f"❌ Execution failed: {exec_message}"))
                    self.root.after(0, lambda: self.status_var.set("Execution Error"))
            else:
                self.root.after(0, lambda: self._append_output(f"✅ {message}"))
                self.root.after(0, lambda: self.status_var.set("Ready"))
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            agent_logger.log_error("COMMAND_EXECUTION", str(e), {"command": command})
            self.root.after(0, lambda: self._append_output(f"❌ {error_msg}"))
            self.root.after(0, lambda: self.status_var.set("Error"))
        
        finally:
            self.root.after(0, lambda: self.execute_btn.config(state=tk.NORMAL))
    
    def _append_output(self, text: str):
        """Append text to output area"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def _show_quick_input(self):
        """Show quick input dialog"""
        self._show_window()  # Bring main window to front
        self.command_entry.focus_set()
    
    def _show_window(self):
        """Show and raise the main window"""
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)
    
    def _show_suggestions(self):
        """Show command suggestions"""
        suggestions = command_interpreter.suggest_commands()
        
        # Create suggestions window
        suggestions_window = tk.Toplevel(self.root)
        suggestions_window.title("Command Suggestions")
        suggestions_window.geometry("400x300")
        
        ttk.Label(suggestions_window, text="Suggested Commands:", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # List of suggestions
        for i, suggestion in enumerate(suggestions, 1):
            frame = ttk.Frame(suggestions_window)
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            ttk.Label(frame, text=f"{i}. {suggestion}").pack(side=tk.LEFT)
            ttk.Button(frame, text="Use", 
                      command=lambda s=suggestion: self._use_suggestion(s, suggestions_window)).pack(side=tk.RIGHT)
    
    def _use_suggestion(self, suggestion: str, window: tk.Toplevel):
        """Use a suggested command"""
        self.command_var.set(suggestion)
        window.destroy()
        self._show_window()
        self.command_entry.focus_set()
    
    def _show_history(self):
        """Show command history"""
        history = command_interpreter.get_conversation_history()
        
        # Create history window
        history_window = tk.Toplevel(self.root)
        history_window.title("Command History")
        history_window.geometry("500x400")
        
        text_area = scrolledtext.ScrolledText(history_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, history)
        text_area.config(state=tk.DISABLED)
    
    def _clear_logs(self):
        """Clear the output area"""
        if messagebox.askyesno("Clear Logs", "Are you sure you want to clear the output?"):
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.config(state=tk.DISABLED)
            self._append_output("Logs cleared.")
    
    def _show_settings(self):
        """Show settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        
        ttk.Label(settings_window, text="Application Agent Settings", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Configuration display
        config_frame = ttk.LabelFrame(settings_window, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(config_frame, text=f"API Model: {config.GPT_MODEL}").pack(anchor=tk.W)
        ttk.Label(config_frame, text=f"Safety Mode: {'Enabled' if config.SAFETY_MODE else 'Disabled'}").pack(anchor=tk.W)
        ttk.Label(config_frame, text=f"Confirmation Required: {'Yes' if config.CONFIRMATION_REQUIRED else 'No'}").pack(anchor=tk.W)
        ttk.Label(config_frame, text=f"Hotkey: {config.ACTIVATION_HOTKEY}").pack(anchor=tk.W)
        
        # Actions
        action_frame = ttk.LabelFrame(settings_window, text="Actions", padding=10)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(action_frame, text="View Recent Logs", 
                  command=self._view_recent_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Export Session", 
                  command=self._export_session).pack(side=tk.LEFT, padx=(0, 5))
    
    def _view_recent_logs(self):
        """View recent log entries"""
        logs = agent_logger.get_recent_logs()
        
        log_window = tk.Toplevel(self.root)
        log_window.title("Recent Logs")
        log_window.geometry("600x400")
        
        text_area = scrolledtext.ScrolledText(log_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, logs)
        text_area.config(state=tk.DISABLED)
    
    def _export_session(self):
        """Export current session logs"""
        session_logs = agent_logger.export_session_log(self.session_start)
        
        if session_logs:
            # Save to file
            filename = f"session_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            try:
                with open(filename, 'w') as f:
                    f.write(session_logs)
                messagebox.showinfo("Export Complete", f"Session logs exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export logs: {str(e)}")
        else:
            messagebox.showinfo("No Data", "No session data to export")
    
    def _quit_application(self):
        """Quit the application"""
        self.cleanup()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
    
    def cleanup(self):
        """Cleanup resources"""
        self.is_running = False
        action_executor.cleanup()
        agent_logger.logger.info("Application Agent shut down")
    
    def run(self):
        """Run the application"""
        try:
            # Check configuration
            if not config.validate_config():
                messagebox.showerror("Configuration Error", 
                                   "No API key configured!\n\nPlease set OPENROUTER_API_KEY or OPENAI_API_KEY in your .env file.")
            
            # Hide window on startup if tray is available
            if TRAY_AVAILABLE:
                self.root.withdraw()
            
            # Set up window close handler
            self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
            
            agent_logger.logger.info("Application Agent GUI started")
            self.root.mainloop()
            
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            agent_logger.log_error("GUI_MAIN", str(e))
            messagebox.showerror("Fatal Error", f"Application error: {str(e)}")
    
    def _on_window_close(self):
        """Handle window close event"""
        if TRAY_AVAILABLE:
            self.root.withdraw()  # Hide to tray instead of closing
        else:
            self._quit_application()

def main():
    """Main entry point"""
    try:
        # Change to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # Check if running in headless environment
        if '--headless' in sys.argv or '--cli' in sys.argv:
            print("Starting Application Agent in CLI mode...")
            from cli import run_cli
            run_cli()
        else:
            # Run GUI
            app = ApplicationAgentGUI()
            app.run()
            
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()