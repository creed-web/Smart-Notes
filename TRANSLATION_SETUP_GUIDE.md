# 🌐 Smart Notes Translation Setup Guide

The Smart Notes system now supports **two translation services** with automatic fallback:

1. **Gemini API** (Recommended) - More reliable and faster
2. **HuggingFace API** - Backup service using specialized translation models

## 🚀 Quick Setup (Recommended: Gemini API)

### Step 1: Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

### Step 2: Set Environment Variable
```powershell
# Windows PowerShell
$env:GEMINI_API_KEY='your_gemini_api_key_here'

# Windows CMD
set GEMINI_API_KEY=your_gemini_api_key_here

# Linux/Mac
export GEMINI_API_KEY='your_gemini_api_key_here'
```

### Step 3: Test the Setup
```bash
python test_gemini.py
```

### Step 4: Start the Backend Server
```bash
cd backend
python app.py
```

You should see:
```
✅ Available translation services: gemini
```

## 🔄 Alternative Setup (HuggingFace API)

### Step 1: Get HuggingFace Token
1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Create a new token (Read access is sufficient)
3. Copy the token

### Step 2: Set Environment Variable
```powershell
# Windows PowerShell
$env:HUGGINGFACE_API_TOKEN='your_hf_token_here'
```

## 🎯 Both Services (Maximum Reliability)

For maximum reliability, set up both API keys:
```powershell
$env:GEMINI_API_KEY='your_gemini_key_here'
$env:HUGGINGFACE_API_TOKEN='your_hf_token_here'
```

The system will automatically:
1. Try Gemini first (faster, more reliable)
2. Fall back to HuggingFace if Gemini fails
3. Retry with exponential backoff

## 🧪 Testing Your Setup

Run the comprehensive test:
```bash
python setup_translation.py
```

This will:
- ✅ Check which API keys are configured
- ✅ Test API connectivity
- ✅ Verify backend server is running
- ✅ Test translation endpoint
- ✅ Confirm extension compatibility

## 🎮 Using the Translation Feature

1. **Load Chrome Extension**: Install the Smart Notes extension
2. **Navigate to Any Webpage**: Go to any website you want to translate
3. **Open Extension**: Click the Smart Notes icon
4. **Click Translate**: Click the "🌐 Translate" button
5. **Select Language**: Choose your target language
6. **Start Translation**: Click "Start Translation"

## 🌍 Supported Languages

- Spanish (Español)
- French (Français) 
- German (Deutsch)
- Italian (Italiano)
- Portuguese (Português)
- Dutch (Nederlands)
- Chinese Simplified (中文)
- Japanese (日本語)
- Korean (한국어)
- Arabic (العربية)
- Russian (Русский)
- Hindi (हिन्दी)

## ⚡ Performance Comparison

| Service | Speed | Reliability | Setup Difficulty | Cost |
|---------|-------|-------------|------------------|------|
| **Gemini API** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Free tier |
| **HuggingFace** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Free tier |

## 🔧 Troubleshooting

### Common Issues

1. **"No translation services configured"**
   - Solution: Set at least one API key (see setup above)

2. **"Failed to fetch"**  
   - Solution: Make sure backend server is running (`python backend/app.py`)

3. **Translation takes too long**
   - Gemini: Usually fast (2-5 seconds)
   - HuggingFace: First request can take 20-60 seconds (model loading)

4. **"API key invalid"**
   - Gemini: Check key at https://makersuite.google.com/app/apikey
   - HuggingFace: Check token at https://huggingface.co/settings/tokens

### Debug Commands

```bash
# Test specific service
python test_gemini.py

# Full system test
python setup_translation.py

# Check backend logs
cd backend && python app.py
# Look for service availability messages

# Test translation endpoint directly
curl -X POST http://localhost:5000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello world",
    "target_language": "spanish"
  }'
```

## 📈 Advanced Configuration

### Multiple Service Priority
The system automatically tries services in this order:
1. Gemini API (if configured)
2. HuggingFace API (if configured)

### Retry Logic
- 3 attempts per service
- Exponential backoff (2s, 4s, 6s)
- Automatic service switching on failure

### Large Content Handling
- Content is automatically chunked for optimal processing
- Smart recombination preserves context
- Maximum efficiency for both services

## 🚨 Important Notes

1. **API Keys Security**: Never commit API keys to version control
2. **Rate Limits**: Both services have free tier limits
3. **Content Length**: Very large pages may take longer to translate
4. **Language Detection**: System assumes English source text by default

## ✅ Success Indicators

When everything is working, you should see:

```
🌐 Smart Notes Translation Services
==================================================
✅ Available translation services: gemini, huggingface
```

And in the browser extension:
- Translation completes in 2-10 seconds
- Page content is accurately translated
- Original formatting is preserved
- No error messages appear

## 🎉 You're Ready!

Once setup is complete, you can translate any webpage instantly with high-quality results using Google's Gemini AI or HuggingFace's specialized translation models.

Need help? Check the logs in the backend console or browser developer tools (F12) for detailed error information.
