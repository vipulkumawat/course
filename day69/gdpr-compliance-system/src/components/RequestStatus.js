import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

const RequestStatus = () => {
  const { requestId } = useParams();
  const [requestData, setRequestData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRequestStatus();
    const interval = setInterval(fetchRequestStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [requestId]);

  const fetchRequestStatus = async () => {
    try {
      const response = await fetch(`/api/erasure-requests/${requestId}`);
      if (response.ok) {
        const data = await response.json();
        setRequestData(data);
        setError(null);
      } else {
        setError('Request not found');
      }
    } catch (err) {
      setError('Error fetching request status');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading request status...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="request-status">
      <div className="status-header">
        <h2>Erasure Request Status</h2>
        <span className={`status-badge ${requestData.status.toLowerCase()}`}>
          {requestData.status}
        </span>
      </div>

      <div className="request-details">
        <p><strong>Request ID:</strong> {requestData.request_id}</p>
        <p><strong>User ID:</strong> {requestData.user_id}</p>
        <p><strong>Created:</strong> {new Date(requestData.created_at).toLocaleString()}</p>
        {requestData.completed_at && (
          <p><strong>Completed:</strong> {new Date(requestData.completed_at).toLocaleString()}</p>
        )}
      </div>

      <div className="audit-logs">
        <h3>Audit Logs ({requestData.audit_logs.length})</h3>
        {requestData.audit_logs.map((log, index) => (
          <div key={index} className="audit-log">
            <div className="audit-log-header">
              <span className="audit-log-action">{log.action} - {log.component}</span>
              <span className="audit-log-timestamp">
                {new Date(log.timestamp).toLocaleString()}
              </span>
            </div>
            <div className="audit-log-details">
              Records affected: {log.records_affected} | Status: {log.status}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RequestStatus;
