import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import axios from 'axios';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const ServiceBarChart = () => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState('requests');

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Service Performance Metrics',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const metric = selectedMetric;
            const value = context.parsed.y;
            
            switch(metric) {
              case 'requests':
                return `Requests: ${value.toLocaleString()}`;
              case 'avg_response_time':
                return `Avg Response: ${value.toFixed(2)}ms`;
              case 'error_rate':
                return `Error Rate: ${value.toFixed(2)}%`;
              default:
                return `${metric}: ${value}`;
            }
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: selectedMetric === 'requests' ? 'Request Count' :
                selectedMetric === 'avg_response_time' ? 'Response Time (ms)' :
                'Error Rate (%)'
        }
      }
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const elementIndex = elements[0].index;
        const serviceName = chartData.labels[elementIndex];
        console.log(`Clicked on service: ${serviceName}`);
        // Could implement drill-down functionality here
      }
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/api/v1/visualization/service-performance?hours=1');
        
        let data;
        if (response.data && response.data.length > 0) {
          data = response.data;
        } else {
          // Demo data
          data = [
            { service: 'API Gateway', requests: 1250, avg_response_time: 125.5, error_rate: 2.1 },
            { service: 'User Service', requests: 980, avg_response_time: 89.3, error_rate: 1.5 },
            { service: 'Payment Service', requests: 567, avg_response_time: 245.7, error_rate: 0.8 },
            { service: 'Notification Service', requests: 423, avg_response_time: 67.2, error_rate: 3.2 },
            { service: 'Analytics Service', requests: 234, avg_response_time: 156.8, error_rate: 1.9 }
          ];
        }

        const labels = data.map(item => item.service);
        const values = data.map(item => item[selectedMetric]);
        
        // Color based on values
        const colors = values.map(value => {
          if (selectedMetric === 'error_rate') {
            return value > 2 ? '#ef4444' : value > 1 ? '#f59e0b' : '#10b981';
          } else if (selectedMetric === 'avg_response_time') {
            return value > 200 ? '#ef4444' : value > 100 ? '#f59e0b' : '#10b981';
          } else {
            return '#3b82f6';
          }
        });

        setChartData({
          labels,
          datasets: [
            {
              label: selectedMetric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
              data: values,
              backgroundColor: colors,
              borderColor: colors.map(color => color.replace('44', '66')),
              borderWidth: 1,
            },
          ],
        });
        setLoading(false);
      } catch (error) {
        console.error('Error fetching service performance:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [selectedMetric]);

  if (loading) {
    return <div className="chart-loading">Loading service performance...</div>;
  }

  return (
    <div className="bar-chart-container">
      <div className="chart-controls">
        <label htmlFor="metric-select">Metric: </label>
        <select
          id="metric-select"
          value={selectedMetric}
          onChange={(e) => setSelectedMetric(e.target.value)}
        >
          <option value="requests">Request Count</option>
          <option value="avg_response_time">Average Response Time</option>
          <option value="error_rate">Error Rate</option>
        </select>
      </div>
      <div className="chart-wrapper">
        <Bar options={options} data={chartData} />
      </div>
    </div>
  );
};

export default ServiceBarChart;
