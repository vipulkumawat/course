import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Settings } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();
  
  return (
    <nav className="navigation">
      <div className="nav-brand">
        <h2>LogProcessor</h2>
      </div>
      <div className="nav-links">
        <Link 
          to="/" 
          className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
        >
          <Home size={18} />
          Dashboard
        </Link>
        <Link 
          to="/preferences" 
          className={`nav-link ${location.pathname === '/preferences' ? 'active' : ''}`}
        >
          <Settings size={18} />
          Preferences
        </Link>
      </div>
    </nav>
  );
};

export default Navigation;
