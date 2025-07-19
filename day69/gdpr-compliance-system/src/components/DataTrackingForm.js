import React, { useState } from 'react';

const DataTrackingForm = () => {
  const [formData, setFormData] = useState({
    user_id: '',
    data_type: '',
    storage_location: '',
    data_path: '',
    metadata: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = {
        ...formData,
        metadata: formData.metadata ? JSON.parse(formData.metadata) : null
      };

      const response = await fetch('/api/user-data-tracking', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Data tracking created successfully! Mapping ID: ${result.mapping_id}`);
        setFormData({
          user_id: '',
          data_type: '',
          storage_location: '',
          data_path: '',
          metadata: ''
        });
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="form-container">
      <h2>Track User Data</h2>
      <form onSubmit={handleSubmit} className="tracking-form">
        <div className="form-group">
          <label htmlFor="user_id">User ID:</label>
          <input
            type="text"
            id="user_id"
            name="user_id"
            value={formData.user_id}
            onChange={handleChange}
            required
            placeholder="Enter user ID"
          />
        </div>

        <div className="form-group">
          <label htmlFor="data_type">Data Type:</label>
          <select
            id="data_type"
            name="data_type"
            value={formData.data_type}
            onChange={handleChange}
            required
          >
            <option value="">Select data type</option>
            <option value="user_logs">User Logs</option>
            <option value="analytics_events">Analytics Events</option>
            <option value="performance_metrics">Performance Metrics</option>
            <option value="personal_data">Personal Data</option>
            <option value="behavioral_data">Behavioral Data</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="storage_location">Storage Location:</label>
          <input
            type="text"
            id="storage_location"
            name="storage_location"
            value={formData.storage_location}
            onChange={handleChange}
            required
            placeholder="e.g., postgresql_main, redis_cache"
          />
        </div>

        <div className="form-group">
          <label htmlFor="data_path">Data Path:</label>
          <input
            type="text"
            id="data_path"
            name="data_path"
            value={formData.data_path}
            onChange={handleChange}
            required
            placeholder="e.g., /logs/user_activity, table:user_sessions"
          />
        </div>

        <div className="form-group">
          <label htmlFor="metadata">Metadata (JSON):</label>
          <textarea
            id="metadata"
            name="metadata"
            value={formData.metadata}
            onChange={handleChange}
            placeholder='{"sensitivity": "high", "retention_days": 30}'
          />
        </div>

        <button type="submit" disabled={loading} className="submit-btn">
          {loading ? 'Processing...' : 'Track Data'}
        </button>
      </form>
    </div>
  );
};

export default DataTrackingForm;
