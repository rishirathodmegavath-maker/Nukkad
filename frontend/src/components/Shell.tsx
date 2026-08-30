import { NavLink } from 'react-router-dom'
import { useEffect, useState, type ReactNode } from 'react'
import { api } from '../lib/api'
import { useRole } from '../lib/roleContext'
import type { RoleOption } from '../lib/types'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
    isActive ? 'text-[var(--text-primary)] bg-[var(--brand-bg)]' : 'text-[var(--text-secondary)] hover:bg-[var(--border)]'
  }`

function RoleSwitcher() {
  const { role, setRole } = useRole()
  const [roles, setRoles] = useState<RoleOption[]>([])

  useEffect(() => {
    api.listRoles().then(setRoles).catch(() => setRoles([]))
  }, [])

  return (
    <div className="flex items-center gap-1.5">
      <span className="hidden md:inline text-xs text-[var(--text-muted)]">Viewing as</span>
      <select
        value={role}
        onChange={(e) => setRole(e.target.value)}
        className="text-xs font-medium rounded-lg border px-2 py-1.5 bg-transparent"
        style={{ borderColor: 'var(--border)', color: 'var(--text-primary)' }}
        title="Simulated role-based access control: which KPIs are visible is filtered server-side by this role."
      >
        {roles.length === 0 && <option value={role}>{role}</option>}
        {roles.map((r) => (
          <option key={r.id} value={r.id}>
            {r.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--page)' }}>
      <header
        className="sticky top-0 z-20 border-b backdrop-blur"
        style={{ borderColor: 'var(--border)', background: 'color-mix(in srgb, var(--surface) 88%, transparent)' }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 shrink-0">
            <div
              className="w-7 h-7 rounded-md flex items-center justify-center text-white text-sm font-bold"
              style={{ background: 'var(--brand)' }}
            >
              C
            </div>
            <span className="font-semibold tracking-tight">Clarity</span>
            <span className="hidden sm:inline text-xs text-[var(--text-muted)] ml-1">AI KPI Storytelling Engine</span>
          </div>
          <div className="flex items-center gap-3">
            <RoleSwitcher />
            <nav className="flex items-center gap-1">
              <NavLink to="/" end className={navLinkClass}>
                Dashboard
              </NavLink>
              <NavLink to="/audit" className={navLinkClass}>
                Audit Log
              </NavLink>
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">{children}</main>
      <footer className="border-t py-4 text-center text-xs text-[var(--text-muted)]" style={{ borderColor: 'var(--border)' }}>
        Clarity — Accenture Innovation Challenge 2026 prototype · Demo data, not connected to production systems
      </footer>
    </div>
  )
}
