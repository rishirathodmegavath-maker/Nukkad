import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { KpiSummary } from '../lib/types'
import { KpiCard } from '../components/KpiCard'

function Hero() {
  return (
    <section
      className="rounded-2xl border p-6 sm:p-8 mb-8"
      style={{ borderColor: 'var(--border)', background: 'linear-gradient(135deg, var(--brand-bg), transparent 60%), var(--surface)' }}
    >
      <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--brand)' }}>
        AI KPI Storytelling Engine
      </p>
      <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight mt-2 max-w-2xl">
        A dashboard tells you revenue dropped 8%. Clarity tells you why — and what to do about it.
      </h1>
      <div className="grid sm:grid-cols-3 gap-4 mt-6 text-sm">
        <div>
          <p className="font-semibold text-[var(--text-primary)]">The problem</p>
          <p className="text-[var(--text-secondary)] mt-1">
            Explaining a metric move — is it real, why did it happen, what should we do — takes an analyst
            hours to days of manual digging across dashboards, tickets, and calendars.
          </p>
        </div>
        <div>
          <p className="font-semibold text-[var(--text-primary)]">What Clarity does</p>
          <p className="text-[var(--text-secondary)] mt-1">
            It runs anomaly detection, ranks contributing segments, pulls corroborating evidence, and
            writes an executive-ready explanation with a confidence score — in seconds.
          </p>
        </div>
        <div>
          <p className="font-semibold text-[var(--text-primary)]">Why AI is necessary</p>
          <p className="text-[var(--text-secondary)] mt-1">
            Root-cause search across many dimensions and unstructured context isn't a fixed query — it
            needs statistical judgment plus natural-language synthesis a static dashboard can't do.
          </p>
        </div>
      </div>
    </section>
  )
}

export function Dashboard() {
  const [kpis, setKpis] = useState<KpiSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listKpis()
      .then(setKpis)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <Hero />

      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
          Monitored KPIs
        </h2>
        {kpis && <span className="text-xs text-[var(--text-muted)]">{kpis.length} metrics · updated live</span>}
      </div>

      {error && (
        <div className="rounded-lg border p-4 text-sm" style={{ borderColor: 'var(--critical)', background: 'var(--critical-bg)', color: 'var(--critical)' }}>
          Couldn't reach the Clarity API at the configured URL. Is the backend running? ({error})
        </div>
      )}

      {!kpis && !error && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="rounded-xl border p-4 h-32 animate-pulse" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }} />
          ))}
        </div>
      )}

      {kpis && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {kpis.map((kpi) => (
            <KpiCard key={kpi.id} kpi={kpi} />
          ))}
        </div>
      )}
    </div>
  )
}
