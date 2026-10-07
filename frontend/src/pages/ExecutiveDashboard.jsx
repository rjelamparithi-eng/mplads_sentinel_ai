import React, { useState, useEffect } from 'react';
import { LayoutDashboard, AlertCircle, FileCheck, Layers, MapPin, CheckCircle, RefreshCw, ArrowRight } from 'lucide-react';
import { getDashboardSummary } from '../services/api';
import { useNavigate } from 'react-router-dom';

const ExecutiveDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDashboardSummary();
      setData(res);
    } catch (err) {
      setError('Backend service unavailable. Displaying cached system state.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const formatCurrency = (val) => {
    if (!val) return '₹0';
    return `₹${Number(val).toLocaleString('en-IN')}`;
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ea580c', letterSpacing: '0.5px' }}>
            MODULE 00
          </div>
          <h1 className="page-title">Executive Dashboard</h1>
          <p className="page-description">
            High-level review summary and system intelligence metrics for MPLADS project monitoring.
          </p>
        </div>

        <button className="btn" onClick={fetchSummary} disabled={loading}>
          <RefreshCw style={{ width: 14, height: 14 }} className={loading ? 'spin' : ''} />
          <span>Refresh Summary</span>
        </button>
      </div>

      {/* Controlled Dataset Notice */}
      <div className="card" style={{ borderLeft: '4px solid #ea580c', padding: '0.85rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#9a3412', fontWeight: 600, fontSize: '0.85rem' }}>
            <AlertCircle style={{ width: 18, height: 18 }} />
            <span>SIH Prototype — Controlled Test Environment</span>
          </div>
          <span className="badge badge-normal" style={{ fontSize: '0.7rem' }}>Controlled Test Data</span>
        </div>
        <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.3rem' }}>
          {data?.data_notice || 'Summary generated strictly from local prototype database records. Not an official Government of India portal.'}
        </p>
      </div>

      {error && (
        <div style={{ backgroundColor: '#fffbe6', border: '1px solid #fef08a', color: '#b45309', padding: '0.65rem 1rem', borderRadius: '6px', marginBottom: '1.25rem', fontSize: '0.8rem' }}>
          {error}
        </div>
      )}

      {/* Top Level Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
        <div className="card">
          <div className="card-title" style={{ fontSize: '0.8rem', color: '#64748b' }}>Projects Analysed</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#0f172a' }}>{loading ? '...' : data?.projects_analysed || 0}</div>
          <span className="badge badge-normal" style={{ marginTop: '0.4rem' }}>Controlled Dataset</span>
        </div>

        <div className="card">
          <div className="card-title" style={{ fontSize: '0.8rem', color: '#64748b' }}>Review Recommended</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#d97706' }}>{loading ? '...' : data?.review_recommended_count || 0}</div>
          <span className="badge badge-warning" style={{ marginTop: '0.4rem' }}>Requires Attention</span>
        </div>

        <div className="card">
          <div className="card-title" style={{ fontSize: '0.8rem', color: '#64748b' }}>High Review Priority</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#dc2626' }}>{loading ? '...' : data?.high_priority_count || 0}</div>
          <span className="badge badge-high" style={{ marginTop: '0.4rem' }}>Priority Audit</span>
        </div>

        <div className="card">
          <div className="card-title" style={{ fontSize: '0.8rem', color: '#64748b' }}>Evidence Pending</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#475569' }}>{loading ? '...' : data?.evidence_pending_count || 0}</div>
          <span className="badge badge-normal" style={{ marginTop: '0.4rem' }}>Missing Docs</span>
        </div>

        <div className="card">
          <div className="card-title" style={{ fontSize: '0.8rem', color: '#64748b' }}>Possible Overlaps</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#ea580c' }}>{loading ? '...' : data?.possible_overlaps_count || 0}</div>
          <span className="badge badge-warning" style={{ marginTop: '0.4rem' }}>Spatial Proximity</span>
        </div>
      </div>

      {/* Grid for High Priority Queue & District Distribution */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* High Priority Review Queue */}
        <div className="card">
          <div className="card-title" style={{ justifyContent: 'space-between', display: 'flex' }}>
            <span>High Review Priority Queue</span>
            <button className="btn" style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }} onClick={() => navigate('/anomaly')}>
              View All Anomalies <ArrowRight style={{ width: 12, height: 12 }} />
            </button>
          </div>

          {loading ? (
            <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Loading priority queue...</p>
          ) : data?.high_priority_queue && data.high_priority_queue.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              {data.high_priority_queue.map((item) => (
                <div key={item.project_id} style={{ padding: '0.65rem', border: '1px solid #fee2e2', borderRadius: '6px', backgroundColor: '#fef2f2' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.85rem' }} className="mono">{item.project_id}</span>
                    <span className="badge badge-high" style={{ fontSize: '0.7rem' }}>High Priority</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, marginTop: '0.2rem' }}>{item.project_name}</div>
                  <div style={{ fontSize: '0.75rem', color: '#b91c1c', marginTop: '0.25rem' }}>
                    <strong>Reason:</strong> {item.main_reason}
                  </div>
                  <div style={{ marginTop: '0.4rem', textAlign: 'right' }}>
                    <button className="btn" style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem' }} onClick={() => navigate('/passport', { state: { projectId: item.project_id } })}>
                      Inspect Risk Passport
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: '0.85rem', color: '#64748b' }}>No high priority review items flagged.</p>
          )}
        </div>

        {/* Breakdown Distributions */}
        <div className="card">
          <div className="card-title">District & Sector Breakdown</div>
          {loading ? (
            <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Loading distribution breakdown...</p>
          ) : (
            <div>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.5rem' }}>District Distribution</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1rem' }}>
                {Object.entries(data?.district_distribution || {}).map(([dist, cnt]) => (
                  <div key={dist} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span>{dist}</span>
                    <strong className="mono">{cnt} projects</strong>
                  </div>
                ))}
              </div>

              <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569', marginBottom: '0.5rem' }}>Project Sector Distribution</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {Object.entries(data?.type_distribution || {}).map(([typ, cnt]) => (
                  <div key={typ} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                    <span>{typ}</span>
                    <strong className="mono">{cnt} projects</strong>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExecutiveDashboard;
