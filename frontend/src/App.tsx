import { Route, Routes } from 'react-router-dom'
import { Shell } from './components/Shell'
import { Dashboard } from './pages/Dashboard'
import { KpiDetail } from './pages/KpiDetail'
import { AuditLog } from './pages/AuditLog'

function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/kpi/:id" element={<KpiDetail />} />
        <Route path="/audit" element={<AuditLog />} />
      </Routes>
    </Shell>
  )
}

export default App
