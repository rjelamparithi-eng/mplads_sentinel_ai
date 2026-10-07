import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  UploadCloud, 
  Sliders, 
  AlertTriangle, 
  ShieldAlert, 
  MapPin, 
  CheckSquare,
  ShieldCheck
} from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { label: 'Executive Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Data Ingestion', path: '/ingestion', icon: UploadCloud },
    { label: 'Baselines', path: '/baselines', icon: Sliders },
    { label: 'Anomaly Detection', path: '/anomaly', icon: AlertTriangle },
    { label: 'Risk Passport', path: '/passport', icon: ShieldAlert },
    { label: 'Spatial Intelligence', path: '/spatial', icon: MapPin },
    { label: 'Audit Workflow', path: '/audit', icon: CheckSquare },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand-title">
          <ShieldCheck style={{ color: '#ea580c', width: 22, height: 22 }} />
          <span>MPLADS SENTINEL</span>
        </div>
        <span className="sidebar-brand-tag">SIH PROTOTYPE</span>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">AUDIT MODULES</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              end={item.path === '/'}
            >
              <Icon className="nav-icon" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <p><strong>Designed for MPLADS / MoSPI use case</strong></p>
        <p style={{ marginTop: '4px', fontSize: '0.7rem' }}>SIH26102 Decision Support Prototype</p>
      </div>
    </aside>
  );
};

export default Sidebar;
