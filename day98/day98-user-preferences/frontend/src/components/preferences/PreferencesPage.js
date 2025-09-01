import React, { useState, useEffect } from 'react';
import { usePreferences } from '../../context/PreferenceContext';
import PreferenceCategory from './PreferenceCategory';
import { Settings, Save, RotateCcw } from 'lucide-react';

const PreferencesPage = () => {
  const { preferences, updatePreference, loading } = usePreferences();
  const [localPreferences, setLocalPreferences] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setLocalPreferences(preferences);
  }, [preferences]);

  const handlePreferenceChange = (category, key, value) => {
    setLocalPreferences(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
    setHasChanges(true);
  };

  const saveChanges = async () => {
    try {
      for (const [category, prefs] of Object.entries(localPreferences)) {
        for (const [key, value] of Object.entries(prefs)) {
          if (preferences[category]?.[key] !== value) {
            await updatePreference(category, key, value);
          }
        }
      }
      setHasChanges(false);
    } catch (error) {
      console.error('Error saving preferences:', error);
    }
  };

  const resetToDefaults = () => {
    setLocalPreferences(preferences);
    setHasChanges(false);
  };

  if (loading) {
    return (
      <div className="preferences-loading">
        <div className="loading-spinner"></div>
        <p>Loading preferences...</p>
      </div>
    );
  }

  return (
    <div className="preferences-page">
      <div className="preferences-header">
        <div className="header-content">
          <Settings className="header-icon" />
          <h1>User Preferences</h1>
        </div>
        {hasChanges && (
          <div className="action-buttons">
            <button onClick={resetToDefaults} className="btn-secondary">
              <RotateCcw size={16} />
              Reset
            </button>
            <button onClick={saveChanges} className="btn-primary">
              <Save size={16} />
              Save Changes
            </button>
          </div>
        )}
      </div>

      <div className="preferences-grid">
        <PreferenceCategory
          title="Dashboard"
          category="dashboard"
          preferences={localPreferences.dashboard || {}}
          onChange={handlePreferenceChange}
        />
        <PreferenceCategory
          title="Notifications"
          category="notifications"
          preferences={localPreferences.notifications || {}}
          onChange={handlePreferenceChange}
        />
        <PreferenceCategory
          title="Theme"
          category="theme"
          preferences={localPreferences.theme || {}}
          onChange={handlePreferenceChange}
        />
        <PreferenceCategory
          title="Data & Privacy"
          category="privacy"
          preferences={localPreferences.privacy || {}}
          onChange={handlePreferenceChange}
        />
      </div>
    </div>
  );
};

export default PreferencesPage;
