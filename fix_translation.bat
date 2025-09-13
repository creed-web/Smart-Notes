@echo off
echo =================================================
echo Smart Notes Translation Quick Fix
echo =================================================
echo.
echo This script will help you set up the translation feature.
echo.
echo Step 1: Check if HuggingFace API token is set...
if "%HUGGINGFACE_API_TOKEN%"=="" (
    echo ❌ HUGGINGFACE_API_TOKEN is not set!
    echo.
    echo Please follow these steps:
    echo 1. Go to https://huggingface.co/settings/tokens
    echo 2. Create a new token (Read access is sufficient)
    echo 3. Copy the token
    echo 4. Run this command in PowerShell:
    echo    $env:HUGGINGFACE_API_TOKEN='your_token_here'
    echo.
    echo Then restart the backend server and try again.
    pause
    exit /b 1
) else (
    echo ✅ HUGGINGFACE_API_TOKEN is configured
)

echo.
echo Step 2: Testing backend server...
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend server is not running!
    echo.
    echo Starting the backend server...
    echo Please keep this window open and run the translation in your browser.
    echo.
    cd backend
    python app.py
) else (
    echo ✅ Backend server is running
)

echo.
echo Step 3: Test translation...
echo You can now use the translation feature in the Chrome extension!
echo.
pause
