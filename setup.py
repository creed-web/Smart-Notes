#!/usr/bin/env python3
"""
Smart Notes System Setup Script
Helps users set up the complete Smart Notes system
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("🚀 Smart Notes System Setup")
    print("="*40)
    print("Setting up your AI-powered web page summarization system...")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        print("Please install Python 3.8 or higher from https://python.org")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def setup_virtual_environment():
    """Set up Python virtual environment"""
    print("🔍 Setting up virtual environment...")
    
    backend_path = Path("backend")
    venv_path = backend_path / "venv"
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        # Create virtual environment
        result = subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], check=True, capture_output=True, text=True)
        
        print("✅ Virtual environment created")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_pip_executable():
    """Get the correct pip executable for the virtual environment"""
    backend_path = Path("backend")
    venv_path = backend_path / "venv"
    
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        return venv_path / "bin" / "pip"

def install_dependencies():
    """Install Python dependencies"""
    print("🔍 Installing Python dependencies...")
    
    backend_path = Path("backend")
    requirements_file = backend_path / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    pip_exe = get_pip_executable()
    
    try:
        # Install dependencies
        result = subprocess.run([
            str(pip_exe), "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Error output:", e.stderr)
        return False

def setup_environment_file():
    """Set up environment configuration file"""
    print("🔍 Setting up environment configuration...")
    
    backend_path = Path("backend")
    env_example = backend_path / ".env.example"
    env_file = backend_path / ".env"
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ .env.example not found")
        return False
    
    try:
        # Copy .env.example to .env
        shutil.copy2(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Remember to add your Hugging Face API token to backend/.env")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def test_installation():
    """Test if the installation was successful"""
    print("🔍 Testing installation...")
    
    try:
        # Run the system test script
        result = subprocess.run([
            sys.executable, "test_system.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Installation test passed")
            return True
        else:
            print("⚠️  Installation test had some issues:")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"⚠️  Could not run installation test: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*50)
    print("🎉 SETUP COMPLETE!")
    print("="*50)
    print()
    print("Next steps:")
    print("1. Get a Hugging Face API token:")
    print("   - Visit: https://huggingface.co/settings/tokens")
    print("   - Create a token with 'Read' permissions")
    print("   - Add it to backend/.env file")
    print()
    print("2. Start the backend server:")
    print("   cd backend")
    print("   python start.py")
    print()
    print("3. Install the Chrome extension:")
    print("   - Open Chrome and go to chrome://extensions/")
    print("   - Enable 'Developer mode'")
    print("   - Click 'Load unpacked'")
    print("   - Select the 'extension' folder")
    print()
    print("4. Test the system:")
    print("   - Visit any web page with content")
    print("   - Click the Smart Notes extension icon")
    print("   - Click 'Make Smart Notes'")
    print()
    print("For troubleshooting, see README.md")

def main():
    """Main setup function"""
    print_banner()
    
    # Check requirements
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Virtual Environment", setup_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Environment Config", setup_environment_file),
        ("Installation Test", test_installation)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ Unexpected error in {step_name}: {e}")
            failed_steps.append(step_name)
    
    # Summary
    if failed_steps:
        print(f"\n⚠️  Setup completed with issues in: {', '.join(failed_steps)}")
        print("Please check the error messages above and fix any issues.")
    else:
        print("\n✅ Setup completed successfully!")
    
    print_next_steps()

if __name__ == "__main__":
    main()
