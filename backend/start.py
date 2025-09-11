#!/usr/bin/env python3
"""
Smart Notes Backend Startup Script
Provides an easy way to start the backend with proper configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    # Check if .env file exists
    if not Path('.env').exists():
        print("⚠️  .env file not found")
        if Path('.env.example').exists():
            print("📝 Please copy .env.example to .env and configure your settings")
            return False
        else:
            print("❌ No .env.example file found")
            return False
    
    # Check if requirements are installed
    try:
        import flask
        import flask_cors
        import requests
        import reportlab
        import nltk
        print("✅ All required packages found")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    
    return True

def check_huggingface_token():
    """Check if Hugging Face token is configured"""
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('HUGGINGFACE_API_TOKEN')
    if not token or token == 'your_huggingface_token_here':
        print("⚠️  Hugging Face API token not configured!")
        print("📝 Please:")
        print("   1. Visit https://huggingface.co/settings/tokens")
        print("   2. Create a new token with 'Read' permissions")
        print("   3. Add it to your .env file as HUGGINGFACE_API_TOKEN")
        return False
    
    print("✅ Hugging Face API token configured")
    return True

def download_nltk_data():
    """Download required NLTK data"""
    print("📦 Downloading NLTK data...")
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        print("✅ NLTK data downloaded")
    except Exception as e:
        print(f"⚠️  NLTK data download failed: {e}")
        print("   The application will still work but may have reduced functionality")

def start_server():
    """Start the Flask server"""
    print("\n🚀 Starting Smart Notes backend server...")
    print("   Server will be available at: http://localhost:5000")
    print("   Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        from app import create_app
        app = create_app()
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

def main():
    """Main startup function"""
    print("🚀 Smart Notes Backend Startup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Check Hugging Face token
    if not check_huggingface_token():
        print("\n⚠️  Warning: API token not configured. Some features may not work.")
        response = input("Continue anyway? (y/N): ").lower().strip()
        if response != 'y':
            sys.exit(1)
    
    # Download NLTK data
    download_nltk_data()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
