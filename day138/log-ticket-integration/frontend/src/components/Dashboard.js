import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import axios from 'axios';

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444'];

function Dashboard() {
  const [stats, setStats] = useState({
    queue: { pending: 0, processing: 0, total: 0 },
    processing: { events_processed: 0, tickets_created: 0, success_rate: 0 },
    system_health: {},
    recent_tickets: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/dashboard/stats');
      setStats(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setLoading(false);
    }
  };

  const generateTestEvents = async () => {
    try {
      await axios.post('/api/events/test/generate', null, {
        params: { count: 20 }
      });
      fetchStats(); // Refresh stats
    } catch (error) {
      console.error('Error generating test events:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const healthStatus = (status) => {
    if (status) return <CheckCircle className="w-5 h-5 text-success-500" />;
    return <AlertTriangle className="w-5 h-5 text-error-500" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Ticket Integration Dashboard</h1>
        <button
          onClick={generateTestEvents}
          className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg transition-colors"
        >
          Generate Test Events
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <Clock className="w-8 h-8 text-warning-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Pending Events</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.queue.pending}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <Activity className="w-8 h-8 text-primary-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Events Processed</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.processing.events_processed}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-success-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Tickets Created</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.processing.tickets_created}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <Activity className="w-8 h-8 text-primary-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.processing.success_rate}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-xl font-semibold mb-4">System Health</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            {healthStatus(stats.system_health.event_processor)}
            <span>Event Processor</span>
          </div>
          <div className="flex items-center space-x-3">
            {healthStatus(stats.system_health.ticket_service)}
            <span>Ticket Service</span>
          </div>
          <div className="flex items-center space-x-3">
            {healthStatus(stats.system_health.redis)}
            <span>Redis Queue</span>
          </div>
        </div>
      </div>

      {/* Recent Tickets */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-xl font-semibold mb-4">Recent Tickets</h2>
        <div className="space-y-3">
          {stats.recent_tickets.map((ticket, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <div className="font-medium">{ticket.title}</div>
                <div className="text-sm text-gray-600">{ticket.id} • {ticket.system}</div>
              </div>
              <div className="text-sm text-gray-500">{ticket.created}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Configuration */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-xl font-semibold mb-4">Configuration</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600">JIRA Project:</span>
            <div className="font-medium">{stats.configuration?.jira_project}</div>
          </div>
          <div>
            <span className="text-gray-600">ServiceNow Table:</span>
            <div className="font-medium">{stats.configuration?.servicenow_table}</div>
          </div>
          <div>
            <span className="text-gray-600">Processing Interval:</span>
            <div className="font-medium">{stats.configuration?.processing_interval}s</div>
          </div>
          <div>
            <span className="text-gray-600">Batch Size:</span>
            <div className="font-medium">{stats.configuration?.batch_size}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
