import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Database, Search } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-2">
              <Database className="w-8 h-8 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900">Tiered Storage</h1>
            </div>
            
            <div className="flex space-x-4">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === '/'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                Dashboard
              </Link>
              <Link
                to="/logs"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === '/logs'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                Log Viewer
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
