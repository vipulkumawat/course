import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { preferenceService } from '../services/preferenceService';

const PreferenceContext = createContext();

const preferenceReducer = (state, action) => {
  switch (action.type) {
    case 'SET_PREFERENCES':
      return {
        ...state,
        preferences: action.payload,
        loading: false
      };
    case 'UPDATE_PREFERENCE':
      return {
        ...state,
        preferences: {
          ...state.preferences,
          [action.payload.category]: {
            ...state.preferences[action.payload.category],
            [action.payload.key]: action.payload.value
          }
        }
      };
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false
      };
    default:
      return state;
  }
};

const initialState = {
  preferences: {},
  loading: true,
  error: null
};

export const PreferenceProvider = ({ children }) => {
  const [state, dispatch] = useReducer(preferenceReducer, initialState);

  useEffect(() => {
    loadPreferences();
    setupWebSocket();
  }, []);

  const loadPreferences = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await preferenceService.getPreferences();
      
      // If no user preferences exist, load defaults
      if (Object.keys(response.preferences).length === 0) {
        const defaultsResponse = await preferenceService.getDefaultPreferences();
        dispatch({ type: 'SET_PREFERENCES', payload: defaultsResponse.defaults });
      } else {
        dispatch({ type: 'SET_PREFERENCES', payload: response.preferences });
      }
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  const updatePreference = async (category, key, value) => {
    try {
      await preferenceService.updatePreference(category, key, value);
      dispatch({
        type: 'UPDATE_PREFERENCE',
        payload: { category, key, value }
      });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  const setupWebSocket = () => {
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/preferences/1');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'preference_updated') {
        dispatch({
          type: 'UPDATE_PREFERENCE',
          payload: data
        });
      }
    };
  };

  return (
    <PreferenceContext.Provider value={{
      ...state,
      updatePreference,
      loadPreferences
    }}>
      {children}
    </PreferenceContext.Provider>
  );
};

export const usePreferences = () => {
  const context = useContext(PreferenceContext);
  if (!context) {
    throw new Error('usePreferences must be used within a PreferenceProvider');
  }
  return context;
};
