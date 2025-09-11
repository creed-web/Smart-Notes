#!/usr/bin/env python3
"""
Smart Notes Backend - Flask Application
Provides AI-powered text summarization using Hugging Face models
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
except:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_notes.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartNotesApp:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for Chrome extension
        
        # Configuration
        self.HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"
        self.HF_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')
        self.MAX_CHUNK_SIZE = 1000  # Max words per chunk
        self.MIN_SUMMARY_LENGTH = 50
        self.MAX_SUMMARY_LENGTH = 300
        
        # Setup routes
        self.setup_routes()
        
        logger.info("Smart Notes Flask backend initialized")

    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'version': '1.0.0',
                'model': 'google/flan-t5-small',
                'timestamp': datetime.utcnow().isoformat()
            })

        @self.app.route('/generate-notes', methods=['POST'])
        def generate_notes():
            """Generate smart notes from web page content"""
            try:
                data = request.json
                if not data or 'content' not in data:
                    return jsonify({'error': 'Missing content in request'}), 400
                
                content = data['content']
                url = data.get('url', 'Unknown')
                title = data.get('title', 'Web Page')
                
                logger.info(f"Processing content from: {url}")
                
                # Validate content
                if len(content.strip()) < 100:
                    return jsonify({'error': 'Content too short for meaningful summarization'}), 400
                
                # Process the content
                processed_content = self.preprocess_text(content)
                
                # Generate smart notes
                notes = self.generate_smart_notes(processed_content, title)
                
                # Prepare response
                response = {
                    'notes': notes,
                    'metadata': {
                        'source_url': url,
                        'source_title': title,
                        'original_length': len(content),
                        'processed_length': len(processed_content),
                        'summary_length': len(notes),
                        'compression_ratio': round(len(notes) / len(content) * 100, 2),
                        'generated_at': datetime.utcnow().isoformat()
                    }
                }
                
                logger.info(f"Successfully generated notes for: {url}")
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Error generating notes: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/download-pdf', methods=['POST'])
        def download_pdf():
            """Generate and download PDF of smart notes"""
            try:
                data = request.json
                if not data or 'notes' not in data:
                    return jsonify({'error': 'Missing notes in request'}), 400
                
                notes = data['notes']
                page_info = data.get('pageInfo', {})
                
                # Generate PDF
                pdf_buffer = self.generate_pdf(notes, page_info)
                
                return send_file(
                    pdf_buffer,
                    as_attachment=True,
                    download_name=f'smart_notes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                    mimetype='application/pdf'
                )
                
            except Exception as e:
                logger.error(f"Error generating PDF: {str(e)}")
                return jsonify({'error': str(e)}), 500

    def preprocess_text(self, text):
        """Clean and preprocess text content"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S*@\S*\s?', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Remove navigation and common webpage text
        navigation_patterns = [
            r'skip to content',
            r'click here',
            r'read more',
            r'learn more',
            r'sign up',
            r'log in',
            r'subscribe',
            r'follow us',
            r'share this',
            r'tweet this',
            r'privacy policy',
            r'terms of service',
            r'cookie policy'
        ]
        
        for pattern in navigation_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()

    def chunk_text(self, text, max_words=1000):
        """Split text into chunks suitable for summarization"""
        try:
            sentences = sent_tokenize(text)
        except:
            # Fallback if NLTK fails
            sentences = text.split('. ')
        
        chunks = []
        current_chunk = ""
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(word_tokenize(sentence))
            
            if current_word_count + sentence_words <= max_words:
                current_chunk += sentence + " "
                current_word_count += sentence_words
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
                current_word_count = sentence_words
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def query_huggingface_model(self, text, prompt_type="summarize"):
        """Query Hugging Face API for text summarization"""
        if not self.HF_TOKEN:
            raise ValueError("Hugging Face API token not configured")
        
        headers = {"Authorization": f"Bearer {self.HF_TOKEN}"}
        
        # Create appropriate prompt based on type
        if prompt_type == "summarize":
            prompt = f"Summarize the following text in a clear and concise way, highlighting the main points and key information: {text}"
        elif prompt_type == "key_points":
            prompt = f"Extract the key points and important information from the following text: {text}"
        else:
            prompt = f"Create smart notes from the following text: {text}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": self.MAX_SUMMARY_LENGTH,
                "min_length": self.MIN_SUMMARY_LENGTH,
                "do_sample": False,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(self.HF_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').strip()
            elif isinstance(result, dict):
                return result.get('generated_text', '').strip()
            else:
                raise ValueError("Unexpected response format from Hugging Face API")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Hugging Face API request failed: {str(e)}")
            raise ValueError(f"AI model request failed: {str(e)}")

    def generate_smart_notes(self, text, title=""):
        """Generate smart notes from preprocessed text"""
        word_count = len(text.split())
        
        if word_count < 50:
            return text  # Return original if too short
        
        try:
            if word_count <= self.MAX_CHUNK_SIZE:
                # Single chunk processing
                summary = self.query_huggingface_model(text, "summarize")
                
                # Clean up the summary
                if summary.startswith(prompt for prompt in ["Summarize", "The following", "This text"]):
                    # Remove prompt remnants
                    summary = re.sub(r'^.*?:', '', summary).strip()
                
                return summary or text[:500] + "..."
            
            else:
                # Multi-chunk processing
                chunks = self.chunk_text(text, self.MAX_CHUNK_SIZE)
                logger.info(f"Processing {len(chunks)} chunks")
                
                chunk_summaries = []
                for i, chunk in enumerate(chunks):
                    try:
                        logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                        summary = self.query_huggingface_model(chunk, "summarize")
                        
                        if summary:
                            chunk_summaries.append(summary)
                    except Exception as e:
                        logger.warning(f"Failed to process chunk {i+1}: {str(e)}")
                        # Use extractive summary as fallback
                        sentences = sent_tokenize(chunk)[:3]  # First 3 sentences
                        fallback_summary = " ".join(sentences)
                        if fallback_summary:
                            chunk_summaries.append(fallback_summary)
                
                if not chunk_summaries:
                    raise ValueError("Failed to generate any summaries")
                
                # Combine chunk summaries
                combined_summary = " ".join(chunk_summaries)
                
                # If the combined summary is still too long, summarize it again
                if len(combined_summary.split()) > self.MAX_CHUNK_SIZE:
                    final_summary = self.query_huggingface_model(combined_summary, "summarize")
                    return final_summary or combined_summary
                
                return combined_summary
                
        except Exception as e:
            logger.error(f"Error in smart notes generation: {str(e)}")
            # Fallback: extractive summary
            try:
                sentences = sent_tokenize(text)
                # Take first few sentences as basic summary
                summary_sentences = sentences[:min(5, len(sentences))]
                return " ".join(summary_sentences)
            except:
                return text[:500] + "..." if len(text) > 500 else text

    def generate_pdf(self, notes, page_info):
        """Generate PDF from smart notes"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor='darkblue'
        )
        
        content = []
        
        # Title
        content.append(Paragraph("Smart Notes", title_style))
        content.append(Spacer(1, 12))
        
        # Page info
        if page_info:
            info_style = styles['Normal']
            if page_info.get('title'):
                content.append(Paragraph(f"<b>Source:</b> {page_info['title']}", info_style))
            if page_info.get('url'):
                content.append(Paragraph(f"<b>URL:</b> {page_info['url']}", info_style))
            if page_info.get('timestamp'):
                content.append(Paragraph(f"<b>Generated:</b> {page_info['timestamp']}", info_style))
            content.append(Spacer(1, 20))
        
        # Notes content
        notes_style = styles['Normal']
        notes_paragraphs = notes.split('\n')
        
        for para in notes_paragraphs:
            if para.strip():
                content.append(Paragraph(para.strip(), notes_style))
                content.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        return buffer

def create_app():
    """Create and configure Flask application"""
    smart_notes = SmartNotesApp()
    return smart_notes.app

if __name__ == '__main__':
    app = create_app()
    
    # Check for Hugging Face token
    if not os.getenv('HUGGINGFACE_API_TOKEN'):
        logger.warning("HUGGINGFACE_API_TOKEN environment variable not set!")
        print("Please set your Hugging Face API token:")
        print("export HUGGINGFACE_API_TOKEN='your_token_here'")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
