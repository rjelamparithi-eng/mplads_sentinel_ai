import React, { useState, useEffect } from 'react';
import { ShieldAlert, FileText, CheckCircle2, AlertOctagon, HelpCircle, Search, ArrowRight, UserCheck } from 'lucide-react';
import { getRiskPassport, getAnomalies } from '../services/api';
import { useLocation, useNavigate } from 'react-router-dom';

const RiskPassport = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const passedPid = location.state?.projectId || '';

  const [searchPid, setSearchPid] = useState(passedPid);
  const [passport, setPassport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [allProjects, setAllProjects] = useState([]);

  const fetchPassport = async (pid) => {
    if (!pid) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getRiskPassport(pid);
      setPassport(data);
    } catch (err) {
      setError(err.response?.data?.detail || `Project ID '${pid}' not found.`);
      setPassport(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const initPage = async () => {
      try {
        const list = await getAnomalies();
        setAllProjects(list || []);
        
        let targetPid = passedPid;
        if (!targetPid && list && list.length > 0) {
          targetPid = list[0].project_id;
        }
        
        if (targetPid) {
          setSearchPid(targetPid);
          fetchPassport(targetPid);
        } else {
          setLoading(false);
        }
      } catch (err) {
        if (passedPid) {
          fetchPassport(passedPid);
        } else {
          setLoading(false);
        }
      }
    };
    initPage();
  }, [passedPid]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchPid.trim()) {
      fetchPassport(searchPid.trim());
    }
  };

  const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'N/A';
    return `₹${Number(val).toLocaleString('en-IN')}`;
  };

  return (
    <div>
      <div className="page-header">
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ea580c', letterSpacing: '0.5px' }}>
          MODULE 04
        </div>
        <h1 className="page-title">Project Risk Passport</h1>
        <p className="page-description">
          Detailed explainable review-priority profile providing evidence, cost/timeline deviations, and audit recommendations.
        </p>
      </div>

      {/* Selector & Search Card */}
      <div className="card">
        <div className="card-title">Select Project for Risk Passport Inspection</div>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            value={searchPid}
            onChange={(e) => {
              setSearchPid(e.target.value);
              fetchPassport(e.target.value);
            }}
            className="search-input"
            style={{ width: '280px' }}
          >
            {allProjects && allProjects.length > 0 ? (
              allProjects.map((p) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.project_id} — {p.district} ({p.review_severity})
                </option>
              ))
            ) : (
              <option value="">No projects available</option>
            )}
          </select>

          <input
            type="text"
            placeholder="Or type Project ID..."
            value={searchPid}
            onChange={(e) => setSearchPid(e.target.value)}
            className="search-input"
            style={{ width: '220px' }}
          />

          <button type="submit" className="btn btn-primary" disabled={loading || !searchPid.trim()}>
            <Search style={{ width: 14, height: 14 }} /> Fetch Passport
          </button>
        </form>

        {error && (
          <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '0.65rem 1rem', borderRadius: '6px', marginTop: '1rem', fontSize: '0.8rem' }}>
            {error}
          </div>
        )}
      </div>

      {!passport && !loading && (
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem 1.5rem', color: '#64748b' }}>
          <p style={{ fontWeight: 600, fontSize: '0.95rem', color: '#475569' }}>No Project Selected or Database Empty</p>
          <p style={{ fontSize: '0.8rem', marginTop: '0.3rem' }}>Please ingest project records or select a valid Project ID to view its Risk Passport.</p>
        </div>
      )}

      {passport && (
        <>
          {/* Header Priority Banner */}
          <div className="card" style={{ borderLeft: passport.review_severity === 'High Review Priority' ? '4px solid #dc2626' : passport.review_severity === 'Review Recommended' ? '4px solid #d97706' : '4px solid #16a34a' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>PROJECT RISK PASSPORT</div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }} className="mono">
                  {passport.project_id} — {passport.project_name}
                </h2>
                <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.2rem' }}>
                  District: <strong>{passport.district}</strong> | Sector: <strong>{passport.project_type}</strong> | Data Source: <span className="badge badge-normal">{passport.data_source}</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>ML SIGNAL</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 700, color: passport.ml_signal === 'ML_ANOMALY' ? '#d97706' : '#16a34a' }}>
                    {passport.ml_signal === 'ML_ANOMALY' ? 'Anomaly' : 'Normal'}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>CONFIDENCE LEVEL</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>{passport.confidence} Confidence</div>
                </div>

                <span className={`badge ${passport.review_severity === 'High Review Priority' ? 'badge-high' : passport.review_severity === 'Review Recommended' ? 'badge-warning' : 'badge-normal'}`} style={{ padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}>
                  {passport.review_severity}
                </span>
              </div>
            </div>
          </div>

          {/* Grid Layout: Financial & Timeline Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
            {/* Financial Comparison */}
            <div className="card">
              <div className="card-title">Financial Comparison & Variance</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Sanctioned Budget:</span>
                  <strong>{formatCurrency(passport.sanctioned_amount)}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Actual Expenditure:</span>
                  <strong style={{ color: passport.expenditure > passport.sanctioned_amount ? '#dc2626' : '#0f172a' }}>
                    {formatCurrency(passport.expenditure)}
                  </strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Peer Cohort Median:</span>
                  <strong>{formatCurrency(passport.peer_median_expenditure)}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #e2e8f0', paddingTop: '0.4rem', marginTop: '0.2rem' }}>
                  <span style={{ color: '#64748b' }}>Variance vs Peer Median:</span>
                  <strong style={{ color: passport.exp_vs_median_pct > 0 ? '#ea580c' : '#16a34a' }}>
                    {passport.exp_vs_median_pct > 0 ? `+${passport.exp_vs_median_pct}%` : `${passport.exp_vs_median_pct}%`}
                  </strong>
                </div>
              </div>
            </div>

            {/* Timeline & Progress */}
            <div className="card">
              <div className="card-title">Timeline & Physical Progress</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Sanction Date:</span>
                  <span>{passport.sanction_date || 'N/A'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Expected Completion:</span>
                  <span>{passport.expected_completion_date || 'N/A'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Physical Progress:</span>
                  <strong>{passport.progress_percent}%</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #e2e8f0', paddingTop: '0.4rem', marginTop: '0.2rem' }}>
                  <span style={{ color: '#64748b' }}>Status:</span>
                  <span className="badge badge-normal">{passport.status}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Explainable Reasons Panel */}
          <div className="card">
            <div className="card-title" style={{ color: '#ea580c' }}>Explainable Priority Reasons ({passport.reasons.length})</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {passport.reasons.map((r, i) => (
                <div key={i} style={{ padding: '0.6rem 0.85rem', backgroundColor: '#fff7ed', border: '1px solid #ffedd5', borderRadius: '4px', fontSize: '0.8rem', color: '#9a3412' }}>
                  <strong>• Reason {i + 1}:</strong> {r}
                </div>
              ))}
            </div>
          </div>

          {/* Evidence Summary & Next Step */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '1.25rem' }}>
            <div className="card">
              <div className="card-title" style={{ justifyContent: 'space-between', display: 'flex' }}>
                <span>Evidence & Document Cross-Check</span>
                <span className={`badge ${passport.evidence_validation?.evidence_confidence === 'HIGH' ? 'badge-normal' : passport.evidence_validation?.evidence_confidence === 'MEDIUM' ? 'badge-warning' : 'badge-high'}`} style={{ fontSize: '0.7rem' }}>
                  Confidence: {passport.evidence_validation?.evidence_confidence || 'LOW'}
                </span>
              </div>
              <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Supporting File:</span>
                  <span className="mono">{passport.evidence_validation?.document_filename || 'No document uploaded'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Project ID Match:</span>
                  <strong style={{ color: passport.evidence_validation?.project_id_match ? '#16a34a' : '#dc2626' }}>
                    {passport.evidence_validation?.project_id_match ? 'Matched' : 'Mismatch'}
                  </strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Reference & Sector Match:</span>
                  <strong style={{ color: passport.evidence_validation?.project_reference_match ? '#16a34a' : '#ea580c' }}>
                    {passport.evidence_validation?.project_reference_match ? 'Confirmed' : 'Unconfirmed'}
                  </strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Financial Amount Match:</span>
                  <strong style={{ color: passport.evidence_validation?.amount_match ? '#16a34a' : '#ea580c' }}>
                    {passport.evidence_validation?.amount_match ? 'Aligned' : 'Variance / Unmatched'}
                  </strong>
                </div>

                {passport.evidence_validation?.issues && passport.evidence_validation.issues.length > 0 && (
                  <div style={{ marginTop: '0.3rem', backgroundColor: '#f8fafc', padding: '0.4rem 0.6rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                    <strong style={{ color: '#475569', fontSize: '0.75rem' }}>Verification Findings:</strong>
                    <ul style={{ paddingLeft: '1.2rem', marginTop: '0.2rem', fontSize: '0.75rem', color: '#64748b' }}>
                      {passport.evidence_validation.issues.map((iss, idx) => (
                        <li key={idx}>{iss}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            <div className="card" style={{ borderLeft: '4px solid #ea580c' }}>
              <div className="card-title">Recommended Next Step</div>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#0f172a', marginBottom: '0.4rem' }}>
                {passport.next_step}
              </div>
              <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
                This Risk Passport provides an explainable review priority. Final official decision remains fully under human auditor control.
              </p>

              <div style={{ marginTop: '1rem' }}>
                <button className="btn btn-primary" onClick={() => navigate('/audit')}>
                  <UserCheck style={{ width: 14, height: 14 }} /> Open in Audit Workflow Queue
                </button>
              </div>
            </div>
          </div>

          {/* Similar Peer Projects */}
          {passport.similar_projects && passport.similar_projects.length > 0 && (
            <div className="card">
              <div className="card-title">Similar Peer Cohort Projects</div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Project ID</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Project Name</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>District</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Sanctioned (₹)</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Expenditure (₹)</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {passport.similar_projects.map((sp) => (
                      <tr key={sp.project_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }} className="mono">{sp.project_id}</td>
                        <td style={{ padding: '0.6rem 0.75rem' }}>{sp.project_name}</td>
                        <td style={{ padding: '0.6rem 0.75rem' }}>{sp.district}</td>
                        <td style={{ padding: '0.6rem 0.75rem' }}>{formatCurrency(sp.sanctioned_amount)}</td>
                        <td style={{ padding: '0.6rem 0.75rem' }}>{formatCurrency(sp.expenditure)}</td>
                        <td style={{ padding: '0.6rem 0.75rem' }}>{sp.progress_percent}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RiskPassport;
