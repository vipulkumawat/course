import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import axios from 'axios';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const ErrorTrendChart = () => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedServices, setSelectedServices] = useState([]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Error Rate Trends by Service',
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`;
          }
        }
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Error Rate (%)'
        },
        min: 0,
        max: 100
      },
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get('/api/v1/visualization/error-trends?hours=24');
        
        if (response.data && response.data.length > 0) {
          const datasets = response.data.map(series => ({
            label: series.series_name,
            data: series.data_points.map(point => ({
              x: new Date(point.timestamp).toLocaleTimeString(),
              y: point.value
            })),
            borderColor: series.color,
            backgroundColor: series.color + '20',
            tension: 0.2,
            fill: false
          }));

          setChartData({
            datasets
          });
        } else {
          // Demo data when no real data available
          setChartData({
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [
              {
                label: 'API Gateway',
                data: Array.from({length: 24}, () => Math.random() * 10),
                borderColor: '#3b82f6',
                backgroundColor: '#3b82f620',
                tension: 0.2
              },
              {
                label: 'User Service',
                data: Array.from({length: 24}, () => Math.random() * 15),
                borderColor: '#ef4444',
                backgroundColor: '#ef444420',
                tension: 0.2
              },
              {
                label: 'Payment Service',
                data: Array.from({length: 24}, () => Math.random() * 5),
                borderColor: '#10b981',
                backgroundColor: '#10b98120',
                tension: 0.2
              }
            ]
          });
        }
        setLoading(false);
      } catch (error) {
        console.error('Error fetching error trends:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [selectedServices]);

  if (loading) {
    return <div className="chart-loading">Loading error trends...</div>;
  }

  return (
    <div className="chart-container">
      <div className="chart-wrapper">
        <Line options={options} data={chartData} />
      </div>
    </div>
  );
};

export default ErrorTrendChart;
