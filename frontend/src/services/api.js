import axios from 'axios';

// API Client pointing to FastAPI backend with 30s timeout
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30s timeout
});

// Response Interceptor for detailed development console diagnostics
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[MPLADS Sentinel API Error Diagnostics]:', {
      code: error.code,
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
    });
    return Promise.reject(error);
  }
);

export const getDashboardSummary = async () => {
  const res = await api.get('/dashboard');
  return res.data;
};

export const getBaselineOptions = async () => {
  const res = await api.get('/baselines/options');
  return res.data;
};

export const calculateBaseline = async (district, projectType) => {
  const res = await api.get('/baselines', {
    params: { district, project_type: projectType },
  });
  return res.data;
};

export const compareProjectToPeers = async (projectId) => {
  const res = await api.get(`/baselines/project/${projectId}`);
  return res.data;
};

export const getAnomalies = async () => {
  const res = await api.get('/anomaly/list');
  return res.data;
};

export const runAnomalyPipeline = async () => {
  const res = await api.post('/anomaly/run');
  return res.data;
};

export const getRiskPassport = async (projectId) => {
  const res = await api.get(`/anomaly/passport/${projectId}`);
  return res.data;
};

export const getSpatialProjects = async (radiusMeters = 1000) => {
  const res = await api.get('/spatial/projects', {
    params: { radius_meters: radiusMeters },
  });
  return res.data;
};

export const getAuditBoard = async () => {
  const res = await api.get('/audit');
  return res.data;
};

export const updateAuditStatus = async (projectId, auditStatus) => {
  const res = await api.patch(`/audit/${projectId}`, {
    audit_status: auditStatus,
  });
  return res.data;
};

// Default export of Axios instance
export default api;
