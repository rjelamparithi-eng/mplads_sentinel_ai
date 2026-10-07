import React, { useState, useEffect } from 'react';
import { Search, UserCheck, Activity, Info, WifiOff } from 'lucide-react';
import api from '../services/api';

const Header = () => {
  const [isBackendOnline, setIsBackendOnline] = useState(false);

  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        const response = await api.get('/health');
        if (response.data && response.data.status === 'ok') {
          setIsBackendOnline(true);
        } else {
          setIsBackendOnline(false);
        }
      } catch (err) {
        setIsBackendOnline(false);
      }
    };

    checkBackendHealth();
    // Periodically poll health every 15s
    const interval = setInterval(checkBackendHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <header className="header">
        <div className="header-left">
          <div className="header-title">
            MPLADS Sentinel AI
          </div>
          <div className="header-subtitle">
            Explainable Project Review Intelligence Prototype
          </div>
        </div>

        <div className="header-center">
          <div className="search-box">
            <Search className="search-icon" />
            <input 
              type="text" 
              placeholder="Search Project ID, District, or Type..." 
              className="search-input"
            />
          </div>
        </div>

        <div className="header-right">
          {isBackendOnline ? (
            <div className="engine-status-badge">
              <span className="pulse-dot"></span>
              <Activity style={{ width: 14, height: 14 }} />
              <span>Analysis Engine Active</span>
            </div>
          ) : (
            <div className="engine-status-badge" style={{ backgroundColor: '#f1f5f9', color: '#64748b', borderColor: '#cbd5e1' }}>
              <WifiOff style={{ width: 14, height: 14, color: '#64748b' }} />
              <span>Analysis Engine Offline</span>
            </div>
          )}

          <div className="user-badge">
            <UserCheck style={{ width: 16, height: 16, color: '#475569' }} />
            <span>Audit Official</span>
          </div>
        </div>
      </header>

      <div className="disclaimer-banner">
        <div className="disclaimer-text">
          <span className="disclaimer-tag">SIH Prototype</span>
          <Info style={{ width: 14, height: 14 }} />
          <span>
            <strong>MPLADS Sentinel AI — SIH Prototype</strong> | Designed for MPLADS / MoSPI use case. Decision support prototype (NOT an official Government of India portal).
          </span>
        </div>
        <div style={{ fontSize: '0.7rem', color: '#b45309', fontWeight: 500 }}>
          Controlled Test Environment
        </div>
      </div>
    </>
  );
};

export default Header;
