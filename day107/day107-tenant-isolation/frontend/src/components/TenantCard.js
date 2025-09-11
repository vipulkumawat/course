import React from 'react';

const TenantCard = ({ tenant, metrics }) => {
  const getTierColor = (tier) => {
    switch (tier) {
      case 'basic': return '#4CAF50';
      case 'premium': return '#FF9800';
      case 'enterprise': return '#9C27B0';
      default: return '#666';
    }
  };

  const getQuotaColor = (utilization) => {
    if (utilization >= 90) return 'quota-critical';
    if (utilization >= 70) return 'quota-warning';
    return 'quota-normal';
  };

  const formatBytes = (bytes) => {
    return `${Math.round(bytes)}MB`;
  };

  if (!metrics) {
    return (
      <div className={`tenant-card tenant-${tenant.tier} loading`}>
        <h3>{tenant.name}</h3>
        <p>Loading metrics...</p>
      </div>
    );
  }

  const { utilization, metrics: tenantMetrics } = metrics;

  return (
    <div className={`tenant-card tenant-${tenant.tier}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3>{tenant.name}</h3>
        <span
          style={{
            background: getTierColor(tenant.tier),
            color: 'white',
            padding: '4px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 'bold',
            textTransform: 'uppercase'
          }}
        >
          {tenant.tier}
        </span>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <p><strong>Tenant ID:</strong> {tenant.id}</p>
      </div>

      <div className="quotas">
        <div style={{ marginBottom: '15px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>CPU Usage</span>
            <span>{utilization.cpu?.toFixed(1) || 0}%</span>
          </div>
          <div className="quota-bar">
            <div
              className={`quota-fill ${getQuotaColor(utilization.cpu || 0)}`}
              style={{ width: `${Math.min(utilization.cpu || 0, 100)}%` }}
            ></div>
          </div>
          <small>{tenant.quota.cpu_cores} cores allocated</small>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Memory Usage</span>
            <span>{utilization.memory?.toFixed(1) || 0}%</span>
          </div>
          <div className="quota-bar">
            <div
              className={`quota-fill ${getQuotaColor(utilization.memory || 0)}`}
              style={{ width: `${Math.min(utilization.memory || 0, 100)}%` }}
            ></div>
          </div>
          <small>{formatBytes(tenant.quota.memory_mb)} allocated</small>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Request Rate</span>
            <span>{utilization.requests?.toFixed(1) || 0}%</span>
          </div>
          <div className="quota-bar">
            <div
              className={`quota-fill ${getQuotaColor(utilization.requests || 0)}`}
              style={{ width: `${Math.min(utilization.requests || 0, 100)}%` }}
            ></div>
          </div>
          <small>{tenant.quota.requests_per_minute}/min limit</small>
        </div>

        <div style={{ marginBottom: '15px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Connections</span>
            <span>{utilization.connections?.toFixed(1) || 0}%</span>
          </div>
          <div className="quota-bar">
            <div
              className={`quota-fill ${getQuotaColor(utilization.connections || 0)}`}
              style={{ width: `${Math.min(utilization.connections || 0, 100)}%` }}
            ></div>
          </div>
          <small>{tenant.quota.concurrent_connections} max connections</small>
        </div>
      </div>

      <div style={{
        marginTop: '20px',
        padding: '15px',
        background: '#f8f9fa',
        borderRadius: '8px'
      }}>
        <h4 style={{ margin: '0 0 10px 0', color: '#333' }}>Current Usage</h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '14px' }}>
          <div>CPU: {tenantMetrics.current_usage?.cpu_usage_percent?.toFixed(1) || 0}%</div>
          <div>Memory: {formatBytes(tenantMetrics.current_usage?.memory_usage_mb || 0)}</div>
          <div>Requests: {tenantMetrics.current_usage?.active_requests || 0}</div>
          <div>Connections: {tenantMetrics.current_usage?.concurrent_connections || 0}</div>
        </div>
      </div>
    </div>
  );
};

export default TenantCard;
