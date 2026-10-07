import React, { useState, useEffect } from 'react';
import { CheckSquare, ArrowRight, UserCheck, RefreshCw, AlertCircle } from 'lucide-react';
import { getAuditBoard, updateAuditStatus } from '../services/api';
import { useNavigate } from 'react-router-dom';

const AuditWorkflow = () => {
  const [board, setBoard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMsg, setActionMsg] = useState(null);
  const navigate = useNavigate();

  const fetchBoard = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAuditBoard();
      setBoard(data);
    } catch (err) {
      setError('Failed to fetch audit workflow board.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBoard();
  }, []);

  const handleStatusChange = async (projectId, newStatus) => {
    setActionMsg(null);
    try {
      const res = await updateAuditStatus(projectId, newStatus);
      setActionMsg(`Project ${projectId} moved to '${newStatus}'. Final decision remains human-controlled.`);
      fetchBoard();
    } catch (err) {
      setError('Failed to update audit status.');
    }
  };

  const columns = [
    { key: 'Pending Review', label: 'Pending Review', color: '#ea580c' },
    { key: 'Field / Document Review', label: 'Field / Document Review', color: '#d97706' },
    { key: 'Verified', label: 'Verified', color: '#16a34a' },
    { key: 'Escalated', label: 'Escalated', color: '#dc2626' }
  ];

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ea580c', letterSpacing: '0.5px' }}>
            MODULE 06
          </div>
          <h1 className="page-title">Audit Workflow & Verification Queue</h1>
          <p className="page-description">
            Kanban-style human verification queue for audit review and escalation lifecycle.
          </p>
        </div>

        <button className="btn" onClick={fetchBoard} disabled={loading}>
          <RefreshCw style={{ width: 14, height: 14 }} /> Refresh Board
        </button>
      </div>

      {actionMsg && (
        <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', color: '#15803d', padding: '0.65rem 1rem', borderRadius: '6px', marginBottom: '1.25rem', fontSize: '0.8rem' }}>
          {actionMsg}
        </div>
      )}

      {error && (
        <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '0.65rem 1rem', borderRadius: '6px', marginBottom: '1.25rem', fontSize: '0.8rem' }}>
          {error}
        </div>
      )}

      {/* Human Controlled Notice */}
      <div className="card" style={{ borderLeft: '4px solid #16a34a', padding: '0.85rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#15803d', fontWeight: 600, fontSize: '0.85rem' }}>
          <UserCheck style={{ width: 18, height: 18 }} />
          <span>Human Verification Lifecycle — Final Decision Human Controlled</span>
        </div>
        <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.2rem' }}>
          AI flags priority review candidates based on statistical rules. Official verification decisions and state transitions are executed by human audit officials.
        </p>
      </div>

      {/* Kanban Board Layout */}
      {loading ? (
        <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Loading audit workflow queue...</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', alignItems: 'start' }}>
          {columns.map((col) => {
            const cards = board?.columns[col.key] || [];

            return (
              <div key={col.key} className="card" style={{ padding: '0.85rem', backgroundColor: '#f8fafc', borderTop: `3px solid ${col.color}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#0f172a' }}>{col.label}</span>
                  <span className="badge badge-normal" style={{ fontSize: '0.7rem' }}>{cards.length}</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {cards.map((card) => (
                    <div key={card.project_id} style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '0.85rem', boxShadow: 'var(--shadow-sm)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 700, fontSize: '0.85rem' }} className="mono">{card.project_id}</span>
                        <span className={`badge ${card.review_priority === 'High Review Priority' ? 'badge-high' : card.review_priority === 'Review Recommended' ? 'badge-warning' : 'badge-normal'}`} style={{ fontSize: '0.65rem' }}>
                          {card.review_priority}
                        </span>
                      </div>

                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#0f172a', marginTop: '0.3rem' }}>
                        {card.project_name}
                      </div>

                      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>
                        District: {card.district} | Exp: ₹{card.expenditure.toLocaleString('en-IN')}
                      </div>

                      <div style={{ fontSize: '0.75rem', color: '#b45309', marginTop: '0.4rem', backgroundColor: '#fffbe6', padding: '0.35rem 0.5rem', borderRadius: '4px' }}>
                        <strong>Reason:</strong> {card.main_reason}
                      </div>

                      {/* Action & Status Move Select */}
                      <div style={{ marginTop: '0.65rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <select
                          value={card.audit_status}
                          onChange={(e) => handleStatusChange(card.project_id, e.target.value)}
                          className="search-input"
                          style={{ padding: '0.15rem 0.35rem', fontSize: '0.7rem', width: 'auto' }}
                        >
                          <option value="Pending Review">Pending Review</option>
                          <option value="Field / Document Review">Field / Document Review</option>
                          <option value="Verified">Verified</option>
                          <option value="Escalated">Escalated</option>
                        </select>

                        <button className="btn" style={{ padding: '0.15rem 0.4rem', fontSize: '0.7rem' }} onClick={() => navigate('/passport', { state: { projectId: card.project_id } })}>
                          Passport
                        </button>
                      </div>
                    </div>
                  ))}

                  {cards.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '1.5rem 0', fontSize: '0.75rem', color: '#94a3b8' }}>
                      No projects in this stage
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AuditWorkflow;
