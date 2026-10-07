import React, { useState, useEffect } from 'react';
import { Sliders, Filter, CheckCircle, AlertTriangle, HelpCircle, ArrowUpRight, Search, BarChart3 } from 'lucide-react';
import { getBaselineOptions, calculateBaseline, compareProjectToPeers } from '../services/api';

const Baselines = () => {
  const [options, setOptions] = useState({ districts: [], project_types: [] });
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [loadingOptions, setLoadingOptions] = useState(true);

  const [baselineData, setBaselineData] = useState(null);
  const [loadingBaseline, setLoadingBaseline] = useState(false);
  const [baselineError, setBaselineError] = useState(null);

  // Compare project state
  const [compareProjectId, setCompareProjectId] = useState('');
  const [comparisonResult, setComparisonResult] = useState(null);
  const [loadingCompare, setLoadingCompare] = useState(false);
  const [compareError, setCompareError] = useState(null);

  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const data = await getBaselineOptions();
        setOptions(data);
        if (data.districts && data.districts.length > 0) {
          setSelectedDistrict(data.districts[0]);
        }
        if (data.project_types && data.project_types.length > 0) {
          setSelectedType(data.project_types[0]);
        }
      } catch (err) {
        console.error('Failed to fetch baseline options:', err);
      } finally {
        setLoadingOptions(false);
      }
    };
    fetchOptions();
  }, []);

  const handleCalculateBaseline = async () => {
    if (!selectedDistrict || !selectedType) return;

    setLoadingBaseline(true);
    setBaselineError(null);
    try {
      const data = await calculateBaseline(selectedDistrict, selectedType);
      setBaselineData(data);
    } catch (err) {
      setBaselineError(err.response?.data?.detail || 'Failed to calculate peer baseline.');
    } finally {
      setLoadingBaseline(false);
    }
  };

  const handleCompareProject = async () => {
    if (!compareProjectId.trim()) return;

    setLoadingCompare(true);
    setCompareError(null);
    try {
      const data = await compareProjectToPeers(compareProjectId.trim());
      setComparisonResult(data);
    } catch (err) {
      setCompareError(err.response?.data?.detail || `Project ID '${compareProjectId}' not found.`);
      setComparisonResult(null);
    } finally {
      setLoadingCompare(false);
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
          MODULE 02
        </div>
        <h1 className="page-title">Rules & Peer Baselines</h1>
        <p className="page-description">
          Compare projects against relevant historical peer groups using robust statistical ranges.
        </p>
      </div>

      {/* Filter Selection Card */}
      <div className="card">
        <div className="card-title">Select Peer Cohort</div>
        <div style={{ display: 'flex', gap: '1.25rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', display: 'block', marginBottom: '0.3rem' }}>
              District
            </label>
            <select
              value={selectedDistrict}
              onChange={(e) => setSelectedDistrict(e.target.value)}
              className="search-input"
              style={{ width: '220px' }}
              disabled={loadingOptions}
            >
              {options.districts && options.districts.length > 0 ? (
                options.districts.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))
              ) : (
                <option value="">No districts available</option>
              )}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', display: 'block', marginBottom: '0.3rem' }}>
              Project Type
            </label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="search-input"
              style={{ width: '240px' }}
              disabled={loadingOptions || !options.project_types || options.project_types.length === 0}
            >
              {options.project_types && options.project_types.length > 0 ? (
                options.project_types.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))
              ) : (
                <option value="">No project types available</option>
              )}
            </select>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleCalculateBaseline}
            disabled={loadingBaseline || !selectedDistrict || !selectedType}
            style={{ marginTop: '1.4rem' }}
          >
            <Filter style={{ width: 14, height: 14 }} />
            {loadingBaseline ? 'Calculating...' : 'Calculate Peer Baseline'}
          </button>
        </div>

        {baselineError && (
          <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '0.65rem 1rem', borderRadius: '6px', marginTop: '1rem', fontSize: '0.8rem' }}>
            {baselineError}
          </div>
        )}
      </div>

      {/* Baseline Summary & Results */}
      {baselineData && (
        <>
          {/* Header Summary Banner */}
          <div className="card" style={{ borderLeft: baselineData.sufficient_peers ? '4px solid #16a34a' : '4px solid #d97706' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>
                  Peer Group: {baselineData.district} • {baselineData.project_type}
                </h3>
                <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.2rem' }}>
                  <strong>Baseline Source:</strong> {baselineData.peer_level === 'DISTRICT_AND_TYPE' ? 'Same District + Same Project Type' : 'Fallback: Same Project Type Across Districts'}
                </div>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                  {baselineData.note} | Label: <span className="badge badge-normal">CONTROLLED TEST DATA</span>
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Peer Cohort Size</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>{baselineData.peer_count} projects</div>
                </div>

                {baselineData.peer_level === 'DISTRICT_AND_TYPE' && (
                  <span className="badge badge-normal" style={{ padding: '0.35rem 0.65rem' }}>
                    <CheckCircle style={{ width: 14, height: 14 }} /> Sufficient Peer Data
                  </span>
                )}
                {baselineData.peer_level === 'TYPE_ONLY_FALLBACK' && (
                  <span className="badge badge-warning" style={{ padding: '0.35rem 0.65rem' }}>
                    <AlertTriangle style={{ width: 14, height: 14 }} /> Fallback Baseline (All Districts)
                  </span>
                )}
                {baselineData.peer_level === 'INSUFFICIENT_DATA' && (
                  <span className="badge badge-high" style={{ padding: '0.35rem 0.65rem' }}>
                    <HelpCircle style={{ width: 14, height: 14 }} /> Insufficient Data (&lt; 3 Peers)
                  </span>
                )}
              </div>
            </div>
          </div>

          {baselineData.sufficient_peers && (
            <>
              {/* Statistic Cards Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Peer Count</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', marginTop: '0.2rem' }}>
                    {baselineData.peer_count} projects
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#16a34a', marginTop: '0.3rem', fontWeight: 600 }}>
                    Sufficient Peer Cohort
                  </div>
                </div>

                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Median Expenditure</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#ea580c', marginTop: '0.2rem' }}>
                    {formatCurrency(baselineData.expenditure?.median)}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.3rem' }}>
                    Sanctioned Median: {formatCurrency(baselineData.sanctioned_amount?.median)}
                  </div>
                </div>

                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Q1 / Q3 Quartiles</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0f172a', marginTop: '0.3rem' }}>
                    Q1: {formatCurrency(baselineData.expenditure?.q1)} <br />
                    Q3: {formatCurrency(baselineData.expenditure?.q3)}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                    Interquartile Range (IQR): {formatCurrency(baselineData.expenditure?.iqr)}
                  </div>
                </div>

                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Expected Expenditure Range</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#0f172a', marginTop: '0.3rem' }}>
                    {formatCurrency(baselineData.expenditure?.lower_bound)} — {formatCurrency(baselineData.expenditure?.upper_bound)}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#16a34a', marginTop: '0.3rem', fontWeight: 600 }}>
                    Robust IQR Bounds (1.5× IQR)
                  </div>
                </div>

                <div className="card">
                  <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Median Expected Duration</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', marginTop: '0.2rem' }}>
                    {baselineData.timeline?.median_expected_days !== undefined ? `${baselineData.timeline.median_expected_days} days` : 'N/A'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '0.3rem' }}>
                    Used {baselineData.timeline?.records_used || 0} valid dates
                  </div>
                </div>
              </div>

              {/* Range Visual Component */}
              <div className="card">
                <div className="card-title">Expected Expenditure Range Visualisation</div>
                <div style={{ padding: '1rem 0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#64748b', marginBottom: '0.4rem', fontWeight: 600 }}>
                    <span>Lower Limit: {formatCurrency(baselineData.expenditure?.lower_bound)}</span>
                    <span style={{ color: '#ea580c', fontWeight: 700 }}>Median: {formatCurrency(baselineData.expenditure?.median)}</span>
                    <span>Upper Limit: {formatCurrency(baselineData.expenditure?.upper_bound)}</span>
                  </div>

                  <div style={{ height: '12px', backgroundColor: '#e2e8f0', borderRadius: '6px', position: 'relative' }}>
                    <div 
                      style={{ 
                        position: 'absolute', 
                        left: '20%', 
                        right: '20%', 
                        top: 0, 
                        bottom: 0, 
                        backgroundColor: '#ffedd5', 
                        borderLeft: '2px solid #ea580c', 
                        borderRight: '2px solid #ea580c' 
                      }} 
                    />
                    <div 
                      style={{ 
                        position: 'absolute', 
                        left: '50%', 
                        top: '-4px', 
                        bottom: '-4px', 
                        width: '4px', 
                        backgroundColor: '#ea580c', 
                        borderRadius: '2px' 
                      }} 
                    />
                  </div>

                  <div style={{ fontSize: '0.75rem', color: '#94a3b8', textAlign: 'center', marginTop: '0.6rem' }}>
                    Projects falling outside the shaded IQR range [Q1 - 1.5×IQR, Q3 + 1.5×IQR] receive a statistical review flag.
                  </div>
                </div>
              </div>

              {/* Underlying Peer Projects Table */}
              <div className="card">
                <div className="card-title">Underlying Peer Cohort Projects ({baselineData.peer_projects.length})</div>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Project ID</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>District</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Type</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Sanctioned (₹)</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Expenditure (₹)</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Progress</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {baselineData.peer_projects.map((p) => (
                        <tr key={p.project_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }} className="mono">{p.project_id}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{p.district}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{p.project_type}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{formatCurrency(p.sanctioned_amount)}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{formatCurrency(p.expenditure)}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{p.progress_percent}%</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>
                            <span className="badge badge-normal">{p.status}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </>
      )}

      {/* Project-Level Baseline Comparison Test Section */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-title">Compare Specific Project Against Peer Baseline</div>
        <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '1rem' }}>
          Test single project metrics against its calculated peer cohort range to evaluate statistical variance.
        </p>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Enter Project ID..."
            value={compareProjectId}
            onChange={(e) => setCompareProjectId(e.target.value)}
            className="search-input"
            style={{ width: '280px' }}
          />

          <button
            className="btn btn-primary"
            onClick={handleCompareProject}
            disabled={loadingCompare || !compareProjectId.trim()}
          >
            <BarChart3 style={{ width: 14, height: 14 }} />
            {loadingCompare ? 'Evaluating...' : 'Compare Against Peers'}
          </button>
        </div>

        {compareError && (
          <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '0.65rem 1rem', borderRadius: '6px', marginTop: '1rem', fontSize: '0.8rem' }}>
            {compareError}
          </div>
        )}

        {comparisonResult && (
          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '1.25rem', marginTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700 }} className="mono">
                {comparisonResult.project_id} — {comparisonResult.project_name}
              </h4>
              <span className={`badge ${comparisonResult.comparison.expenditure_outside_expected_range ? 'badge-warning' : 'badge-normal'}`}>
                {comparisonResult.comparison.expenditure_outside_expected_range ? 'Outside Peer Range' : 'Inside Peer Range'}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem', marginTop: '0.85rem', fontSize: '0.8rem' }}>
              <div>
                <span style={{ color: '#64748b' }}>Expenditure:</span> <br />
                <strong style={{ fontSize: '0.95rem' }}>{formatCurrency(comparisonResult.expenditure)}</strong>
              </div>

              <div>
                <span style={{ color: '#64748b' }}>Exp vs Peer Median %:</span> <br />
                <strong style={{ fontSize: '0.95rem', color: comparisonResult.comparison.expenditure_vs_peer_median_percent > 0 ? '#ea580c' : '#16a34a' }}>
                  {comparisonResult.comparison.expenditure_vs_peer_median_percent !== null ? `${comparisonResult.comparison.expenditure_vs_peer_median_percent}%` : 'N/A'}
                </strong>
              </div>

              <div>
                <span style={{ color: '#64748b' }}>Peer Level Used:</span> <br />
                <strong style={{ fontSize: '0.85rem' }}>{comparisonResult.peer_level_used} ({comparisonResult.peer_count} peers)</strong>
              </div>
            </div>

            <div style={{ backgroundColor: '#ffffff', border: '1px solid #cbd5e1', padding: '0.65rem 0.85rem', borderRadius: '4px', marginTop: '0.85rem', fontSize: '0.8rem', color: '#334155' }}>
              <strong>Statistical Review Indicator:</strong> {comparisonResult.interpretation}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Baselines;
