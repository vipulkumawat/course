// SSO Log Platform JavaScript

class LogPlatformApp {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadLogs();
    }

    bindEvents() {
        const refreshButton = document.getElementById('refreshLogs');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.loadLogs());
        }
    }

    async loadLogs() {
        const container = document.getElementById('logsContainer');
        if (!container) return;

        try {
            // Show loading spinner
            container.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">Loading logs...</p>
                </div>
            `;

            const response = await fetch('/api/logs');
            if (!response.ok) throw new Error('Failed to fetch logs');

            const data = await response.json();
            this.renderLogs(data.logs);
            
            // Update total logs counter
            const totalLogsElement = document.getElementById('totalLogs');
            if (totalLogsElement) {
                totalLogsElement.textContent = data.total_count;
            }

        } catch (error) {
            console.error('Error loading logs:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error loading logs: ${error.message}
                </div>
            `;
        }
    }

    renderLogs(logs) {
        const container = document.getElementById('logsContainer');
        if (!container) return;

        if (!logs || logs.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <p>No logs found</p>
                </div>
            `;
            return;
        }

        const logsHtml = logs.map(log => `
            <div class="log-entry ${log.level.toLowerCase()}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            <span class="badge bg-${this.getLevelColor(log.level)} me-2">
                                ${log.level}
                            </span>
                            <span class="log-service">${log.service}</span>
                        </div>
                        <div class="log-message">${log.message}</div>
                    </div>
                    <small class="log-timestamp">
                        ${new Date(log.timestamp).toLocaleString()}
                    </small>
                </div>
            </div>
        `).join('');

        container.innerHTML = logsHtml;
    }

    getLevelColor(level) {
        const colors = {
            'INFO': 'info',
            'DEBUG': 'secondary',
            'WARN': 'warning',
            'ERROR': 'danger'
        };
        return colors[level] || 'primary';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LogPlatformApp();
});
