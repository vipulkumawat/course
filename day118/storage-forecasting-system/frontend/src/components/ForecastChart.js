import React from 'react';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area,
  ComposedChart,
  ResponsiveContainer
} from 'recharts';
import { format, parseISO } from 'date-fns';

const ForecastChart = ({ data }) => {
  if (!data || !data.forecast) return <div>No forecast data available</div>;

  const chartData = data.forecast.dates.map((date, index) => ({
    date: format(parseISO(date), 'MMM dd'),
    predicted: Math.round(data.forecast.predicted_usage_gb[index] * 100) / 100,
    lower: Math.round(data.forecast.confidence_lower_gb[index] * 100) / 100,
    upper: Math.round(data.forecast.confidence_upper_gb[index] * 100) / 100,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis label={{ value: 'Storage (GB)', angle: -90, position: 'insideLeft' }} />
        <Tooltip 
          formatter={(value, name) => [
            `${value} GB`,
            name === 'predicted' ? 'Predicted Usage' : 
            name === 'lower' ? 'Lower Bound' : 'Upper Bound'
          ]}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Legend />
        
        {/* Confidence interval area */}
        <Area
          dataKey="upper"
          stackId="1"
          stroke="none"
          fill="#a5b4fc"
          fillOpacity={0.2}
        />
        <Area
          dataKey="lower"
          stackId="1"
          stroke="none"
          fill="#ffffff"
          fillOpacity={1}
        />
        
        {/* Main prediction line */}
        <Line
          type="monotone"
          dataKey="predicted"
          stroke="#6366f1"
          strokeWidth={3}
          dot={{ fill: '#6366f1', r: 4 }}
          activeDot={{ r: 6, fill: '#4338ca' }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default ForecastChart;
