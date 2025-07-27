#!/usr/bin/env python3
"""
Setup script for Application Agent
Installs dependencies and validates the installation
"""

import sys
import subprocess
import os
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("✅ Dependencies installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def validate_installation():
    """Validate that all modules can be imported"""
    print("🔍 Validating installation...")
    
    modules = [
        'dotenv', 'openai', 'pyautogui', 'keyboard', 
        'psutil', 'pygetwindow', 'requests', 'pillow', 
        'pystray', 'plyer'
    ]
    
    failed_modules = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
            failed_modules.append(module)
    
    if failed_modules:
        print(f"\n❌ Failed to import: {', '.join(failed_modules)}")
        return False
    
    print("\n✅ All dependencies validated!")
    return True

def validate_agent_modules():
    """Validate that agent modules can be imported"""
    print("🔍 Validating agent modules...")
    
    agent_modules = [
        'config', 'logger', 'safety', 'gpt_interface',
        'interpreter', 'actions', 'main', 'cli'
    ]
    
    failed_modules = []
    
    for module in agent_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_modules.append(module)
    
    if failed_modules:
        print(f"\n❌ Failed to import agent modules: {', '.join(failed_modules)}")
        return False
    
    print("\n✅ All agent modules validated!")
    return True

def setup_environment():
    """Setup environment files"""
    print("⚙️ Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("  📋 Copying .env.example to .env")
        env_file.write_text(env_example.read_text())
        print("  ✅ .env file created")
        print("  ⚠️  Please edit .env file with your API keys")
    elif env_file.exists():
        print("  ✅ .env file already exists")
    else:
        print("  ❌ No .env.example file found")
        return False
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print("  ✅ logs directory created")
    
    return True

def main():
    """Main setup function"""
    print("🚀 Application Agent Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Validate installation
    if not validate_installation():
        print("❌ Installation validation failed")
        sys.exit(1)
    
    # Validate agent modules
    if not validate_agent_modules():
        print("❌ Agent module validation failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Run: python main.py (GUI mode)")
    print("3. Or run: python main.py --cli (CLI mode)")
    print("\nFor help, run: python main.py --help")

if __name__ == "__main__":
    main()