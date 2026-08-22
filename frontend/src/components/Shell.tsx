import { NavLink } from 'react-router-dom'
import type { ReactNode } from 'react'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
    isActive ? 'text-[var(--text-primary)] bg-[var(--brand-bg)]' : 'text-[var(--text-secondary)] hover:bg-[var(--border)]'
  }`

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--page)' }}>
      <header
        className="sticky top-0 z-20 border-b backdrop-blur"
        style={{ borderColor: 'var(--border)', background: 'color-mix(in srgb, var(--surface) 88%, transparent)' }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-md flex items-center justify-center text-white text-sm font-bold"
              style={{ background: 'var(--brand)' }}
            >
              C
            </div>
            <span className="font-semibold tracking-tight">Clarity</span>
            <span className="hidden sm:inline text-xs text-[var(--text-muted)] ml-1">AI KPI Storytelling Engine</span>
          </div>
          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              Dashboard
            </NavLink>
            <NavLink to="/audit" className={navLinkClass}>
              Audit Log
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">{children}</main>
      <footer className="border-t py-4 text-center text-xs text-[var(--text-muted)]" style={{ borderColor: 'var(--border)' }}>
        Clarity — Accenture Innovation Challenge 2026 prototype · Demo data, not connected to production systems
      </footer>
    </div>
  )
}
