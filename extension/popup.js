// Smart Notes Extension - Popup Script
class SmartNotesPopup {
    constructor() {
        this.backendUrl = 'http://localhost:5000';
        this.currentNotes = '';
        this.currentPageInfo = {};
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        document.getElementById('generateNotes').addEventListener('click', () => this.generateNotes());
        document.getElementById('copyNotes').addEventListener('click', () => this.copyNotes());
        document.getElementById('downloadPdf').addEventListener('click', () => this.downloadPdf());
        document.getElementById('settingsLink').addEventListener('click', (e) => {
            e.preventDefault();
            this.showSettings();
        });
    }

    async generateNotes() {
        try {
            this.showLoading();
            
            // Get current tab information
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            this.currentPageInfo = {
                url: tab.url,
                title: tab.title,
                timestamp: new Date().toLocaleString()
            };

            // Extract page content using content script
            const [result] = await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                function: () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style, noscript');
                    scripts.forEach(el => el.remove());

                    // Get main content
                    let content = '';
                    
                    // Try to find main content areas
                    const contentSelectors = [
                        'article',
                        '[role="main"]',
                        'main',
                        '.content',
                        '.post-content',
                        '.entry-content',
                        '.article-body',
                        '#content',
                        '.main-content'
                    ];

                    let mainContent = null;
                    for (const selector of contentSelectors) {
                        mainContent = document.querySelector(selector);
                        if (mainContent) break;
                    }

                    // If no main content found, use body
                    if (!mainContent) {
                        mainContent = document.body;
                    }

                    // Extract text content
                    content = mainContent.innerText || mainContent.textContent || '';
                    
                    // Clean up the text
                    content = content
                        .replace(/\s+/g, ' ')  // Replace multiple spaces with single space
                        .replace(/\n+/g, ' ')  // Replace newlines with spaces
                        .trim();

                    return {
                        text: content,
                        wordCount: content.split(/\s+/).length
                    };
                }
            });

            if (!result || !result.result) {
                throw new Error('Failed to extract page content');
            }

            const pageContent = result.result;
            
            // Send content to backend for processing
            const response = await fetch(`${this.backendUrl}/generate-notes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: pageContent.text,
                    url: tab.url,
                    title: tab.title,
                    wordCount: pageContent.wordCount
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate notes');
            }

            const data = await response.json();
            this.currentNotes = data.notes;
            
            this.showResults();
            
        } catch (error) {
            console.error('Error generating notes:', error);
            this.showError(error.message || 'Failed to generate notes. Please try again.');
        }
    }


    async copyNotes() {
        try {
            await navigator.clipboard.writeText(this.currentNotes);
            this.showTemporaryMessage('Notes copied to clipboard!');
        } catch (error) {
            console.error('Failed to copy notes:', error);
            this.showTemporaryMessage('Failed to copy notes', true);
        }
    }

    async downloadPdf() {
        try {
            const response = await fetch(`${this.backendUrl}/download-pdf`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    notes: this.currentNotes,
                    pageInfo: this.currentPageInfo
                })
            });

            if (!response.ok) {
                throw new Error('Failed to generate PDF');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `smart-notes-${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            this.showTemporaryMessage('PDF downloaded successfully!');
        } catch (error) {
            console.error('Failed to download PDF:', error);
            this.showTemporaryMessage('Failed to download PDF', true);
        }
    }

    showLoading() {
        document.getElementById('generateNotes').style.display = 'none';
        document.getElementById('loading').style.display = 'block';
        document.getElementById('error').style.display = 'none';
        document.getElementById('results').style.display = 'none';
    }

    showResults() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'none';
        document.getElementById('results').style.display = 'block';
        
        // Display the notes with animation
        const notesContent = document.getElementById('notesContent');
        notesContent.classList.add('loading-animation');
        notesContent.innerHTML = this.formatNotes(this.currentNotes);
        
        // Display page info
        document.getElementById('pageUrl').textContent = this.currentPageInfo.url;
        document.getElementById('timestamp').textContent = this.currentPageInfo.timestamp;
        
        // Show generate button again
        document.getElementById('generateNotes').style.display = 'flex';
        
        // Add a small delay to show the enhancement
        setTimeout(() => {
            this.showTemporaryMessage('✨ Enhanced structured notes generated!');
        }, 500);
    }

    showError(message) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('results').style.display = 'none';
        document.getElementById('generateNotes').style.display = 'flex';
        
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('error').style.display = 'block';
    }

    formatNotes(notes) {
        // Convert markdown-style notes to HTML with proper formatting
        return this.convertMarkdownToHTML(notes);
    }
    
    convertMarkdownToHTML(markdown) {
        let html = markdown;
        
        // Convert headers
        html = html.replace(/^### (.*$)/gim, '<h3 class="note-h3">$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2 class="note-h2">$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1 class="note-h1">$1</h1>');
        
        // Convert bold text
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="note-bold">$1</strong>');
        
        // Convert bullet points with icons
        html = html.replace(/^- (.*$)/gim, '<li class="note-bullet">$1</li>');
        html = html.replace(/^🔑 (.*$)/gim, '<li class="note-key">🔑 $1</li>');
        html = html.replace(/^✅ (.*$)/gim, '<li class="note-action">✅ $1</li>');
        html = html.replace(/^⚠️ (.*$)/gim, '<li class="note-warning">⚠️ $1</li>');
        html = html.replace(/^✨ (.*$)/gim, '<li class="note-benefit">✨ $1</li>');
        html = html.replace(/^❌ (.*$)/gim, '<li class="note-problem">❌ $1</li>');
        
        // Convert code blocks
        html = html.replace(/```([\s\S]*?)```/g, '<pre class="note-code">$1</pre>');
        
        // Convert horizontal rules
        html = html.replace(/^---$/gim, '<hr class="note-divider">');
        
        // Convert emphasis text
        html = html.replace(/\*(.*?)\*/g, '<em class="note-emphasis">$1</em>');
        
        // Wrap consecutive list items in ul tags
        html = html.replace(/((<li[^>]*>.*?<\/li>\s*)+)/g, '<ul class="note-list">$1</ul>');
        
        // Convert remaining paragraphs
        const lines = html.split('\n');
        const processedLines = lines.map(line => {
            const trimmed = line.trim();
            if (!trimmed) return '<br>';
            if (trimmed.startsWith('<') && trimmed.endsWith('>')) return line;
            if (!trimmed.match(/^<(h[1-6]|li|ul|pre|hr)/)) {
                return `<p class="note-paragraph">${trimmed}</p>`;
            }
            return line;
        });
        
        return processedLines.join('\n');
    }

    showTemporaryMessage(message, isError = false) {
        const messageEl = document.createElement('div');
        messageEl.textContent = message;
        messageEl.style.cssText = `
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            ${isError ? 'background: #d63031; color: white;' : 'background: #00b894; color: white;'}
        `;
        
        document.body.appendChild(messageEl);
        
        setTimeout(() => {
            if (document.body.contains(messageEl)) {
                document.body.removeChild(messageEl);
            }
        }, 3000);
    }

    showSettings() {
        // For now, just show an alert. Could be expanded to a settings page
        alert('Settings panel coming soon! You can configure your Hugging Face API key and other preferences.');
    }
}

// Initialize the popup when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SmartNotesPopup();
});
