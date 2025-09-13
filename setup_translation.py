#!/usr/bin/env python3
"""
Setup script for Smart Notes Translation Feature
This script helps configure the HuggingFace API token and tests the translation functionality
"""

import os
import sys
import json
import requests
import time

def check_api_token():
    """Check if HuggingFace API token is set"""
    token = os.getenv('HUGGINGFACE_API_TOKEN')
    if not token:
        print("❌ HUGGINGFACE_API_TOKEN is not set")
        return False
    print("✅ HUGGINGFACE_API_TOKEN is configured")
    return True

def test_huggingface_api(token):
    """Test the HuggingFace API with a simple request"""
    print("\n🔍 Testing HuggingFace API connection...")
    
    # Test with a simple translation model
    test_url = "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-en-es"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": "Hello, world!"}
    
    try:
        response = requests.post(test_url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ HuggingFace API is accessible")
            return True
        else:
            print(f"❌ HuggingFace API test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Failed to connect to HuggingFace API: {e}")
        return False

def test_backend_server():
    """Test if the backend server is running"""
    print("\n🔍 Testing backend server...")
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            data = response.json()
            print(f"   Version: {data.get('version', 'Unknown')}")
            print(f"   Model: {data.get('model', 'Unknown')}")
            return True
        else:
            print(f"❌ Backend server returned status: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Backend server is not accessible: {e}")
        print("   Make sure to run: python backend/app.py")
        return False

def test_translation_endpoint():
    """Test the translation endpoint"""
    print("\n🔍 Testing translation endpoint...")
    
    test_data = {
        "content": "Hello, this is a test message.",
        "target_language": "spanish",
        "pageInfo": {
            "url": "test://example.com",
            "title": "Test Page"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/translate", 
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Translation endpoint is working")
                print(f"   Original: {test_data['content']}")
                print(f"   Translated: {result.get('translated_content', 'N/A')}")
                return True
            else:
                print(f"❌ Translation failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Translation endpoint returned status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Failed to test translation endpoint: {e}")
        return False

def setup_environment():
    """Guide user through environment setup"""
    print("\n🔧 Environment Setup")
    print("=" * 50)
    
    if not check_api_token():
        print("\nTo set up your HuggingFace API token:")
        print("1. Go to https://huggingface.co/settings/tokens")
        print("2. Create a new token (Read access is sufficient)")
        print("3. Set the environment variable:")
        print("   Windows (PowerShell): $env:HUGGINGFACE_API_TOKEN='your_token_here'")
        print("   Windows (CMD): set HUGGINGFACE_API_TOKEN=your_token_here")
        print("   Linux/Mac: export HUGGINGFACE_API_TOKEN='your_token_here'")
        print("\n4. Restart this script after setting the token")
        return False
    
    return True

def main():
    """Main setup and test function"""
    print("🌐 Smart Notes Translation Setup & Test")
    print("=" * 50)
    
    # Check environment setup
    if not setup_environment():
        sys.exit(1)
    
    # Test HuggingFace API
    token = os.getenv('HUGGINGFACE_API_TOKEN')
    if not test_huggingface_api(token):
        print("\n❌ HuggingFace API test failed. Please check your token.")
        sys.exit(1)
    
    # Test backend server
    if not test_backend_server():
        print("\n❌ Backend server test failed.")
        print("Make sure to start the server with: python backend/app.py")
        sys.exit(1)
    
    # Test translation endpoint
    if not test_translation_endpoint():
        print("\n❌ Translation endpoint test failed.")
        sys.exit(1)
    
    print("\n🎉 All tests passed! Translation system is ready.")
    print("\nYou can now:")
    print("1. Load the Chrome extension")
    print("2. Navigate to any webpage")
    print("3. Click the extension icon")
    print("4. Use the '🌐 Translate' button")
    print("\nSupported languages: Spanish, French, German, Italian, Portuguese,")
    print("Chinese, Japanese, Korean, Arabic, Russian, Hindi, Dutch")

if __name__ == "__main__":
    main()
