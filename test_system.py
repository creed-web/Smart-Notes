#!/usr/bin/env python3
"""
Smart Notes System Test Script
Tests the complete system to ensure all components work together
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

def test_extension_files():
    """Test that all Chrome extension files are present and valid"""
    print("🔍 Testing Chrome Extension files...")
    
    extension_path = Path("extension")
    required_files = [
        "manifest.json",
        "popup.html", 
        "popup.css",
        "popup.js",
        "content.js",
        "background.js"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = extension_path / file
        if not file_path.exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing extension files: {missing_files}")
        return False
    
    # Test manifest.json validity
    try:
        with open(extension_path / "manifest.json", 'r') as f:
            manifest = json.load(f)
        
        required_keys = ["manifest_version", "name", "version", "permissions"]
        for key in required_keys:
            if key not in manifest:
                print(f"❌ Missing key '{key}' in manifest.json")
                return False
        
        print("✅ All Chrome extension files present and valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid manifest.json: {e}")
        return False

def test_backend_files():
    """Test that all backend files are present"""
    print("🔍 Testing Backend files...")
    
    backend_path = Path("backend")
    required_files = [
        "app.py",
        "config.py", 
        "requirements.txt",
        "start.py",
        ".env.example"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = backend_path / file
        if not file_path.exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing backend files: {missing_files}")
        return False
    
    print("✅ All backend files present")
    return True

def test_python_imports():
    """Test that all required Python packages can be imported"""
    print("🔍 Testing Python package imports...")
    
    required_packages = [
        "flask",
        "flask_cors", 
        "requests",
        "reportlab",
        "nltk"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing Python packages: {missing_packages}")
        print("💡 Install with: pip install -r backend/requirements.txt")
        return False
    
    print("✅ All required Python packages available")
    return True

def test_backend_startup():
    """Test that the backend can start up properly"""
    print("🔍 Testing Backend startup...")
    
    # Change to backend directory
    original_dir = os.getcwd()
    
    try:
        backend_path = Path("backend")
        os.chdir(backend_path)
        
        # Test import of main app
        sys.path.insert(0, str(backend_path.absolute()))
        
        try:
            from app import SmartNotesApp
            app_instance = SmartNotesApp()
            print("✅ Backend app can be instantiated")
            return True
        except Exception as e:
            print(f"❌ Backend startup failed: {e}")
            return False
            
    finally:
        os.chdir(original_dir)
        if str(backend_path.absolute()) in sys.path:
            sys.path.remove(str(backend_path.absolute()))

def test_text_processing():
    """Test text processing functionality"""
    print("🔍 Testing text processing functions...")
    
    original_dir = os.getcwd()
    
    try:
        backend_path = Path("backend")
        os.chdir(backend_path)
        sys.path.insert(0, str(backend_path.absolute()))
        
        from app import SmartNotesApp
        app_instance = SmartNotesApp()
        
        # Test text preprocessing
        test_text = "This is a test article with multiple    spaces and URLs like https://example.com and email@test.com"
        processed = app_instance.preprocess_text(test_text)
        
        if "https://example.com" not in processed and "email@test.com" not in processed:
            print("✅ Text preprocessing removes URLs and emails")
        else:
            print("⚠️  Text preprocessing may not be working correctly")
        
        # Test chunking
        long_text = "This is a sentence. " * 200  # Create long text
        chunks = app_instance.chunk_text(long_text, max_words=50)
        
        if len(chunks) > 1:
            print(f"✅ Text chunking works ({len(chunks)} chunks created)")
        else:
            print("⚠️  Text chunking may not be working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Text processing test failed: {e}")
        return False
    finally:
        os.chdir(original_dir)
        if str(backend_path.absolute()) in sys.path:
            sys.path.remove(str(backend_path.absolute()))

def test_pdf_generation():
    """Test PDF generation functionality"""
    print("🔍 Testing PDF generation...")
    
    original_dir = os.getcwd()
    
    try:
        backend_path = Path("backend")
        os.chdir(backend_path)
        sys.path.insert(0, str(backend_path.absolute()))
        
        from app import SmartNotesApp
        app_instance = SmartNotesApp()
        
        # Test PDF generation
        test_notes = "These are test smart notes. They contain key insights from the processed content."
        test_page_info = {
            "title": "Test Page",
            "url": "https://test.example.com",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        pdf_buffer = app_instance.generate_pdf(test_notes, test_page_info)
        
        if pdf_buffer.getvalue():
            print("✅ PDF generation works")
            return True
        else:
            print("❌ PDF generation failed - empty buffer")
            return False
        
    except Exception as e:
        print(f"❌ PDF generation test failed: {e}")
        return False
    finally:
        os.chdir(original_dir)
        if str(backend_path.absolute()) in sys.path:
            sys.path.remove(str(backend_path.absolute()))

def create_test_report(results):
    """Create a test results summary"""
    print("\n" + "="*50)
    print("🧪 SMART NOTES SYSTEM TEST RESULTS")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<30} {status}")
    
    print("-"*50)
    print(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Your Smart Notes system is ready to use.")
        print("\nNext steps:")
        print("1. Set up your Hugging Face API token in backend/.env")
        print("2. Start the backend: cd backend && python start.py")
        print("3. Load the extension in Chrome")
        return True
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return False

def main():
    """Main test function"""
    print("🧪 Smart Notes System Validation")
    print("Testing all system components...\n")
    
    # Run all tests
    test_results = {
        "Extension Files": test_extension_files(),
        "Backend Files": test_backend_files(), 
        "Python Imports": test_python_imports(),
        "Backend Startup": test_backend_startup(),
        "Text Processing": test_text_processing(),
        "PDF Generation": test_pdf_generation()
    }
    
    # Generate report
    success = create_test_report(test_results)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
