import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Recommendations from './pages/Recommendations'
import InstanceFinder from './pages/InstanceFinder'
import PriceComparison from './pages/PriceComparison'
import CostCalculator from './pages/CostCalculator'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/instances" element={<InstanceFinder />} />
        <Route path="/compare" element={<PriceComparison />} />
        <Route path="/calculator" element={<CostCalculator />} />
      </Routes>
    </Layout>
  )
}

export default App

