import React, { useState, useEffect } from 'react';
import { AlertTriangle, Play, Eye, CheckCircle, RefreshCw, Info } from 'lucide-react';
import { getAnomalies, runAnomalyPipeline } from '../services/api';
import { useNavigate } from 'react-router-dom';

const AnomalyDetection = () => {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [summaryMsg, setSummaryMsg] = useState(null);
  const navigate = useNavigate();

  const fetchAnomalies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAnomalies();
      setAnomalies(data);
    } catch (err) {
      setError('Failed to fetch anomaly evaluations. Ensure backend service is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, []);

  const handleRunPipeline = async () => {
    setRunning(true);
    setError(null);
    setSummaryMsg(null);
    try {
      const res = await runAnomalyPipeline();
      setSummaryMsg(`Pipeline execution completed. Analysed ${res.total_analysed} projects (${res.high_priority_count} High Review Priority, ${res.review_recommended_count} Review Recommended).`);
      fetchAnomalies();
    } catch (err) {
      setError('Error running anomaly detection pipeline.');
    } finally {
      setRunning(false);
    }
  };

  const handleInspect = (projectId) => {
    navigate('/passport', { state: { projectId } });
  };

  const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'N/A';
    return `₹${Number(val).toLocaleString('en-IN')}`;
  };

  return (
    <div>
      <div className="page-header">
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ea580c', letterSpacing: '0.5px' }}>
          MODULE 03
        </div>
        <h1 className="page-title">Anomaly Detection Engine</h1>
        <p className="page-description">
          Analyse project-level statistical anomalies, expenditure variances, and timeline delay indicators.
        </p>
      </div>

      {/* Control Action Card */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Statistical & Rule-Based Anomaly Pipeline</h3>
          <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.2rem' }}>
            Evaluates cost variance against peer IQR baselines, timeline delays, and document completeness.
          </p>
        </div>

        <button className="btn btn-primary" onClick={handleRunPipeline} disabled={running}>
          <Play style={{ width: 14, height: 14 }} />
          {running ? 'Running Pipeline...' : 'Run Detection Engine'}
        </button>
      </div>

      {summaryMsg && (
        <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', color: '#15803d', padding: '0.65rem 1rem', borderRadius: '6px', marginBottom: '1.25rem', fontSize: '0.8rem' }}>
          {summaryMsg}
        </div>
      )}

      {error && (
        <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '0.65rem 1rem', borderRadius: '6px', marginBottom: '1.25rem', fontSize: '0.8rem' }}>
          {error}
        </div>
      )}

      {/* Anomaly Evaluation Table */}
      <div className="card">
        <div className="card-title" style={{ justifyContent: 'space-between', display: 'flex' }}>
          <span>Project Anomaly Review Table ({anomalies.length})</span>
          <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 400 }}>Explainable Review Severity Classification</span>
        </div>

        {loading ? (
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Evaluating anomaly signals...</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                  <th style={{ padding: '0.65rem 0.75rem' }}>Project ID</th>
                  <th style={{ padding: '0.65rem 0.75rem' }}>Project Name</th>
                  <th style={{ padding: '0.65rem 0.75rem' }}>District</th>
                  <th style={{ padding: '0.65rem 0.75rem' }}>Sanctioned (₹)</th>
                  <th style={{ padding: '0.65rem 0.75rem' }}>Expenditure (₹)</th>
                  <th style={{ padding: '0.65rem 0.75rem' }}>Score</th>
                  <th style={{ padding: '0.65rem 0.75rem' }}>ML Signal</th>
                  <th style={{ padding: '0.65rem 0.75rem' }}>Review Severity</th>
                  <th style={{ padding: '0.65rem 0.75rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.map((item) => {
                  let badgeClass = 'badge-normal';
                  if (item.review_severity === 'Review Recommended') badgeClass = 'badge-warning';
                  if (item.review_severity === 'High Review Priority') badgeClass = 'badge-high';

                  return (
                    <tr key={item.project_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.65rem 0.75rem', fontWeight: 600 }} className="mono">{item.project_id}</td>
                      <td style={{ padding: '0.65rem 0.75rem' }}>{item.project_name}</td>
                      <td style={{ padding: '0.65rem 0.75rem' }}>{item.district}</td>
                      <td style={{ padding: '0.65rem 0.75rem' }}>{formatCurrency(item.sanctioned_amount)}</td>
                      <td style={{ padding: '0.65rem 0.75rem' }}>{formatCurrency(item.expenditure)}</td>
                      <td style={{ padding: '0.65rem 0.75rem' }} className="mono">{item.anomaly_score.toFixed(2)}</td>
                      <td style={{ padding: '0.65rem 0.75rem' }}>
                        <span className={`badge ${item.ml_signal === 'ML_ANOMALY' ? 'badge-warning' : 'badge-normal'}`}>
                          {item.ml_signal === 'ML_ANOMALY' ? 'Anomaly' : 'Normal'}
                        </span>
                      </td>
                      <td style={{ padding: '0.65rem 0.75rem' }}>
                        <span className={`badge ${badgeClass}`}>{item.review_severity}</span>
                      </td>
                      <td style={{ padding: '0.65rem 0.75rem' }}>
                        <button className="btn" style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }} onClick={() => handleInspect(item.project_id)}>
                          <Eye style={{ width: 12, height: 12 }} /> Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnomalyDetection;
