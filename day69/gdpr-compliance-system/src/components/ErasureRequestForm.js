import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const ErasureRequestForm = () => {
  const [formData, setFormData] = useState({
    user_id: '',
    request_type: 'DELETE'
  });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/erasure-requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Erasure request created successfully! Request ID: ${result.request_id}`);
        navigate(`/request-status/${result.request_id}`);
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
      <h2>Request Data Erasure</h2>
      <form onSubmit={handleSubmit} className="erasure-form">
        <div className="form-group">
          <label htmlFor="user_id">User ID:</label>
          <input
            type="text"
            id="user_id"
            name="user_id"
            value={formData.user_id}
            onChange={handleChange}
            required
            placeholder="Enter user ID to erase"
          />
        </div>

        <div className="form-group">
          <label htmlFor="request_type">Request Type:</label>
          <select
            id="request_type"
            name="request_type"
            value={formData.request_type}
            onChange={handleChange}
          >
            <option value="DELETE">Complete Deletion</option>
            <option value="ANONYMIZE">Anonymization</option>
          </select>
        </div>

        <button type="submit" disabled={loading} className="submit-btn">
          {loading ? 'Processing...' : 'Submit Request'}
        </button>
      </form>
    </div>
  );
};

export default ErasureRequestForm;
