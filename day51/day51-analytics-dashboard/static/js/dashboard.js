// Dashboard JavaScript with WebSocket support
class DashboardApp {
    constructor() {
        this.websocket = null;
        this.charts = {};
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        console.log('DashboardApp constructor called');
        this.init();
    }
    
    async init() {
        console.log('Initializing Analytics Dashboard...');
        
        try {
            // Initialize UI components
            this.initializeUI();
            console.log('UI initialized');
            
            // Test dashboard elements
            this.testDashboardElements();
            
            // Load initial data
            await this.loadInitialData();
            console.log('Initial data loaded');
            
            // Setup WebSocket connection
            this.connectWebSocket();
            console.log('WebSocket connection attempted');
            
            // Setup periodic updates
            this.setupPeriodicUpdates();
            console.log('Periodic updates setup complete');
            
            console.log('Dashboard initialization complete');
        } catch (error) {
            console.error('Error during initialization:', error);
        }
    }
    
    initializeUI() {
        console.log('Initializing UI components...');
        
        // Test chart containers exist
        this.testChartContainers();
        
        // Setup time range selector
        const timeSelector = document.getElementById('timeRange');
        if (timeSelector) {
            console.log('Time selector found');
            timeSelector.addEventListener('change', (e) => {
                this.updateTimeRange(e.target.value);
            });
        } else {
            console.warn('Time selector not found');
        }
        
        // Setup service filter
        const serviceFilter = document.getElementById('serviceFilter');
        if (serviceFilter) {
            console.log('Service filter found');
            serviceFilter.addEventListener('change', (e) => {
                this.updateServiceFilter(e.target.value);
            });
        } else {
            console.warn('Service filter not found');
        }
        
        // Setup refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            console.log('Refresh button found');
            refreshBtn.addEventListener('click', () => {
                this.refreshDashboard();
            });
        } else {
            console.warn('Refresh button not found');
        }
        
        // Setup sample data generator
        const generateBtn = document.getElementById('generateSampleData');
        if (generateBtn) {
            console.log('Generate sample data button found');
            generateBtn.addEventListener('click', () => {
                this.generateSampleData();
            });
        } else {
            console.warn('Generate sample data button not found');
        }
        
        // Setup debug button
        const debugBtn = document.getElementById('debugBtn');
        if (debugBtn) {
            console.log('Debug button found');
            debugBtn.addEventListener('click', () => {
                this.runDebugTests();
            });
        } else {
            console.warn('Debug button not found');
        }
        
        // Update connection status to show we're loading
        this.updateConnectionStatus(false);
        console.log('UI initialization complete');
    }
    
    testChartContainers() {
        console.log('Testing chart containers...');
        const services = ['web', 'api', 'database'];
        const metrics = ['response_time', 'error_count', 'request_count'];
        
        for (const service of services) {
            for (const metric of metrics) {
                const chartId = `chart-${service}-${metric}`;
                const element = document.getElementById(chartId);
                if (element) {
                    console.log(`✅ Chart container found: ${chartId}`);
                    // Add a visual indicator that the container is ready
                    element.style.border = '2px solid #e0e0e0';
                    element.style.backgroundColor = '#fafafa';
                } else {
                    console.error(`❌ Chart container missing: ${chartId}`);
                }
            }
        }
        
        // Test Plotly if available
        if (typeof Plotly !== 'undefined') {
            console.log('✅ Plotly is available');
            this.testPlotly();
        } else {
            console.error('❌ Plotly is not available');
        }
    }
    
    testPlotly() {
        // Test with a simple chart
        const testElement = document.getElementById('chart-web-response_time');
        if (testElement && typeof Plotly !== 'undefined') {
            console.log('Testing Plotly with simple chart...');
            const testData = [{
                x: [1, 2, 3, 4, 5],
                y: [10, 11, 12, 13, 14],
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Test Chart'
            }];
            
            const layout = {
                title: 'Plotly Test Chart',
                height: 200,
                autosize: true,
                width: null
            };
            
            Plotly.newPlot(testElement, testData, layout).then(() => {
                console.log('✅ Plotly test chart rendered successfully');
                // Remove test chart after 3 seconds
                setTimeout(() => {
                    testElement.innerHTML = '<div style="text-align: center; padding: 20px;">Loading chart...</div>';
                }, 3000);
            }).catch((error) => {
                console.error('❌ Plotly test failed:', error);
            });
        }
    }
    
    testDashboardElements() {
        console.log('Testing dashboard elements...');
        
        // Test metric cards
        const testValues = {
            'totalConnections': 5,
            'activeSubscriptions': 3,
            'recentMetrics': 150
        };
        
        for (const [cardId, value] of Object.entries(testValues)) {
            this.updateMetricCard(cardId, value);
        }
        
        // Test connection status
        this.updateConnectionStatus(true);
        
        console.log('Dashboard element test complete');
    }
    
    runDebugTests() {
        console.log('🔍 Running debug tests...');
        
        // Test 1: Check if Plotly is available
        if (typeof Plotly !== 'undefined') {
            console.log('✅ Plotly is available');
        } else {
            console.error('❌ Plotly is not available');
        }
        
        // Test 2: Check metric cards
        const metricCards = ['totalConnections', 'activeSubscriptions', 'recentMetrics'];
        metricCards.forEach(cardId => {
            const card = document.getElementById(cardId);
            if (card) {
                console.log(`✅ Metric card found: ${cardId}`);
                const valueElement = card.querySelector('.metric-value');
                if (valueElement) {
                    console.log(`✅ Value element found in ${cardId}: ${valueElement.textContent}`);
                } else {
                    console.error(`❌ Value element missing in ${cardId}`);
                }
            } else {
                console.error(`❌ Metric card missing: ${cardId}`);
            }
        });
        
        // Test 3: Check chart containers
        const services = ['web', 'api', 'database'];
        const metrics = ['response_time', 'error_count', 'request_count'];
        let foundCharts = 0;
        
        services.forEach(service => {
            metrics.forEach(metric => {
                const chartId = `chart-${service}-${metric}`;
                const element = document.getElementById(chartId);
                if (element) {
                    foundCharts++;
                    console.log(`✅ Chart container: ${chartId}`);
                } else {
                    console.error(`❌ Chart container missing: ${chartId}`);
                }
            });
        });
        
        console.log(`📊 Found ${foundCharts} chart containers out of ${services.length * metrics.length} expected`);
        
        // Test 4: Test API connectivity
        this.testAPIConnectivity();
        
        // Test 5: Force update dashboard stats
        this.updateDashboardStats();
        
        console.log('🔍 Debug tests complete');
    }
    
    async testAPIConnectivity() {
        console.log('🌐 Testing API connectivity...');
        
        try {
            const response = await fetch('/api/dashboard-stats');
            if (response.ok) {
                const data = await response.json();
                console.log('✅ API connectivity test passed:', data);
            } else {
                console.error('❌ API connectivity test failed:', response.status);
            }
        } catch (error) {
            console.error('❌ API connectivity test error:', error);
        }
    }
    
    async loadInitialData() {
        console.log('Loading initial data...');
        try {
            // Load dashboard statistics
            await this.updateDashboardStats();
            console.log('Dashboard stats updated');
            
            // Load metrics for each service
            const services = ['web', 'api', 'database'];
            const metrics = ['response_time', 'error_count', 'request_count'];
            
            for (const service of services) {
                for (const metric of metrics) {
                    console.log(`Loading ${service}/${metric}...`);
                    await this.loadMetricChart(service, metric);
                }
            }
            
            // Load anomalies
            await this.loadAnomalies();
            console.log('Anomalies loaded');
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial dashboard data');
        }
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            
            // Subscribe to metrics updates
            this.subscribeToMetrics();
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            
            // Attempt to reconnect
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                setTimeout(() => this.connectWebSocket(), 5000);
            } else {
                this.showError('WebSocket connection lost. Please refresh the page.');
            }
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    subscribeToMetrics() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'subscribe',
                subscription: 'metrics'
            }));
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'metrics_update':
                this.handleMetricsUpdate(data);
                break;
            case 'anomaly_detected':
                this.handleAnomalyDetected(data);
                break;
            case 'heartbeat_request':
                this.sendHeartbeat();
                break;
            case 'subscription_response':
                console.log('Subscription response:', data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    sendHeartbeat() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'heartbeat'
            }));
        }
    }
    
    async loadMetricChart(service, metricName) {
        try {
            console.log(`Fetching ${service}/${metricName}...`);
            const response = await fetch(`/api/metrics/${service}/${metricName}?limit=100&_t=${Date.now()}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log(`Got ${data.metrics?.length || 0} metrics for ${service}/${metricName}`);
            
            if (data.metrics && data.metrics.length > 0) {
                console.log(`Sample metric: ${JSON.stringify(data.metrics[0])}`);
                this.renderChart(service, metricName, data.metrics);
            } else {
                console.log(`No metrics data for ${service}/${metricName}`);
                // Show a placeholder message
                const chartId = `chart-${service}-${metricName}`;
                const chartElement = document.getElementById(chartId);
                if (chartElement) {
                    chartElement.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">No data available for this metric</div>';
                }
            }
            
        } catch (error) {
            console.error(`Error loading ${service}/${metricName}:`, error);
            // Show error message in chart container
            const chartId = `chart-${service}-${metricName}`;
            const chartElement = document.getElementById(chartId);
            if (chartElement) {
                chartElement.innerHTML = `<div style="text-align: center; padding: 20px; color: red;">Error loading data: ${error.message}</div>`;
            }
        }
    }
    
    renderChart(service, metricName, metrics) {
        const chartId = `chart-${service}-${metricName}`;
        const chartElement = document.getElementById(chartId);
        
        if (!chartElement) {
            console.warn(`Chart element ${chartId} not found`);
            return;
        }
        
        console.log(`Rendering chart for ${chartId} with ${metrics.length} data points`);
        
        // Check if Plotly is available
        if (typeof Plotly === 'undefined') {
            console.error('Plotly is not loaded');
            chartElement.innerHTML = '<div style="color: red; text-align: center; padding: 20px;">Error: Plotly library not loaded</div>';
            return;
        }
        
        // Show loading state
        chartElement.innerHTML = '<div style="text-align: center; padding: 20px;">Rendering chart...</div>';
        
        // Prepare data for Plotly
        const x = metrics.map(m => new Date(m.timestamp));
        const y = metrics.map(m => m.value);
        
        console.log(`Data prepared: ${x.length} x values, ${y.length} y values`);
        console.log(`Sample data: x[0]=${x[0]}, y[0]=${y[0]}`);
        
        const trace = {
            x: x,
            y: y,
            type: 'scatter',
            mode: 'lines+markers',
            name: `${service} ${metricName}`,
            line: {
                color: this.getColorForMetric(metricName),
                width: 2
            },
            marker: {
                size: 4,
                color: this.getColorForMetric(metricName)
            }
        };
        
        const layout = {
            title: {
                text: `${service.toUpperCase()} - ${this.formatMetricName(metricName)}`,
                font: { size: 14 }
            },
            xaxis: {
                title: 'Time',
                type: 'date',
                showgrid: true,
                gridcolor: '#f0f0f0'
            },
            yaxis: {
                title: this.getYAxisLabel(metricName),
                showgrid: true,
                gridcolor: '#f0f0f0'
            },
            margin: { t: 40, r: 20, b: 40, l: 50 },
            showlegend: false,
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            height: 300,
            autosize: true,
            width: null
        };
        
        const config = {
            responsive: true,
            displayModeBar: false,
            staticPlot: false
        };
        
        try {
            // Clear the element first
            chartElement.innerHTML = '';
            
            // Render the chart
            Plotly.newPlot(chartElement, [trace], layout, config).then(() => {
                console.log(`Chart ${chartId} rendered successfully`);
                this.charts[chartId] = { element: chartElement, trace: trace };
            }).catch((error) => {
                console.error(`Plotly error for ${chartId}:`, error);
                chartElement.innerHTML = `<div style="color: red; text-align: center; padding: 20px;">Chart error: ${error.message}</div>`;
            });
            
        } catch (error) {
            console.error(`Error rendering chart ${chartId}:`, error);
            chartElement.innerHTML = `<div style="color: red; text-align: center; padding: 20px;">Error rendering chart: ${error.message}</div>`;
        }
    }
    
    getColorForMetric(metricName) {
        const colors = {
            response_time: '#1a73e8',
            error_count: '#ea4335',
            request_count: '#34a853'
        };
        return colors[metricName] || '#1a73e8';
    }
    
    formatMetricName(metricName) {
        return metricName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    getYAxisLabel(metricName) {
        const labels = {
            response_time: 'Response Time (ms)',
            error_count: 'Error Count',
            request_count: 'Request Count'
        };
        return labels[metricName] || 'Value';
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            statusElement.innerHTML = `
                <div class="status-dot"></div>
                ${connected ? 'Connected' : 'Disconnected'}
            `;
            console.log(`Connection status updated: ${connected ? 'Connected' : 'Disconnected'}`);
        } else {
            console.warn('Connection status element not found');
        }
    }
    
    async updateDashboardStats() {
        try {
            console.log('Updating dashboard stats...');
            const response = await fetch('/api/dashboard-stats');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const stats = await response.json();
            console.log('Dashboard stats:', stats);
            
            // Update metric cards with detailed logging
            console.log('Updating totalConnections:', stats.websocket_connections);
            this.updateMetricCard('totalConnections', stats.websocket_connections);
            
            console.log('Updating activeSubscriptions:', stats.active_subscriptions);
            this.updateMetricCard('activeSubscriptions', stats.active_subscriptions);
            
            console.log('Updating recentMetrics:', stats.recent_metrics_count);
            this.updateMetricCard('recentMetrics', stats.recent_metrics_count);
            
            // Also update the connection status if we have WebSocket connections
            if (stats.websocket_connections > 0) {
                this.updateConnectionStatus(true);
            }
            
        } catch (error) {
            console.error('Error updating dashboard stats:', error);
        }
    }
    
    updateMetricCard(cardId, value) {
        const card = document.getElementById(cardId);
        if (card) {
            const valueElement = card.querySelector('.metric-value');
            if (valueElement) {
                valueElement.textContent = value;
                console.log(`Updated ${cardId} to ${value}`);
            } else {
                console.warn(`Value element not found in ${cardId}`);
            }
        } else {
            console.warn(`Metric card ${cardId} not found`);
        }
    }
    
    async loadAnomalies() {
        try {
            console.log('Loading anomalies...');
            const response = await fetch('/api/anomalies?hours=1');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log(`Found ${data.anomalies?.length || 0} anomalies`);
            
            this.renderAnomalies(data.anomalies);
            
        } catch (error) {
            console.error('Error loading anomalies:', error);
        }
    }
    
    renderAnomalies(anomalies) {
        const container = document.getElementById('anomaliesList');
        if (!container) {
            console.warn('Anomalies container not found');
            return;
        }
        
        if (anomalies.length === 0) {
            container.innerHTML = '<div class="no-anomalies">No anomalies detected in the last hour</div>';
            console.log('No anomalies to display');
            return;
        }
        
        const html = anomalies.map(anomaly => `
            <div class="alert-item ${anomaly.severity}">
                <svg class="alert-icon" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M12,2L13.09,8.26L22,9L13.09,9.74L12,16L10.91,9.74L2,9L10.91,8.26L12,2Z"/>
                </svg>
                <div class="alert-content">
                    <div class="alert-message">
                        ${anomaly.service.toUpperCase()} ${this.formatMetricName(anomaly.metric_name)} Anomaly
                    </div>
                    <div class="alert-details">
                        Value: ${anomaly.value.toFixed(2)} | Z-Score: ${anomaly.z_score.toFixed(2)} | ${new Date(anomaly.timestamp).toLocaleTimeString()}
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
        console.log(`Rendered ${anomalies.length} anomalies`);
    }
    
    async generateSampleData() {
        try {
            const btn = document.getElementById('generateSampleData');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<div class="loading"></div> Generating...';
            }
            
            console.log('Generating sample data...');
            const response = await fetch('/api/generate-sample-data', {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('Sample data generated:', result);
            
            // Refresh dashboard after generating data
            setTimeout(() => {
                this.refreshDashboard();
            }, 1000);
            
        } catch (error) {
            console.error('Error generating sample data:', error);
            this.showError('Failed to generate sample data');
        } finally {
            const btn = document.getElementById('generateSampleData');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = 'Generate Sample Data';
            }
        }
    }
    
    async refreshDashboard() {
        console.log('Refreshing dashboard...');
        await this.loadInitialData();
    }
    
    handleMetricsUpdate(data) {
        console.log('Metrics update received:', data);
        // Update relevant charts
        this.refreshDashboard();
    }
    
    handleAnomalyDetected(data) {
        console.log('Anomaly detected:', data);
        // Show notification or update alerts
        this.showNotification(`Anomaly detected in ${data.service}: ${data.metric_name}`, 'warning');
    }
    
    showError(message) {
        console.error(message);
        // You could implement a toast notification system here
        alert(`Error: ${message}`);
    }
    
    showNotification(message, type = 'info') {
        console.log(`${type.toUpperCase()}: ${message}`);
        // You could implement a toast notification system here
    }
    
    setupPeriodicUpdates() {
        // Update dashboard stats every 30 seconds
        setInterval(() => {
            this.updateDashboardStats();
        }, 30000);
        
        // Reload anomalies every 60 seconds
        setInterval(() => {
            this.loadAnomalies();
        }, 60000);
    }
    
    updateTimeRange(range) {
        console.log('Time range updated:', range);
        // Implement time range filtering
        this.refreshDashboard();
    }
    
    updateServiceFilter(service) {
        console.log('Service filter updated:', service);
        // Implement service filtering
        this.refreshDashboard();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing dashboard...');
    window.dashboard = new DashboardApp();
});

// Also try to initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
    console.log('DOM still loading, waiting...');
} else {
    console.log('DOM already loaded, initializing immediately...');
    window.dashboard = new DashboardApp();
} 