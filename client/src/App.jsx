import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DecisionCenter from './pages/DecisionCenter';
import Analytics from './pages/Analytics';
import Forecast from './pages/Forecast';
import Inventory from './pages/Inventory';
import Advisor from './pages/Advisor';
import WhatIf from './pages/WhatIf';
import Upload from './pages/Upload';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600" /></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function App() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="decisions" element={<DecisionCenter />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="forecast" element={<Forecast />} />
        <Route path="inventory" element={<Inventory />} />
        <Route path="advisor" element={<Advisor />} />
        <Route path="what-if" element={<WhatIf />} />
        <Route path="upload" element={<Upload />} />
        {/* Catch-all redirect to Decision Center */}
        <Route path="*" element={<Navigate to="/decisions" replace />} />
      </Route>
    </Routes>
  );
}

export default App;


