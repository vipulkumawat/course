import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const HeatmapChart = () => {
  const canvasRef = useRef(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [loading, setLoading] = useState(true);

  const drawHeatmap = (canvas, data) => {
    const ctx = canvas.getContext('2d');
    const { x_labels, y_labels, values } = data;
    
    const cellWidth = canvas.width / x_labels.length;
    const cellHeight = canvas.height / y_labels.length;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Find min and max values for color scaling
    const flatValues = values.flat();
    const minValue = Math.min(...flatValues);
    const maxValue = Math.max(...flatValues);
    
    // Draw heatmap cells
    for (let y = 0; y < y_labels.length; y++) {
      for (let x = 0; x < x_labels.length; x++) {
        const value = values[y][x];
        const intensity = (value - minValue) / (maxValue - minValue);
        
        // Color based on intensity (blue to red)
        const red = Math.floor(intensity * 255);
        const blue = Math.floor((1 - intensity) * 255);
        const green = 50;
        
        ctx.fillStyle = `rgb(${red}, ${green}, ${blue})`;
        ctx.fillRect(x * cellWidth, y * cellHeight, cellWidth, cellHeight);
        
        // Add value text
        ctx.fillStyle = intensity > 0.5 ? 'white' : 'black';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(
          value.toFixed(1),
          x * cellWidth + cellWidth / 2,
          y * cellHeight + cellHeight / 2 + 4
        );
      }
    }
    
    // Draw labels
    ctx.fillStyle = 'black';
    ctx.font = '10px Arial';
    
    // X-axis labels
    for (let x = 0; x < x_labels.length; x++) {
      ctx.save();
      ctx.translate(x * cellWidth + cellWidth / 2, canvas.height + 15);
      ctx.rotate(-Math.PI / 4);
      ctx.textAlign = 'right';
      ctx.fillText(x_labels[x], 0, 0);
      ctx.restore();
    }
    
    // Y-axis labels
    ctx.textAlign = 'right';
    for (let y = 0; y < y_labels.length; y++) {
      ctx.fillText(
        y_labels[y],
        -5,
        y * cellHeight + cellHeight / 2 + 4
      );
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/api/v1/visualization/response-time-heatmap?hours=24');
        
        if (response.data) {
          setHeatmapData(response.data);
        } else {
          // Demo data
          const demoData = {
            x_labels: Array.from({length: 24}, (_, i) => `${i.toString().padStart(2, '0')}:00`),
            y_labels: ['API Gateway', 'User Service', 'Payment Service', 'Database'],
            values: Array.from({length: 4}, () => 
              Array.from({length: 24}, () => Math.random() * 500 + 100)
            )
          };
          setHeatmapData(demoData);
        }
        setLoading(false);
      } catch (error) {
        console.error('Error fetching heatmap data:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (heatmapData && canvasRef.current) {
      drawHeatmap(canvasRef.current, heatmapData);
    }
  }, [heatmapData]);

  if (loading) {
    return <div className="chart-loading">Loading heatmap...</div>;
  }

  return (
    <div className="heatmap-container">
      <div className="heatmap-wrapper">
        <canvas
          ref={canvasRef}
          width={600}
          height={300}
          style={{ maxWidth: '100%', height: 'auto' }}
        />
      </div>
      <div className="heatmap-legend">
        <span>Response Time (ms)</span>
        <div className="color-scale">
          <span>Low</span>
          <div className="gradient-bar"></div>
          <span>High</span>
        </div>
      </div>
    </div>
  );
};

export default HeatmapChart;
