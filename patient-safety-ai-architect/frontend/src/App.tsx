import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import Layout from '@/components/Layout'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import IncidentReport from '@/pages/IncidentReport'
import IncidentList from '@/pages/IncidentList'
import IncidentDetail from '@/pages/IncidentDetail'
import IndicatorList from '@/pages/IndicatorList'
import IndicatorForm from '@/pages/IndicatorForm'
import IndicatorDetail from '@/pages/IndicatorDetail'
import AccessLog from '@/pages/AccessLog'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="incidents" element={<IncidentList />} />
        <Route path="incidents/new" element={<IncidentReport />} />
        <Route path="incidents/:id" element={<IncidentDetail />} />
        <Route path="indicators" element={<IndicatorList />} />
        <Route path="indicators/new" element={<IndicatorForm />} />
        <Route path="indicators/:id" element={<IndicatorDetail />} />
        <Route path="indicators/:id/edit" element={<IndicatorForm />} />
        <Route path="access-log" element={<AccessLog />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
