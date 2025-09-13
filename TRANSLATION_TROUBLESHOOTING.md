# 🔧 Smart Notes Translation Troubleshooting Guide

## Common Issues and Solutions

### 1. "Translation failed: Failed to fetch" Error

**Cause**: This error typically occurs when:
- The backend server is not running
- Network connection issues
- CORS configuration problems

**Solutions**:
1. **Check if backend server is running**:
   ```bash
   # Navigate to backend directory
   cd backend
   python app.py
   ```
   
2. **Verify server is accessible**:
   ```bash
   # Test health endpoint
   curl http://localhost:5000/health
   # Or in PowerShell:
   Invoke-WebRequest -Uri http://localhost:5000/health -UseBasicParsing
   ```

3. **Check firewall/antivirus**: Make sure localhost:5000 is not blocked

### 2. "Translation service not configured" Error

**Cause**: Missing HuggingFace API token

**Solution**:
1. **Get a HuggingFace API token**:
   - Go to https://huggingface.co/settings/tokens
   - Create a new token (Read access is sufficient)
   - Copy the token

2. **Set the environment variable**:
   ```bash
   # Windows PowerShell
   $env:HUGGINGFACE_API_TOKEN='your_token_here'
   
   # Windows CMD
   set HUGGINGFACE_API_TOKEN=your_token_here
   
   # Linux/Mac
   export HUGGINGFACE_API_TOKEN='your_token_here'
   ```

3. **Restart the backend server** after setting the token

### 3. Translation Taking Too Long or Timing Out

**Cause**: 
- HuggingFace models need to "warm up" (first request can take 20+ seconds)
- Large content being translated
- Network latency

**Solutions**:
1. **Wait for model initialization**: First translation can take 20-60 seconds
2. **Try with smaller content**: Test with a shorter webpage first
3. **Check network connection**: Ensure stable internet connection
4. **Use setup script**: Run `python setup_translation.py` to test

### 4. Translation Returns Original Text Unchanged

**Cause**:
- Translation model failed but didn't throw an error
- Language not properly detected
- Content too technical or domain-specific

**Solutions**:
1. **Try a different target language**: Some models work better than others
2. **Check content**: Very technical content may not translate well
3. **Check logs**: Look at the backend console for detailed error messages

### 5. "Model is loading" Messages

**Cause**: HuggingFace inference API initializes models on first use

**Solutions**:
1. **Wait patiently**: First request can take 20-60 seconds
2. **Don't retry immediately**: Let the model finish loading
3. **Subsequent requests will be faster**: Models stay loaded for a while

## Testing and Validation

### Quick Test Script
Run the setup script to validate your configuration:
```bash
python setup_translation.py
```

### Manual Testing Steps
1. **Test backend server**:
   ```bash
   curl http://localhost:5000/health
   ```

2. **Test translation endpoint**:
   ```bash
   curl -X POST http://localhost:5000/translate \
     -H "Content-Type: application/json" \
     -d '{
       "content": "Hello, world!",
       "target_language": "spanish"
     }'
   ```

3. **Test in extension**:
   - Open Chrome extension
   - Navigate to any webpage
   - Click translate button
   - Select target language

## Debug Mode

### Enable Detailed Logging
The backend runs in debug mode by default and logs to both console and `smart_notes.log` file.

### Check Browser Console
1. Open Chrome Developer Tools (F12)
2. Go to Console tab
3. Look for error messages from the extension

### Common Log Messages
- `Translation attempt 1/3`: Normal retry mechanism
- `Model {model_name} is loading`: Model initialization in progress
- `Translation successful on attempt X`: Success after retries
- `HuggingFace API error`: API-level error from HuggingFace

## Supported Languages

The following languages are currently supported:
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

## Performance Tips

1. **First translation is slowest**: Models need to warm up
2. **Shorter content translates faster**: Large pages take more time
3. **Popular languages work better**: English to Spanish/French/German typically fastest
4. **Refresh if stuck**: Sometimes refreshing the page and trying again helps

## Getting Help

If you continue to have issues:

1. **Check the logs**: Look at both browser console and backend logs
2. **Run setup script**: `python setup_translation.py`
3. **Restart everything**: Backend server, browser, extension
4. **Test with simple content**: Try translating a simple webpage first

## Architecture Overview

```
Chrome Extension → Backend Server → HuggingFace API → Translation Models
     (popup.js)      (app.py)      (Helsinki-NLP models)
```

The translation system uses:
- **Frontend**: Chrome extension (JavaScript)
- **Backend**: Flask server (Python)
- **API**: HuggingFace Inference API
- **Models**: Helsinki-NLP OPUS-MT translation models

## Environment Variables

Required:
- `HUGGINGFACE_API_TOKEN`: Your HuggingFace API token

Optional:
- `FLASK_DEBUG`: Set to 1 for debug mode (default)
- `FLASK_HOST`: Server host (default: 0.0.0.0)
- `FLASK_PORT`: Server port (default: 5000)
