// Dashboard JavaScript for Field-Level Encryption System

class EncryptionDashboard {
    constructor() {
        this.refreshInterval = 5000; // 5 seconds
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startAutoRefresh();
        this.loadInitialData();
    }
    
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshStats());
        }
        
        // Test encryption form
        const testForm = document.getElementById('test-form');
        if (testForm) {
            testForm.addEventListener('submit', (e) => this.handleTestEncryption(e));
        }
        
        // Decrypt test form
        const decryptForm = document.getElementById('decrypt-form');
        if (decryptForm) {
            decryptForm.addEventListener('submit', (e) => this.handleTestDecryption(e));
        }
    }
    
    async loadInitialData() {
        await this.refreshStats();
    }
    
    async refreshStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            this.updateStatsDisplay(stats);
            this.updateStatus('online');
        } catch (error) {
            console.error('Failed to refresh stats:', error);
            this.updateStatus('offline');
        }
    }
    
    updateStatsDisplay(stats) {
        // Update encryption metrics
        this.updateElement('logs-processed', stats.logs_processed || 0);
        this.updateElement('fields-encrypted', stats.fields_encrypted || 0);
        this.updateElement('fields-detected', stats.fields_detected || 0);
        this.updateElement('error-count', stats.errors || 0);
        
        // Update encryption engine stats
        if (stats.encryption_stats) {
            this.updateElement('current-key', stats.encryption_stats.current_key_id || 'None');
            this.updateElement('key-count', stats.encryption_stats.key_count || 0);
        }
        
        // Update field detector stats
        if (stats.field_detector_stats) {
            this.updateElement('pattern-count', stats.field_detector_stats.total_patterns || 0);
            this.updateElement('sensitive-fields', stats.field_detector_stats.sensitive_field_names || 0);
        }
        
        // Calculate and display rates
        const totalProcessed = stats.logs_processed || 1;
        const encryptionRate = ((stats.fields_encrypted || 0) / totalProcessed * 100).toFixed(1);
        const detectionRate = ((stats.fields_detected || 0) / totalProcessed * 100).toFixed(1);
        
        this.updateElement('encryption-rate', `${encryptionRate}%`);
        this.updateElement('detection-rate', `${detectionRate}%`);
        
        // Update last refresh time
        this.updateElement('last-refresh', new Date().toLocaleTimeString());
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    updateStatus(status) {
        const indicator = document.getElementById('status-indicator');
        if (indicator) {
            indicator.className = `status-indicator ${status}`;
        }
    }
    
    // Format encrypted data for better display
    formatEncryptedData(data) {
        const formatted = {};
        const encryptedFields = [];
        
        for (const [key, value] of Object.entries(data)) {
            if (key === '_processing') {
                // Skip processing metadata
                continue;
            }
            
            if (typeof value === 'object' && value !== null && value._encrypted) {
                // This is an encrypted field
                formatted[key] = `🔐 ENCRYPTED (${value._original_type})`;
                encryptedFields.push({
                    field: key,
                    type: value._original_type,
                    key_id: value._metadata.key_id,
                    algorithm: value._metadata.algorithm
                });
            } else {
                // This is a regular field
                formatted[key] = value;
            }
        }
        
        return {
            formatted_data: formatted,
            encrypted_fields: encryptedFields,
            summary: {
                total_fields: Object.keys(data).filter(k => k !== '_processing').length,
                encrypted_count: encryptedFields.length,
                regular_count: Object.keys(data).filter(k => k !== '_processing').length - encryptedFields.length
            }
        };
    }
    
    async handleTestEncryption(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const testData = formData.get('test-data');
        
        if (!testData) {
            this.showResult('error', 'Please enter test data');
            return;
        }
        
        try {
            const submitBtn = document.getElementById('test-submit');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            
            const response = await fetch('/api/test-encryption', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ data: JSON.parse(testData) })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                const formatted = this.formatEncryptedData(result);
                
                let displayContent = `
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: var(--success-green); margin-bottom: 0.5rem;">✅ Encryption Summary</h4>
                        <p><strong>Fields processed:</strong> ${formatted.summary.total_fields}</p>
                        <p><strong>Fields encrypted:</strong> ${formatted.summary.encrypted_count}</p>
                        <p><strong>Fields left as-is:</strong> ${formatted.summary.regular_count}</p>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: var(--primary-blue); margin-bottom: 0.5rem;">🔐 Encrypted Fields</h4>
                        <ul style="list-style: none; padding: 0;">
                            ${formatted.encrypted_fields.map(field => 
                                `<li style="margin-bottom: 0.5rem;">
                                    <strong>${field.field}</strong> (${field.type}) - Key: ${field.key_id}
                                </li>`
                            ).join('')}
                        </ul>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">📊 Processed Data</h4>
                        <div class="code-block" style="background: var(--bg-secondary); padding: 1rem; border-radius: 4px; font-family: monospace; font-size: 0.9rem;">
                            ${JSON.stringify(formatted.formatted_data, null, 2)}
                        </div>
                    </div>
                    
                    <div style="margin-top: 1rem;">
                        <h4 style="color: var(--warning-orange); margin-bottom: 0.5rem;">📋 Raw Encrypted Data (for decryption testing)</h4>
                        <div class="code-block" style="background: var(--bg-secondary); padding: 1rem; border-radius: 4px; font-family: monospace; font-size: 0.8rem; max-height: 200px; overflow-y: auto;">
                            ${JSON.stringify(result, null, 2)}
                        </div>
                    </div>
                `;
                
                this.showResult('success', 'Encryption Test Result', displayContent);
            } else {
                this.showResult('error', 'Encryption failed', result.error || 'Unknown error');
            }
            
        } catch (error) {
            this.showResult('error', 'Test failed', error.message);
        } finally {
            const submitBtn = document.getElementById('test-submit');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Test Encryption';
        }
    }
    
    async handleTestDecryption(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const encryptedData = formData.get('encrypted-data');
        
        if (!encryptedData) {
            this.showDecryptResult('error', 'Please enter encrypted data');
            return;
        }
        
        try {
            const submitBtn = document.getElementById('decrypt-submit');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Decrypting...';
            
            const response = await fetch('/api/test-decryption', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ data: JSON.parse(encryptedData) })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                let displayContent = `
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: var(--success-green); margin-bottom: 0.5rem;">✅ Decryption Successful</h4>
                        <p>All encrypted fields have been successfully decrypted.</p>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <h4 style="color: var(--text-primary); margin-bottom: 0.5rem;">🔓 Decrypted Data</h4>
                        <div class="code-block" style="background: var(--bg-secondary); padding: 1rem; border-radius: 4px; font-family: monospace; font-size: 0.9rem;">
                            ${JSON.stringify(result, null, 2)}
                        </div>
                    </div>
                `;
                
                this.showDecryptResult('success', 'Decryption Test Result', displayContent);
            } else {
                this.showDecryptResult('error', 'Decryption failed', result.error || 'Unknown error');
            }
            
        } catch (error) {
            this.showDecryptResult('error', 'Test failed', error.message);
        } finally {
            const submitBtn = document.getElementById('decrypt-submit');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Test Decryption';
        }
    }
    
    showResult(type, title, content = '') {
        const resultSection = document.getElementById('test-result');
        if (resultSection) {
            resultSection.innerHTML = `
                <h3 style="color: ${type === 'success' ? 'var(--success-green)' : 'var(--error-red)'}">
                    ${title}
                </h3>
                ${content}
            `;
            resultSection.style.display = 'block';
        }
    }
    
    showDecryptResult(type, title, content = '') {
        const resultSection = document.getElementById('decrypt-result');
        if (resultSection) {
            resultSection.innerHTML = `
                <h3 style="color: ${type === 'success' ? 'var(--success-green)' : 'var(--error-red)'}">
                    ${title}
                </h3>
                ${content}
            `;
            resultSection.style.display = 'block';
        }
    }
    
    startAutoRefresh() {
        setInterval(() => {
            this.refreshStats();
        }, this.refreshInterval);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EncryptionDashboard();
});
