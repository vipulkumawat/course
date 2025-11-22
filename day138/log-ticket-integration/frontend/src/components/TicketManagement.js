import React, { useState, useEffect } from 'react';
import { ExternalLink, Ticket } from 'lucide-react';
import axios from 'axios';

function TicketManagement() {
  const [stats, setStats] = useState({});
  const [templates, setTemplates] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTicketStats();
    fetchTemplates();
    const interval = setInterval(() => {
      fetchTicketStats();
      fetchTemplates();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchTicketStats = async () => {
    try {
      const response = await axios.get('/api/tickets/stats');
      setStats(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching ticket stats:', error);
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await axios.get('/api/tickets/templates');
      setTemplates(response.data.templates || {});
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const getPriorityLabel = (priority) => {
    const priorityMap = {
      '1': { label: 'Critical', color: 'bg-red-100 text-red-800' },
      '2': { label: 'High Priority', color: 'bg-red-100 text-red-800' },
      '3': { label: 'Medium Priority', color: 'bg-yellow-100 text-yellow-800' },
      '4': { label: 'Low Priority', color: 'bg-blue-100 text-blue-800' },
      '5': { label: 'Lowest', color: 'bg-gray-100 text-gray-800' },
    };
    return priorityMap[priority] || { label: 'Unknown', color: 'bg-gray-100 text-gray-800' };
  };

  const getTemplateDisplayName = (key) => {
    const nameMap = {
      'database_error': 'Database Error Template',
      'api_timeout': 'API Timeout Template',
      'infrastructure_alert': 'Infrastructure Alert Template',
    };
    return nameMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getTemplateDescription = (key) => {
    const descMap = {
      'database_error': 'For database connection issues, timeouts, and query failures',
      'api_timeout': 'For API endpoint timeouts and performance issues',
      'infrastructure_alert': 'For infrastructure and system-level issues',
    };
    return descMap[key] || 'Template for ticket creation';
  };

  const getSystemForTemplate = (key) => {
    // Determine which system to show based on template
    if (key === 'infrastructure_alert') {
      return { name: 'ServiceNow', color: 'bg-green-100 text-green-800' };
    }
    return { name: 'JIRA', color: 'bg-blue-100 text-blue-800' };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Ticket Management</h1>

      {/* Ticket Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <Ticket className="w-8 h-8 text-primary-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Total Created</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.total_created || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-500 rounded flex items-center justify-center text-white font-bold">
              J
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">JIRA Tickets</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.jira_tickets || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-500 rounded flex items-center justify-center text-white font-bold">
              S
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">ServiceNow</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.servicenow_tickets || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Ticket Templates */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-xl font-semibold mb-4">Available Templates</h2>
        
        {Object.keys(templates).length === 0 ? (
          <p className="text-gray-500">Loading templates...</p>
        ) : (
          <div className="space-y-4">
            {Object.entries(templates).map(([key, template]) => {
              const priority = getPriorityLabel(template.priority);
              const system = getSystemForTemplate(key);
              return (
                <div key={key} className="border rounded-lg p-4">
                  <h3 className="font-medium text-gray-900">{getTemplateDisplayName(key)}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {getTemplateDescription(key)}
                  </p>
                  <div className="flex space-x-2 mt-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${system.color}`}>
                      {system.name}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${priority.color}`}>
                      {priority.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Integration Links */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-xl font-semibold mb-4">External Systems</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a
            href="https://demo-jira.atlassian.net"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div>
              <h3 className="font-medium">JIRA Dashboard</h3>
              <p className="text-sm text-gray-600">View created issues and bugs</p>
            </div>
            <ExternalLink className="w-5 h-5 text-gray-400" />
          </a>

          <a
            href="https://demo.service-now.com"
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div>
              <h3 className="font-medium">ServiceNow Portal</h3>
              <p className="text-sm text-gray-600">View incidents and requests</p>
            </div>
            <ExternalLink className="w-5 h-5 text-gray-400" />
          </a>
        </div>
      </div>
    </div>
  );
}

export default TicketManagement;
