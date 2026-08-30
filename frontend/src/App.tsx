import { Route, Routes } from 'react-router-dom'
import { Shell } from './components/Shell'
import { Dashboard } from './pages/Dashboard'
import { KpiDetail } from './pages/KpiDetail'
import { AuditLog } from './pages/AuditLog'
import { RoleProvider } from './lib/roleContext'

function App() {
  return (
    <RoleProvider>
      <Shell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/kpi/:id" element={<KpiDetail />} />
          <Route path="/audit" element={<AuditLog />} />
        </Routes>
      </Shell>
    </RoleProvider>
  )
}

export default App
