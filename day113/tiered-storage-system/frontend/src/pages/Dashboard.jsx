import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { Database, Activity, DollarSign, Clock, RefreshCw, Zap } from 'lucide-react';
import toast from 'react-hot-toast';
import { getStatistics, triggerAutoMigration } from '../services/api';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'];

const Dashboard = () => {
  const queryClient = useQueryClient();
  
  const { data: stats, isLoading, error, isFetching } = useQuery({
    queryKey: ['statistics'],
    queryFn: getStatistics,
    refetchInterval: 5000, // Refetch every 5 seconds
    refetchIntervalInBackground: true, // Continue refetching when tab is not active
    staleTime: 1000, // Consider data stale after 1 second
  });
  
  const migrationMutation = useMutation({
    mutationFn: triggerAutoMigration,
    onSuccess: (data) => {
      toast.success(`Migration completed! ${data.migrations_performed} migrations performed`);
      queryClient.invalidateQueries(['statistics']);
    },
    onError: (error) => {
      toast.error(`Migration failed: ${error.message}`);
    }
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">Error loading statistics: {error.message}</p>
      </div>
    );
  }

  const tierStats = stats?.tier_statistics || {};
  const queryStats = stats?.query_statistics || {};
  const migrationStats = tierStats.migration_stats || {};

  // Prepare data for charts
  const tierData = Object.entries(tierStats)
    .filter(([key]) => !key.includes('_stats'))
    .map(([tier, data]) => ({
      tier: tier.toUpperCase(),
      entries: data.entry_count || 0,
      sizeGB: data.total_size_gb || 0,
      cost: data.monthly_cost || 0
    }));

  const queryDistributionData = [
    { name: 'Hot', value: queryStats.hot_queries || 0, color: COLORS[0] },
    { name: 'Warm', value: queryStats.warm_queries || 0, color: COLORS[1] },
    { name: 'Cold', value: queryStats.cold_queries || 0, color: COLORS[2] },
    { name: 'Archive', value: queryStats.archive_queries || 0, color: COLORS[3] }
  ].filter(item => item.value > 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-3xl font-bold text-gray-900">Tiered Storage Dashboard</h1>
            {isFetching && (
              <div className="flex items-center space-x-2 text-sm text-blue-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span>Updating...</span>
              </div>
            )}
          </div>
          <p className="text-gray-600 mt-1">Monitor and manage your distributed log storage system</p>
        </div>
        <button
          onClick={() => migrationMutation.mutate()}
          disabled={migrationMutation.isPending}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
        >
          {migrationMutation.isPending ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Zap className="w-4 h-4" />
          )}
          <span>Trigger Migration</span>
        </button>
      </div>

      {/* Real-time Status */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${isFetching ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'}`}></div>
            <span className="text-sm font-medium text-gray-700">
              {isFetching ? 'Updating data...' : 'Live data'}
            </span>
          </div>
          <div className="text-sm text-gray-500">
            Last updated: {stats?.timestamp ? new Date(stats.timestamp).toLocaleTimeString() : 'Never'}
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Entries</p>
              <p className="text-2xl font-bold text-gray-900">
                {tierData.reduce((sum, tier) => sum + tier.entries, 0)}
              </p>
            </div>
            <Database className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Storage</p>
              <p className="text-2xl font-bold text-gray-900">
                {tierData.reduce((sum, tier) => sum + tier.sizeGB, 0).toFixed(2)} GB
              </p>
            </div>
            <Activity className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Monthly Cost</p>
              <p className="text-2xl font-bold text-gray-900">
                ${tierData.reduce((sum, tier) => sum + tier.cost, 0).toFixed(2)}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-yellow-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Cache Hit Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {queryStats.cache_hit_rate || 0}%
              </p>
            </div>
            <Clock className="w-8 h-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tier Distribution */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Distribution by Tier</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tierData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tier" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="entries" fill="#3B82F6" name="Entries" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Query Distribution */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Query Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={queryDistributionData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {queryDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Cost Analysis */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost Analysis by Tier</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={tierData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="tier" />
            <YAxis />
            <Tooltip formatter={(value) => [`$${value.toFixed(2)}`, 'Monthly Cost']} />
            <Bar dataKey="cost" fill="#10B981" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Migration Statistics */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Migration Statistics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm font-medium text-blue-600">Total Migrated</p>
            <p className="text-xl font-bold text-blue-800">{migrationStats.total_migrated || 0}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm font-medium text-green-600">Bytes Migrated</p>
            <p className="text-xl font-bold text-green-800">
              {((migrationStats.bytes_migrated || 0) / (1024 * 1024)).toFixed(2)} MB
            </p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4">
            <p className="text-sm font-medium text-yellow-600">Cost Savings</p>
            <p className="text-xl font-bold text-yellow-800">
              ${(migrationStats.cost_savings || 0).toFixed(2)}/month
            </p>
          </div>
        </div>
        {migrationStats.last_migration && (
          <p className="text-sm text-gray-600 mt-4">
            Last migration: {new Date(migrationStats.last_migration).toLocaleString()}
          </p>
        )}
      </div>

      {/* Tier Details Table */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Tier Details</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tier
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entries
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size (GB)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Monthly Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Performance
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tierData.map((tier) => (
                <tr key={tier.tier}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      tier.tier === 'HOT' ? 'bg-red-100 text-red-800' :
                      tier.tier === 'WARM' ? 'bg-orange-100 text-orange-800' :
                      tier.tier === 'COLD' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {tier.tier}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {tier.entries}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {tier.sizeGB.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${tier.cost.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {tier.tier === 'HOT' ? '< 10ms' :
                     tier.tier === 'WARM' ? '50-200ms' :
                     tier.tier === 'COLD' ? '1-5s' : '1-5min'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
