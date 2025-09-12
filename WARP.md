# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common Development Commands

### Backend Development
```bash
# Setup backend (one-time)
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
copy .env.example .env

# Start backend server
cd backend
python start.py
# Alternative: python app.py

# Test backend functionality
python ../test_system.py

# Production deployment
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Chrome Extension Development
```bash
# Load extension in Chrome
# 1. Navigate to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select the extension/ folder

# Test extension components
# Extension files are static - no build process required
```

### Full System Testing
```bash
# Automated system validation
python test_system.py

# Test enhanced features
python test_enhanced_features.py

# Test export system
python test_export_system.py

# Manual testing workflow:
# 1. Start backend: cd backend && python start.py
# 2. Load extension in Chrome
# 3. Visit any content-rich webpage
# 4. Click Smart Notes extension icon
# 5. Generate structured notes with enhanced formatting
```

## Architecture Overview

### Two-Component System
This is a **dual-component AI-powered web summarization system** consisting of:
1. **Flask Backend** (Python) - AI processing engine
2. **Chrome Extension** (JavaScript) - User interface and content extraction

### Backend Architecture (`backend/`)
- **`app.py`**: Core Flask application with `SmartNotesApp` class
  - `/health` - Backend status endpoint
  - `/generate-notes` - Main AI summarization endpoint  
  - `/download-pdf` - PDF generation endpoint
- **Text Processing Pipeline**:
  1. Content extraction and cleaning (`preprocess_text()`)
  2. Intelligent text chunking (`chunk_text()`) for large articles
  3. Hugging Face API integration (`query_huggingface_model()`)
  4. Summary consolidation for multi-chunk content
- **AI Model**: Uses `google/flan-t5-small` via Hugging Face Inference API
- **PDF Generation**: ReportLab integration for formatted note export

### Chrome Extension Architecture (`extension/`)
- **Manifest V3** compliance with required permissions
- **`popup.js`**: Main UI controller with `SmartNotesPopup` class
  - Communicates with backend via fetch API
  - Handles content extraction through content scripts
- **`content.js`**: Page content extraction with `SmartNotesContent` class
  - Intelligent content area detection (article, main, etc.)
  - Filters out ads, navigation, scripts
  - Adds visual indicator for extension availability
- **Communication Flow**: popup.js → content script injection → backend API → UI update

### Key Integration Points
- **Content Extraction**: Extension injects scripts to extract clean text from web pages
- **API Communication**: Extension communicates with backend on `http://localhost:5000`
- **Error Handling**: Both components have fallback mechanisms for content processing
- **Configuration**: Backend uses `.env` file; extension hardcoded to localhost

## Required Environment Setup

### Hugging Face API Token
The system requires a Hugging Face API token with read permissions:
```bash
# Add to backend/.env
HUGGINGFACE_API_TOKEN=your_token_here
```

### Python Dependencies
Key packages that drive functionality:
- **Flask + Flask-CORS**: Backend API server
- **requests**: Hugging Face API communication
- **reportlab**: PDF generation
- **nltk**: Text tokenization and processing (auto-downloads 'punkt')
- **python-dotenv**: Environment configuration

## Development Patterns

### Text Processing Strategy
The system uses a **chunked processing approach** for handling long content:
1. Content longer than 1000 words gets split into chunks
2. Each chunk processed individually by AI model
3. Chunk summaries combined and optionally re-summarized
4. Fallback to extractive summarization if AI fails

### Error Handling Architecture
- **Progressive degradation**: AI failure → extractive summary → truncated content
- **Backend validation**: Content length checks, token verification
- **Extension resilience**: Multiple content selector attempts, error user feedback

### Chrome Extension Content Strategy
Uses hierarchical content detection:
```javascript
const contentSelectors = [
  'article', '[role="main"]', 'main', '.content',
  '.post-content', '.entry-content', '.article-body'
];
```

### Testing Philosophy
The `test_system.py` provides comprehensive validation:
- File presence verification
- Python import validation
- Backend instantiation testing
- Text processing functionality verification
- PDF generation capability testing

## Configuration Files

### Backend Configuration (`backend/.env`)
```bash
HUGGINGFACE_API_TOKEN=your_token_here
MAX_CHUNK_SIZE=1000
MIN_SUMMARY_LENGTH=50
MAX_SUMMARY_LENGTH=300
REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
```

### Extension Configuration
- Backend URL hardcoded in `popup.js`: `'http://localhost:5000'`
- For production deployment, update `backendUrl` variable

## Development Workflow

1. **Initial Setup**: Run `python setup.py` for automated environment setup
2. **Backend Development**: Use `start.py` for development server with validation checks
3. **Extension Testing**: Load unpacked extension, test on content-rich sites
4. **System Validation**: Run `test_system.py` before deployment
5. **Production**: Use gunicorn for backend, package extension for Chrome Web Store

## API Contract

### Generate Notes Endpoint
```bash
POST /generate-notes
{
  "content": "webpage text content",
  "url": "https://example.com", 
  "title": "Page Title"
}
```

### Response Structure
```json
{
  "notes": "AI-generated summary",
  "metadata": {
    "source_url": "https://example.com",
    "compression_ratio": 15.2,
    "generated_at": "2024-01-01T00:00:00Z"
  }
}
```

This architecture enables robust AI-powered web content summarization with graceful error handling and multiple content extraction strategies.

## Enhanced Features (Latest Version)

### Structured Note Generation
The system now generates well-formatted notes with:
- **Markdown-style headers** (`#`, `##`, `###`) for hierarchical organization
- **Visual bullet points** with emoji indicators:
  - 🔑 Key points and main concepts
  - ✅ Action items and tasks
  - ⚠️ Warnings and important notes
  - ✨ Benefits and advantages
  - ❌ Problems and disadvantages
- **Bold and italic formatting** for emphasis
- **Professional structure** instead of copy-paste summaries

### AI Prompt Engineering
Multiple sophisticated prompt types for better output:
- `structured_notes`: Comprehensive formatting with headers and bullets
- `key_insights`: Organized extraction of main points and takeaways
- `topic_breakdown`: Analysis by primary topics with structured information
- Progressive fallback system ensures reliable output even if AI fails

### Visual Enhancements
- **Simple text-based diagrams** for processes and workflows
- **Relationship maps** for comparisons and connections
- **Basic mind maps** for complex topics with multiple concepts
- **Process flow diagrams** automatically detected and generated
- **Enhanced typography** with proper emphasis and formatting

### Enhanced PDF Generation
- **Structured PDF output** that preserves markdown formatting
- **Custom styling** with different header levels and bullet point types
- **Visual hierarchy** maintained in print format
- **Professional layout** with proper spacing and typography

### Frontend Improvements
- **Real-time markdown rendering** in Chrome extension popup
- **Animated loading** with visual feedback
- **Enhanced CSS styling** for better readability
- **Responsive design** with improved user experience
- **Visual indicators** showing enhanced features are active

### Comprehensive Export System
**10+ Export Formats Available:**

#### File Formats (8 formats ready)
- **PDF**: Professional document with enhanced formatting and styling
- **Markdown**: Universal format with YAML frontmatter and metadata
- **HTML**: Complete styled webpage with professional CSS
- **JSON**: Structured data with parsed sections and metadata
- **TXT**: Plain text with headers and proper formatting
- **Obsidian**: Enhanced markdown with backlinks and vault compatibility
- **OneNote**: HTML format optimized for Microsoft OneNote import
- **Evernote**: ENEX format for direct Evernote import

#### Platform Integrations (API-based)
- **Notion**: Direct API integration (requires NOTION_API_TOKEN)
- **Google Slides**: Presentation format (requires GOOGLE_CREDENTIALS_JSON)

#### Export System Features
- **Unified export interface** with single API endpoint
- **Format-specific optimizations** for each platform
- **Proper metadata preservation** across all formats
- **Professional styling** maintained in visual formats
- **Frontmatter and headers** added automatically
- **Error handling** with graceful fallbacks
- **Chrome extension dropdown** with visual format selector
