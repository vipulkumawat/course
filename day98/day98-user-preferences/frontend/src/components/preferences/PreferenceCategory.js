import React from 'react';
import { ChevronRight } from 'lucide-react';

const PreferenceCategory = ({ title, category, preferences, onChange }) => {
  const handleToggle = (key, value) => {
    onChange(category, key, !value);
  };

  const handleSelect = (key, value) => {
    onChange(category, key, value);
  };

  const handleSlider = (key, value) => {
    onChange(category, key, parseInt(value));
  };

  const renderPreferenceInput = (key, value) => {
    switch (key) {
      case 'theme':
        return (
          <select
            value={value || 'light'}
            onChange={(e) => handleSelect(key, e.target.value)}
            className="preference-select"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="auto">Auto</option>
          </select>
        );
      
      case 'auto_refresh':
      case 'notifications_enabled':
      case 'email_alerts':
      case 'sound_enabled':
      case 'data_collection':
        return (
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={value || false}
              onChange={() => handleToggle(key, value)}
            />
            <span className="toggle-slider"></span>
          </label>
        );
      
      case 'refresh_interval':
      case 'items_per_page':
        return (
          <div className="slider-container">
            <input
              type="range"
              min="5"
              max="60"
              value={value || 30}
              onChange={(e) => handleSlider(key, e.target.value)}
              className="preference-slider"
            />
            <span className="slider-value">{value || 30}</span>
          </div>
        );
      
      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => handleSelect(key, e.target.value)}
            className="preference-input"
          />
        );
    }
  };

  const getPreferenceLabel = (key) => {
    const labels = {
      theme: 'Color Theme',
      auto_refresh: 'Auto Refresh',
      refresh_interval: 'Refresh Interval (seconds)',
      items_per_page: 'Items Per Page',
      notifications_enabled: 'Enable Notifications',
      email_alerts: 'Email Alerts',
      sound_enabled: 'Sound Notifications',
      data_collection: 'Data Collection',
      timezone: 'Timezone',
      language: 'Language'
    };
    return labels[key] || key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="preference-category">
      <div className="category-header">
        <h3>{title}</h3>
        <ChevronRight size={16} />
      </div>
      <div className="category-content">
        {Object.entries(preferences).map(([key, value]) => (
          <div key={key} className="preference-item">
            <div className="preference-label">
              {getPreferenceLabel(key)}
            </div>
            <div className="preference-control">
              {renderPreferenceInput(key, value)}
            </div>
          </div>
        ))}
        {Object.keys(preferences).length === 0 && (
          <div className="no-preferences">
            No preferences configured for this category
          </div>
        )}
      </div>
    </div>
  );
};

export default PreferenceCategory;
