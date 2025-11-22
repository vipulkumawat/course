import React, { useState } from 'react';
import { Send, AlertCircle } from 'lucide-react';
import axios from 'axios';

function EventSubmission() {
  const [event, setEvent] = useState({
    level: 'error',
    service: 'web-api',
    component: 'handler',
    message: 'Database connection timeout after 30 seconds'
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      const eventData = {
        id: `event-${Date.now()}`,
        timestamp: new Date().toISOString(),
        ...event,
        host: 'demo-host-1.cluster.local',
        request_id: `req-${Date.now()}`,
        metadata: {
          environment: 'production',
          region: 'us-east-1'
        }
      };
      
      const response = await axios.post('/api/events/submit', eventData);
      setResult({ type: 'success', data: response.data });
    } catch (error) {
      setResult({ type: 'error', message: error.response?.data?.detail || error.message });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white p-8 rounded-lg shadow-sm border">
        <h1 className="text-2xl font-bold mb-6">Submit Log Event</h1>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Log Level
            </label>
            <select
              value={event.level}
              onChange={(e) => setEvent({ ...event, level: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Service
            </label>
            <select
              value={event.service}
              onChange={(e) => setEvent({ ...event, service: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="web-api">Web API</option>
              <option value="payment-service">Payment Service</option>
              <option value="user-auth">User Auth</option>
              <option value="database">Database</option>
              <option value="cache">Cache</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Component
            </label>
            <input
              type="text"
              value={event.component}
              onChange={(e) => setEvent({ ...event, component: e.target.value })}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="handler, processor, validator..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Error Message
            </label>
            <textarea
              value={event.message}
              onChange={(e) => setEvent({ ...event, message: e.target.value })}
              rows={4}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Describe the error or event..."
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center space-x-2 bg-primary-500 hover:bg-primary-600 disabled:bg-gray-400 text-white py-3 px-6 rounded-lg transition-colors"
          >
            {submitting ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>{submitting ? 'Submitting...' : 'Submit Event'}</span>
          </button>
        </form>

        {result && (
          <div className={`mt-6 p-4 rounded-lg ${
            result.type === 'success' ? 'bg-success-50 text-success-700' : 'bg-error-50 text-error-700'
          }`}>
            {result.type === 'success' ? (
              <div>
                <h3 className="font-medium">Event submitted successfully!</h3>
                <p className="text-sm mt-1">Event ID: {result.data.event_id}</p>
                <p className="text-sm">Queue position: {result.data.queue_position}</p>
              </div>
            ) : (
              <div className="flex items-start space-x-2">
                <AlertCircle className="w-5 h-5 mt-0.5" />
                <div>
                  <h3 className="font-medium">Error submitting event</h3>
                  <p className="text-sm mt-1">{result.message}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default EventSubmission;
