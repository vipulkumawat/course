import React from 'react';
import './MetricsCards.css';

const MetricsCards = ({ metrics }) => {
  if (!metrics) return null;

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const cards = [
    {
      title: 'Total Logs',
      value: formatNumber(metrics.total_logs),
      subtitle: 'Last hour',
      icon: '📊',
      trend: metrics.total_logs > 1000 ? '+12%' : '+5%',
      trendUp: true
    },
    {
      title: 'Error Rate',
      value: metrics.error_rate + '%',
      subtitle: 'Current',
      icon: '🚨',
      trend: metrics.error_rate < 2 ? '-0.5%' : '+1.2%',
      trendUp: metrics.error_rate < 2
    },
    {
      title: 'Avg Response',
      value: metrics.avg_response_time + 'ms',
      subtitle: 'P50 latency',
      icon: '⚡',
      trend: metrics.avg_response_time < 100 ? '-15ms' : '+8ms',
      trendUp: metrics.avg_response_time < 100
    },
    {
      title: 'Active Services',
      value: metrics.active_services,
      subtitle: 'Online now',
      icon: '🟢',
      trend: '100%',
      trendUp: true
    }
  ];

  return (
    <div className="metrics-cards">
      {cards.map((card, index) => (
        <div key={index} className="metric-card">
          <div className="card-header">
            <span className="card-icon">{card.icon}</span>
            <span className="card-title">{card.title}</span>
          </div>
          <div className="card-value">{card.value}</div>
          <div className="card-footer">
            <span className="card-subtitle">{card.subtitle}</span>
            <span className={`card-trend ${card.trendUp ? 'up' : 'down'}`}>
              {card.trend}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MetricsCards;
