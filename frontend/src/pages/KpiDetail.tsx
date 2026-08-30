import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import type { KpiContract, KpiDetail as KpiDetailType } from '../lib/types'
import { StatusBadge, statusColor } from '../components/StatusBadge'
import { TimeseriesChart } from '../components/TimeseriesChart'
import { AnalysisPanel } from '../components/AnalysisPanel'
import { useRole } from '../lib/roleContext'

function ContractViewer({ kpiId, role }: { kpiId: string; role: string }) {
  const [open, setOpen] = useState(false)
  const [contract, setContract] = useState<KpiContract | null>(null)
  const [error, setError] = useState<string | null>(null)

  const toggle = () => {
    if (!open && !contract && !error) {
      api.getKpiContract(kpiId, role).then(setContract).catch((e) => setError(e.message))
    }
    setOpen((v) => !v)
  }

  return (
    <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
      <button onClick={toggle} className="w-full flex items-center justify-between text-left">
        <span className="text-sm font-semibold">KPI / semantic contract</span>
        <span className="text-xs text-[var(--text-muted)]">{open ? 'Hide' : 'View definition, lineage & access'}</span>
      </button>
      {open && error && <p className="text-xs mt-3" style={{ color: 'var(--critical)' }}>{error}</p>}
      {open && contract && (
        <dl className="mt-4 space-y-3 text-xs">
          <div>
            <dt className="text-[var(--text-muted)] uppercase tracking-wide mb-0.5">Definition</dt>
            <dd className="text-[var(--text-secondary)]">{contract.definition}</dd>
          </div>
          <div>
            <dt className="text-[var(--text-muted)] uppercase tracking-wide mb-0.5">Calculation</dt>
            <dd className="text-[var(--text-secondary)] font-mono">{contract.calculation}</dd>
          </div>
          <div>
            <dt className="text-[var(--text-muted)] uppercase tracking-wide mb-0.5">Lineage</dt>
            <dd className="text-[var(--text-secondary)] font-mono">{contract.lineage}</dd>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <dt className="text-[var(--text-muted)] uppercase tracking-wide mb-0.5">Source system</dt>
              <dd className="text-[var(--text-secondary)]">{contract.source_system}</dd>
            </div>
            <div>
              <dt className="text-[var(--text-muted)] uppercase tracking-wide mb-0.5">Refresh cadence</dt>
              <dd className="text-[var(--text-secondary)]">{contract.refresh_cadence}</dd>
            </div>
          </div>
          <div>
            <dt className="text-[var(--text-muted)] uppercase tracking-wide mb-0.5">Drivers ({contract.dimension_label})</dt>
            <dd className="text-[var(--text-secondary)]">{contract.drivers.join(', ')}</dd>
          </div>
          <div>
            <dt className="text-[var(--text-muted)] uppercase tracking-wide mb-1">Materiality thresholds</dt>
            <dd className="space-y-1">
              {Object.entries(contract.thresholds).map(([k, v]) => (
                <p key={k} className="text-[var(--text-secondary)]">
                  <span className="font-medium text-[var(--text-primary)]">{k}:</span> {v}
                </p>
              ))}
            </dd>
          </div>
          <div>
            <dt className="text-[var(--text-muted)] uppercase tracking-wide mb-0.5">Access restrictions</dt>
            <dd className="text-[var(--text-secondary)]">{contract.access_roles.join(', ')}</dd>
          </div>
          <div>
            <dt className="text-[var(--text-muted)] uppercase tracking-wide mb-0.5">History available</dt>
            <dd className="text-[var(--text-secondary)]">{contract.history_days} day(s)</dd>
          </div>
        </dl>
      )}
    </div>
  )
}

export function KpiDetail() {
  const { id } = useParams<{ id: string }>()
  const { role } = useRole()
  const [kpi, setKpi] = useState<KpiDetailType | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setKpi(null)
    setError(null)
    api
      .getKpi(id, role)
      .then(setKpi)
      .catch((e) => setError(e.message))
  }, [id, role])

  if (error) {
    return (
      <div>
        <Link to="/" className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
          ← Back to dashboard
        </Link>
        <div className="mt-4 rounded-lg border p-4 text-sm" style={{ borderColor: 'var(--critical)', background: 'var(--critical-bg)', color: 'var(--critical)' }}>
          {error}
        </div>
      </div>
    )
  }

  if (!kpi) {
    return <div className="h-64 rounded-xl border animate-pulse" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }} />
  }

  const positive = kpi.pct_change >= 0

  return (
    <div>
      <Link to="/" className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]">
        ← Back to dashboard
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3 mt-2 mb-6">
        <div>
          <p className="text-xs text-[var(--text-muted)]">{kpi.category}</p>
          <h1 className="text-2xl font-semibold tracking-tight">{kpi.name}</h1>
        </div>
        <StatusBadge status={kpi.status} />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
            <div className="flex items-end justify-between mb-4">
              <div>
                <p className="text-3xl font-semibold tabular tracking-tight">
                  {kpi.current_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  <span className="text-base text-[var(--text-muted)] ml-1.5">{kpi.unit}</span>
                </p>
                <p className="text-sm mt-1" style={{ color: positive ? 'var(--good)' : 'var(--critical)' }}>
                  {positive ? '↑' : '↓'} {Math.abs(kpi.pct_change).toFixed(1)}% vs prior period ({kpi.prior_value.toLocaleString()} {kpi.unit})
                </p>
              </div>
              <p className="text-xs text-[var(--text-muted)]">Last {kpi.timeseries.length} days · daily</p>
            </div>
            <TimeseriesChart data={kpi.timeseries} unit={kpi.unit} color={statusColor(kpi.status)} />
            <p className="text-xs text-[var(--text-muted)] mt-2">
              Circled points are flagged by the rolling z-score anomaly detector (window = 14 days, threshold = 2.5σ).
            </p>
          </div>

          {kpi.known_drivers.length > 0 && (
            <div className="rounded-xl border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
              <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">
                Known / simulated contributing factors
              </p>
              <ul className="space-y-1 text-sm">
                {kpi.known_drivers.map((d, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="mt-0.5 text-[var(--brand)]">•</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="rounded-xl border p-5 text-xs text-[var(--text-secondary)] flex items-center justify-between" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
            <span>Data completeness for this metric</span>
            <span className="font-semibold tabular text-[var(--text-primary)]">{Math.round(kpi.data_completeness * 100)}%</span>
          </div>

          <ContractViewer kpiId={kpi.id} role={role} />
        </div>

        <div>
          <AnalysisPanel kpi={kpi} role={role} />
        </div>
      </div>
    </div>
  )
}
