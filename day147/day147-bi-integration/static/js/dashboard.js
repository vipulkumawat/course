// Dashboard state
let authToken = null;
let refreshInterval = null;
let charts = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Check for stored token
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
        authToken = storedToken;
        showDashboard();
    } else {
        showLogin();
    }
});

// Login functionality
async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        formData.append('grant_type', 'password');
        
        const response = await fetch('/oauth/token', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Authentication failed');
        }
        
        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);
        
        showDashboard();
    } catch (error) {
        showError('Login failed. Please check your credentials.');
        console.error('Login error:', error);
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    showLogin();
}

function showLogin() {
    document.getElementById('login-section').classList.remove('hidden');
    document.getElementById('dashboard-section').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('dashboard-section').classList.remove('hidden');
    loadDashboardData();
    startAutoRefresh();
}

// API calls
async function apiCall(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetch(endpoint, {
        ...options,
        headers
    });
    
    if (response.status === 401) {
        logout();
        throw new Error('Session expired');
    }
    
    if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
    }
    
    return response.json();
}

// Load dashboard data
async function loadDashboardData() {
    try {
        showLoading();
        
        // Load data in parallel for faster loading
        const [schema, recentData, exports] = await Promise.allSettled([
            apiCall('/api/v1/metrics/schema'),
            fetchRecentMetrics(),
            apiCall('/api/v1/exports/manifest').catch(() => [])
        ]);
        
        // Update metrics if successful
        if (schema.status === 'fulfilled' && recentData.status === 'fulfilled') {
            updateMetrics(schema.value, recentData.value);
        } else if (recentData.status === 'rejected') {
            console.error('Failed to fetch metrics:', recentData.reason);
            // Show zero values if data fetch fails
            updateMetricCard('requests', '0', 'N/A');
            updateMetricCard('response-time', '0 ms', 'N/A');
            updateMetricCard('error-rate', '0%', 'N/A');
        }
        
        // Load charts
        if (recentData.status === 'fulfilled') {
            loadCharts();
        } else {
            // Show message if chart data unavailable
            const chartContainer = document.getElementById('timeseries-chart');
            if (chartContainer && chartContainer.parentElement) {
                chartContainer.parentElement.innerHTML = '<p class="loading">Unable to load chart data. Please check InfluxDB connection.</p>';
            }
        }
        
        // Load exports
        if (exports.status === 'fulfilled') {
            const exportsList = Array.isArray(exports.value) ? exports.value : (exports.value.exports || []);
            renderExports(exportsList);
        } else {
            renderExports([]);
        }
        
        hideLoading();
        updateLastRefresh();
    } catch (error) {
        showError('Failed to load dashboard data: ' + error.message);
        console.error('Dashboard load error:', error);
        hideLoading();
    }
}

async function fetchRecentMetrics() {
    const end = new Date();
    const start = new Date(end.getTime() - 24 * 60 * 60 * 1000); // Last 24 hours
    
    try {
        const query = {
            measurement: "http_requests",
            time_range: {
                start: start.toISOString(),
                end: end.toISOString()
            },
            aggregation_window: "1h",
            metrics: ["count", "avg"],
            page_size: 1000
        };
        
        return await apiCall('/api/v1/metrics/timeseries', {
            method: 'POST',
            body: JSON.stringify(query)
        });
    } catch (error) {
        console.error('Error fetching metrics:', error);
        return { data: [], total_rows: 0 };
    }
}

function updateMetrics(schema, dataResponse) {
    const data = dataResponse.data || [];
    
    // Calculate metrics
    let totalRequests = 0;
    let totalResponseTime = 0;
    let responseTimeCount = 0;
    let errorCount = 0;
    
    data.forEach(item => {
        if (item.value !== undefined && item.value !== null) {
            totalRequests += parseFloat(item.value) || 0;
        }
        if (item.avg_response_time !== undefined && item.avg_response_time !== null) {
            totalResponseTime += parseFloat(item.avg_response_time);
            responseTimeCount++;
        }
        if (item.error_rate !== undefined && item.error_rate !== null) {
            errorCount += parseFloat(item.error_rate);
        }
    });
    
    const avgResponseTime = responseTimeCount > 0 ? totalResponseTime / responseTimeCount : 0;
    const errorRate = data.length > 0 ? (errorCount / data.length) * 100 : 0;
    
    // Update metric cards (show 0 if no data)
    updateMetricCard('requests', totalRequests > 0 ? totalRequests.toLocaleString() : '0', '+0%');
    updateMetricCard('response-time', avgResponseTime > 0 ? avgResponseTime.toFixed(2) + ' ms' : '0 ms', '+0%');
    updateMetricCard('error-rate', errorRate > 0 ? errorRate.toFixed(2) + '%' : '0%', '+0%');
}

function updateMetricCard(id, value, change) {
    const card = document.getElementById(`metric-${id}`);
    if (card) {
        const valueEl = card.querySelector('.metric-value');
        const changeEl = card.querySelector('.metric-change');
        if (valueEl) valueEl.textContent = value;
        if (changeEl) {
            changeEl.textContent = change;
            changeEl.className = 'metric-change ' + (change.startsWith('+') ? 'positive' : 'negative');
        }
    }
}

function loadCharts() {
    loadTimeSeriesChart();
}

async function loadTimeSeriesChart() {
    const end = new Date();
    const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000); // Last 7 days
    
    try {
        const query = {
            measurement: "http_requests",
            time_range: {
                start: start.toISOString(),
                end: end.toISOString()
            },
            aggregation_window: "1h",
            metrics: ["count", "avg"],
            page_size: 10000
        };
        
        const response = await apiCall('/api/v1/metrics/timeseries', {
            method: 'POST',
            body: JSON.stringify(query)
        });
        
        renderTimeSeriesChart(response.data || []);
    } catch (error) {
        console.error('Error loading chart:', error);
    }
}

function renderTimeSeriesChart(data) {
    const ctx = document.getElementById('timeseries-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.timeseries) {
        charts.timeseries.destroy();
    }
    
    // Prepare data
    const labels = [];
    const requestData = [];
    const responseTimeData = [];
    
    if (!data || data.length === 0) {
        ctx.parentElement.innerHTML = '<p class="loading">No data available for the selected time range</p>';
        return;
    }
    
    data.forEach(item => {
        // Handle both 'time' and 'timestamp' fields
        const timeField = item.time || item.timestamp;
        if (timeField) {
            const date = new Date(timeField);
            labels.push(date.toLocaleString());
            requestData.push(item.value || 0);
            responseTimeData.push(item.avg_response_time || 0);
        }
    });
    
    if (labels.length === 0) {
        ctx.parentElement.innerHTML = '<p class="loading">No valid data points found</p>';
        return;
    }
    
    // Create chart using Chart.js (fallback to simple visualization if not available)
    if (typeof Chart !== 'undefined' && Chart.Chart) {
        charts.timeseries = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Request Count',
                        data: requestData,
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Avg Response Time (ms)',
                        data: responseTimeData,
                        borderColor: '#e67e22',
                        backgroundColor: 'rgba(230, 126, 34, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Request Count'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Response Time (ms)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    } else {
        // Simple fallback visualization
        ctx.innerHTML = '<p>Chart library not loaded. Data points: ' + data.length + '</p>';
    }
}

// Export functionality
async function generateExport(event) {
    event.preventDefault();
    
    const dateInput = document.getElementById('export-date');
    const formatSelect = document.getElementById('export-format');
    
    const date = new Date(dateInput.value);
    if (isNaN(date.getTime())) {
        showError('Please select a valid date');
        return;
    }
    
    try {
        const exportBtn = document.getElementById('export-btn');
        exportBtn.disabled = true;
        exportBtn.textContent = 'Generating...';
        
        const request = {
            date: date.toISOString(),
            format: formatSelect.value
        };
        
        const metadata = await apiCall('/api/v1/exports/generate', {
            method: 'POST',
            body: JSON.stringify(request)
        });
        
        showSuccess(`Export generated successfully! ID: ${metadata.export_id}`);
        loadExports();
        
        exportBtn.disabled = false;
        exportBtn.textContent = 'Generate Export';
    } catch (error) {
        showError('Failed to generate export: ' + error.message);
        const exportBtn = document.getElementById('export-btn');
        exportBtn.disabled = false;
        exportBtn.textContent = 'Generate Export';
    }
}

async function loadExports() {
    try {
        const exports = await apiCall('/api/v1/exports/manifest');
        // Handle both array response and object with exports key
        const exportsList = Array.isArray(exports) ? exports : (exports.exports || []);
        renderExports(exportsList);
    } catch (error) {
        console.error('Error loading exports:', error);
        renderExports([]);
    }
}

function renderExports(exports) {
    const container = document.getElementById('export-list');
    if (!container) return;
    
    if (exports.length === 0) {
        container.innerHTML = '<p class="loading">No exports available</p>';
        return;
    }
    
    container.innerHTML = exports.map(exp => `
        <div class="export-item">
            <div class="export-item-info">
                <strong>Export ${exp.export_id}</strong>
                <span>${new Date(exp.date).toLocaleDateString()} • ${exp.format.toUpperCase()} • ${exp.row_count} rows</span>
            </div>
            <a href="${exp.url}" class="btn btn-primary" download>Download</a>
        </div>
    `).join('');
}

// Auto-refresh
function startAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Refresh every 30 seconds
    refreshInterval = setInterval(() => {
        loadDashboardData();
    }, 30000);
}

function manualRefresh() {
    loadDashboardData();
}

// UI helpers
function showLoading() {
    const loading = document.getElementById('loading-indicator');
    if (loading) loading.classList.remove('hidden');
}

function hideLoading() {
    const loading = document.getElementById('loading-indicator');
    if (loading) loading.classList.add('hidden');
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    
    const dashboard = document.getElementById('dashboard-section');
    if (dashboard) {
        dashboard.insertBefore(errorDiv, dashboard.firstChild);
        setTimeout(() => errorDiv.remove(), 5000);
    }
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.textContent = message;
    
    const dashboard = document.getElementById('dashboard-section');
    if (dashboard) {
        dashboard.insertBefore(successDiv, dashboard.firstChild);
        setTimeout(() => successDiv.remove(), 5000);
    }
}

function updateLastRefresh() {
    const indicator = document.getElementById('last-refresh');
    if (indicator) {
        indicator.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
    }
}
