import React from 'react';
import ErrorTrendChart from './ErrorTrendChart';
import HeatmapChart from './HeatmapChart';
import ServiceBarChart from './ServiceBarChart';

const ChartContainer = () => {
  return (
    <div className="chart-container-page">
      <h2>Interactive Charts</h2>
      <p>Explore your log data with interactive visualizations</p>
      
      <div className="charts-grid">
        <div className="chart-section">
          <h3>Error Trends</h3>
          <ErrorTrendChart />
        </div>
        
        <div className="chart-section">
          <h3>Response Time Heatmap</h3>
          <HeatmapChart />
        </div>
        
        <div className="chart-section full-width">
          <h3>Service Performance</h3>
          <ServiceBarChart />
        </div>
      </div>
    </div>
  );
};

export default ChartContainer;
