#!/usr/bin/env python3
"""
Simple test script for Gemini API translation
This doesn't require the google-generativeai library and uses direct HTTP requests
"""

import os
import json
import requests

def test_gemini_direct():
    """Test Gemini API with direct HTTP requests"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY environment variable not set")
        print("\n1. Go to https://makersuite.google.com/app/apikey")
        print("2. Create a new API key")
        print("3. Set environment variable:")
        print("   PowerShell: $env:GEMINI_API_KEY='your_key_here'")
        return False
    
    print("🔍 Testing Gemini API with direct HTTP request...")
    
    # Gemini API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Test translation request
    payload = {
        "contents": [{
            "parts": [{
                "text": "Translate the following text to Spanish. Provide only the translation without any additional text or explanations.\n\nText to translate:\nHello, world! This is a test.\n\nTranslation:"
            }]
        }]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("  Making request to Gemini API...")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                translated_text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ Gemini API is working!")
                print(f"   Original: Hello, world! This is a test.")
                print(f"   Translation: {translated_text.strip()}")
                return True
            else:
                print("❌ Gemini API returned unexpected format")
                print(f"Response: {json.dumps(result, indent=2)}")
                return False
        else:
            print(f"❌ Gemini API request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Failed to connect to Gemini API: {e}")
        return False

if __name__ == "__main__":
    print("🌐 Gemini API Translation Test")
    print("=" * 40)
    test_gemini_direct()
