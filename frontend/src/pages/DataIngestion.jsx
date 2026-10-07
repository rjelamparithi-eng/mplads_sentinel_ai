import React, { useState } from 'react';
import { UploadCloud, Download, CheckCircle, AlertTriangle, XCircle, FileText, ArrowRight, Database, Info, Layers } from 'lucide-react';
import api from '../services/api';

const DataIngestion = () => {
  const [datasetType, setDatasetType] = useState("CONTROLLED_TEST"); // CONTROLLED_TEST or PUBLIC_MPLADS_DERIVED
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progressStage, setProgressStage] = useState("IDLE"); // IDLE, PARSING, VALIDATING, STANDARDISING, IMPORTING
  const [previewData, setPreviewData] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [commitStatus, setCommitStatus] = useState(null);
  const [dataSourceLabel, setDataSourceLabel] = useState("CONTROLLED_TEST");

  const handleDatasetTypeSelect = (type) => {
    setDatasetType(type);
    setSelectedFile(null);
    setPreviewData(null);
    setErrorMsg(null);
    setCommitStatus(null);
    setProgressStage("IDLE");
    setDataSourceLabel(type === "PUBLIC_MPLADS_DERIVED" ? "PUBLIC_MPLADS_DERIVED_GITHUB" : "CONTROLLED_TEST");
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewData(null);
      setErrorMsg(null);
      setCommitStatus(null);
      setProgressStage("IDLE");
    }
  };

  const handleDownloadTemplate = () => {
    window.open(`${api.defaults.baseURL}/ingestion/template?dataset_type=${datasetType}`, '_blank');
  };

  const isPublicMode = (datasetType === "PUBLIC_MPLADS_DERIVED");

  const handleValidateAndClean = async () => {
    if (!selectedFile) return;

    const maxBytes = isPublicMode ? 50 * 1024 * 1024 : 10 * 1024 * 1024;
    if (selectedFile.size > maxBytes) {
      setErrorMsg(
        isPublicMode 
          ? "File exceeds 50 MB limit for Public MPLADS dataset." 
          : "File exceeds 10 MB limit for Controlled Test dataset."
      );
      return;
    }

    setLoading(true);
    setProgressStage("PARSING");
    setErrorMsg(null);
    setCommitStatus(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setProgressStage("VALIDATING");
      const res = await api.post(`/ingestion/preview?dataset_type=${datasetType}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000,
      });
      
      setProgressStage("STANDARDISING");
      setPreviewData(res.data);
      if (res.data.dataset_type) {
        setDatasetType(res.data.dataset_type);
      }
    } catch (err) {
      let msg = 'Failed to process file.';
      if (err.code === 'ECONNABORTED' || (err.message && err.message.includes('timeout'))) {
        msg = 'Backend timeout while processing large dataset.';
      } else if (err.response?.status === 413) {
        msg = isPublicMode ? 'File exceeds 50 MB.' : 'File exceeds 10 MB.';
      } else if (err.response?.data?.detail) {
        msg = err.response.data.detail;
      } else if (err.message) {
        msg = err.message;
      }
      setErrorMsg(msg);
    } finally {
      setLoading(false);
      setProgressStage("IDLE");
    }
  };

  const handleCommit = async () => {
    if (!previewData) return;

    setLoading(true);
    setProgressStage("IMPORTING");
    setErrorMsg(null);

    try {
      let res;
      if (isPublicMode && selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('dataset_type', datasetType);
        formData.append('data_source', dataSourceLabel);

        res = await api.post('/ingestion/commit', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 180000,
        });
      } else {
        const recordsToCommit = (previewData.clean_preview || []).map((row) => ({
          status: row.status,
          data: row.data,
        }));

        res = await api.post('/ingestion/commit', {
          dataset_type: datasetType,
          records: recordsToCommit,
          data_source: dataSourceLabel,
        });
      }

      setCommitStatus(res.data);
    } catch (err) {
      let msg = 'Failed to commit records to database.';
      if (err.code === 'ECONNABORTED' || (err.message && err.message.includes('timeout'))) {
        msg = 'Backend timeout while committing records to database.';
      } else if (err.response?.data?.detail) {
        msg = err.response.data.detail;
      } else if (err.message) {
        msg = err.message;
      }
      setErrorMsg(msg);
    } finally {
      setLoading(false);
      setProgressStage("IDLE");
    }
  };

  return (
    <div>
      <div className="page-header">
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ea580c', letterSpacing: '0.5px' }}>
          MODULE 01
        </div>
        <h1 className="page-title">Data Ingestion</h1>
        <p className="page-description">
          Structured MPLADS-style data intake, cleaning and operator preview.
        </p>
      </div>

      {/* Dataset Type Selector */}
      <div className="card" style={{ marginBottom: '1.25rem', padding: '1rem 1.25rem' }}>
        <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#475569', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Select Ingestion Dataset Type:
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            className={`btn ${isPublicMode ? 'btn-primary' : ''}`}
            onClick={() => handleDatasetTypeSelect("PUBLIC_MPLADS_DERIVED")}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            Public MPLADS-Derived Data (Up to 50 MB)
          </button>

          <button
            className={`btn ${!isPublicMode ? 'btn-primary' : ''}`}
            onClick={() => handleDatasetTypeSelect("CONTROLLED_TEST")}
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            Controlled Test Data (Up to 10 MB)
          </button>
        </div>
      </div>

      {/* Pipeline Stage Bar with dynamic progress indicators */}
      <div className="card" style={{ padding: '0.85rem 1.25rem', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem', fontWeight: 600 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: progressStage === "PARSING" ? '#ea580c' : (selectedFile ? '#16a34a' : '#94a3b8') }}>
            <span style={{ width: 22, height: 22, borderRadius: '50%', backgroundColor: progressStage === "PARSING" ? '#ea580c' : (selectedFile ? '#16a34a' : '#94a3b8'), color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem' }}>1</span>
            <span>Parsing</span>
          </div>
          <ArrowRight style={{ width: 14, height: 14, color: '#cbd5e1' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: progressStage === "VALIDATING" ? '#ea580c' : (previewData ? '#16a34a' : '#94a3b8') }}>
            <span style={{ width: 22, height: 22, borderRadius: '50%', backgroundColor: progressStage === "VALIDATING" ? '#ea580c' : (previewData ? '#16a34a' : '#94a3b8'), color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem' }}>2</span>
            <span>Validating</span>
          </div>
          <ArrowRight style={{ width: 14, height: 14, color: '#cbd5e1' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: progressStage === "STANDARDISING" ? '#ea580c' : (previewData ? '#16a34a' : '#94a3b8') }}>
            <span style={{ width: 22, height: 22, borderRadius: '50%', backgroundColor: progressStage === "STANDARDISING" ? '#ea580c' : (previewData ? '#16a34a' : '#94a3b8'), color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem' }}>3</span>
            <span>Standardising</span>
          </div>
          <ArrowRight style={{ width: 14, height: 14, color: '#cbd5e1' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: progressStage === "IMPORTING" ? '#ea580c' : (commitStatus ? '#16a34a' : '#94a3b8') }}>
            <span style={{ width: 22, height: 22, borderRadius: '50%', backgroundColor: progressStage === "IMPORTING" ? '#ea580c' : (commitStatus ? '#16a34a' : '#94a3b8'), color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem' }}>4</span>
            <span>Importing</span>
          </div>
        </div>
      </div>

      {/* Dataset Disclaimer Banner */}
      <div style={{ backgroundColor: '#fff7ed', border: '1px solid #ffedd5', padding: '0.65rem 1rem', borderRadius: '6px', marginBottom: '1.25rem', fontSize: '0.8rem', color: '#9a3412', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Info style={{ width: 16, height: 16, flexShrink: 0 }} />
        <span>
          {isPublicMode ? (
            <strong>Public MPLADS-derived records mode (50 MB Limit) — pandas streaming validation enabled.</strong>
          ) : (
            <strong>Controlled Test Data mode (10 MB Limit) — structured project records.</strong>
          )}
        </span>
      </div>

      {/* Upload Card */}
      <div className="card">
        <div className="card-title" style={{ justifyContent: 'space-between', display: 'flex' }}>
          <span>1. File Selection ({isPublicMode ? 'Public MPLADS Mode - Max 50 MB' : 'Controlled Test Mode - Max 10 MB'})</span>
          <button className="btn" onClick={handleDownloadTemplate} style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}>
            <Download style={{ width: 12, height: 12 }} /> Download {isPublicMode ? 'Public CSV Template' : 'CSV Template'}
          </button>
        </div>

        <div style={{ padding: '1.5rem', border: '2px dashed #cbd5e1', borderRadius: '8px', textAlign: 'center', backgroundColor: '#f8fafc' }}>
          <UploadCloud style={{ width: 38, height: 38, color: '#ea580c', margin: '0 auto 0.5rem' }} />
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#0f172a' }}>
            {selectedFile ? selectedFile.name : `Drop ${isPublicMode ? 'Public MPLADS CSV / XLSX' : 'Controlled Test CSV / XLSX'} file here`}
          </h4>
          <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.2rem' }}>
            {selectedFile 
              ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB (${selectedFile.size.toLocaleString()} bytes)` 
              : `Supports structured CSV and XLSX files up to ${isPublicMode ? '50 MB' : '10 MB'}.`
            }
          </p>

          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'center', gap: '0.75rem' }}>
            <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
              <span>Browse File</span>
              <input type="file" accept=".csv, .xlsx, .xls" onChange={handleFileChange} style={{ display: 'none' }} />
            </label>

            {selectedFile && (
              <button className="btn" onClick={handleValidateAndClean} disabled={loading}>
                {loading ? `${progressStage || 'Processing'}...` : 'Validate & Clean'}
              </button>
            )}
          </div>
        </div>

        {errorMsg && (
          <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '0.65rem 1rem', borderRadius: '6px', marginTop: '1rem', fontSize: '0.8rem' }}>
            <strong>Error:</strong> {errorMsg}
          </div>
        )}
      </div>

      {/* Cleaning Metrics Summary */}
      {previewData && (
        <>
          <div className="card-title" style={{ marginTop: '1.5rem', marginBottom: '0.75rem' }}>
            2. Data Cleaning & Metrics Summary ({previewData.rows_received?.toLocaleString()} Total Rows Processed)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.85rem', marginBottom: '1.25rem' }}>
            <div className="card" style={{ padding: '0.85rem' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Rows Received</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', marginTop: '0.2rem' }}>{previewData.rows_received?.toLocaleString()}</div>
            </div>

            <div className="card" style={{ padding: '0.85rem', borderLeft: '3px solid #16a34a' }}>
              <div style={{ fontSize: '0.75rem', color: '#15803d', fontWeight: 600 }}>Valid Rows</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#16a34a', marginTop: '0.2rem' }}>{previewData.valid_rows?.toLocaleString()}</div>
            </div>

            <div className="card" style={{ padding: '0.85rem', borderLeft: '3px solid #d97706' }}>
              <div style={{ fontSize: '0.75rem', color: '#b45309', fontWeight: 600 }}>Warnings</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#d97706', marginTop: '0.2rem' }}>{previewData.warning_rows?.toLocaleString()}</div>
            </div>

            <div className="card" style={{ padding: '0.85rem', borderLeft: '3px solid #dc2626' }}>
              <div style={{ fontSize: '0.75rem', color: '#b91c1c', fontWeight: 600 }}>Rejected Rows</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#dc2626', marginTop: '0.2rem' }}>{previewData.rejected_rows?.toLocaleString()}</div>
            </div>

            <div className="card" style={{ padding: '0.85rem' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Exact Source Duplicates</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#ea580c', marginTop: '0.2rem' }}>{previewData.duplicate_rows?.toLocaleString()}</div>
            </div>

            <div className="card" style={{ padding: '0.85rem' }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>Missing Optional Fields</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#475569', marginTop: '0.2rem' }}>{previewData.missing_values?.toLocaleString()}</div>
            </div>
          </div>

          {/* Cleaned Records Preview Table */}
          <div className="card">
            <div className="card-title">
              3. Cleaned Records Preview (First {previewData.clean_preview?.length || 0} Preview Rows shown out of {previewData.rows_received?.toLocaleString()})
            </div>
            <div style={{ overflowX: 'auto' }}>
              {isPublicMode ? (
                /* Public MPLADS Derived Table */
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Status</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Row</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Internal Record Key</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Work Description</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>State</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Constituency</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Recommended (₹)</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Status</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Data Quality</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(previewData.clean_preview || []).slice(0, 50).map((row) => {
                      const d = row.data;
                      let badgeClass = 'badge-normal';
                      if (row.status === 'WARNING') badgeClass = 'badge-warning';
                      if (row.status === 'REJECTED') badgeClass = 'badge-high';

                      return (
                        <tr key={row.row_number} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '0.6rem 0.75rem' }}>
                            <span className={`badge ${badgeClass}`}>{row.status}</span>
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }}>#{row.row_number}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }} className="mono">{d.internal_record_key || 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.work_description || d.normalized_work || 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.state || 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.constituency || 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.recommended_amount ? `₹${Number(d.recommended_amount).toLocaleString('en-IN')}` : 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.work_status || d.ida_approval_status || 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>
                            <span className="badge badge-normal">{d.data_quality_status || 'COMPLETE'}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : (
                /* Controlled Test Table */
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Status</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Row</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Project ID</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Project Name</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>District</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Type</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Sanctioned (₹)</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Expenditure (₹)</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>Progress</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(previewData.clean_preview || []).slice(0, 50).map((row) => {
                      const d = row.data;
                      let badgeClass = 'badge-normal';
                      if (row.status === 'WARNING') badgeClass = 'badge-warning';
                      if (row.status === 'REJECTED') badgeClass = 'badge-high';

                      return (
                        <tr key={row.row_number} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '0.6rem 0.75rem' }}>
                            <span className={`badge ${badgeClass}`}>{row.status}</span>
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }}>#{row.row_number}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }} className="mono">{d.project_id || 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.project_name || 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.district || 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.project_type || 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.sanctioned_amount ? `₹${Number(d.sanctioned_amount).toLocaleString('en-IN')}` : 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.expenditure ? `₹${Number(d.expenditure).toLocaleString('en-IN')}` : 'N/A'}</td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>{d.progress_percent !== undefined ? `${d.progress_percent}%` : 'N/A'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* Validation Issues Panel */}
          {previewData.issues && previewData.issues.length > 0 && (
            <div className="card">
              <div className="card-title" style={{ color: '#b45309' }}>Validation & Cleaning Logs ({previewData.issues.length})</div>
              <div style={{ maxHeight: '200px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {previewData.issues.map((iss, i) => (
                  <div 
                    key={i} 
                    style={{ 
                      fontSize: '0.75rem', 
                      padding: '0.4rem 0.75rem', 
                      borderRadius: '4px',
                      backgroundColor: iss.issue_type === 'INVALID_VALUE' || iss.issue_type === 'MISSING_FIELD' ? '#fef2f2' : '#fffbe6',
                      border: iss.issue_type === 'INVALID_VALUE' || iss.issue_type === 'MISSING_FIELD' ? '1px solid #fecaca' : '1px solid #fef08a',
                      color: iss.issue_type === 'INVALID_VALUE' || iss.issue_type === 'MISSING_FIELD' ? '#b91c1c' : '#b45309'
                    }}
                  >
                    <strong>Row #{iss.row_number}</strong> {iss.project_id ? `[${iss.project_id}]` : ''} — <em>{iss.field}</em>: {iss.message}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Commit Action Panel */}
          <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Ready to Import Clean Records</div>
              <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.1rem' }}>
                Validated records will be batch inserted into database in chunks of 1,000. Duplicate keys will be skipped.
              </p>
              <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem' }}>
                <label style={{ fontWeight: 600 }}>Data Source Tag:</label>
                <input 
                  type="text" 
                  value={dataSourceLabel} 
                  onChange={(e) => setDataSourceLabel(e.target.value)}
                  className="search-input" 
                  style={{ padding: '0.2rem 0.5rem', width: '220px', fontSize: '0.75rem' }}
                />
              </div>
            </div>

            <button 
              className="btn btn-primary" 
              onClick={handleCommit} 
              disabled={loading || (previewData.valid_rows === 0 && previewData.warning_rows === 0)}
            >
              <Database style={{ width: 14, height: 14 }} />
              {loading ? (progressStage === 'IMPORTING' ? 'Importing Batches...' : 'Processing...') : `Import Clean ${isPublicMode ? 'Public Works' : 'Controlled Records'}`}
            </button>
          </div>

          {/* Commit Success Result Notification */}
          {commitStatus && (
            <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', color: '#15803d', padding: '0.85rem 1.25rem', borderRadius: '6px', marginTop: '1rem', fontSize: '0.85rem' }}>
              <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <CheckCircle style={{ width: 18, height: 18 }} />
                <span>Import Completed (Batch ID: {commitStatus.batch_id})</span>
              </div>
              <p style={{ marginTop: '0.3rem', fontSize: '0.8rem' }}>
                <strong>{commitStatus.inserted?.toLocaleString()}</strong> records imported in batches of 1,000. <br />
                <strong>{commitStatus.skipped_duplicates?.toLocaleString()}</strong> duplicate record keys skipped. <br />
                <strong>{commitStatus.rejected?.toLocaleString()}</strong> rejected records excluded.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default DataIngestion;
