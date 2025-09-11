// Smart Notes Extension - Content Script
// This script runs in the context of web pages

class SmartNotesContent {
    constructor() {
        this.initializeContentScript();
    }

    initializeContentScript() {
        // Listen for messages from the popup
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'extractContent') {
                try {
                    const content = this.extractPageContent();
                    sendResponse({ success: true, content });
                } catch (error) {
                    sendResponse({ success: false, error: error.message });
                }
            }
        });

        // Add visual indicator when extension is active
        this.addExtensionIndicator();
    }

    extractPageContent() {
        // Create a copy of the document to avoid modifying the original
        const docClone = document.cloneNode(true);
        
        // Remove unwanted elements from the clone
        const unwantedElements = docClone.querySelectorAll(`
            script, style, noscript, nav, header, footer,
            .advertisement, .ads, .sidebar, .menu, .navigation,
            [class*="ad-"], [class*="advertisement"], [id*="ad-"],
            .social-share, .comments, .comment-section,
            .popup, .modal, .overlay
        `);
        
        unwantedElements.forEach(el => el.remove());

        // Try to find the main content area
        const contentSelectors = [
            'article',
            '[role="main"]',
            'main',
            '.content',
            '.post-content', 
            '.entry-content',
            '.article-body',
            '.article-content',
            '#content',
            '.main-content',
            '.page-content'
        ];

        let mainContent = null;
        for (const selector of contentSelectors) {
            mainContent = docClone.querySelector(selector);
            if (mainContent && mainContent.innerText.trim().length > 100) {
                break;
            }
        }

        // Fallback to body if no main content found
        if (!mainContent || mainContent.innerText.trim().length < 100) {
            mainContent = docClone.body;
        }

        // Extract and clean text
        let textContent = mainContent.innerText || mainContent.textContent || '';
        
        // Clean up the text
        textContent = textContent
            .replace(/\s+/g, ' ')  // Multiple spaces to single space
            .replace(/\n\s*\n/g, '\n')  // Multiple newlines to single
            .replace(/\t/g, ' ')  // Tabs to spaces
            .trim();

        // Extract metadata
        const metadata = this.extractPageMetadata();
        
        return {
            text: textContent,
            wordCount: textContent.split(/\s+/).filter(word => word.length > 0).length,
            characterCount: textContent.length,
            metadata: metadata,
            extractedAt: new Date().toISOString()
        };
    }

    extractPageMetadata() {
        const metadata = {
            title: document.title || '',
            url: window.location.href,
            domain: window.location.hostname,
            description: '',
            author: '',
            publishDate: '',
            keywords: []
        };

        // Extract meta description
        const descriptionMeta = document.querySelector('meta[name="description"]');
        if (descriptionMeta) {
            metadata.description = descriptionMeta.content;
        }

        // Extract author
        const authorMeta = document.querySelector('meta[name="author"]') || 
                          document.querySelector('[rel="author"]') ||
                          document.querySelector('.author') ||
                          document.querySelector('.byline');
        if (authorMeta) {
            metadata.author = authorMeta.content || authorMeta.textContent || '';
        }

        // Extract publish date
        const dateMeta = document.querySelector('meta[property="article:published_time"]') ||
                        document.querySelector('meta[name="publishdate"]') ||
                        document.querySelector('time[datetime]') ||
                        document.querySelector('.date') ||
                        document.querySelector('.published');
        if (dateMeta) {
            metadata.publishDate = dateMeta.getAttribute('datetime') || 
                                  dateMeta.content || 
                                  dateMeta.textContent || '';
        }

        // Extract keywords
        const keywordsMeta = document.querySelector('meta[name="keywords"]');
        if (keywordsMeta) {
            metadata.keywords = keywordsMeta.content.split(',').map(k => k.trim());
        }

        return metadata;
    }

    addExtensionIndicator() {
        // Add a subtle indicator that Smart Notes is available
        if (document.querySelector('#smart-notes-indicator')) return;

        const indicator = document.createElement('div');
        indicator.id = 'smart-notes-indicator';
        indicator.innerHTML = '📝';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            cursor: pointer;
            z-index: 10000;
            opacity: 0.8;
            transition: all 0.3s ease;
        `;

        indicator.addEventListener('mouseenter', () => {
            indicator.style.opacity = '1';
            indicator.style.transform = 'scale(1.1)';
        });

        indicator.addEventListener('mouseleave', () => {
            indicator.style.opacity = '0.8';
            indicator.style.transform = 'scale(1)';
        });

        indicator.addEventListener('click', () => {
            // Trigger the extension popup
            chrome.runtime.sendMessage({ action: 'openPopup' });
        });

        // Add tooltip
        indicator.title = 'Smart Notes - Click to generate AI-powered notes from this page';

        document.body.appendChild(indicator);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (indicator && indicator.parentNode) {
                indicator.style.opacity = '0.3';
            }
        }, 5000);
    }

    // Helper method to check if content is substantial enough for summarization
    isContentSubstantial(text) {
        const minWords = 50;
        const minChars = 200;
        const wordCount = text.split(/\s+/).filter(word => word.length > 0).length;
        
        return wordCount >= minWords && text.length >= minChars;
    }

    // Helper method to estimate reading time
    estimateReadingTime(text) {
        const wordsPerMinute = 200; // Average reading speed
        const wordCount = text.split(/\s+/).filter(word => word.length > 0).length;
        const minutes = Math.ceil(wordCount / wordsPerMinute);
        return minutes;
    }
}

// Initialize the content script
const smartNotesContent = new SmartNotesContent();

// Export for use in popup script injection
window.smartNotesExtractContent = () => {
    return smartNotesContent.extractPageContent();
};
