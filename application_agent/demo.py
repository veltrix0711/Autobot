#!/usr/bin/env python3
"""
Demo script for Application Agent
Shows functionality without requiring API keys
"""

import sys
import os
from datetime import datetime

def demo_config():
    """Demo configuration module"""
    print("🔧 Configuration Demo")
    print("-" * 30)
    
    try:
        from config import config
        print(f"✅ Configuration loaded")
        print(f"   Safety Mode: {config.SAFETY_MODE}")
        print(f"   Confirmation Required: {config.CONFIRMATION_REQUIRED}")
        print(f"   Log Level: {config.LOG_LEVEL}")
        print(f"   Whitelisted Apps: {len(config.WHITELISTED_APPLICATIONS)} apps")
        print(f"   Dangerous Keywords: {len(config.DANGEROUS_KEYWORDS)} patterns")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def demo_logger():
    """Demo logging functionality"""
    print("\n📝 Logging Demo")
    print("-" * 30)
    
    try:
        from logger import agent_logger
        
        # Test different log types
        agent_logger.log_command("demo command", {"action": "demo", "reasoning": "testing"})
        agent_logger.log_action("DEMO", {"test": "value"}, True)
        agent_logger.log_safety_check("DEMO_CHECK", True, "Demo safety check")
        agent_logger.log_file_operation("READ", "demo.txt", True)
        
        print("✅ Logging system working")
        print(f"   Log file: {agent_logger.log_file}")
        return True
    except Exception as e:
        print(f"❌ Logger error: {e}")
        return False

def demo_safety():
    """Demo safety checks"""
    print("\n🛡️  Safety Demo")
    print("-" * 30)
    
    try:
        from safety import safety_checker
        
        # Test safe action
        safe_action = {"action": "click", "x": 100, "y": 200}
        is_safe, reason = safety_checker.validate_action(safe_action)
        print(f"✅ Safe action validation: {is_safe} - {reason}")
        
        # Test dangerous action
        dangerous_action = {"action": "type", "text": "rm -rf /"}
        is_safe, reason = safety_checker.validate_action(dangerous_action)
        print(f"🚫 Dangerous action blocked: {not is_safe} - {reason}")
        
        # Test confirmation requirement
        requires_conf = safety_checker.requires_confirmation({"action": "file_write", "file_path": "test.txt"})
        print(f"⚠️  Confirmation required: {requires_conf}")
        
        return True
    except Exception as e:
        print(f"❌ Safety error: {e}")
        return False

def demo_interpreter():
    """Demo command interpretation (without GPT)"""
    print("\n🧠 Interpreter Demo")
    print("-" * 30)
    
    try:
        from interpreter import command_interpreter
        
        # Test action format validation
        valid_action = {"action": "click", "x": 100, "y": 200, "reasoning": "test click"}
        is_valid, reason = command_interpreter.validate_action_format(valid_action)
        print(f"✅ Valid action format: {is_valid} - {reason}")
        
        # Test invalid action
        invalid_action = {"action": "click", "reasoning": "missing coordinates"}
        is_valid, reason = command_interpreter.validate_action_format(invalid_action)
        print(f"❌ Invalid action format: {not is_valid} - {reason}")
        
        # Show suggestions
        suggestions = command_interpreter.suggest_commands()
        print(f"💡 Available suggestions: {len(suggestions)} commands")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"   {i}. {suggestion}")
        
        return True
    except Exception as e:
        print(f"❌ Interpreter error: {e}")
        return False

def demo_actions():
    """Demo action execution (safe actions only)"""
    print("\n⚡ Actions Demo")
    print("-" * 30)
    
    try:
        from actions import action_executor
        
        # Test wait action (safe)
        wait_action = {"action": "wait", "seconds": 0.1}
        success, message = action_executor.execute_action(wait_action)
        print(f"✅ Wait action: {success} - {message}")
        
        # Test screen info
        screen_info = action_executor.get_screen_info()
        if screen_info:
            print(f"🖥️  Screen info available: {len(screen_info)} properties")
        else:
            print("ℹ️  Screen info not available (display needed)")
        
        return True
    except Exception as e:
        print(f"❌ Actions error: {e}")
        return False

def demo_file_operations():
    """Demo safe file operations"""
    print("\n📁 File Operations Demo")
    print("-" * 30)
    
    try:
        from actions import action_executor
        
        # Test file write
        test_file = "demo_test.txt"
        write_action = {
            "action": "file_write",
            "file_path": test_file,
            "content": "This is a demo file created by Application Agent\nTimestamp: " + str(datetime.now())
        }
        
        success, message = action_executor.execute_action(write_action)
        print(f"✅ File write: {success} - {message}")
        
        if success:
            # Test file read
            read_action = {"action": "file_read", "file_path": test_file}
            success, message = action_executor.execute_action(read_action)
            print(f"✅ File read: {success}")
            if success:
                print(f"   Content preview: {message[:100]}...")
            
            # Cleanup
            try:
                os.remove(test_file)
                print("🧹 Demo file cleaned up")
            except:
                pass
        
        return True
    except Exception as e:
        print(f"❌ File operations error: {e}")
        return False

def main():
    """Run the complete demo"""
    print("🚀 Application Agent Demo")
    print("=" * 50)
    print("This demo shows all components working without requiring API keys")
    print()
    
    demos = [
        demo_config,
        demo_logger,
        demo_safety,
        demo_interpreter,
        demo_actions,
        demo_file_operations
    ]
    
    passed = 0
    failed = 0
    
    for demo in demos:
        try:
            if demo():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Demo Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All demos passed! The Application Agent is ready to use.")
        print("\nNext steps:")
        print("1. Add your API key to .env file")
        print("2. Run: python main.py")
        print("3. Try commands like 'Click at coordinates 100, 200'")
    else:
        print(f"\n⚠️  {failed} demos failed. Check the error messages above.")
        print("You may need to install dependencies: python setup.py")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)