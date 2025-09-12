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
        document.getElementById('settingsLink').addEventListener('click', (e) => {
            e.preventDefault();
            this.showSettings();
        });
        
        // Translation event listeners
        document.getElementById('translatePage').addEventListener('click', () => this.showTranslateOptions());
        document.getElementById('closeTranslate').addEventListener('click', () => this.hideTranslateOptions());
        document.getElementById('startTranslation').addEventListener('click', () => this.translatePage());
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.results-header')) {
                this.hideExportDropdown();
            }
        });
    }
    
    initializeExportListeners() {
        // Initialize export-related event listeners (called after results are shown)
        const copyButton = document.getElementById('copyNotes');
        const exportButton = document.getElementById('exportMenu');
        
        console.log('Initializing export listeners', { copyButton, exportButton });
        
        if (copyButton) {
            copyButton.removeEventListener('click', this.copyNotesHandler);
            this.copyNotesHandler = () => this.copyNotes();
            copyButton.addEventListener('click', this.copyNotesHandler);
        }
        
        if (exportButton) {
            exportButton.removeEventListener('click', this.toggleExportHandler);
            this.toggleExportHandler = () => this.toggleExportDropdown();
            exportButton.addEventListener('click', this.toggleExportHandler);
            console.log('Export button listener attached');
        }
        
        // Handle export option clicks
        document.querySelectorAll('.export-option').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const format = e.currentTarget.getAttribute('data-format');
                if (!e.currentTarget.disabled) {
                    this.exportNotes(format);
                }
            });
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

    toggleExportDropdown() {
        const dropdown = document.getElementById('exportDropdown');
        const button = document.getElementById('exportMenu');
        
        if (dropdown.style.display === 'none' || dropdown.style.display === '') {
            this.showExportDropdown();
        } else {
            this.hideExportDropdown();
        }
    }
    
    showExportDropdown() {
        const dropdown = document.getElementById('exportDropdown');
        const button = document.getElementById('exportMenu');
        
        console.log('Showing export dropdown', dropdown, button);
        dropdown.style.display = 'block';
        button.classList.add('active');
    }
    
    hideExportDropdown() {
        const dropdown = document.getElementById('exportDropdown');
        const button = document.getElementById('exportMenu');
        
        dropdown.style.display = 'none';
        button.classList.remove('active');
    }
    
    async exportNotes(format) {
        try {
            this.hideExportDropdown();
            
            // Show loading message
            this.showTemporaryMessage(`Exporting to ${format.toUpperCase()}...`);
            
            const response = await fetch(`${this.backendUrl}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    notes: this.currentNotes,
                    pageInfo: this.currentPageInfo,
                    format: format,
                    options: {}
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Export failed');
            }
            
            // Check if this is a file download or a service response
            const contentType = response.headers.get('content-type');
            
            if (contentType && (contentType.includes('application/') || contentType.includes('text/'))) {
                // File download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                // Get filename from content-disposition header or generate one
                const disposition = response.headers.get('content-disposition');
                let filename = `smart_notes_${format}_${Date.now()}`;
                
                if (disposition && disposition.includes('filename=')) {
                    filename = disposition.split('filename=')[1].replace(/"/g, '');
                } else {
                    // Add appropriate extension
                    const extensions = {
                        'pdf': '.pdf',
                        'markdown': '.md',
                        'html': '.html',
                        'txt': '.txt',
                        'json': '.json',
                        'obsidian': '.md',
                        'onenote': '.html',
                        'evernote': '.enex'
                    };
                    filename += extensions[format] || '';
                }
                
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showTemporaryMessage(`${format.toUpperCase()} exported successfully!`);
            } else {
                // Service response (e.g., Notion, Google Slides)
                const data = await response.json();
                
                if (data.success) {
                    if (data.url) {
                        // Open the created resource
                        chrome.tabs.create({ url: data.url });
                        this.showTemporaryMessage(`Exported to ${format} successfully!`);
                    } else {
                        this.showTemporaryMessage(data.message || 'Export completed successfully!');
                    }
                } else {
                    throw new Error(data.error || 'Export failed');
                }
            }
            
        } catch (error) {
            console.error(`Failed to export to ${format}:`, error);
            
            if (error.message.includes('requires API setup') || error.message.includes('setup_required')) {
                this.showSetupRequiredMessage(format);
            } else {
                this.showTemporaryMessage(`Failed to export to ${format}: ${error.message}`, true);
            }
        }
    }
    
    showSetupRequiredMessage(format) {
        const setupMessages = {
            'notion': 'Notion export requires API setup. Add NOTION_API_TOKEN to your backend environment.',
            'google_slides': 'Google Slides export requires API setup. Add GOOGLE_CREDENTIALS_JSON to your backend environment.'
        };
        
        const message = setupMessages[format] || `${format} export requires additional setup.`;
        this.showTemporaryMessage(message, true, 5000);
    }
    
    // Legacy PDF download method (keeping for compatibility)
    async downloadPdf() {
        await this.exportNotes('pdf');
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
        
        // Initialize export listeners now that the elements exist
        this.initializeExportListeners();
        
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

    showTemporaryMessage(message, isError = false, duration = 3000) {
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
            max-width: 300px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            ${isError ? 'background: #d63031; color: white;' : 'background: #00b894; color: white;'}
        `;
        
        document.body.appendChild(messageEl);
        
        setTimeout(() => {
            if (document.body.contains(messageEl)) {
                document.body.removeChild(messageEl);
            }
        }, duration);
    }

    showSettings() {
        // For now, just show an alert. Could be expanded to a settings page
        alert('Settings panel coming soon! You can configure your Hugging Face API key and other preferences.');
    }
    
    showTranslateOptions() {
        const translateOptions = document.getElementById('translateOptions');
        translateOptions.style.display = 'block';
    }
    
    hideTranslateOptions() {
        const translateOptions = document.getElementById('translateOptions');
        translateOptions.style.display = 'none';
    }
    
    async translatePage() {
        try {
            const targetLanguage = document.getElementById('targetLanguage').value;
            const translateBtn = document.getElementById('startTranslation');
            
            // Show loading state
            translateBtn.disabled = true;
            translateBtn.innerHTML = '<span class="btn-icon">⏳</span>Translating...';
            
            this.showTranslationStatus('Extracting page content...', 'loading');
            
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
                    // Function to extract all text content from the entire page
                    function extractAllTextContent() {
                        const textContent = [];
                        const textNodes = [];
                        
                        // Create a tree walker to traverse all text nodes
                        const walker = document.createTreeWalker(
                            document.documentElement, // Start from html element to get everything
                            NodeFilter.SHOW_TEXT,
                            {
                                acceptNode: function(node) {
                                    // Skip script, style, noscript elements
                                    if (node.parentElement && 
                                        ['SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK', 'HEAD'].includes(node.parentElement.tagName)) {
                                        return NodeFilter.FILTER_REJECT;
                                    }
                                    
                                    // Only include nodes with meaningful text content
                                    const text = node.nodeValue.trim();
                                    if (text.length > 0) {
                                        return NodeFilter.FILTER_ACCEPT;
                                    }
                                    return NodeFilter.FILTER_REJECT;
                                }
                            }
                        );
                        
                        let node;
                        while (node = walker.nextNode()) {
                            const text = node.nodeValue.trim();
                            if (text) {
                                textContent.push(text);
                                textNodes.push({
                                    node: node,
                                    text: text,
                                    parent: node.parentElement ? node.parentElement.tagName : 'UNKNOWN'
                                });
                            }
                        }
                        
                        return {
                            fullText: textContent.join(' '),
                            textNodes: textNodes.length,
                            totalElements: document.querySelectorAll('*').length
                        };
                    }
                    
                    const extracted = extractAllTextContent();
                    return {
                        text: extracted.fullText,
                        wordCount: extracted.fullText.split(/\s+/).length,
                        textNodes: extracted.textNodes,
                        totalElements: extracted.totalElements
                    };
                }
            });
            
            if (!result || !result.result || !result.result.text) {
                throw new Error('Failed to extract page content');
            }
            
            const pageContent = result.result;
            
            this.showTranslationStatus(`Translating to ${targetLanguage}...`, 'loading');
            
            // Send content to backend for translation
            const response = await fetch(`${this.backendUrl}/translate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: pageContent.text,
                    target_language: targetLanguage,
                    pageInfo: this.currentPageInfo
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Translation failed');
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Translation failed');
            }
            
            this.showTranslationStatus('Applying translation to page...', 'loading');
            
            // Apply translation to the page
            await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                function: (translatedContent) => {
                    // Enhanced function to translate the entire page
                    function translateEntirePage(translatedText) {
                        const textNodes = [];
                        const originalTexts = [];
                        
                        // Use same traversal logic as extraction to ensure we get all nodes
                        const walker = document.createTreeWalker(
                            document.documentElement, // Start from html element to get everything
                            NodeFilter.SHOW_TEXT,
                            {
                                acceptNode: function(node) {
                                    // Skip script, style, noscript elements
                                    if (node.parentElement && 
                                        ['SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK', 'HEAD'].includes(node.parentElement.tagName)) {
                                        return NodeFilter.FILTER_REJECT;
                                    }
                                    
                                    // Only include nodes with meaningful text content
                                    const text = node.nodeValue.trim();
                                    if (text.length > 0) {
                                        return NodeFilter.FILTER_ACCEPT;
                                    }
                                    return NodeFilter.FILTER_REJECT;
                                }
                            }
                        );
                        
                        let node;
                        while (node = walker.nextNode()) {
                            const text = node.nodeValue.trim();
                            if (text) {
                                textNodes.push(node);
                                originalTexts.push(text);
                            }
                        }
                        
                        console.log(`Found ${textNodes.length} text nodes to translate`);
                        
                        // Split translated content into words for better distribution
                        const translatedWords = translatedText.split(/\s+/).filter(word => word.trim());
                        const originalWords = originalTexts.join(' ').split(/\s+/).filter(word => word.trim());
                        
                        console.log(`Original words: ${originalWords.length}, Translated words: ${translatedWords.length}`);
                        
                        // Create a more sophisticated mapping
                        let wordIndex = 0;
                        const wordRatio = translatedWords.length / originalWords.length;
                        
                        textNodes.forEach((node, nodeIndex) => {
                            const originalNodeText = node.nodeValue.trim();
                            const nodeWords = originalNodeText.split(/\s+/).filter(word => word.trim());
                            
                            if (nodeWords.length > 0) {
                                // Calculate how many translated words this node should get
                                const expectedTranslatedWords = Math.ceil(nodeWords.length * wordRatio);
                                const endIndex = Math.min(wordIndex + expectedTranslatedWords, translatedWords.length);
                                
                                // Get the translated words for this node
                                const nodeTranslatedWords = translatedWords.slice(wordIndex, endIndex);
                                
                                if (nodeTranslatedWords.length > 0) {
                                    // Preserve original spacing and punctuation patterns
                                    let newText = nodeTranslatedWords.join(' ');
                                    
                                    // Try to preserve some formatting patterns
                                    if (originalNodeText.endsWith('.')) newText += '.';
                                    else if (originalNodeText.endsWith('!')) newText += '!';
                                    else if (originalNodeText.endsWith('?')) newText += '?';
                                    else if (originalNodeText.endsWith(',')) newText += ',';
                                    else if (originalNodeText.endsWith(':')) newText += ':';
                                    else if (originalNodeText.endsWith(';')) newText += ';';
                                    
                                    // Preserve leading/trailing whitespace from original
                                    const leadingWhitespace = node.nodeValue.match(/^\s*/)[0];
                                    const trailingWhitespace = node.nodeValue.match(/\s*$/)[0];
                                    
                                    node.nodeValue = leadingWhitespace + newText + trailingWhitespace;
                                    wordIndex = endIndex;
                                }
                            }
                        });
                        
                        return textNodes.length;
                    }
                    
                    // Perform the translation
                    const translatedNodeCount = translateEntirePage(translatedContent);
                    console.log(`Translated ${translatedNodeCount} text nodes`);
                    
                    // Add a visual indicator that the page has been translated
                    const indicator = document.createElement('div');
                    indicator.innerHTML = `🌐 Page translated (${translatedNodeCount} nodes)`;
                    indicator.style.cssText = `
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background: #00b894;
                        color: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        font-size: 12px;
                        z-index: 10000;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                        max-width: 200px;
                    `;
                    document.body.appendChild(indicator);
                    
                    // Remove indicator after 4 seconds
                    setTimeout(() => {
                        if (indicator.parentElement) {
                            indicator.parentElement.removeChild(indicator);
                        }
                    }, 4000);
                },
                args: [data.translated_content]
            });
            
            this.showTranslationStatus(`✓ Page translated to ${targetLanguage}!`, 'success');
            
            // Hide translation options after successful translation
            setTimeout(() => {
                this.hideTranslateOptions();
            }, 2000);
            
        } catch (error) {
            console.error('Translation error:', error);
            this.showTranslationStatus(`✗ Translation failed: ${error.message}`, 'error');
        } finally {
            // Reset button state
            const translateBtn = document.getElementById('startTranslation');
            translateBtn.disabled = false;
            translateBtn.innerHTML = '<span class="btn-icon">🔄</span>Start Translation';
        }
    }
    
    showTranslationStatus(message, type = 'loading') {
        // Remove existing status if any
        const existingStatus = document.querySelector('.translation-status');
        if (existingStatus) {
            existingStatus.remove();
        }
        
        // Create new status element
        const statusEl = document.createElement('div');
        statusEl.className = `translation-status ${type}`;
        statusEl.textContent = message;
        
        // Add to translate options
        const translateOptions = document.getElementById('translateOptions');
        translateOptions.appendChild(statusEl);
        
        // Auto-remove success/error messages after 5 seconds
        if (type !== 'loading') {
            setTimeout(() => {
                if (statusEl.parentElement) {
                    statusEl.remove();
                }
            }, 5000);
        }
    }
}

// Initialize the popup when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SmartNotesPopup();
});
