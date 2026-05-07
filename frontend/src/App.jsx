import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Layout from './components/Layout'
import ErrorBoundary from './components/ErrorBoundary'
import ProtectedRoute from './components/ProtectedRoute'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import Recommendations from './pages/Recommendations'
import InstanceFinder from './pages/InstanceFinder'
import PriceComparison from './pages/PriceComparison'
import CostCalculator from './pages/CostCalculator'
import CloudCostAI from './pages/CloudCostAI'
import SpotIntelligence from './pages/SpotIntelligence'
import InfraIntelligence from './pages/InfraIntelligence'
import FinOpsIntelligence from './pages/FinOpsIntelligence'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          
          {/* Protected Routes - All inside Layout */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/ai" element={
            <ProtectedRoute>
              <Layout>
                <CloudCostAI />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/spot-intelligence" element={
            <ProtectedRoute>
              <Layout>
                <SpotIntelligence />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/infra-intelligence" element={
            <ProtectedRoute>
              <Layout>
                <InfraIntelligence />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/finops" element={
            <ProtectedRoute>
              <Layout>
                <FinOpsIntelligence />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/recommendations" element={
            <ProtectedRoute>
              <Layout>
                <Recommendations />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/instances" element={
            <ProtectedRoute>
              <Layout>
                <InstanceFinder />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/compare" element={
            <ProtectedRoute>
              <Layout>
                <PriceComparison />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/calculator" element={
            <ProtectedRoute>
              <Layout>
                <CostCalculator />
              </Layout>
            </ProtectedRoute>
          } />

          {/* Catch all - redirect to landing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
