import React, { useEffect, useRef } from 'react';
import './TrafficGraph.css';

function TrafficGraph({ topology, threats }) {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    if (!canvasRef.current || !topology.nodes.length) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = canvas.offsetHeight;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Create threat lookup
    const threatMap = new Map();
    threats.forEach(threat => {
      threatMap.set(threat.source_ip, threat.threat_score);
    });
    
    // Position nodes in a circle
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.35;
    
    const nodePositions = new Map();
    topology.nodes.forEach((node, i) => {
      const angle = (i / topology.nodes.length) * 2 * Math.PI;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      nodePositions.set(node.id, { x, y });
    });
    
    // Draw edges
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    topology.edges.forEach(edge => {
      const source = nodePositions.get(edge.source);
      const target = nodePositions.get(edge.target);
      if (source && target) {
        const lineWidth = Math.min(5, Math.max(1, edge.bytes / 20000));
        ctx.lineWidth = lineWidth;
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      }
    });
    
    // Draw nodes
    topology.nodes.forEach(node => {
      const pos = nodePositions.get(node.id);
      if (!pos) return;
      
      // Use threat_score from node or threat map
      const threatScore = threatMap.get(node.id) || node.threat_score || 0;
      const nodeRadius = 20;
      
      // Node color based on threat score
      if (threatScore > 70) {
        ctx.fillStyle = '#dc2626'; // High risk - red
      } else if (threatScore > 40) {
        ctx.fillStyle = '#f97316'; // Medium risk - orange
      } else {
        ctx.fillStyle = '#10b981'; // Low risk - green
      }
      
      // Draw node
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeRadius, 0, 2 * Math.PI);
      ctx.fill();
      ctx.strokeStyle = 'white';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // Draw label
      ctx.fillStyle = '#1f2937';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(node.label, pos.x, pos.y + nodeRadius + 15);
    });
    
    // Draw legend
    ctx.fillStyle = '#1f2937';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('● Low Risk', 20, height - 60);
    ctx.fillStyle = '#f97316';
    ctx.fillText('● Medium Risk', 20, height - 40);
    ctx.fillStyle = '#dc2626';
    ctx.fillText('● High Risk', 20, height - 20);
    
  }, [topology, threats]);
  
  return (
    <div className="traffic-graph">
      <h2>🌐 Network Topology</h2>
      <canvas ref={canvasRef} className="topology-canvas"></canvas>
    </div>
  );
}

export default TrafficGraph;
