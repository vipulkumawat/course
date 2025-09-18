import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Eye, Clock, Database, AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react';
import { searchLogs, getStatistics } from '../services/api';

const LogViewer = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTier, setSelectedTier] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);

  const { data: searchResults, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['searchLogs', searchQuery, selectedTier],
    queryFn: () => searchLogs(searchQuery, selectedTier || null),
    enabled: searchQuery.length > 0,
    refetchInterval: 10000, // Refetch every 10 seconds for search results
    refetchIntervalInBackground: true,
    staleTime: 5000, // Consider data stale after 5 seconds
  });

  // Get real-time statistics for activity feed
  const { data: stats } = useQuery({
    queryKey: ['statistics'],
    queryFn: getStatistics,
    refetchInterval: 5000, // Refetch every 5 seconds
    refetchIntervalInBackground: true,
    staleTime: 1000,
  });

  // Auto-search as user types (with debounce)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery.trim()) {
        refetch();
      }
    }, 500); // 500ms debounce

    return () => clearTimeout(timeoutId);
  }, [searchQuery, selectedTier, refetch]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      refetch();
    }
  };

  const getLogLevelIcon = (level) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'WARN':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'INFO':
        return <Info className="w-4 h-4 text-blue-500" />;
      case 'DEBUG':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      default:
        return <Info className="w-4 h-4 text-gray-500" />;
    }
  };

  const getTierBadgeColor = (tier) => {
    switch (tier?.toLowerCase()) {
      case 'hot':
        return 'bg-red-100 text-red-800';
      case 'warm':
        return 'bg-orange-100 text-orange-800';
      case 'cold':
        return 'bg-blue-100 text-blue-800';
      case 'archive':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-3">
          <h1 className="text-3xl font-bold text-gray-900">Log Viewer</h1>
          {isFetching && searchQuery && (
            <div className="flex items-center space-x-2 text-sm text-blue-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span>Updating...</span>
            </div>
          )}
        </div>
        <p className="text-gray-600 mt-1">Search and explore log entries across all storage tiers</p>
      </div>

      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
                Search Query
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  id="search"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Enter search terms, service names, or log levels..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="md:w-48">
              <label htmlFor="tier" className="block text-sm font-medium text-gray-700 mb-2">
                Storage Tier
              </label>
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <select
                  id="tier"
                  value={selectedTier}
                  onChange={(e) => setSelectedTier(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
                >
                  <option value="">All Tiers</option>
                  <option value="hot">Hot</option>
                  <option value="warm">Warm</option>
                  <option value="cold">Cold</option>
                  <option value="archive">Archive</option>
                </select>
              </div>
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={!searchQuery.trim() || isLoading}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg flex items-center space-x-2"
              >
                <Search className="w-4 h-4" />
                <span>{isLoading ? 'Searching...' : 'Search'}</span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Search Results */}
      {searchQuery && (
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              Search Results
              {searchResults && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({searchResults.results?.length || searchResults.length || 0} entries found)
                </span>
              )}
            </h2>
          </div>

          {isLoading && (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}

          {error && (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-800">Error searching logs: {error.message}</p>
              </div>
            </div>
          )}

          {searchResults && (searchResults.results?.length === 0 || searchResults.length === 0) && !isLoading && (
            <div className="p-6 text-center">
              <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No log entries found matching your search criteria.</p>
            </div>
          )}

          {searchResults && (searchResults.results?.length > 0 || searchResults.length > 0) && (
            <div className="divide-y divide-gray-200">
              {(searchResults.results || searchResults).map((log, index) => (
                <div
                  key={log.entry_id || index}
                  className="p-6 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => setSelectedLog(log)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        {getLogLevelIcon(log.level)}
                        <span className="font-medium text-gray-900">{log.level}</span>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTierBadgeColor(log.tier)}`}>
                          {log.tier?.toUpperCase() || 'UNKNOWN'}
                        </span>
                        <span className="text-sm text-gray-500">{log.service}</span>
                      </div>
                      <p className="text-gray-800 mb-2">{log.message}</p>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <div className="flex items-center space-x-1">
                          <Clock className="w-4 h-4" />
                          <span>{formatTimestamp(log.timestamp)}</span>
                        </div>
                        {log.metadata?.user_id && (
                          <span>User: {log.metadata.user_id}</span>
                        )}
                        {log.metadata?.request_id && (
                          <span>Request: {log.metadata.request_id}</span>
                        )}
                      </div>
                    </div>
                    <Eye className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Log Entry Details</h3>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Entry ID</label>
                    <p className="mt-1 text-sm text-gray-900 font-mono">{selectedLog.entry_id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Timestamp</label>
                    <p className="mt-1 text-sm text-gray-900">{formatTimestamp(selectedLog.timestamp)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Level</label>
                    <div className="mt-1 flex items-center space-x-2">
                      {getLogLevelIcon(selectedLog.level)}
                      <span className="text-sm text-gray-900">{selectedLog.level}</span>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Service</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedLog.service}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Tier</label>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTierBadgeColor(selectedLog.tier)}`}>
                      {selectedLog.tier?.toUpperCase() || 'UNKNOWN'}
                    </span>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Priority</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedLog.priority}</p>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Message</label>
                  <p className="mt-1 text-sm text-gray-900 bg-gray-50 p-3 rounded-lg">{selectedLog.message}</p>
                </div>

                {selectedLog.metadata && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Metadata</label>
                    <pre className="mt-1 text-sm text-gray-900 bg-gray-50 p-3 rounded-lg overflow-x-auto">
                      {JSON.stringify(selectedLog.metadata, null, 2)}
                    </pre>
                  </div>
                )}

                {selectedLog.raw_data && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Raw Data</label>
                    <pre className="mt-1 text-sm text-gray-900 bg-gray-50 p-3 rounded-lg overflow-x-auto">
                      {JSON.stringify(selectedLog.raw_data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Live Activity Feed */}
      {!searchQuery && stats && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Live Activity</h3>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>Live</span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-red-600" />
                <div>
                  <p className="text-sm font-medium text-red-600">Hot Tier</p>
                  <p className="text-xl font-bold text-red-800">
                    {stats.tier_statistics?.hot?.entry_count || 0} entries
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-orange-600" />
                <div>
                  <p className="text-sm font-medium text-orange-600">Warm Tier</p>
                  <p className="text-xl font-bold text-orange-800">
                    {stats.tier_statistics?.warm?.entry_count || 0} entries
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-blue-600">Cold Tier</p>
                  <p className="text-xl font-bold text-blue-800">
                    {stats.tier_statistics?.cold?.entry_count || 0} entries
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-gray-600" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Archive Tier</p>
                  <p className="text-xl font-bold text-gray-800">
                    {stats.tier_statistics?.archive?.entry_count || 0} entries
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4 text-sm text-gray-500">
            Last updated: {stats.timestamp ? new Date(stats.timestamp).toLocaleTimeString() : 'Never'}
          </div>
        </div>
      )}

      {/* Instructions */}
      {!searchQuery && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <Info className="w-6 h-6 text-blue-600 mt-0.5" />
            <div>
              <h3 className="text-lg font-medium text-blue-900">How to use the Log Viewer</h3>
              <div className="mt-2 text-sm text-blue-800 space-y-1">
                <p>• Enter search terms in the search box to find log entries</p>
                <p>• Use the tier filter to search within specific storage tiers</p>
                <p>• Click on any log entry to view detailed information</p>
                <p>• Search supports service names, log levels, and message content</p>
                <p>• Live activity feed shows real-time metrics from all tiers</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LogViewer;
