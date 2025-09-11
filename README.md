# Smart Notes System

An AI-powered Chrome extension that automatically generates concise, meaningful notes from web page content using advanced text summarization.

## 🌟 Features

- **AI-Powered Summarization**: Uses Hugging Face's `google/flan-t5-small` model for high-quality text summarization
- **Intelligent Content Extraction**: Automatically identifies and extracts main content from web pages
- **Smart Text Processing**: Removes noise, navigation elements, and ads for cleaner summarization
- **Chunked Processing**: Handles long articles by processing them in manageable chunks
- **PDF Export**: Download your smart notes as professionally formatted PDFs
- **Browser Integration**: Seamless Chrome extension with intuitive popup interface
- **Notes History**: Automatically saves generated notes for future reference
- **Visual Indicators**: Shows availability status on compatible web pages

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js (for development, optional)
- Chrome browser
- Hugging Face account (for API access)

### 1. Get Your Hugging Face API Token

1. Visit [Hugging Face Settings](https://huggingface.co/settings/tokens)
2. Create a new token with "Read" permissions
3. Copy the token for later use

### 2. Backend Setup

```bash
# Navigate to backend directory
cd smart-notes-system/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env and add your Hugging Face API token
```

### 3. Chrome Extension Setup

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `smart-notes-system/extension` folder
5. The Smart Notes extension should now appear in your extensions list

### 4. Start the Backend Server

```bash
# From the backend directory
python app.py
```

The server will start on `http://localhost:5000`

### 5. Use the Extension

1. Navigate to any web page with substantial text content
2. Click the Smart Notes extension icon in your Chrome toolbar
3. Click "Make Smart Notes" to generate AI-powered notes
4. Copy notes to clipboard or download as PDF

## 🛠️ Architecture

### Chrome Extension (Frontend)
- **Manifest V3** compliance
- **Popup Interface**: Clean, modern UI for interaction
- **Content Script**: Intelligent content extraction from web pages
- **Background Script**: Manages extension state and communication

### Python Flask Backend
- **Flask Web Server**: Handles API requests
- **Text Preprocessing**: Cleans and normalizes web content
- **AI Integration**: Hugging Face API for text summarization
- **PDF Generation**: Creates formatted PDF documents
- **Error Handling**: Robust error handling with fallbacks

### Text Processing Pipeline

1. **Content Extraction**: Remove HTML, scripts, ads, navigation
2. **Text Cleaning**: Normalize whitespace, remove URLs, fix punctuation
3. **Content Chunking**: Split long texts into manageable pieces
4. **AI Summarization**: Process each chunk through the AI model
5. **Summary Combination**: Merge and refine chunk summaries
6. **Final Processing**: Clean and format the final notes

## 📁 Project Structure

```
smart-notes-system/
├── extension/                 # Chrome Extension
│   ├── manifest.json         # Extension configuration
│   ├── popup.html            # Main UI
│   ├── popup.css             # Styling
│   ├── popup.js              # Frontend logic
│   ├── content.js            # Content extraction
│   └── background.js         # Background tasks
├── backend/                  # Python Flask Backend
│   ├── app.py               # Main Flask application
│   ├── config.py            # Configuration settings
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variables template
└── README.md                # This file
```

## ⚙️ Configuration

### Backend Configuration (.env file)

```bash
# Required
HUGGINGFACE_API_TOKEN=your_token_here

# Optional customization
HUGGINGFACE_MODEL=google/flan-t5-small
MAX_CHUNK_SIZE=1000
MIN_SUMMARY_LENGTH=50
MAX_SUMMARY_LENGTH=300
REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
```

### Extension Configuration

The extension automatically detects the backend at `http://localhost:5000`. For production deployment, update the `backendUrl` in `popup.js`.

## 🔧 API Endpoints

### Health Check
```
GET /health
```
Returns backend status and configuration.

### Generate Notes
```
POST /generate-notes
Content-Type: application/json

{
  "content": "Web page text content...",
  "url": "https://example.com",
  "title": "Page Title"
}
```

### Download PDF
```
POST /download-pdf
Content-Type: application/json

{
  "notes": "Generated smart notes...",
  "pageInfo": {
    "url": "https://example.com",
    "title": "Page Title",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 🔍 Troubleshooting

### Common Issues

1. **Extension not working**: Ensure backend is running on port 5000
2. **API errors**: Check your Hugging Face token in .env file
3. **Content not extracted**: Some pages may have anti-bot measures
4. **PDF generation fails**: Check reportlab installation

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your .env file.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- [Hugging Face](https://huggingface.co/) for the AI models
- [Google FLAN-T5](https://huggingface.co/google/flan-t5-small) for text summarization
- [ReportLab](https://www.reportlab.com/) for PDF generation
- [NLTK](https://www.nltk.org/) for text processing

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review closed issues on GitHub
- Create a new issue with detailed information

---

Made with ❤️ for better web reading experience
