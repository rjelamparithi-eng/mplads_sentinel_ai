import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ExecutiveDashboard from './pages/ExecutiveDashboard';
import DataIngestion from './pages/DataIngestion';
import Baselines from './pages/Baselines';
import AnomalyDetection from './pages/AnomalyDetection';
import RiskPassport from './pages/RiskPassport';
import SpatialIntelligence from './pages/SpatialIntelligence';
import AuditWorkflow from './pages/AuditWorkflow';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<ExecutiveDashboard />} />
        <Route path="ingestion" element={<DataIngestion />} />
        <Route path="baselines" element={<Baselines />} />
        <Route path="anomaly" element={<AnomalyDetection />} />
        <Route path="passport" element={<RiskPassport />} />
        <Route path="spatial" element={<SpatialIntelligence />} />
        <Route path="audit" element={<AuditWorkflow />} />
      </Route>
    </Routes>
  );
}

export default App;
