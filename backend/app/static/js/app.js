// GenHook Configuration Interface JavaScript

// Global variables
window.GenHook = {
    currentStep: 1,
    analyzedPayload: null,
    selectedFields: [],
    currentWebhookType: '',
    
    // Configuration
    config: {
        apiBaseUrl: '',
        maxPayloadSize: 10 * 1024 * 1024, // 10MB
        debounceTimeout: 300,
        maxFieldsDisplay: 100
    },
    
    // Utilities
    utils: {
        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Format file size
        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        
        // Validate JSON
        isValidJSON: function(str) {
            try {
                JSON.parse(str);
                return true;
            } catch (e) {
                return false;
            }
        },
        
        // Escape HTML
        escapeHTML: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },
        
        // Copy to clipboard
        copyToClipboard: function(text) {
            if (navigator.clipboard) {
                return navigator.clipboard.writeText(text);
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    return Promise.resolve();
                } catch (err) {
                    document.body.removeChild(textArea);
                    return Promise.reject(err);
                }
            }
        }
    },
    
    // API methods
    api: {
        // Make API request
        request: async function(endpoint, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            };
            
            const response = await fetch(endpoint, {
                ...defaultOptions,
                ...options
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
            }
            
            return response.json();
        },
        
        // Analyze payload
        analyzePayload: function(payload, webhookType) {
            return this.request('/api/analyze-payload', {
                method: 'POST',
                body: JSON.stringify({
                    payload: payload,
                    webhook_type: webhookType
                })
            });
        },
        
        // Generate configuration
        generateConfig: function(webhookType, selectedFields, messageTemplate) {
            return this.request('/api/generate-config', {
                method: 'POST',
                body: JSON.stringify({
                    webhook_type: webhookType,
                    selected_fields: selectedFields,
                    message_template: messageTemplate
                })
            });
        },
        
        // Save configuration
        saveConfig: function(webhookType, configLine, createBackup = true, restartService = true) {
            return this.request('/api/save-config', {
                method: 'POST',
                body: JSON.stringify({
                    webhook_type: webhookType,
                    config_line: configLine,
                    create_backup: createBackup,
                    restart_service: restartService
                })
            });
        },
        
        // Test configuration
        testConfig: function(webhookType, testPayload) {
            return this.request('/api/test-config', {
                method: 'POST',
                body: JSON.stringify({
                    webhook_type: webhookType,
                    test_payload: testPayload
                })
            });
        },
        
        // Get configurations
        getConfigs: function() {
            return this.request('/api/configs');
        },
        
        // Get specific configuration
        getConfig: function(webhookType) {
            return this.request(`/api/config/${webhookType}`);
        },
        
        // Delete configuration
        deleteConfig: function(webhookType) {
            return this.request(`/api/config/${webhookType}`, {
                method: 'DELETE'
            });
        }
    },
    
    // UI methods
    ui: {
        // Show loading spinner
        showLoading: function(text = 'Processing...') {
            const modal = document.getElementById('loadingModal');
            const messageEl = modal.querySelector('.modal-body div:last-child');
            if (messageEl) {
                messageEl.textContent = text;
            }
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            return bsModal;
        },
        
        // Hide loading spinner
        hideLoading: function() {
            const modal = document.getElementById('loadingModal');
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        },
        
        // Show notification
        showNotification: function(title, message, type = 'info', duration = 5000) {
            const toast = document.getElementById('notificationToast');
            if (!toast) return;
            
            const toastTitle = document.getElementById('toastTitle');
            const toastMessage = document.getElementById('toastMessage');
            const toastHeader = toast.querySelector('.toast-header');
            
            // Set content
            toastTitle.textContent = title;
            toastMessage.textContent = message;
            
            // Reset classes
            toastHeader.className = 'toast-header';
            
            // Set color based on type
            switch (type) {
                case 'success':
                    toastHeader.classList.add('bg-success', 'text-white');
                    break;
                case 'error':
                case 'danger':
                    toastHeader.classList.add('bg-danger', 'text-white');
                    break;
                case 'warning':
                    toastHeader.classList.add('bg-warning');
                    break;
                case 'info':
                default:
                    toastHeader.classList.add('bg-info', 'text-white');
                    break;
            }
            
            // Show toast
            const bsToast = new bootstrap.Toast(toast, { delay: duration });
            bsToast.show();
        },
        
        // Confirm dialog
        confirm: function(message, title = 'Confirm') {
            return new Promise((resolve) => {
                // For now, use browser confirm - could be enhanced with custom modal
                resolve(window.confirm(message));
            });
        },
        
        // Update element with loading state
        setElementLoading: function(element, loading = true, originalText = null) {
            if (loading) {
                element.dataset.originalText = element.textContent;
                element.disabled = true;
                element.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Loading...';
            } else {
                element.disabled = false;
                element.textContent = originalText || element.dataset.originalText || 'Submit';
                delete element.dataset.originalText;
            }
        }
    },
    
    // Form validation
    validation: {
        // Validate webhook type name
        isValidWebhookType: function(name) {
            return /^[a-zA-Z0-9_-]+$/.test(name);
        },
        
        // Validate JSON payload
        validatePayload: function(payloadStr) {
            if (!payloadStr || !payloadStr.trim()) {
                return { valid: false, error: 'Payload cannot be empty' };
            }
            
            if (payloadStr.length > GenHook.config.maxPayloadSize) {
                return { 
                    valid: false, 
                    error: `Payload too large (${GenHook.utils.formatFileSize(payloadStr.length)} > ${GenHook.utils.formatFileSize(GenHook.config.maxPayloadSize)})` 
                };
            }
            
            try {
                const parsed = JSON.parse(payloadStr);
                return { valid: true, payload: parsed };
            } catch (e) {
                return { valid: false, error: `Invalid JSON: ${e.message}` };
            }
        },
        
        // Validate message template
        validateTemplate: function(template) {
            if (!template || !template.trim()) {
                return { valid: false, error: 'Template cannot be empty' };
            }
            
            // Check for balanced variable markers
            const markers = template.match(/\$/g);
            if (markers && markers.length % 2 !== 0) {
                return { valid: false, error: 'Unmatched variable markers ($)' };
            }
            
            return { valid: true };
        }
    },
    
    // Sample data
    samples: {
        github: {
            type: 'github',
            payload: {
                action: 'opened',
                pull_request: {
                    title: 'Add new feature',
                    user: { login: 'developer' }
                },
                repository: { name: 'my-repo' }
            }
        },
        
        stripe: {
            type: 'stripe', 
            payload: {
                type: 'payment_intent.succeeded',
                data: {
                    object: {
                        amount: 2000,
                        currency: 'usd',
                        status: 'succeeded'
                    }
                }
            }
        },
        
        slack: {
            type: 'slack',
            payload: {
                event: {
                    type: 'message',
                    user: 'U1234567',
                    text: 'Hello world'
                }
            }
        },
        
        meraki: {
            type: 'meraki',
            payload: {
                alertType: 'Device down',
                deviceName: 'Switch-01',
                deviceSerial: 'Q2XX-1234-ABCD',
                networkName: 'Production Network',
                networkUrl: 'https://dashboard.meraki.com/o/12345'
            }
        }
    }
};

// Recent payload loading functions
async function loadAvailableWebhookTypes() {
    try {
        const response = await fetch('/api/webhook-logs/types');
        const data = await response.json();
        
        const select = document.getElementById('webhookTypeSelect');
        if (select) {
            // Clear existing options except the first one
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            // Add webhook types
            if (data.success && data.webhook_types) {
                data.webhook_types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.warn('Could not load webhook types for recent payloads:', error);
    }
}

async function loadRecentPayloads(webhookType) {
    try {
        const response = await fetch(`/api/webhook-logs/${webhookType}/recent?limit=10`);
        const data = await response.json();
        
        const select = document.getElementById('recentPayloadSelect');
        const loadBtn = document.getElementById('loadRecentBtn');
        
        if (select) {
            // Clear existing options except the first one
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            if (data.success && data.payloads) {
                data.payloads.forEach((entry, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    
                    // Create a readable timestamp
                    const timestamp = new Date(entry.timestamp).toLocaleString();
                    const status = entry.processing_status || 'logged';
                    
                    option.textContent = `${timestamp} (${status})`;
                    option.dataset.payload = JSON.stringify(entry.payload);
                    select.appendChild(option);
                });
                
                select.disabled = false;
            } else {
                select.disabled = true;
            }
            
            loadBtn.disabled = true; // Will be enabled when a payload is selected
        }
    } catch (error) {
        console.error('Error loading recent payloads:', error);
        GenHook.ui.showNotification('Error loading recent payloads', 'error');
    }
}

function loadRecentPayload() {
    const payloadSelect = document.getElementById('recentPayloadSelect');
    const selectedOption = payloadSelect.selectedOptions[0];
    
    if (selectedOption && selectedOption.dataset.payload) {
        try {
            const payload = JSON.parse(selectedOption.dataset.payload);
            const textarea = document.getElementById('jsonPayload');
            
            if (textarea) {
                textarea.value = JSON.stringify(payload, null, 2);
                
                // Trigger validation and enable analyze button
                validateJson();
                
                GenHook.ui.showNotification('Recent payload loaded successfully', 'success');
            }
        } catch (error) {
            console.error('Error loading payload:', error);
            GenHook.ui.showNotification('Error loading payload', 'error');
        }
    }
}

// Load recent payload for edit mode
function loadRecentPayloadToEdit() {
    const payloadSelect = document.getElementById('editRecentPayloadSelect');
    const selectedOption = payloadSelect.selectedOptions[0];
    
    if (selectedOption && selectedOption.dataset.payload) {
        try {
            const payload = JSON.parse(selectedOption.dataset.payload);
            const textarea = document.getElementById('editTestPayload');
            
            if (textarea) {
                textarea.value = JSON.stringify(payload, null, 2);
                GenHook.ui.showNotification('Recent payload loaded to edit mode', 'success');
            }
        } catch (error) {
            console.error('Error loading payload to edit mode:', error);
            GenHook.ui.showNotification('Error loading payload', 'error');
        }
    }
}

// Initialize recent payload loading when page loads
function initRecentPayloadLoading() {
    // Load available webhook types on page load for both regular and edit mode
    loadAvailableWebhookTypes();
    loadAvailableWebhookTypesForEdit();
    
    // Handle webhook type selection (regular mode)
    const webhookTypeSelect = document.getElementById('webhookTypeSelect');
    if (webhookTypeSelect) {
        webhookTypeSelect.addEventListener('change', function() {
            const webhookType = this.value;
            if (webhookType) {
                loadRecentPayloads(webhookType);
            } else {
                resetPayloadSelection();
            }
        });
    }
    
    // Handle recent payload selection (regular mode)
    const recentPayloadSelect = document.getElementById('recentPayloadSelect');
    if (recentPayloadSelect) {
        recentPayloadSelect.addEventListener('change', function() {
            const loadBtn = document.getElementById('loadRecentBtn');
            if (loadBtn) {
                loadBtn.disabled = !this.value;
            }
        });
    }
    
    // Handle webhook type selection (edit mode)
    const editWebhookTypeSelect = document.getElementById('editWebhookTypeSelect');
    if (editWebhookTypeSelect) {
        editWebhookTypeSelect.addEventListener('change', function() {
            const webhookType = this.value;
            if (webhookType) {
                loadRecentPayloadsForEdit(webhookType);
            } else {
                resetEditPayloadSelection();
            }
        });
    }
    
    // Handle recent payload selection (edit mode)
    const editRecentPayloadSelect = document.getElementById('editRecentPayloadSelect');
    if (editRecentPayloadSelect) {
        editRecentPayloadSelect.addEventListener('change', function() {
            const loadBtn = document.getElementById('editLoadRecentBtn');
            if (loadBtn) {
                loadBtn.disabled = !this.value;
            }
        });
    }
}

// Helper function to reset payload selection
function resetPayloadSelection() {
    const payloadSelect = document.getElementById('recentPayloadSelect');
    const loadBtn = document.getElementById('loadRecentBtn');
    if (payloadSelect) {
        payloadSelect.disabled = true;
        payloadSelect.innerHTML = '<option value="">Select a recent payload...</option>';
    }
    if (loadBtn) loadBtn.disabled = true;
}

// Helper function to reset edit mode payload selection
function resetEditPayloadSelection() {
    const payloadSelect = document.getElementById('editRecentPayloadSelect');
    const loadBtn = document.getElementById('editLoadRecentBtn');
    if (payloadSelect) {
        payloadSelect.disabled = true;
        payloadSelect.innerHTML = '<option value="">Select a recent payload...</option>';
    }
    if (loadBtn) loadBtn.disabled = true;
}

// Load available webhook types for edit mode
async function loadAvailableWebhookTypesForEdit() {
    try {
        const response = await fetch('/api/webhook-logs/types');
        const data = await response.json();
        
        const select = document.getElementById('editWebhookTypeSelect');
        if (select) {
            // Clear existing options except the first one
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            // Add webhook types
            if (data.success && data.webhook_types) {
                data.webhook_types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.warn('Could not load webhook types for edit mode recent payloads:', error);
    }
}

// Load recent payloads for edit mode
async function loadRecentPayloadsForEdit(webhookType) {
    try {
        const response = await fetch(`/api/webhook-logs/${webhookType}/recent?limit=10`);
        const data = await response.json();
        
        const select = document.getElementById('editRecentPayloadSelect');
        const loadBtn = document.getElementById('editLoadRecentBtn');
        
        if (select) {
            // Clear existing options except the first one
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            if (data.success && data.payloads) {
                data.payloads.forEach((entry, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    
                    // Create a readable timestamp
                    const timestamp = new Date(entry.timestamp).toLocaleString();
                    const status = entry.processing_status || 'logged';
                    
                    option.textContent = `${timestamp} (${status})`;
                    option.dataset.payload = JSON.stringify(entry.payload);
                    select.appendChild(option);
                });
                
                select.disabled = false;
            } else {
                select.disabled = true;
            }
            
            loadBtn.disabled = true; // Will be enabled when a payload is selected
        }
    } catch (error) {
        console.error('Error loading recent payloads for edit mode:', error);
        GenHook.ui.showNotification('Error loading recent payloads', 'error');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('GenHook Configuration Interface loaded');
    
    // Initialize recent payload loading functionality
    initRecentPayloadLoading();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter or Cmd+Enter to proceed to next step
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const nextBtn = document.querySelector('.btn-primary[onclick*="showStep"], .btn-primary[onclick*="analyzePayload"]');
            if (nextBtn && !nextBtn.disabled) {
                nextBtn.click();
            }
        }
    });
    
    // Auto-resize textareas
    document.querySelectorAll('textarea').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
});

// Export for use in HTML inline scripts
window.showNotification = GenHook.ui.showNotification;
window.formatFileSize = GenHook.utils.formatFileSize;

// Export recent payload functions to global scope
window.loadAvailableWebhookTypes = loadAvailableWebhookTypes;
window.loadRecentPayloads = loadRecentPayloads;
window.loadRecentPayload = loadRecentPayload;
window.loadRecentPayloadToEdit = loadRecentPayloadToEdit;
window.initRecentPayloadLoading = initRecentPayloadLoading;
window.loadAvailableWebhookTypesForEdit = loadAvailableWebhookTypesForEdit;
window.loadRecentPayloadsForEdit = loadRecentPayloadsForEdit;