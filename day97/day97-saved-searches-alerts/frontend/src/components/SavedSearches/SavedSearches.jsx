import React, { useState } from 'react';
import { Plus, Search, Save, Trash2, Edit } from 'lucide-react';

const SavedSearches = () => {
  const [searches, setSearches] = useState([
    {
      id: 1,
      name: 'Error Logs',
      query: 'level:ERROR',
      description: 'All error level logs',
      lastRun: '2024-01-15T10:30:00Z',
      frequency: 'daily'
    },
    {
      id: 2,
      name: 'High CPU Usage',
      query: 'cpu_usage > 80',
      description: 'Logs indicating high CPU usage',
      lastRun: '2024-01-15T09:15:00Z',
      frequency: 'hourly'
    }
  ]);

  const [newSearch, setNewSearch] = useState({
    name: '',
    query: '',
    description: '',
    frequency: 'daily'
  });

  const [showForm, setShowForm] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (newSearch.name && newSearch.query) {
      const search = {
        ...newSearch,
        id: Date.now(),
        lastRun: new Date().toISOString()
      };
      setSearches([...searches, search]);
      setNewSearch({ name: '', query: '', description: '', frequency: 'daily' });
      setShowForm(false);
    }
  };

  const deleteSearch = (id) => {
    setSearches(searches.filter(search => search.id !== id));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Saved Searches</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Search
        </button>
      </div>

      {/* New Search Form */}
      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Search</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={newSearch.name}
                  onChange={(e) => setNewSearch({...newSearch, name: e.target.value})}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Search name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Frequency</label>
                <select
                  value={newSearch.frequency}
                  onChange={(e) => setNewSearch({...newSearch, frequency: e.target.value})}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Query</label>
              <input
                type="text"
                value={newSearch.query}
                onChange={(e) => setNewSearch({...newSearch, query: e.target.value})}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="Search query"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={newSearch.description}
                onChange={(e) => setNewSearch({...newSearch, description: e.target.value})}
                rows={3}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="Search description"
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                Save Search
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Saved Searches List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {searches.map((search) => (
            <li key={search.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Search className="h-5 w-5 text-gray-400 mr-3" />
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">{search.name}</h3>
                    <p className="text-sm text-gray-500">{search.description}</p>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className="text-xs text-gray-400">Query: {search.query}</span>
                      <span className="text-xs text-gray-400">Frequency: {search.frequency}</span>
                      <span className="text-xs text-gray-400">Last run: {new Date(search.lastRun).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button className="p-2 text-gray-400 hover:text-gray-600">
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => deleteSearch(search.id)}
                    className="p-2 text-gray-400 hover:text-red-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default SavedSearches;
