const axios = require('axios');
const { v4: uuidv4 } = require('uuid');
const { EventEmitter } = require('events');

const LogLevel = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARNING: 'WARNING',
    ERROR: 'ERROR',
    CRITICAL: 'CRITICAL'
};

class LogEntry {
    constructor(level, message, service, component, metadata = {}) {
        this.timestamp = new Date().toISOString();
        this.level = level;
        this.message = message;
        this.service = service;
        this.component = component;
        this.metadata = metadata;
        this.request_id = uuidv4();
        this.session_id = null;
        this.user_id = null;
    }
}

class LogBatch {
    constructor(maxSize = 100) {
        this.entries = [];
        this.maxSize = maxSize;
        this.createdAt = new Date();
    }
    
    addEntry(entry) {
        this.entries.push(entry);
        return this.entries.length >= this.maxSize;
    }
    
    isEmpty() {
        return this.entries.length === 0;
    }
    
    size() {
        return this.entries.length;
    }
    
    toJSON() {
        return JSON.stringify(this.entries);
    }
}

class DistributedLogger extends EventEmitter {
    constructor(config = {}) {
        super();
        
        this.config = {
            endpoint: config.endpoint || 'http://localhost:8080/api/logs',
            apiKey: config.apiKey || null,
            serviceName: config.serviceName || 'unknown-service',
            componentName: config.componentName || 'main',
            batchSize: config.batchSize || 100,
            batchTimeoutMs: config.batchTimeoutMs || 5000,
            retryAttempts: config.retryAttempts || 3,
            retryBackoffBase: config.retryBackoffBase || 1000,
            asyncEnabled: config.asyncEnabled !== false
        };
        
        this.currentBatch = new LogBatch(this.config.batchSize);
        this.batchQueue = [];
        this.running = false;
        this.lastBatchTime = Date.now();
        this.stats = {
            logs_sent: 0,
            logs_failed: 0,
            batches_sent: 0,
            errors: []
        };
        
        // Setup HTTP client
        this.httpClient = axios.create({
            timeout: 5000,
            headers: {
                'Content-Type': 'application/json',
                ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
            }
        });
    }
    
    start() {
        if (this.running) return;
        
        this.running = true;
        
        // Start batch timeout checker
        this.batchTimeoutInterval = setInterval(() => {
            this.checkBatchTimeout();
        }, this.config.batchTimeoutMs);
        
        // Start batch processor
        this.processBatches();
        
        this.emit('started');
    }
    
    stop() {
        this.running = false;
        
        if (this.batchTimeoutInterval) {
            clearInterval(this.batchTimeoutInterval);
        }
        
        // Send remaining logs
        if (!this.currentBatch.isEmpty()) {
            this.batchQueue.push(this.currentBatch);
            this.currentBatch = new LogBatch(this.config.batchSize);
        }
        
        this.emit('stopped');
    }
    
    checkBatchTimeout() {
        const currentTime = Date.now();
        if (!this.currentBatch.isEmpty() && 
            (currentTime - this.lastBatchTime) >= this.config.batchTimeoutMs) {
            
            this.batchQueue.push(this.currentBatch);
            this.currentBatch = new LogBatch(this.config.batchSize);
            this.lastBatchTime = currentTime;
        }
    }
    
    async processBatches() {
        while (this.running) {
            try {
                if (this.batchQueue.length > 0) {
                    const batch = this.batchQueue.shift();
                    await this.sendBatch(batch);
                } else {
                    // Small delay to prevent busy waiting
                    await new Promise(resolve => setTimeout(resolve, 100));
                }
            } catch (error) {
                this.stats.errors.push(`Batch processing error: ${error.message}`);
                this.emit('error', error);
            }
        }
    }
    
    async sendBatch(batch) {
        if (batch.isEmpty()) return;
        
        let retryCount = 0;
        
        while (retryCount < this.config.retryAttempts) {
            try {
                const response = await this.httpClient.post(
                    this.config.endpoint, 
                    batch.toJSON()
                );
                
                if (response.status === 200) {
                    this.stats.logs_sent += batch.size();
                    this.stats.batches_sent += 1;
                    this.emit('batch_sent', { size: batch.size() });
                    return;
                }
                
            } catch (error) {
                retryCount++;
                
                if (retryCount >= this.config.retryAttempts) {
                    this.stats.logs_failed += batch.size();
                    this.stats.errors.push(`Failed to send batch: ${error.message}`);
                    this.emit('batch_failed', { size: batch.size(), error: error.message });
                    return;
                }
                
                // Exponential backoff
                const delay = this.config.retryBackoffBase * Math.pow(2, retryCount);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    
    createLogEntry(level, message, metadata = {}) {
        return new LogEntry(
            level, 
            message, 
            this.config.serviceName, 
            this.config.componentName, 
            metadata
        );
    }
    
    addLogEntry(entry) {
        if (!this.running) {
            this.start();
        }
        
        const batchFull = this.currentBatch.addEntry(entry);
        
        if (batchFull) {
            this.batchQueue.push(this.currentBatch);
            this.currentBatch = new LogBatch(this.config.batchSize);
            this.lastBatchTime = Date.now();
        }
    }
    
    debug(message, metadata = {}) {
        const entry = this.createLogEntry(LogLevel.DEBUG, message, metadata);
        this.addLogEntry(entry);
    }
    
    info(message, metadata = {}) {
        const entry = this.createLogEntry(LogLevel.INFO, message, metadata);
        this.addLogEntry(entry);
    }
    
    warning(message, metadata = {}) {
        const entry = this.createLogEntry(LogLevel.WARNING, message, metadata);
        this.addLogEntry(entry);
    }
    
    error(message, metadata = {}) {
        const entry = this.createLogEntry(LogLevel.ERROR, message, metadata);
        this.addLogEntry(entry);
    }
    
    critical(message, metadata = {}) {
        const entry = this.createLogEntry(LogLevel.CRITICAL, message, metadata);
        this.addLogEntry(entry);
    }
    
    custom(eventType, data = {}) {
        const metadata = { event_type: eventType, ...data };
        const entry = this.createLogEntry(LogLevel.INFO, `Custom event: ${eventType}`, metadata);
        this.addLogEntry(entry);
    }
    
    getStats() {
        return {
            ...this.stats,
            current_batch_size: this.currentBatch.size(),
            queue_size: this.batchQueue.length,
            running: this.running
        };
    }
}

module.exports = {
    DistributedLogger,
    LogLevel,
    LogEntry
};
