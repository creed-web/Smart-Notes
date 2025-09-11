// Smart Notes Extension - Background Service Worker
// This script handles background tasks and communication

class SmartNotesBackground {
    constructor() {
        this.initializeBackground();
    }

    initializeBackground() {
        // Handle extension installation
        chrome.runtime.onInstalled.addListener(() => {
            this.onExtensionInstalled();
        });

        // Handle messages from content scripts and popup
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Keep the message channel open for async responses
        });

        // Handle extension icon click
        chrome.action.onClicked.addListener((tab) => {
            this.onIconClicked(tab);
        });

        // Handle tab updates to manage extension state
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            this.onTabUpdated(tabId, changeInfo, tab);
        });
    }

    onExtensionInstalled() {
        console.log('Smart Notes extension installed successfully!');
        
        // Set default settings
        chrome.storage.sync.set({
            backendUrl: 'http://localhost:5000',
            autoShowIndicator: true,
            summaryLength: 'medium',
            enableNotifications: true
        });

        // Show welcome notification
        if (chrome.notifications) {
            chrome.notifications.create({
                type: 'basic',
                title: 'Smart Notes Installed!',
                message: 'Click the extension icon on any webpage to generate AI-powered notes.'
            });
        }
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'openPopup':
                    await this.openPopup(sender.tab);
                    sendResponse({ success: true });
                    break;

                case 'extractContent':
                    const content = await this.extractContentFromTab(sender.tab.id);
                    sendResponse({ success: true, content });
                    break;

                case 'checkBackendStatus':
                    const status = await this.checkBackendStatus();
                    sendResponse({ success: true, status });
                    break;

                case 'saveNotes':
                    await this.saveNotesToStorage(request.notes, request.pageInfo);
                    sendResponse({ success: true });
                    break;

                case 'getNotesHistory':
                    const history = await this.getNotesHistory();
                    sendResponse({ success: true, history });
                    break;

                default:
                    sendResponse({ success: false, error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Background script error:', error);
            sendResponse({ success: false, error: error.message });
        }
    }

    onIconClicked(tab) {
        // The popup will open automatically due to manifest configuration
        console.log('Extension icon clicked for tab:', tab.url);
    }

    onTabUpdated(tabId, changeInfo, tab) {
        // Check if the page has finished loading
        if (changeInfo.status === 'complete' && tab.url) {
            this.checkPageCompatibility(tab);
        }
    }

    async checkPageCompatibility(tab) {
        // Check if the page is suitable for Smart Notes
        const unsuitableProtocols = ['chrome:', 'chrome-extension:', 'edge:', 'about:', 'moz-extension:'];
        const isUnsuitable = unsuitableProtocols.some(protocol => tab.url.startsWith(protocol));

        if (isUnsuitable) {
            chrome.action.setTitle({
                title: 'Smart Notes (Not available on this page)',
                tabId: tab.id
            });
        } else {
            chrome.action.setTitle({
                title: 'Smart Notes - Generate AI-powered notes',
                tabId: tab.id
            });
        }
    }

    async openPopup(tab) {
        // The popup opens automatically, but we can perform additional setup here
        console.log('Preparing popup for tab:', tab.url);
        
        // Pre-check backend status
        try {
            await this.checkBackendStatus();
        } catch (error) {
            console.warn('Backend not available:', error);
        }
    }

    async extractContentFromTab(tabId) {
        try {
            const [result] = await chrome.scripting.executeScript({
                target: { tabId },
                function: () => {
                    if (window.smartNotesExtractContent) {
                        return window.smartNotesExtractContent();
                    } else {
                        throw new Error('Content extraction function not available');
                    }
                }
            });

            return result.result;
        } catch (error) {
            throw new Error(`Failed to extract content: ${error.message}`);
        }
    }

    async checkBackendStatus() {
        const settings = await this.getSettings();
        const backendUrl = settings.backendUrl;

        try {
            const response = await fetch(`${backendUrl}/health`, {
                method: 'GET',
                timeout: 5000
            });

            if (response.ok) {
                const data = await response.json();
                return {
                    available: true,
                    version: data.version,
                    model: data.model
                };
            } else {
                return { available: false, error: 'Backend returned error status' };
            }
        } catch (error) {
            return { available: false, error: error.message };
        }
    }

    async saveNotesToStorage(notes, pageInfo) {
        try {
            const timestamp = new Date().toISOString();
            const noteItem = {
                id: `note_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                notes,
                pageInfo,
                timestamp,
                wordCount: notes.split(/\s+/).length
            };

            // Get existing notes history
            const result = await chrome.storage.local.get(['notesHistory']);
            const notesHistory = result.notesHistory || [];

            // Add new note to the beginning of the array
            notesHistory.unshift(noteItem);

            // Limit to 50 most recent notes
            const limitedHistory = notesHistory.slice(0, 50);

            // Save back to storage
            await chrome.storage.local.set({ notesHistory: limitedHistory });

            console.log('Notes saved to storage:', noteItem.id);
        } catch (error) {
            throw new Error(`Failed to save notes: ${error.message}`);
        }
    }

    async getNotesHistory() {
        try {
            const result = await chrome.storage.local.get(['notesHistory']);
            return result.notesHistory || [];
        } catch (error) {
            throw new Error(`Failed to get notes history: ${error.message}`);
        }
    }

    async getSettings() {
        try {
            const result = await chrome.storage.sync.get([
                'backendUrl',
                'autoShowIndicator',
                'summaryLength',
                'enableNotifications'
            ]);

            return {
                backendUrl: result.backendUrl || 'http://localhost:5000',
                autoShowIndicator: result.autoShowIndicator !== false,
                summaryLength: result.summaryLength || 'medium',
                enableNotifications: result.enableNotifications !== false
            };
        } catch (error) {
            console.error('Failed to get settings:', error);
            return {
                backendUrl: 'http://localhost:5000',
                autoShowIndicator: true,
                summaryLength: 'medium',
                enableNotifications: true
            };
        }
    }

    async updateSettings(newSettings) {
        try {
            await chrome.storage.sync.set(newSettings);
            console.log('Settings updated:', newSettings);
        } catch (error) {
            throw new Error(`Failed to update settings: ${error.message}`);
        }
    }

    // Context menu integration (optional)
    createContextMenu() {
        chrome.contextMenus.create({
            id: 'generateSmartNotes',
            title: 'Generate Smart Notes',
            contexts: ['page', 'selection']
        });

        chrome.contextMenus.onClicked.addListener((info, tab) => {
            if (info.menuItemId === 'generateSmartNotes') {
                // Open popup or trigger note generation
                chrome.action.openPopup();
            }
        });
    }
}

// Initialize the background service worker
const smartNotesBackground = new SmartNotesBackground();
