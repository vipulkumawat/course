import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import 'antd/dist/reset.css';

// Suppress findDOMNode warnings in development (known issue with Antd)
if (process.env.NODE_ENV === 'development') {
  const originalError = console.error;
  console.error = (...args) => {
    if (typeof args[0] === 'string' && args[0].includes('findDOMNode is deprecated')) {
      return;
    }
    originalError.call(console, ...args);
  };
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
