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
from export_system import ExportSystem

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
        # Enhanced CORS configuration for Chrome extensions
        CORS(self.app, 
             origins=["chrome-extension://*", "http://localhost:*", "https://localhost:*"],
             allow_headers=["Content-Type", "Authorization"],
             methods=["GET", "POST", "OPTIONS"])
        
        # Configuration
        self.HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"
        self.HF_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')
        self.GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        self.MAX_CHUNK_SIZE = 1000  # Max words per chunk
        self.MIN_SUMMARY_LENGTH = 50
        self.MAX_SUMMARY_LENGTH = 300
        
        # Translation service priority (try Gemini first, then HuggingFace)
        self.translation_services = []
        if self.GEMINI_API_KEY:
            self.translation_services.append('gemini')
        if self.HF_TOKEN:
            self.translation_services.append('huggingface')
        
        # Initialize export system
        self.export_system = ExportSystem()
        
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
            """Generate and download PDF of smart notes (legacy endpoint)"""
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
        
        @self.app.route('/export-formats', methods=['GET'])
        def get_export_formats():
            """Get list of supported export formats"""
            try:
                formats = self.export_system.get_supported_formats()
                return jsonify({
                    'success': True,
                    'formats': formats
                })
            except Exception as e:
                logger.error(f"Error getting export formats: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/export', methods=['POST'])
        def export_notes():
            """Export notes to specified format"""
            try:
                data = request.json
                if not data or 'notes' not in data or 'format' not in data:
                    return jsonify({'error': 'Missing notes or format in request'}), 400
                
                notes = data['notes']
                export_format = data['format']
                page_info = data.get('pageInfo', {})
                options = data.get('options', {})
                
                logger.info(f"Exporting notes to {export_format}")
                
                # Export using the export system
                result = self.export_system.export_notes(notes, page_info, export_format, options)
                
                if result.get('success'):
                    # For file downloads, return the file
                    if 'data' in result:
                        return send_file(
                            BytesIO(result['data']),
                            as_attachment=True,
                            download_name=result['filename'],
                            mimetype=result['mimetype']
                        )
                    # For web service integrations, return JSON response
                    else:
                        return jsonify(result)
                else:
                    return jsonify(result), 400
                
            except ValueError as ve:
                logger.error(f"Invalid export request: {str(ve)}")
                return jsonify({'error': str(ve)}), 400
            except Exception as e:
                logger.error(f"Error exporting notes: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/translate', methods=['POST'])
        def translate_page():
            """Translate web page content to specified language"""
            try:
                # Check if any translation service is configured
                if not self.translation_services:
                    logger.error("No translation services configured")
                    error_msg = 'Translation service not configured. Please set either:\n'
                    error_msg += '• GEMINI_API_KEY (recommended): Get from https://makersuite.google.com/app/apikey\n'
                    error_msg += '• HUGGINGFACE_API_TOKEN: Get from https://huggingface.co/settings/tokens'
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 500
                
                data = request.json
                if not data or 'content' not in data or 'target_language' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Missing content or target_language in request'
                    }), 400
                
                content = data['content']
                target_language = data['target_language']
                source_language = data.get('source_language', 'auto')
                page_info = data.get('pageInfo', {})
                
                logger.info(f"Translating content to {target_language} (length: {len(content)} chars)")
                
                # Validate content
                if len(content.strip()) < 10:
                    return jsonify({
                        'success': False,
                        'error': 'Content too short for translation (minimum 10 characters required)'
                    }), 400
                
                # Preprocess content for translation
                processed_content = self.preprocess_text_for_translation(content)
                logger.info(f"Processed content length: {len(processed_content)} chars")
                
                # Translate the content with retry logic
                translated_content = self.translate_content_with_retry(processed_content, target_language, source_language)
                
                if not translated_content or translated_content == processed_content:
                    logger.warning("Translation may have failed - content unchanged")
                
                # Prepare response
                response = {
                    'success': True,
                    'translated_content': translated_content,
                    'source_language': source_language,
                    'target_language': target_language,
                    'metadata': {
                        'source_url': page_info.get('url', 'Unknown'),
                        'source_title': page_info.get('title', 'Web Page'),
                        'original_length': len(content),
                        'processed_length': len(processed_content),
                        'translated_length': len(translated_content),
                        'translated_at': datetime.utcnow().isoformat()
                    }
                }
                
                logger.info(f"Successfully translated content to {target_language}")
                return jsonify(response)
                
            except ValueError as ve:
                logger.error(f"Translation validation error: {str(ve)}")
                return jsonify({
                    'success': False,
                    'error': f'Translation error: {str(ve)}'
                }), 400
            except requests.exceptions.RequestException as re:
                logger.error(f"Network error during translation: {str(re)}")
                return jsonify({
                    'success': False,
                    'error': f'Network error: Unable to connect to translation service. Please check your internet connection.'
                }), 503
            except Exception as e:
                logger.error(f"Unexpected error translating content: {str(e)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f'Translation service error: {str(e)}'
                }), 500
        
        @self.app.route('/supported-languages', methods=['GET'])
        def get_supported_languages():
            """Get list of supported translation languages"""
            try:
                languages = self.get_supported_translation_languages()
                return jsonify({
                    'success': True,
                    'languages': languages
                })
            except Exception as e:
                logger.error(f"Error getting supported languages: {str(e)}")
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
        """Query Hugging Face API for text processing"""
        if not self.HF_TOKEN:
            raise ValueError("Hugging Face API token not configured")
        
        headers = {"Authorization": f"Bearer {self.HF_TOKEN}"}
        
        # Create structured prompts for better output
        if prompt_type == "structured_notes":
            prompt = f"""Create comprehensive structured notes from the following text. Format your response with:
- Main heading using ##
- Subheadings using ###
- Bullet points for key information using -
- Important concepts in **bold**
- Include key takeaways at the end

Text: {text}

Structured Notes:"""
        elif prompt_type == "key_insights":
            prompt = f"""Extract and organize the key insights from this text into a structured format:

## Key Insights
### Main Points
- [List main points as bullets]

### Important Details
- [List supporting details]

### Takeaways
- [List actionable takeaways]

Text: {text}"""
        elif prompt_type == "topic_breakdown":
            prompt = f"""Analyze this text and break it down by topics with clear structure:

## Topic Analysis
### Primary Topics
- Topic 1: [Brief description]
- Topic 2: [Brief description]

### Key Information per Topic
**Topic 1:**
- Point 1
- Point 2

**Topic 2:**
- Point 1
- Point 2

### Summary
[Brief overall summary]

Text: {text}"""
        elif prompt_type == "summarize":
            prompt = f"Create a clear, well-organized summary with headings and bullet points from the following text: {text}"
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
        """Generate enhanced structured notes from preprocessed text"""
        word_count = len(text.split())
        
        if word_count < 50:
            return self.format_basic_notes(text, title)
        
        try:
            logger.info(f"Generating structured notes for content with {word_count} words")
            
            if word_count <= self.MAX_CHUNK_SIZE:
                # Single chunk - generate comprehensive structured notes
                return self.create_structured_notes(text, title)
            else:
                # Multi-chunk processing with enhanced combination
                return self.process_long_content(text, title)
                
        except Exception as e:
            logger.error(f"Error in smart notes generation: {str(e)}")
            return self.create_fallback_notes(text, title)
    
    def create_structured_notes(self, text, title=""):
        """Create comprehensive structured notes from single chunk"""
        try:
            # Try structured notes approach first
            structured_notes = self.query_huggingface_model(text, "structured_notes")
            if structured_notes and len(structured_notes) > 100:
                formatted_notes = self.format_notes_output(structured_notes, title)
                return formatted_notes
            
            # Fallback to key insights approach
            logger.info("Trying key insights approach")
            insights_notes = self.query_huggingface_model(text, "key_insights")
            if insights_notes:
                formatted_notes = self.format_notes_output(insights_notes, title)
                return formatted_notes
                
            # Final fallback to topic breakdown
            logger.info("Trying topic breakdown approach")
            topic_notes = self.query_huggingface_model(text, "topic_breakdown")
            formatted_notes = self.format_notes_output(topic_notes or text[:500], title)
            return formatted_notes
            
        except Exception as e:
            logger.warning(f"Structured notes generation failed: {e}")
            return self.create_fallback_notes(text, title)
    
    def process_long_content(self, text, title=""):
        """Process long content with enhanced multi-chunk strategy"""
        chunks = self.chunk_text(text, self.MAX_CHUNK_SIZE)
        logger.info(f"Processing {len(chunks)} chunks for long content")
        
        chunk_notes = []
        chunk_topics = []
        
        for i, chunk in enumerate(chunks):
            try:
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                # Generate structured notes for each chunk
                chunk_structured = self.query_huggingface_model(chunk, "key_insights")
                if chunk_structured:
                    chunk_notes.append(chunk_structured)
                    
                    # Extract topics from this chunk
                    topics = self.extract_topics_from_chunk(chunk)
                    chunk_topics.extend(topics)
                    
            except Exception as e:
                logger.warning(f"Failed to process chunk {i+1}: {str(e)}")
                # Fallback for this chunk
                fallback = self.create_extractive_summary(chunk)
                chunk_notes.append(fallback)
        
        if not chunk_notes:
            return self.create_fallback_notes(text, title)
        
        # Combine all chunk notes intelligently
        return self.combine_chunk_notes(chunk_notes, chunk_topics, title)
    
    def extract_topics_from_chunk(self, chunk):
        """Extract main topics from a text chunk"""
        try:
            # Simple keyword extraction based on sentence structure
            sentences = sent_tokenize(chunk)
            topics = []
            
            for sentence in sentences[:3]:  # Look at first few sentences
                # Look for sentence patterns that indicate topics
                words = word_tokenize(sentence.lower())
                if len(words) > 5:
                    # Extract potential topic words (nouns, important terms)
                    topic_candidates = [word for word in words if len(word) > 4 and word.isalpha()]
                    if topic_candidates:
                        topics.extend(topic_candidates[:2])  # Take top 2 candidates per sentence
            
            return list(set(topics))[:5]  # Return unique topics, max 5
            
        except Exception:
            return []
    
    def combine_chunk_notes(self, chunk_notes, topics, title=""):
        """Intelligently combine notes from multiple chunks"""
        try:
            # Create a structured combination of all chunk notes
            combined_content = "\n\n".join(chunk_notes)
            
            # If the combined content is still manageable, try to structure it
            if len(combined_content.split()) <= self.MAX_CHUNK_SIZE * 1.5:
                final_prompt = f"""Organize these related notes into a comprehensive, well-structured document with:

## Main Topic: {title if title else 'Key Information'}

### Overview
[Brief overview of the main themes]

### Key Points
- [Organized bullet points of main information]

### Important Details
- [Supporting details and specifics]

### Summary & Takeaways
- [Key conclusions and actionable insights]

Notes to organize: {combined_content}"""
                
                final_notes = self.query_huggingface_model(combined_content, "topic_breakdown")
                return self.format_notes_output(final_notes or combined_content, title)
            else:
                # Too long, use the combined content with basic formatting
                return self.format_notes_output(combined_content, title)
                
        except Exception as e:
            logger.warning(f"Failed to combine chunk notes: {e}")
            # Return basic combination
            return self.format_basic_combination(chunk_notes, title)
    
    def format_notes_output(self, notes_content, title=""):
        """Format the notes output with enhanced structure and potential visual elements"""
        try:
            formatted_notes = notes_content
            
            # Clean up AI model artifacts
            formatted_notes = re.sub(r'^.*?Structured Notes:?\s*', '', formatted_notes, flags=re.IGNORECASE)
            formatted_notes = re.sub(r'^.*?Text:.*?\n', '', formatted_notes, flags=re.DOTALL | re.IGNORECASE)
            
            # Ensure proper markdown formatting
            if not formatted_notes.startswith('#'):
                main_title = title if title else "Smart Notes"
                formatted_notes = f"# {main_title}\n\n{formatted_notes}"
            
            # Add visual elements and enhancements
            enhanced_notes = self.add_visual_enhancements(formatted_notes)
            
            # Add metadata footer
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            enhanced_notes += f"\n\n---\n*Generated on {timestamp} by Smart Notes AI*"
            
            return enhanced_notes
            
        except Exception as e:
            logger.warning(f"Error formatting notes: {e}")
            return notes_content
    
    def add_visual_enhancements(self, notes):
        """Add visual enhancements like simple diagrams and better formatting"""
        try:
            enhanced = notes
            
            # Add simple text-based diagrams for processes or relationships
            if any(keyword in notes.lower() for keyword in ['process', 'steps', 'workflow', 'procedure']):
                enhanced = self.add_process_diagram(enhanced)
            
            if any(keyword in notes.lower() for keyword in ['relationship', 'connection', 'between', 'versus']):
                enhanced = self.add_relationship_diagram(enhanced)
            
            # Add mind map for complex topics
            if any(keyword in notes.lower() for keyword in ['concept', 'topic', 'analysis', 'overview']):
                enhanced = self.add_mind_map(enhanced)
            
            # Enhance bullet points with icons/symbols
            enhanced = self.enhance_bullet_points(enhanced)
            
            # Add emphasis to important terms
            enhanced = self.add_emphasis_formatting(enhanced)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Error adding visual enhancements: {e}")
            return notes
    
    def add_process_diagram(self, text):
        """Add simple text-based process diagrams"""
        # Look for numbered steps or process indicators
        if re.search(r'step\s*\d|\d+\.', text.lower()):
            diagram = "\n\n### Process Flow\n```\n"
            diagram += "[Start] → [Step 1] → [Step 2] → [Step 3] → [End]\n"
            diagram += "```\n\n"
            return text + diagram
        return text
    
    def add_relationship_diagram(self, text):
        """Add simple relationship diagrams"""
        if any(word in text.lower() for word in ['versus', 'compared to', 'relationship']):
            diagram = "\n\n### Relationship Map\n```\n"
            diagram += "   Concept A\n      ↓\n  [Relationship]\n      ↓\n   Concept B\n"
            diagram += "```\n\n"
            return text + diagram
        return text
    
    def add_mind_map(self, text):
        """Generate a simple text-based mind map"""
        try:
            # Extract key topics from the text
            topics = self.extract_mind_map_topics(text)
            if len(topics) >= 3:
                diagram = "\n\n### Mind Map Overview\n```\n"
                diagram += "                    [MAIN TOPIC]\n"
                diagram += "                         |\n"
                diagram += "        ┌────────────────┼────────────────┐\n"
                
                # Add main branches
                for i, topic in enumerate(topics[:4]):  # Limit to 4 main branches
                    if i == 0:
                        diagram += f"     [{topic[:12]}...]\n"
                    elif i == 1:
                        diagram += f"                              [{topic[:12]}...]\n"
                    elif i == 2:
                        diagram += f"  [{topic[:12]}...]                     [{topic[:12]}...]\n" if len(topics) > 3 else f"     [{topic[:12]}...]\n"
                    else:
                        continue
                
                diagram += "\n    💡 Key concepts interconnected above\n"
                diagram += "```\n\n"
                return text + diagram
        except Exception as e:
            logger.warning(f"Failed to generate mind map: {e}")
        return text
    
    def extract_mind_map_topics(self, text):
        """Extract main topics for mind map generation"""
        try:
            # Look for headings and key terms
            topics = []
            
            # Extract from headings
            heading_matches = re.findall(r'^#+\s*(.+)$', text, re.MULTILINE)
            for match in heading_matches:
                clean_topic = re.sub(r'[^\w\s]', '', match).strip()
                if clean_topic and len(clean_topic) > 3:
                    topics.append(clean_topic)
            
            # Extract from bullet points that seem like topics
            bullet_matches = re.findall(r'^[-•*]\s*([A-Z][^.!?]+?)(?:[.!?]|$)', text, re.MULTILINE)
            for match in bullet_matches:
                clean_topic = re.sub(r'[^\w\s]', '', match).strip()
                if clean_topic and len(clean_topic) > 5 and len(clean_topic.split()) <= 4:
                    topics.append(clean_topic)
            
            # Remove duplicates and return unique topics
            unique_topics = list(dict.fromkeys(topics))  # Preserve order
            return unique_topics[:6]  # Limit to 6 topics for clarity
            
        except Exception:
            return []
    
    def enhance_bullet_points(self, text):
        """Enhance bullet points with visual symbols"""
        # Replace different types of bullet points with visual symbols
        text = re.sub(r'^- (Key|Main|Important)', r'🔑 \1', text, flags=re.MULTILINE)
        text = re.sub(r'^- (Action|Task|Do)', r'✅ \1', text, flags=re.MULTILINE)
        text = re.sub(r'^- (Note|Remember|Warning)', r'⚠️ \1', text, flags=re.MULTILINE)
        text = re.sub(r'^- (Benefit|Advantage|Pro)', r'✨ \1', text, flags=re.MULTILINE)
        text = re.sub(r'^- (Problem|Issue|Con)', r'❌ \1', text, flags=re.MULTILINE)
        return text
    
    def add_emphasis_formatting(self, text):
        """Add emphasis to important terms"""
        # Emphasize terms that appear to be important concepts
        important_patterns = [
            (r'\b(conclusion|summary|key point|important|critical|essential)\b', r'**\1**'),
            (r'\b(\d+%)\b', r'**\1**'),  # Percentages
            (r'\$([\d,]+)', r'**$\1**'),  # Money amounts
        ]
        
        for pattern, replacement in important_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def create_fallback_notes(self, text, title=""):
        """Create basic but structured fallback notes"""
        try:
            sentences = sent_tokenize(text)
            
            # Create a structured fallback
            fallback_notes = f"# {title if title else 'Smart Notes'}\n\n"
            fallback_notes += "## Key Information\n\n"
            
            # Take the most important sentences (first few and any with key indicators)
            important_sentences = sentences[:3]  # First 3 sentences
            
            # Look for sentences with important indicators
            for sentence in sentences[3:8]:  # Check next 5 sentences
                if any(indicator in sentence.lower() for indicator in 
                      ['important', 'key', 'significant', 'main', 'primary', 'conclusion']):
                    important_sentences.append(sentence)
            
            for i, sentence in enumerate(important_sentences[:5]):
                fallback_notes += f"- {sentence.strip()}\n"
            
            fallback_notes += "\n## Summary\n\n"
            fallback_notes += f"This content covers {len(sentences)} main points with key information extracted above."
            
            return fallback_notes
            
        except Exception:
            return f"# {title if title else 'Smart Notes'}\n\n{text[:500]}..."
    
    def format_basic_notes(self, text, title=""):
        """Format very short content into basic notes structure"""
        return f"# {title if title else 'Smart Notes'}\n\n## Content\n\n{text}\n\n*Note: Content was too brief for advanced processing.*"
    
    def create_extractive_summary(self, text):
        """Create extractive summary as fallback"""
        try:
            sentences = sent_tokenize(text)
            # Take first few sentences as summary
            summary_sentences = sentences[:min(3, len(sentences))]
            return "\n".join([f"- {sentence.strip()}" for sentence in summary_sentences])
        except:
            return text[:200] + "..."
    
    def format_basic_combination(self, chunk_notes, title=""):
        """Basic combination of chunk notes"""
        combined = f"# {title if title else 'Smart Notes'}\n\n"
        
        for i, chunk_note in enumerate(chunk_notes, 1):
            combined += f"## Section {i}\n\n{chunk_note}\n\n"
        
        return combined

    def generate_pdf(self, notes, page_info):
        """Generate enhanced PDF from structured smart notes"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        
        # Get styles and create custom ones
        styles = getSampleStyleSheet()
        
        # Enhanced custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            textColor='darkblue',
            alignment=1  # Center alignment
        )
        
        h1_style = ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            spaceBefore=15,
            textColor='darkblue'
        )
        
        h2_style = ParagraphStyle(
            'CustomH2', 
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=12,
            textColor='darkgreen'
        )
        
        h3_style = ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=10,
            spaceBefore=8,
            textColor='darkred'
        )
        
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=8
        )
        
        content = []
        
        # Title
        content.append(Paragraph("Enhanced Smart Notes", title_style))
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
        
        # Process notes content with markdown parsing
        content.extend(self.parse_markdown_for_pdf(notes, styles, h1_style, h2_style, h3_style, bullet_style))
        
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        return buffer
    
    def parse_markdown_for_pdf(self, notes, styles, h1_style, h2_style, h3_style, bullet_style):
        """Parse markdown content for PDF generation"""
        content = []
        lines = notes.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                content.append(Spacer(1, 6))
                continue
            
            # Headers
            if line.startswith('# '):
                text = line[2:].strip()
                content.append(Paragraph(text, h1_style))
            elif line.startswith('## '):
                text = line[3:].strip()
                content.append(Paragraph(text, h2_style))
            elif line.startswith('### '):
                text = line[4:].strip()
                content.append(Paragraph(text, h3_style))
            # Bullet points (including emoji bullets)
            elif line.startswith(('- ', '• ', '🔑 ', '✅ ', '⚠️ ', '✨ ', '❌ ')):
                # Clean the bullet point
                if line.startswith('- '):
                    text = '• ' + line[2:].strip()
                else:
                    text = line
                
                # Handle bold formatting
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                
                content.append(Paragraph(text, bullet_style))
            # Code blocks
            elif line.startswith('```'):
                continue  # Skip code block markers for now
            # Horizontal rules
            elif line == '---':
                content.append(Spacer(1, 10))
                # Add a line using a paragraph with underline
                content.append(Paragraph('_' * 50, styles['Normal']))
                content.append(Spacer(1, 10))
            # Regular paragraphs
            else:
                # Skip lines that look like code content or diagram content
                if not any(char in line for char in ['┌', '─', '└', '┐', '┴', '┼', '│', '→', '↓']):
                    # Handle bold and italic formatting
                    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                    
                    content.append(Paragraph(text, styles['Normal']))
                    content.append(Spacer(1, 6))
        
        return content
    
    def preprocess_text_for_translation(self, text):
        """Preprocess text for translation to preserve structure"""
        # Keep the original structure but clean up for better translation
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Preserve line breaks for better structure
        text = re.sub(r'\n+', '\n', text)
        
        # Don't remove URLs completely as they might be important for context
        # Just normalize them
        text = re.sub(r'http[s]?://[^\s]+', '[URL]', text)
        
        return text.strip()
    
    def translate_content(self, content, target_language, source_language="auto"):
        """Translate content using Hugging Face translation models"""
        if not self.HF_TOKEN:
            raise ValueError("Hugging Face API token not configured")
        
        try:
            # Split content into chunks if it's too long
            chunks = self.chunk_text_for_translation(content)
            translated_chunks = []
            
            for chunk in chunks:
                translated_chunk = self.translate_chunk(chunk, target_language, source_language)
                translated_chunks.append(translated_chunk)
            
            return ' '.join(translated_chunks)
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            raise ValueError(f"Translation failed: {str(e)}")
    
    def chunk_text_for_translation(self, text, max_chars=1000):
        """Split text into chunks for translation"""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        sentences = sent_tokenize(text)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chars:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def translate_chunk(self, text, target_language, source_language="auto"):
        """Translate a single chunk using Hugging Face API"""
        import time
        # Map language codes to appropriate models
        language_models = {
            'spanish': 'Helsinki-NLP/opus-mt-en-es',
            'french': 'Helsinki-NLP/opus-mt-en-fr',
            'german': 'Helsinki-NLP/opus-mt-en-de',
            'italian': 'Helsinki-NLP/opus-mt-en-it',
            'portuguese': 'Helsinki-NLP/opus-mt-en-pt',
            'dutch': 'Helsinki-NLP/opus-mt-en-nl',
            'chinese': 'Helsinki-NLP/opus-mt-en-zh',
            'japanese': 'Helsinki-NLP/opus-mt-en-jap',
            'korean': 'Helsinki-NLP/opus-mt-en-ko',
            'arabic': 'Helsinki-NLP/opus-mt-en-ar',
            'russian': 'Helsinki-NLP/opus-mt-en-ru',
            'hindi': 'Helsinki-NLP/opus-mt-en-hi'
        }
        
        model_name = language_models.get(target_language.lower(), 'Helsinki-NLP/opus-mt-en-es')
        translation_api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        
        headers = {"Authorization": f"Bearer {self.HF_TOKEN}"}
        
        payload = {
            "inputs": text
        }
        
        try:
            response = requests.post(translation_api_url, headers=headers, json=payload, timeout=30)
            
            # Handle different response status codes
            if response.status_code == 503:
                # Model is loading, wait and retry
                logger.info(f"Model {model_name} is loading, waiting...")
                time.sleep(20)  # Wait for model to load
                response = requests.post(translation_api_url, headers=headers, json=payload, timeout=30)
            
            response.raise_for_status()
            
            result = response.json()
            
            # Handle error responses from HuggingFace
            if isinstance(result, dict) and 'error' in result:
                logger.warning(f"HuggingFace API error: {result['error']}")
                return self.translate_with_general_model(text, target_language)
            
            if isinstance(result, list) and len(result) > 0:
                if 'translation_text' in result[0]:
                    return result[0]['translation_text']
                elif 'generated_text' in result[0]:
                    return result[0]['generated_text']
            
            # Fallback: try using the general model with prompting
            return self.translate_with_general_model(text, target_language)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Translation API request failed: {str(e)}")
            # Fallback to general model
            return self.translate_with_general_model(text, target_language)
    
    def translate_with_general_model(self, text, target_language):
        """Fallback translation using general language model"""
        prompt = f"Translate the following text to {target_language}:\n\n{text}\n\nTranslation:"
        
        headers = {"Authorization": f"Bearer {self.HF_TOKEN}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": len(text) * 2,  # Allow for expansion
                "min_length": len(text) // 2,
                "do_sample": False,
                "temperature": 0.3
            }
        }
        
        try:
            response = requests.post(self.HF_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                translated = result[0].get('generated_text', '').strip()
                # Remove the prompt from the response
                if 'Translation:' in translated:
                    translated = translated.split('Translation:')[-1].strip()
                return translated
            
            return text  # Return original if translation fails
            
        except Exception as e:
            logger.error(f"General model translation failed: {str(e)}")
            return text  # Return original text as fallback
    
    def translate_with_gemini(self, content, target_language, source_language="auto"):
        """Translate content using Google Gemini API with direct HTTP requests"""
        try:
            import json
            
            # Language mapping for better prompts
            language_names = {
                'spanish': 'Spanish',
                'french': 'French', 
                'german': 'German',
                'italian': 'Italian',
                'portuguese': 'Portuguese',
                'dutch': 'Dutch',
                'chinese': 'Chinese (Simplified)',
                'japanese': 'Japanese',
                'korean': 'Korean',
                'arabic': 'Arabic',
                'russian': 'Russian',
                'hindi': 'Hindi'
            }
            
            target_lang_name = language_names.get(target_language.lower(), target_language)
            
            # Create translation prompt
            prompt = f"""Translate the following text to {target_lang_name}. 
Provide only the translation without any additional text or explanations.

Text to translate:
{content}

Translation:"""
            
            # Gemini API endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.GEMINI_API_KEY}"
            
            # Request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,  # Low temperature for consistent translation
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 2048
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            logger.info(f"Using Gemini API for translation to {target_language}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    translated = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # Remove any leading "Translation:" if Gemini adds it
                    if translated.lower().startswith('translation:'):
                        translated = translated[12:].strip()
                    
                    # Clean up any remaining prefixes
                    lines = translated.split('\n')
                    if lines:
                        translated = lines[-1].strip() if len(lines) > 1 else lines[0].strip()
                    
                    return translated
                else:
                    raise ValueError("Gemini returned unexpected response format")
            else:
                error_msg = f"Gemini API request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data}"
                except:
                    error_msg += f" - {response.text}"
                raise ValueError(error_msg)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API network error: {str(e)}")
            raise ValueError(f"Gemini API network error: {str(e)}")
        except Exception as e:
            logger.error(f"Gemini translation failed: {str(e)}")
            raise ValueError(f"Gemini translation failed: {str(e)}")
    
    def translate_content_with_retry(self, content, target_language, source_language="auto", max_retries=3):
        """Translate content with retry logic and multiple service support"""
        import time
        
        last_errors = []
        
        # Try each available translation service
        for service in self.translation_services:
            logger.info(f"Trying translation with {service} service")
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"{service} translation attempt {attempt + 1}/{max_retries}")
                    
                    if service == 'gemini':
                        translated = self.translate_with_gemini(content, target_language, source_language)
                    elif service == 'huggingface':
                        translated = self.translate_content(content, target_language, source_language)
                    else:
                        continue
                    
                    # Validate translation result
                    if translated and translated.strip() and translated != content:
                        logger.info(f"Translation successful with {service} on attempt {attempt + 1}")
                        return translated
                    else:
                        logger.warning(f"{service} attempt {attempt + 1} returned empty or unchanged content")
                        if attempt < max_retries - 1:
                            time.sleep(1)  # Wait before retry
                            continue
                    
                except requests.exceptions.Timeout as e:
                    error_msg = f"{service} request timeout: {str(e)}"
                    last_errors.append(error_msg)
                    logger.warning(f"{service} attempt {attempt + 1} timed out: {e}")
                except requests.exceptions.ConnectionError as e:
                    error_msg = f"{service} connection error: {str(e)}"
                    last_errors.append(error_msg)
                    logger.warning(f"{service} attempt {attempt + 1} connection failed: {e}")
                except requests.exceptions.RequestException as e:
                    error_msg = f"{service} request failed: {str(e)}"
                    last_errors.append(error_msg)
                    logger.warning(f"{service} attempt {attempt + 1} request failed: {e}")
                except Exception as e:
                    error_msg = f"{service} translation error: {str(e)}"
                    last_errors.append(error_msg)
                    logger.warning(f"{service} attempt {attempt + 1} failed: {e}")
                
                # Wait before retry (exponential backoff)
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
            
            # If this service failed all attempts, try the next service
            logger.warning(f"{service} service failed after {max_retries} attempts, trying next service")
        
        # All services and attempts failed
        error_summary = "; ".join(last_errors[-3:])  # Show last 3 errors
        error_msg = f"Translation failed with all available services. Last errors: {error_summary}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def get_supported_translation_languages(self):
        """Get list of supported translation languages"""
        return [
            {"code": "spanish", "name": "Spanish", "native": "Español"},
            {"code": "french", "name": "French", "native": "Français"},
            {"code": "german", "name": "German", "native": "Deutsch"},
            {"code": "italian", "name": "Italian", "native": "Italiano"},
            {"code": "portuguese", "name": "Portuguese", "native": "Português"},
            {"code": "dutch", "name": "Dutch", "native": "Nederlands"},
            {"code": "chinese", "name": "Chinese (Simplified)", "native": "中文"},
            {"code": "japanese", "name": "Japanese", "native": "日本語"},
            {"code": "korean", "name": "Korean", "native": "한국어"},
            {"code": "arabic", "name": "Arabic", "native": "العربية"},
            {"code": "russian", "name": "Russian", "native": "Русский"},
            {"code": "hindi", "name": "Hindi", "native": "हिन्दी"}
        ]

def create_app():
    """Create and configure Flask application"""
    smart_notes = SmartNotesApp()
    return smart_notes.app

if __name__ == '__main__':
    app = create_app()
    
    # Check for API tokens and show available services
    smart_notes = SmartNotesApp()
    available_services = smart_notes.translation_services
    
    print("\n" + "=" * 50)
    print("🌐 Smart Notes Translation Services")
    print("=" * 50)
    
    if available_services:
        print(f"✅ Available translation services: {', '.join(available_services)}")
    else:
        print("❌ No translation services configured!")
        print("\nTo enable translation, set one of these API keys:")
        print("• GEMINI_API_KEY (recommended): https://makersuite.google.com/app/apikey")
        print("• HUGGINGFACE_API_TOKEN: https://huggingface.co/settings/tokens")
        print("\nExample:")
        print("  $env:GEMINI_API_KEY='your_gemini_key_here'")
    
    print("\n💡 To test translation: python setup_translation.py")
    print("=" * 50 + "\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
