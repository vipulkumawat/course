// Service Dependency Mapper - Frontend
let ws;
let graph = { nodes: [], edges: [] };
let simulation;

// Connect to WebSocket server
function connect() {
    ws = new WebSocket('ws://localhost:8765');
    
    ws.onopen = () => {
        console.log('Connected to server');
        updateStatus(true);
    };
    
    ws.onclose = () => {
        console.log('Disconnected from server');
        updateStatus(false);
        setTimeout(connect, 3000); // Reconnect after 3s
    };
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

function updateStatus(connected) {
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');
    
    if (connected) {
        indicator.className = 'connection-status connected';
        text.textContent = 'Connected';
    } else {
        indicator.className = 'connection-status disconnected';
        text.textContent = 'Disconnected';
    }
}

function handleMessage(message) {
    switch (message.type) {
        case 'init':
            graph = message.data;
            initializeGraph();
            updateStats();
            requestCriticalPaths();
            break;
        
        case 'update':
            addDependency(message.dependency);
            updateStats();
            break;
        
        case 'alert':
            showAlert(message);
            break;
        
        case 'critical_paths':
            displayCriticalPaths(message.paths);
            break;
    }
}

function initializeGraph() {
    const container = document.getElementById('graph-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Clear existing SVG
    d3.select('#graph-container').selectAll('*').remove();
    
    const svg = d3.select('#graph-container')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // Create arrow marker
    svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '-0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('orient', 'auto')
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .append('svg:path')
        .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
        .attr('fill', '#999');
    
    simulation = d3.forceSimulation(graph.nodes)
        .force('link', d3.forceLink(graph.edges).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30));
    
    const link = svg.append('g')
        .selectAll('line')
        .data(graph.edges)
        .enter()
        .append('line')
        .attr('class', 'link')
        .attr('stroke-width', d => Math.min(Math.sqrt(d.weight) * 2, 8))
        .attr('marker-end', 'url(#arrowhead)');
    
    const node = svg.append('g')
        .selectAll('circle')
        .data(graph.nodes)
        .enter()
        .append('circle')
        .attr('class', 'node')
        .attr('r', 15)
        .attr('fill', d => getNodeColor(d.id))
        .call(drag(simulation))
        .on('click', (event, d) => {
            // Request impact analysis
            ws.send(JSON.stringify({
                type: 'get_impact',
                service: d.id
            }));
        });
    
    const label = svg.append('g')
        .selectAll('text')
        .data(graph.nodes)
        .enter()
        .append('text')
        .attr('class', 'node-label')
        .attr('dy', 25)
        .text(d => d.label);
    
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        label
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
}

function addDependency(dep) {
    // Add nodes if they don't exist
    if (!graph.nodes.find(n => n.id === dep.caller)) {
        graph.nodes.push({ id: dep.caller, label: dep.caller });
    }
    if (!graph.nodes.find(n => n.id === dep.callee)) {
        graph.nodes.push({ id: dep.callee, label: dep.callee });
    }
    
    // Update or add edge
    const existingEdge = graph.edges.find(
        e => e.source.id === dep.caller && e.target.id === dep.callee
    );
    
    if (existingEdge) {
        existingEdge.weight += 1;
    } else {
        graph.edges.push({
            source: dep.caller,
            target: dep.callee,
            weight: 1,
            avgLatency: dep.latency
        });
    }
    
    // Restart simulation with new data
    if (simulation) {
        simulation.nodes(graph.nodes);
        simulation.force('link').links(graph.edges);
        simulation.alpha(0.3).restart();
    }
}

function getNodeColor(nodeId) {
    const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b'];
    const hash = nodeId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[hash % colors.length];
}

function drag(simulation) {
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
    
    return d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended);
}

function updateStats() {
    document.getElementById('services-count').textContent = graph.nodes.length;
    document.getElementById('dependencies-count').textContent = graph.edges.length;
}

function showAlert(message) {
    const container = document.getElementById('alerts-container');
    
    if (message.alert_type === 'cycle') {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger';
        alert.innerHTML = `<strong>⚠ Circular Dependency:</strong> ${message.cycles[0].join(' → ')}`;
        container.insertBefore(alert, container.firstChild);
    } else if (message.alert_type === 'spof') {
        const alert = document.createElement('div');
        alert.className = 'alert alert-warning';
        const service = message.spofs[0];
        alert.innerHTML = `<strong>⚠ Single Point of Failure:</strong> ${service.service} (${service.count} dependencies)`;
        container.insertBefore(alert, container.firstChild);
    }
    
    // Keep only last 10 alerts
    while (container.children.length > 10) {
        container.removeChild(container.lastChild);
    }
}

function requestCriticalPaths() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'get_critical_paths' }));
    }
}

function displayCriticalPaths(paths) {
    const container = document.getElementById('paths-container');
    container.innerHTML = '';
    
    if (paths.length === 0) {
        container.innerHTML = '<div class="list-item">No critical paths detected</div>';
        return;
    }
    
    paths.slice(0, 5).forEach((pathData, index) => {
        const div = document.createElement('div');
        div.className = 'list-item';
        div.innerHTML = `
            <strong>Path ${index + 1}:</strong> ${pathData.path.join(' → ')}<br>
            <small>Total Latency: ${pathData.latency}ms</small>
        `;
        container.appendChild(div);
    });
}

// Initialize connection on page load
connect();

// Request critical paths every 5 seconds
setInterval(requestCriticalPaths, 5000);
