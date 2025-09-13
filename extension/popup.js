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
        
        // Read Aloud event listeners
        document.getElementById('readAloudPage').addEventListener('click', () => this.showReadAloudOptions());
        document.getElementById('closeReadAloud').addEventListener('click', () => this.hideReadAloudOptions());
        document.getElementById('playButton').addEventListener('click', () => this.startReading());
        document.getElementById('pauseButton').addEventListener('click', () => this.pauseReading());
        document.getElementById('stopButton').addEventListener('click', () => this.stopReading());
        
        // Voice and control listeners
        document.getElementById('speechRate').addEventListener('input', (e) => this.updateRateDisplay(e.target.value));
        document.getElementById('speechPitch').addEventListener('input', (e) => this.updatePitchDisplay(e.target.value));
        document.getElementById('speechVolume').addEventListener('input', (e) => this.updateVolumeDisplay(e.target.value));
        
        // Initialize speech synthesis
        this.initializeSpeechSynthesis();
        
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
            
            this.showTranslationStatus(`🔄 Translating to ${targetLanguage}...`, 'loading');
            this.addTranslationProgressBar();
            
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
                let errorMessage = 'Translation failed';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || 'Translation failed';
                } catch (parseError) {
                    console.error('Failed to parse error response:', parseError);
                    if (response.status === 500) {
                        errorMessage = 'Translation service error. Please check if the backend server is properly configured.';
                    } else if (response.status === 503) {
                        errorMessage = 'Translation service unavailable. Please check your internet connection.';
                    } else {
                        errorMessage = `Translation failed (HTTP ${response.status})`;
                    }
                }
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Translation failed');
            }
            
            this.showTranslationStatus('🎨 Applying translation with visual highlighting...', 'loading');
            
            // Apply translation to the page with progressive highlighting
            await this.applyTranslationWithHighlighting(tab.id, data.translated_content, targetLanguage);
            
            this.showTranslationStatus(`✨ Page translated to ${targetLanguage} with visual highlighting!`, 'success');
            this.removeTranslationProgressBar();
            
            // Update current language for read aloud feature
            this.currentLanguage = this.getLanguageCodeFromName(targetLanguage);
            
            // Show read aloud option for translated content
            this.showTemporaryMessage('🔊 Now you can use Read Aloud in ' + targetLanguage + '!', false, 4000);
            
            // Hide translation options after successful translation
            setTimeout(() => {
                this.hideTranslateOptions();
            }, 2000);
            
        } catch (error) {
            console.error('Translation error:', error);
            this.showTranslationStatus(`✗ Translation failed: ${error.message}`, 'error');
            this.removeTranslationProgressBar(); // Clean up progress bar on error
        } finally {
            // Reset button state
            const translateBtn = document.getElementById('startTranslation');
            translateBtn.disabled = false;
            translateBtn.innerHTML = '<span class="btn-icon">🔄</span>Start Translation';
        }
    }
    
    async applyTranslationWithHighlighting(tabId, translatedContent, targetLanguage) {
        try {
            // First, inject the highlighting styles
            await chrome.scripting.insertCSS({
                target: { tabId: tabId },
                css: `
                    .smart-notes-translating {
                        background: linear-gradient(90deg, #3498db, #74b9ff) !important;
                        color: white !important;
                        padding: 2px 4px !important;
                        border-radius: 3px !important;
                        transition: all 0.3s ease !important;
                        box-shadow: 0 2px 4px rgba(52, 152, 219, 0.3) !important;
                        animation: translationPulse 1s infinite alternate !important;
                    }
                    
                    .smart-notes-translated {
                        background: linear-gradient(90deg, #27ae60, #00b894) !important;
                        color: white !important;
                        padding: 2px 4px !important;
                        border-radius: 3px !important;
                        transition: all 0.5s ease !important;
                        box-shadow: 0 2px 4px rgba(39, 174, 96, 0.3) !important;
                    }
                    
                    .smart-notes-translation-fade {
                        background: transparent !important;
                        color: inherit !important;
                        padding: 0 !important;
                        border-radius: 0 !important;
                        box-shadow: none !important;
                        transition: all 1s ease !important;
                    }
                    
                    @keyframes translationPulse {
                        0% { opacity: 0.8; transform: scale(1); }
                        100% { opacity: 1; transform: scale(1.02); }
                    }
                    
                    .smart-notes-progress-bar {
                        position: fixed !important;
                        top: 0 !important;
                        left: 0 !important;
                        height: 4px !important;
                        background: linear-gradient(90deg, #3498db, #74b9ff) !important;
                        z-index: 10001 !important;
                        transition: width 0.3s ease !important;
                        box-shadow: 0 2px 10px rgba(52, 152, 219, 0.5) !important;
                    }
                `
            });
            
            // Apply translation with progressive highlighting
            await chrome.scripting.executeScript({
                target: { tabId: tabId },
                function: (translatedContent, targetLang) => {
                    return new Promise((resolve) => {
                        // Create progress bar
                        const progressBar = document.createElement('div');
                        progressBar.className = 'smart-notes-progress-bar';
                        progressBar.style.width = '0%';
                        document.body.appendChild(progressBar);
                        
                        // Enhanced function to translate with highlighting
                        function translateWithHighlighting(translatedText) {
                            const textNodes = [];
                            const originalTexts = [];
                            
                            // Get all text nodes
                            const walker = document.createTreeWalker(
                                document.documentElement,
                                NodeFilter.SHOW_TEXT,
                                {
                                    acceptNode: function(node) {
                                        if (node.parentElement && 
                                            ['SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK', 'HEAD'].includes(node.parentElement.tagName)) {
                                            return NodeFilter.FILTER_REJECT;
                                        }
                                        
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
                            
                            // Split content for mapping
                            const translatedWords = translatedText.split(/\s+/).filter(word => word.trim());
                            const originalWords = originalTexts.join(' ').split(/\s+/).filter(word => word.trim());
                            const wordRatio = translatedWords.length / originalWords.length;
                            
                            let wordIndex = 0;
                            let processedNodes = 0;
                            
                            // Process nodes progressively with highlighting
                            function processNextNode() {
                                if (processedNodes >= textNodes.length) {
                                    // All nodes processed, show completion
                                    setTimeout(() => {
                                        // Fade out highlighting
                                        document.querySelectorAll('.smart-notes-translated').forEach(el => {
                                            el.classList.add('smart-notes-translation-fade');
                                        });
                                        
                                        // Remove progress bar
                                        if (progressBar.parentElement) {
                                            progressBar.parentElement.removeChild(progressBar);
                                        }
                                        
                                        // Add completion indicator
                                        const indicator = document.createElement('div');
                                        indicator.innerHTML = `🌐 Page translated to ${targetLang} (${textNodes.length} nodes)`;
                                        indicator.style.cssText = `
                                            position: fixed;
                                            top: 20px;
                                            right: 20px;
                                            background: linear-gradient(135deg, #27ae60, #00b894);
                                            color: white;
                                            padding: 12px 16px;
                                            border-radius: 8px;
                                            font-size: 14px;
                                            z-index: 10002;
                                            box-shadow: 0 4px 20px rgba(39, 174, 96, 0.3);
                                            max-width: 300px;
                                            animation: slideInRight 0.5s ease;
                                        `;
                                        
                                        // Add slide-in animation
                                        const style = document.createElement('style');
                                        style.textContent = `
                                            @keyframes slideInRight {
                                                from { transform: translateX(100%); opacity: 0; }
                                                to { transform: translateX(0); opacity: 1; }
                                            }
                                        `;
                                        document.head.appendChild(style);
                                        document.body.appendChild(indicator);
                                        
                                        // Remove indicator after 5 seconds
                                        setTimeout(() => {
                                            if (indicator.parentElement) {
                                                indicator.style.transform = 'translateX(100%)';
                                                indicator.style.opacity = '0';
                                                setTimeout(() => {
                                                    if (indicator.parentElement) {
                                                        indicator.parentElement.removeChild(indicator);
                                                    }
                                                    if (style.parentElement) {
                                                        style.parentElement.removeChild(style);
                                                    }
                                                }, 300);
                                            }
                                        }, 5000);
                                        
                                        // Remove highlighting classes after fade
                                        setTimeout(() => {
                                            document.querySelectorAll('.smart-notes-translation-fade').forEach(el => {
                                                el.classList.remove('smart-notes-translated', 'smart-notes-translation-fade');
                                            });
                                        }, 1000);
                                    }, 1000);
                                    
                                    resolve(textNodes.length);
                                    return;
                                }
                                
                                const node = textNodes[processedNodes];
                                const originalNodeText = node.nodeValue.trim();
                                const nodeWords = originalNodeText.split(/\s+/).filter(word => word.trim());
                                
                                if (nodeWords.length > 0) {
                                    // Wrap the node in a span for highlighting
                                    const parent = node.parentElement;
                                    if (parent && !parent.classList.contains('smart-notes-translating')) {
                                        const span = document.createElement('span');
                                        span.className = 'smart-notes-translating';
                                        span.textContent = originalNodeText;
                                        
                                        // Replace text node with highlighted span
                                        parent.replaceChild(span, node);
                                        
                                        // Calculate translation for this node
                                        const expectedTranslatedWords = Math.ceil(nodeWords.length * wordRatio);
                                        const endIndex = Math.min(wordIndex + expectedTranslatedWords, translatedWords.length);
                                        const nodeTranslatedWords = translatedWords.slice(wordIndex, endIndex);
                                        
                                        if (nodeTranslatedWords.length > 0) {
                                            let newText = nodeTranslatedWords.join(' ');
                                            
                                            // Preserve punctuation
                                            if (originalNodeText.endsWith('.')) newText += '.';
                                            else if (originalNodeText.endsWith('!')) newText += '!';
                                            else if (originalNodeText.endsWith('?')) newText += '?';
                                            else if (originalNodeText.endsWith(',')) newText += ',';
                                            else if (originalNodeText.endsWith(':')) newText += ':';
                                            else if (originalNodeText.endsWith(';')) newText += ';';
                                            
                                            // Animate translation
                                            setTimeout(() => {
                                                span.textContent = newText;
                                                span.classList.remove('smart-notes-translating');
                                                span.classList.add('smart-notes-translated');
                                                wordIndex = endIndex;
                                            }, 200);
                                        }
                                    }
                                }
                                
                                processedNodes++;
                                
                                // Update progress bar
                                const progress = (processedNodes / textNodes.length) * 100;
                                progressBar.style.width = progress + '%';
                                
                                // Process next node after a short delay
                                setTimeout(processNextNode, 50); // 50ms delay between nodes
                            }
                            
                            // Start processing
                            processNextNode();
                        }
                        
                        // Start translation with highlighting
                        translateWithHighlighting(translatedContent);
                    });
                },
                args: [translatedContent, targetLanguage]
            });
            
        } catch (error) {
            console.error('Error applying translation with highlighting:', error);
            throw error;
        }
    }
    
    addTranslationProgressBar() {
        // Add progress bar to translation options
        const translateOptions = document.getElementById('translateOptions');
        const existingProgress = translateOptions.querySelector('.translation-progress');
        
        if (!existingProgress) {
            const progressContainer = document.createElement('div');
            progressContainer.className = 'translation-progress';
            progressContainer.innerHTML = `
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" id="translationProgressFill"></div>
                </div>
                <div class="progress-text">🔄 Processing translation...</div>
            `;
            
            translateOptions.appendChild(progressContainer);
            
            // Start progress animation
            const progressFill = document.getElementById('translationProgressFill');
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + 2, 95); // Don't go to 100% until complete
                if (progressFill) {
                    progressFill.style.width = progress + '%';
                }
                if (progress >= 95) {
                    clearInterval(progressInterval);
                }
            }, 100);
            
            // Store interval for cleanup
            this.progressInterval = progressInterval;
        }
    }
    
    removeTranslationProgressBar() {
        const progressContainer = document.querySelector('.translation-progress');
        if (progressContainer) {
            // Complete the progress bar first
            const progressFill = document.getElementById('translationProgressFill');
            if (progressFill) {
                progressFill.style.width = '100%';
            }
            
            // Remove after animation
            setTimeout(() => {
                if (progressContainer.parentElement) {
                    progressContainer.parentElement.removeChild(progressContainer);
                }
            }, 1000);
        }
        
        // Clean up interval
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
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
    
    // ============ READ ALOUD FUNCTIONALITY ============
    
    initializeSpeechSynthesis() {
        // Initialize speech synthesis variables
        this.speechSynthesis = window.speechSynthesis;
        this.currentUtterance = null;
        this.speechQueue = [];
        this.isReading = false;
        this.isPaused = false;
        this.currentChunkIndex = 0;
        this.currentLanguage = 'en';
        this.pageTextChunks = [];
        
        // Load available voices
        this.loadVoices();
        
        // Update voices when they change (some browsers load voices asynchronously)
        if (this.speechSynthesis.onvoiceschanged !== undefined) {
            this.speechSynthesis.onvoiceschanged = () => this.loadVoices();
        }
    }
    
    loadVoices() {
        const voices = this.speechSynthesis.getVoices();
        const voiceSelect = document.getElementById('voiceSelect');
        
        // Clear existing options
        voiceSelect.innerHTML = '';
        
        if (voices.length === 0) {
            voiceSelect.innerHTML = '<option value="">Loading voices...</option>';
            return;
        }
        
        // Group voices by language
        const voicesByLanguage = {};
        voices.forEach((voice, index) => {
            const lang = voice.lang.split('-')[0]; // Get base language code
            if (!voicesByLanguage[lang]) {
                voicesByLanguage[lang] = [];
            }
            voicesByLanguage[lang].push({ voice, index });
        });
        
        // Add default option
        voiceSelect.innerHTML = '<option value="">Auto (Browser Default)</option>';
        
        // Add voices grouped by language
        Object.keys(voicesByLanguage).sort().forEach(lang => {
            const langName = this.getLanguageName(lang);
            const optgroup = document.createElement('optgroup');
            optgroup.label = langName;
            
            voicesByLanguage[lang].forEach(({ voice, index }) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `${voice.name} (${voice.lang})`;
                if (voice.default) {
                    option.textContent += ' - Default';
                }
                optgroup.appendChild(option);
            });
            
            voiceSelect.appendChild(optgroup);
        });
        
        console.log(`Loaded ${voices.length} voices`);
    }
    
    getLanguageName(langCode) {
        const languageNames = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'nl': 'Dutch',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'ru': 'Russian',
            'hi': 'Hindi'
        };
        return languageNames[langCode] || langCode.toUpperCase();
    }
    
    getLanguageCodeFromName(languageName) {
        const languageCodes = {
            'spanish': 'es',
            'french': 'fr',
            'german': 'de',
            'italian': 'it',
            'portuguese': 'pt',
            'dutch': 'nl',
            'chinese': 'zh',
            'japanese': 'ja',
            'korean': 'ko',
            'arabic': 'ar',
            'russian': 'ru',
            'hindi': 'hi'
        };
        return languageCodes[languageName.toLowerCase()] || 'en';
    }
    
    showReadAloudOptions() {
        const readAloudOptions = document.getElementById('readAloudOptions');
        readAloudOptions.style.display = 'block';
        
        // Refresh voices in case they weren't loaded initially
        this.loadVoices();
    }
    
    hideReadAloudOptions() {
        const readAloudOptions = document.getElementById('readAloudOptions');
        readAloudOptions.style.display = 'none';
        
        // Stop reading if currently active
        if (this.isReading) {
            this.stopReading();
        }
    }
    
    updateRateDisplay(value) {
        document.getElementById('rateValue').textContent = value + 'x';
    }
    
    updatePitchDisplay(value) {
        document.getElementById('pitchValue').textContent = value;
    }
    
    updateVolumeDisplay(value) {
        const percentage = Math.round(value * 100);
        document.getElementById('volumeValue').textContent = percentage + '%';
    }
    
    async startReading() {
        try {
            if (this.isPaused && this.speechSynthesis.paused) {
                // Resume if paused
                this.speechSynthesis.resume();
                this.isPaused = false;
                this.updatePlaybackControls('playing');
                this.showSpeechStatus('Resuming reading...', 'speaking');
                return;
            }
            
            // Extract page content for reading
            this.showSpeechStatus('Extracting page content...', 'speaking');
            
            // Get current tab and extract content
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            const [result] = await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                function: () => {
                    // Enhanced content extraction for reading
                    function extractReadableContent() {
                        const readableTexts = [];
                        
                        // Create tree walker to get all text nodes
                        const walker = document.createTreeWalker(
                            document.documentElement,
                            NodeFilter.SHOW_TEXT,
                            {
                                acceptNode: function(node) {
                                    // Skip technical elements
                                    if (node.parentElement && 
                                        ['SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK', 'HEAD'].includes(node.parentElement.tagName)) {
                                        return NodeFilter.FILTER_REJECT;
                                    }
                                    
                                    // Only meaningful content
                                    const text = node.nodeValue.trim();
                                    if (text.length > 5) { // Minimum length for readable content
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
                                readableTexts.push(text);
                            }
                        }
                        
                        // Join with periods to create natural reading flow
                        const fullText = readableTexts.join('. ').replace(/\.\.+/g, '.');
                        
                        return {
                            text: fullText,
                            chunks: readableTexts.length,
                            language: document.documentElement.lang || 'en'
                        };
                    }
                    
                    return extractReadableContent();
                }
            });
            
            if (!result || !result.result || !result.result.text) {
                throw new Error('No readable content found on this page');
            }
            
            const pageData = result.result;
            this.currentLanguage = pageData.language;
            
            // Split content into manageable chunks (about 200 characters each)
            this.pageTextChunks = this.splitTextIntoChunks(pageData.text, 200);
            
            console.log(`Prepared ${this.pageTextChunks.length} text chunks for reading`);
            
            // Auto-select appropriate voice based on page language
            this.selectVoiceForLanguage(this.currentLanguage);
            
            // Start reading from the beginning
            this.currentChunkIndex = 0;
            this.isReading = true;
            this.readNextChunk();
            
            this.updatePlaybackControls('playing');
            
        } catch (error) {
            console.error('Error starting read aloud:', error);
            this.showSpeechStatus(`Error: ${error.message}`, 'error');
        }
    }
    
    splitTextIntoChunks(text, maxLength) {
        const chunks = [];
        const sentences = text.split(/[\.!?]+/).filter(s => s.trim());
        let currentChunk = '';
        
        for (const sentence of sentences) {
            const trimmedSentence = sentence.trim();
            if (!trimmedSentence) continue;
            
            if (currentChunk.length + trimmedSentence.length + 2 <= maxLength) {
                currentChunk += (currentChunk ? '. ' : '') + trimmedSentence;
            } else {
                if (currentChunk) {
                    chunks.push(currentChunk + '.');
                }
                currentChunk = trimmedSentence;
            }
        }
        
        if (currentChunk) {
            chunks.push(currentChunk + '.');
        }
        
        return chunks.filter(chunk => chunk.trim().length > 5);
    }
    
    selectVoiceForLanguage(language) {
        const voices = this.speechSynthesis.getVoices();
        const voiceSelect = document.getElementById('voiceSelect');
        
        // Try to find a voice that matches the page language
        let bestVoice = null;
        let exactMatch = null;
        
        voices.forEach((voice, index) => {
            if (voice.lang.startsWith(language)) {
                if (voice.lang === language) {
                    exactMatch = index;
                } else if (!bestVoice) {
                    bestVoice = index;
                }
            }
        });
        
        const selectedVoiceIndex = exactMatch !== null ? exactMatch : bestVoice;
        
        if (selectedVoiceIndex !== null) {
            voiceSelect.value = selectedVoiceIndex;
            console.log(`Auto-selected voice: ${voices[selectedVoiceIndex].name} for language: ${language}`);
        }
    }
    
    readNextChunk() {
        if (!this.isReading || this.currentChunkIndex >= this.pageTextChunks.length) {
            this.stopReading();
            return;
        }
        
        const chunk = this.pageTextChunks[this.currentChunkIndex];
        const utterance = new SpeechSynthesisUtterance(chunk);
        
        // Apply voice settings
        const voiceSelect = document.getElementById('voiceSelect');
        const selectedVoiceIndex = voiceSelect.value;
        
        if (selectedVoiceIndex && selectedVoiceIndex !== '') {
            const voices = this.speechSynthesis.getVoices();
            utterance.voice = voices[selectedVoiceIndex];
        }
        
        // Apply speech settings
        utterance.rate = parseFloat(document.getElementById('speechRate').value);
        utterance.pitch = parseFloat(document.getElementById('speechPitch').value);
        utterance.volume = parseFloat(document.getElementById('speechVolume').value);
        
        // Event handlers
        utterance.onstart = () => {
            this.showSpeechStatus('Reading...', 'speaking');
            this.updateCurrentText(chunk);
        };
        
        utterance.onend = () => {
            if (this.isReading) {
                this.currentChunkIndex++;
                this.updateProgress();
                // Small delay between chunks for better listening experience
                setTimeout(() => this.readNextChunk(), 100);
            }
        };
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event);
            this.showSpeechStatus('Error occurred during reading', 'error');
            this.stopReading();
        };
        
        this.currentUtterance = utterance;
        this.speechSynthesis.speak(utterance);
    }
    
    pauseReading() {
        if (this.isReading && !this.isPaused) {
            this.speechSynthesis.pause();
            this.isPaused = true;
            this.updatePlaybackControls('paused');
            this.showSpeechStatus('Reading paused', 'paused');
        }
    }
    
    stopReading() {
        this.speechSynthesis.cancel();
        this.isReading = false;
        this.isPaused = false;
        this.currentChunkIndex = 0;
        this.currentUtterance = null;
        
        this.updatePlaybackControls('stopped');
        this.showSpeechStatus('Ready to read...', '');
        this.updateCurrentText('Ready to read...');
        this.updateProgress(0);
    }
    
    updatePlaybackControls(state) {
        const playButton = document.getElementById('playButton');
        const pauseButton = document.getElementById('pauseButton');
        const stopButton = document.getElementById('stopButton');
        
        switch (state) {
            case 'playing':
                playButton.disabled = true;
                pauseButton.disabled = false;
                stopButton.disabled = false;
                playButton.innerHTML = '<span class="btn-icon">▶️</span>Playing';
                break;
            case 'paused':
                playButton.disabled = false;
                pauseButton.disabled = true;
                stopButton.disabled = false;
                playButton.innerHTML = '<span class="btn-icon">▶️</span>Resume';
                break;
            case 'stopped':
            default:
                playButton.disabled = false;
                pauseButton.disabled = true;
                stopButton.disabled = true;
                playButton.innerHTML = '<span class="btn-icon">▶️</span>Play';
                break;
        }
    }
    
    updateProgress(progress = null) {
        if (progress !== null) {
            const progressFill = document.getElementById('progressFill');
            progressFill.style.width = progress + '%';
        } else if (this.pageTextChunks.length > 0) {
            const progressPercent = (this.currentChunkIndex / this.pageTextChunks.length) * 100;
            const progressFill = document.getElementById('progressFill');
            progressFill.style.width = progressPercent + '%';
        }
    }
    
    updateCurrentText(text) {
        const currentTextEl = document.getElementById('currentText');
        // Truncate long text for display
        const displayText = text.length > 60 ? text.substring(0, 57) + '...' : text;
        currentTextEl.textContent = displayText;
    }
    
    showSpeechStatus(message, type = '') {
        // Remove existing status if any
        const existingStatus = document.querySelector('.speech-status');
        if (existingStatus) {
            existingStatus.remove();
        }
        
        if (type) {
            // Create new status element
            const statusEl = document.createElement('div');
            statusEl.className = `speech-status ${type}`;
            statusEl.textContent = message;
            
            // Add to read aloud options
            const readAloudOptions = document.getElementById('readAloudOptions');
            readAloudOptions.appendChild(statusEl);
            
            // Auto-remove error messages after 5 seconds
            if (type === 'error') {
                setTimeout(() => {
                    if (statusEl.parentElement) {
                        statusEl.remove();
                    }
                }, 5000);
            }
        }
    }
}

// Initialize the popup when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SmartNotesPopup();
});
