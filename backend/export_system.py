#!/usr/bin/env python3
"""
Smart Notes Export System
Comprehensive export functionality for multiple formats and platforms
"""

import os
import json
import logging
import requests
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import Dict, Any, List, Optional
import base64

# For various export formats
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)

class ExportSystem:
    """Comprehensive export system for Smart Notes"""
    
    def __init__(self):
        self.supported_formats = [
            'pdf', 'markdown', 'html', 'json', 'txt', 'notion', 
            'google_slides', 'obsidian', 'onenote', 'evernote'
        ]
        
        # API configurations (to be set via environment variables)
        self.notion_token = os.getenv('NOTION_API_TOKEN')
        self.google_credentials = os.getenv('GOOGLE_CREDENTIALS_JSON')
        
        logger.info(f"Export system initialized with {len(self.supported_formats)} formats")
    
    def export_notes(self, notes: str, page_info: Dict[str, Any], export_format: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main export function that routes to appropriate format handler
        
        Args:
            notes: The structured notes content
            page_info: Information about the source page
            export_format: Target export format
            options: Additional export options
        
        Returns:
            Dictionary with export result and metadata
        """
        if export_format not in self.supported_formats:
            raise ValueError(f"Unsupported export format: {export_format}")
        
        options = options or {}
        
        logger.info(f"Exporting notes to {export_format}")
        
        # Route to appropriate export handler
        export_handlers = {
            'pdf': self.export_to_pdf,
            'markdown': self.export_to_markdown,
            'html': self.export_to_html,
            'json': self.export_to_json,
            'txt': self.export_to_txt,
            'notion': self.export_to_notion,
            'google_slides': self.export_to_google_slides,
            'obsidian': self.export_to_obsidian,
            'onenote': self.export_to_onenote,
            'evernote': self.export_to_evernote
        }
        
        handler = export_handlers[export_format]
        return handler(notes, page_info, options)
    
    def export_to_pdf(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to PDF format with enhanced formatting"""
        try:
            from app import SmartNotesApp
            app = SmartNotesApp()
            buffer = app.generate_pdf(notes, page_info)
            
            filename = f"smart_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            return {
                'success': True,
                'format': 'pdf',
                'filename': filename,
                'data': buffer.getvalue(),
                'mimetype': 'application/pdf',
                'size': len(buffer.getvalue())
            }
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_to_markdown(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to Markdown format"""
        try:
            # Enhance the markdown with frontmatter and metadata
            frontmatter = self._generate_frontmatter(page_info)
            
            markdown_content = f"{frontmatter}\n{notes}"
            
            filename = f"smart_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            return {
                'success': True,
                'format': 'markdown',
                'filename': filename,
                'data': markdown_content.encode('utf-8'),
                'mimetype': 'text/markdown',
                'size': len(markdown_content.encode('utf-8'))
            }
        except Exception as e:
            logger.error(f"Markdown export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_to_html(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to HTML format with styling"""
        try:
            # Convert markdown to HTML
            html_content = markdown.markdown(notes, extensions=['tables', 'fenced_code', 'toc'])
            
            # Create a complete HTML document
            full_html = self._create_html_document(html_content, page_info)
            
            filename = f"smart_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            return {
                'success': True,
                'format': 'html',
                'filename': filename,
                'data': full_html.encode('utf-8'),
                'mimetype': 'text/html',
                'size': len(full_html.encode('utf-8'))
            }
        except Exception as e:
            logger.error(f"HTML export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_to_json(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to JSON format with structured data"""
        try:
            structured_data = {
                'metadata': {
                    'title': page_info.get('title', 'Untitled'),
                    'url': page_info.get('url', ''),
                    'generated_at': datetime.now().isoformat(),
                    'export_format': 'json',
                    'version': '2.0'
                },
                'content': {
                    'raw_notes': notes,
                    'structured_notes': self._parse_notes_structure(notes),
                    'word_count': len(notes.split()),
                    'sections': self._extract_sections(notes)
                }
            }
            
            json_content = json.dumps(structured_data, indent=2, ensure_ascii=False)
            filename = f"smart_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            return {
                'success': True,
                'format': 'json',
                'filename': filename,
                'data': json_content.encode('utf-8'),
                'mimetype': 'application/json',
                'size': len(json_content.encode('utf-8'))
            }
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_to_txt(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to plain text format"""
        try:
            # Convert markdown to plain text
            plain_text = self._markdown_to_plaintext(notes)
            
            # Add header with metadata
            header = f"Smart Notes - {page_info.get('title', 'Untitled')}\n"
            header += f"Source: {page_info.get('url', 'Unknown')}\n"
            header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            header += "=" * 50 + "\n\n"
            
            full_content = header + plain_text
            filename = f"smart_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            return {
                'success': True,
                'format': 'txt',
                'filename': filename,
                'data': full_content.encode('utf-8'),
                'mimetype': 'text/plain',
                'size': len(full_content.encode('utf-8'))
            }
        except Exception as e:
            logger.error(f"TXT export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_to_notion(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to Notion via API"""
        try:
            if not self.notion_token:
                return {
                    'success': False, 
                    'error': 'Notion API token not configured',
                    'setup_required': True,
                    'setup_instructions': 'Add NOTION_API_TOKEN to environment variables'
                }
            
            # Create Notion page structure
            notion_blocks = self._convert_to_notion_blocks(notes)
            
            # Create page in Notion
            result = self._create_notion_page(
                title=page_info.get('title', 'Smart Notes'),
                blocks=notion_blocks,
                parent_database_id=options.get('database_id')
            )
            
            if result['success']:
                return {
                    'success': True,
                    'format': 'notion',
                    'url': result['page_url'],
                    'page_id': result['page_id'],
                    'message': 'Successfully exported to Notion'
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Notion export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_to_google_slides(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to Google Slides presentation"""
        try:
            if not self.google_credentials:
                return {
                    'success': False, 
                    'error': 'Google credentials not configured',
                    'setup_required': True,
                    'setup_instructions': 'Add GOOGLE_CREDENTIALS_JSON to environment variables'
                }
            
            # Convert notes to slides structure
            slides_content = self._convert_to_slides_format(notes, page_info)
            
            # Create Google Slides presentation
            result = self._create_google_slides_presentation(slides_content)
            
            return result
                
        except Exception as e:
            logger.error(f"Google Slides export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_to_obsidian(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to Obsidian-compatible markdown format"""
        try:
            # Enhance markdown for Obsidian
            obsidian_content = self._format_for_obsidian(notes, page_info)
            
            filename = f"smart_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            return {
                'success': True,
                'format': 'obsidian',
                'filename': filename,
                'data': obsidian_content.encode('utf-8'),
                'mimetype': 'text/markdown',
                'size': len(obsidian_content.encode('utf-8')),
                'instructions': 'Save to your Obsidian vault folder'
            }
        except Exception as e:
            logger.error(f"Obsidian export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_to_onenote(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to OneNote format (HTML-based)"""
        try:
            # OneNote accepts HTML format
            html_content = markdown.markdown(notes, extensions=['tables', 'fenced_code'])
            onenote_html = self._format_for_onenote(html_content, page_info)
            
            filename = f"smart_notes_onenote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            return {
                'success': True,
                'format': 'onenote',
                'filename': filename,
                'data': onenote_html.encode('utf-8'),
                'mimetype': 'text/html',
                'size': len(onenote_html.encode('utf-8')),
                'instructions': 'Import into OneNote by opening this HTML file'
            }
        except Exception as e:
            logger.error(f"OneNote export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_to_evernote(self, notes: str, page_info: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Export to Evernote format (ENEX)"""
        try:
            # Create ENEX format
            enex_content = self._create_enex_format(notes, page_info)
            
            filename = f"smart_notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enex"
            
            return {
                'success': True,
                'format': 'evernote',
                'filename': filename,
                'data': enex_content.encode('utf-8'),
                'mimetype': 'application/xml',
                'size': len(enex_content.encode('utf-8')),
                'instructions': 'Import into Evernote using File > Import Notes'
            }
        except Exception as e:
            logger.error(f"Evernote export failed: {e}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods for format conversion
    
    def _generate_frontmatter(self, page_info: Dict[str, Any]) -> str:
        """Generate YAML frontmatter for markdown"""
        frontmatter = "---\n"
        frontmatter += f"title: {page_info.get('title', 'Smart Notes')}\n"
        frontmatter += f"source: {page_info.get('url', 'Unknown')}\n"
        frontmatter += f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        frontmatter += f"tags: [smart-notes, ai-generated]\n"
        frontmatter += "---\n"
        return frontmatter
    
    def _create_html_document(self, content: str, page_info: Dict[str, Any]) -> str:
        """Create a complete HTML document with styling"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_info.get('title', 'Smart Notes')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{ color: #2d3748; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #4a5568; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; }}
        h3 {{ color: #718096; }}
        ul {{ list-style-type: none; padding-left: 0; }}
        li {{ 
            margin: 8px 0; 
            padding: 8px 12px; 
            border-left: 3px solid #e2e8f0; 
            background: rgba(248, 250, 252, 0.7); 
        }}
        .metadata {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        code {{
            background: #f1f1f1;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
        }}
        pre {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="metadata">
        <strong>Source:</strong> <a href="{page_info.get('url', '')}">{page_info.get('title', 'Untitled')}</a><br>
        <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        <strong>Tool:</strong> Smart Notes AI
    </div>
    {content}
</body>
</html>"""
    
    def _parse_notes_structure(self, notes: str) -> Dict[str, Any]:
        """Parse the structure of notes for JSON export"""
        lines = notes.split('\n')
        structure = {
            'headers': [],
            'bullet_points': [],
            'sections': []
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line.lstrip('# ').strip()
                header = {'level': level, 'text': text}
                structure['headers'].append(header)
                
                if current_section:
                    structure['sections'].append(current_section)
                current_section = {'header': header, 'content': []}
                
            elif line.startswith('-') or any(line.startswith(emoji) for emoji in ['🔑', '✅', '⚠️', '✨', '❌']):
                bullet = {'text': line, 'type': 'bullet'}
                structure['bullet_points'].append(bullet)
                if current_section:
                    current_section['content'].append(bullet)
        
        if current_section:
            structure['sections'].append(current_section)
        
        return structure
    
    def _extract_sections(self, notes: str) -> List[Dict[str, Any]]:
        """Extract sections from notes"""
        # This would be more sophisticated in a real implementation
        sections = []
        current_section = None
        
        for line in notes.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': line.lstrip('# ').strip(),
                    'content': []
                }
            elif current_section and line:
                current_section['content'].append(line)
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _markdown_to_plaintext(self, markdown_text: str) -> str:
        """Convert markdown to plain text"""
        import re
        
        # Remove markdown formatting
        text = re.sub(r'^#+\s*', '', markdown_text, flags=re.MULTILINE)  # Headers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Italic
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Code blocks
        text = re.sub(r'`(.*?)`', r'\1', text)  # Inline code
        text = re.sub(r'^\s*[-*+]\s*', '• ', text, flags=re.MULTILINE)  # Bullets
        
        return text
    
    def _convert_to_notion_blocks(self, notes: str) -> List[Dict[str, Any]]:
        """Convert notes to Notion block format"""
        # This would implement the actual Notion API block format
        # For now, return a placeholder
        return [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": notes[:2000]}}]
                }
            }
        ]
    
    def _create_notion_page(self, title: str, blocks: List[Dict[str, Any]], parent_database_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a page in Notion"""
        # Placeholder for actual Notion API implementation
        return {
            'success': False,
            'error': 'Notion integration requires API implementation',
            'setup_required': True
        }
    
    def _convert_to_slides_format(self, notes: str, page_info: Dict[str, Any]) -> Dict[str, Any]:
        """Convert notes to Google Slides format"""
        # This would parse the notes and create slide content
        return {
            'title': page_info.get('title', 'Smart Notes Presentation'),
            'slides': []
        }
    
    def _create_google_slides_presentation(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Create Google Slides presentation"""
        # Placeholder for actual Google Slides API implementation
        return {
            'success': False,
            'error': 'Google Slides integration requires API implementation',
            'setup_required': True
        }
    
    def _format_for_obsidian(self, notes: str, page_info: Dict[str, Any]) -> str:
        """Format notes for Obsidian"""
        # Add Obsidian-specific features
        obsidian_notes = f"# {page_info.get('title', 'Smart Notes')}\n\n"
        obsidian_notes += f"Source:: [[{page_info.get('url', 'Unknown')}]]\n"
        obsidian_notes += f"Created:: {datetime.now().strftime('%Y-%m-%d')}\n"
        obsidian_notes += f"Tags:: #smart-notes #ai-generated\n\n"
        obsidian_notes += "---\n\n"
        obsidian_notes += notes
        
        # Add backlinks and connections
        obsidian_notes += "\n\n## Related\n"
        obsidian_notes += "- [[Smart Notes Index]]\n"
        obsidian_notes += "- [[AI Generated Notes]]\n"
        
        return obsidian_notes
    
    def _format_for_onenote(self, html_content: str, page_info: Dict[str, Any]) -> str:
        """Format HTML for OneNote import"""
        return f"""<?xml version="1.0" encoding="utf-8"?>
<html>
<head>
    <title>{page_info.get('title', 'Smart Notes')}</title>
</head>
<body>
    <div style="font-family: Segoe UI; margin: 20px;">
        <h1>{page_info.get('title', 'Smart Notes')}</h1>
        <p><strong>Source:</strong> {page_info.get('url', 'Unknown')}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr/>
        {html_content}
    </div>
</body>
</html>"""
    
    def _create_enex_format(self, notes: str, page_info: Dict[str, Any]) -> str:
        """Create Evernote ENEX format"""
        html_content = markdown.markdown(notes, extensions=['tables', 'fenced_code'])
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export export-date="{datetime.now().strftime('%Y%m%dT%H%M%SZ')}" application="Smart Notes" version="2.0">
    <note>
        <title>{page_info.get('title', 'Smart Notes')}</title>
        <content><![CDATA[<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/></head>
<body>
    <div>Source: {page_info.get('url', 'Unknown')}</div>
    <div>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    <hr/>
    {html_content}
</body></html>]]></content>
        <created>{datetime.now().strftime('%Y%m%dT%H%M%SZ')}</created>
        <source-url>{page_info.get('url', '')}</source-url>
    </note>
</en-export>"""

    def get_supported_formats(self) -> List[Dict[str, Any]]:
        """Get list of supported export formats with metadata"""
        return [
            {
                'id': 'pdf',
                'name': 'PDF Document',
                'description': 'Professional PDF with formatting',
                'icon': '📄',
                'requires_setup': False
            },
            {
                'id': 'markdown',
                'name': 'Markdown',
                'description': 'Universal markdown format',
                'icon': '📝',
                'requires_setup': False
            },
            {
                'id': 'html',
                'name': 'HTML Document',
                'description': 'Styled web page',
                'icon': '🌐',
                'requires_setup': False
            },
            {
                'id': 'json',
                'name': 'JSON Data',
                'description': 'Structured data format',
                'icon': '📊',
                'requires_setup': False
            },
            {
                'id': 'txt',
                'name': 'Plain Text',
                'description': 'Simple text file',
                'icon': '📄',
                'requires_setup': False
            },
            {
                'id': 'notion',
                'name': 'Notion',
                'description': 'Export directly to Notion',
                'icon': '🗒️',
                'requires_setup': True
            },
            {
                'id': 'google_slides',
                'name': 'Google Slides',
                'description': 'Create presentation',
                'icon': '📊',
                'requires_setup': True
            },
            {
                'id': 'obsidian',
                'name': 'Obsidian',
                'description': 'Enhanced markdown for Obsidian',
                'icon': '🔗',
                'requires_setup': False
            },
            {
                'id': 'onenote',
                'name': 'OneNote',
                'description': 'Microsoft OneNote format',
                'icon': '📓',
                'requires_setup': False
            },
            {
                'id': 'evernote',
                'name': 'Evernote',
                'description': 'Evernote ENEX format',
                'icon': '🐘',
                'requires_setup': False
            }
        ]
