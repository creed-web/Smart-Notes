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

def check_api_tokens():
    """Check which API tokens are configured"""
    gemini_key = os.getenv('GEMINI_API_KEY')
    hf_token = os.getenv('HUGGINGFACE_API_TOKEN')
    
    available_services = []
    
    if gemini_key:
        print("✅ GEMINI_API_KEY is configured")
        available_services.append('gemini')
    else:
        print("❌ GEMINI_API_KEY is not set")
    
    if hf_token:
        print("✅ HUGGINGFACE_API_TOKEN is configured")
        available_services.append('huggingface')
    else:
        print("❌ HUGGINGFACE_API_TOKEN is not set")
    
    return available_services

def test_gemini_api():
    """Test the Gemini API with direct HTTP request"""
    print("\n🔍 Testing Gemini API connection...")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Gemini API key not configured")
        return False
    
    try:
        import json
        
        # Gemini API endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        # Test translation request
        payload = {
            "contents": [{
                "parts": [{
                    "text": "Translate 'Hello, world!' to Spanish. Provide only the translation."
                }]
            }]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                translated_text = result['candidates'][0]['content']['parts'][0]['text']
                print("✅ Gemini API is accessible")
                print(f"   Test response: {translated_text.strip()[:50]}...")
                return True
            else:
                print("❌ Gemini API returned unexpected format")
                return False
        else:
            print(f"❌ Gemini API test failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Failed to connect to Gemini API: {e}")
        return False
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

def test_huggingface_api():
    """Test the HuggingFace API with a simple request"""
    print("\n🔍 Testing HuggingFace API connection...")
    
    token = os.getenv('HUGGINGFACE_API_TOKEN')
    if not token:
        print("❌ HuggingFace API token not configured")
        return False
    
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
    
    available_services = check_api_tokens()
    
    if not available_services:
        print("\n❌ No translation API keys configured!")
        print("\nChoose one of these options:")
        print("\n✅ Option 1: Gemini API (Recommended - More reliable)")
        print("1. Go to https://makersuite.google.com/app/apikey")
        print("2. Create a new API key")
        print("3. Set the environment variable:")
        print("   Windows (PowerShell): $env:GEMINI_API_KEY='your_gemini_key_here'")
        print("   Windows (CMD): set GEMINI_API_KEY=your_gemini_key_here")
        print("   Linux/Mac: export GEMINI_API_KEY='your_gemini_key_here'")
        print("4. Install required library: pip install google-generativeai")
        
        print("\n✅ Option 2: HuggingFace API")
        print("1. Go to https://huggingface.co/settings/tokens")
        print("2. Create a new token (Read access is sufficient)")
        print("3. Set the environment variable:")
        print("   Windows (PowerShell): $env:HUGGINGFACE_API_TOKEN='your_token_here'")
        print("   Windows (CMD): set HUGGINGFACE_API_TOKEN=your_token_here")
        print("   Linux/Mac: export HUGGINGFACE_API_TOKEN='your_token_here'")
        
        print("\n5. Restart this script after setting a token")
        return False
    
    print(f"\n✅ Available services: {', '.join(available_services)}")
    return True

def main():
    """Main setup and test function"""
    print("🌐 Smart Notes Translation Setup & Test")
    print("=" * 50)
    
    # Check environment setup
    if not setup_environment():
        sys.exit(1)
    
    # Test available APIs
    api_tests_passed = []
    
    if os.getenv('GEMINI_API_KEY'):
        if test_gemini_api():
            api_tests_passed.append('gemini')
        else:
            print("\n⚠️ Gemini API test failed, but continuing...")
    
    if os.getenv('HUGGINGFACE_API_TOKEN'):
        if test_huggingface_api():
            api_tests_passed.append('huggingface')
        else:
            print("\n⚠️ HuggingFace API test failed, but continuing...")
    
    if not api_tests_passed:
        print("\n❌ All API tests failed. Please check your configuration.")
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
    
    print(f"\n🎉 Translation system is ready with {len(api_tests_passed)} service(s): {', '.join(api_tests_passed)}")
    print("\nYou can now:")
    print("1. Load the Chrome extension")
    print("2. Navigate to any webpage")
    print("3. Click the extension icon")
    print("4. Use the '🌐 Translate' button")
    print("\n📝 Note: The system will automatically try the best available service")
    if 'gemini' in api_tests_passed:
        print("  • Gemini API will be tried first (more reliable)")
    if 'huggingface' in api_tests_passed:
        print("  • HuggingFace API available as backup")
    print("\nSupported languages: Spanish, French, German, Italian, Portuguese,")
    print("Chinese, Japanese, Korean, Arabic, Russian, Hindi, Dutch")

if __name__ == "__main__":
    main()
