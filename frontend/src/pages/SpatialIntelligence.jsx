import React, { useState, useEffect } from 'react';
import { MapPin, Compass, Layers, Info, AlertTriangle } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import { getSpatialProjects } from '../services/api';
import L from 'leaflet';

// Fix default marker icon issues in Leaflet with Vite
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

const SpatialIntelligence = () => {
  const [spatialData, setSpatialData] = useState(null);
  const [radiusMeters, setRadiusMeters] = useState(1000);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSpatial = async (r) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSpatialProjects(r);
      setSpatialData(data);
    } catch (err) {
      setError('Failed to load spatial intelligence data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSpatial(radiusMeters);
  }, [radiusMeters]);

  const mapCenter = [11.2750, 77.5833]; // Default center (Tamil Nadu)

  return (
    <div>
      <div className="page-header">
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#ea580c', letterSpacing: '0.5px' }}>
          MODULE 05
        </div>
        <h1 className="page-title">Spatial Intelligence</h1>
        <p className="page-description">
          Geographic plotting and proximity relationship analysis across stored MPLADS projects.
        </p>
      </div>

      {/* Control Panel Card */}
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#0f172a', fontWeight: 600, fontSize: '0.9rem' }}>
            <span>Proximity Radius Selection:</span>
          </div>
          <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>
            Detects candidate project pairs located within selected distance radius.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {[250, 500, 1000, 2000].map((r) => (
            <button
              key={r}
              className={`btn ${radiusMeters === r ? 'btn-primary' : ''}`}
              onClick={() => setRadiusMeters(r)}
              style={{ fontSize: '0.8rem', padding: '0.3rem 0.65rem' }}
            >
              {r >= 1000 ? `${r / 1000} km` : `${r} m`}
            </button>
          ))}
        </div>
      </div>

      {/* Disclaimer Banner */}
      <div style={{ backgroundColor: '#fff7ed', border: '1px solid #ffedd5', padding: '0.65rem 1rem', borderRadius: '6px', marginBottom: '1.25rem', fontSize: '0.8rem', color: '#9a3412', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Info style={{ width: 16, height: 16, flexShrink: 0 }} />
        <span>
          <strong>Controlled Test Data</strong> — Map renders valid coordinates from prototype database only. No coordinates fabricated.
        </span>
      </div>

      {error && (
        <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '0.65rem 1rem', borderRadius: '6px', marginBottom: '1.25rem', fontSize: '0.8rem' }}>
          {error}
        </div>
      )}

      {/* Map Container */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div className="card-title" style={{ padding: '1rem 1.25rem', marginBottom: '0', borderBottom: '1px solid #e2e8f0' }}>
          Interactive Map — OpenStreetMap Mapped Projects ({spatialData?.total_mapped_projects || 0})
        </div>

        <div style={{ height: '420px', width: '100%', position: 'relative' }}>
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', backgroundColor: '#f8fafc', color: '#64748b' }}>
              Loading map layer...
            </div>
          ) : (
            <MapContainer center={mapCenter} zoom={8} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {spatialData?.features.map((feat) => (
                <React.Fragment key={feat.project_id}>
                  <Marker position={[feat.latitude, feat.longitude]}>
                    <Popup>
                      <div style={{ fontSize: '0.8rem', lineHeight: '1.4' }}>
                        <strong className="mono">{feat.project_id}</strong> <br />
                        <strong>{feat.project_name}</strong> <br />
                        District: {feat.district} <br />
                        Sector: {feat.project_type} <br />
                        Exp: ₹{feat.expenditure.toLocaleString('en-IN')} <br />
                        Priority: <span style={{ fontWeight: 600, color: feat.review_priority === 'High Review Priority' ? '#dc2626' : '#16a34a' }}>{feat.review_priority}</span>
                      </div>
                    </Popup>
                  </Marker>

                  <Circle
                    center={[feat.latitude, feat.longitude]}
                    radius={radiusMeters}
                    pathOptions={{ color: '#ea580c', fillColor: '#ea580c', fillOpacity: 0.08, weight: 1 }}
                  />
                </React.Fragment>
              ))}
            </MapContainer>
          )}
        </div>
      </div>

      {/* Mapped Candidates & Proximity Pairs Table */}
      <div className="card" style={{ marginTop: '1.25rem' }}>
        <div className="card-title">Mapped Project Geolocation Inventory</div>
        {loading ? (
          <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Loading coordinate inventory...</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#475569' }}>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Project ID</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Project Name</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>District</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Coordinates</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Distance (m)</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Text Similarity</th>
                  <th style={{ padding: '0.6rem 0.75rem' }}>Relationship Status</th>
                </tr>
              </thead>
              <tbody>
                {spatialData?.features.map((f) => {
                  const topCand = f.nearby_candidates && f.nearby_candidates.length > 0 ? f.nearby_candidates[0] : null;
                  const distText = topCand ? `${topCand.distance_meters} m` : 'N/A';
                  const simText = topCand ? `${topCand.text_similarity_percent}%` : 'N/A';
                  const statusLabel = topCand ? topCand.similarity_status : 'Isolated Location';

                  let badgeClass = 'badge-normal';
                  if (statusLabel.includes('Overlap')) badgeClass = 'badge-high';
                  else if (statusLabel.includes('Proximity') || statusLabel.includes('Similar')) badgeClass = 'badge-warning';

                  return (
                    <tr key={f.project_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600 }} className="mono">{f.project_id}</td>
                      <td style={{ padding: '0.6rem 0.75rem' }}>{f.project_name}</td>
                      <td style={{ padding: '0.6rem 0.75rem' }}>{f.district}</td>
                      <td style={{ padding: '0.6rem 0.75rem' }} className="mono">{f.latitude.toFixed(4)}, {f.longitude.toFixed(4)}</td>
                      <td style={{ padding: '0.6rem 0.75rem' }} className="mono">{distText}</td>
                      <td style={{ padding: '0.6rem 0.75rem' }} className="mono">{simText}</td>
                      <td style={{ padding: '0.6rem 0.75rem' }}>
                        <span className={`badge ${badgeClass}`} style={{ fontSize: '0.7rem' }}>
                          {statusLabel}
                        </span>
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

export default SpatialIntelligence;
