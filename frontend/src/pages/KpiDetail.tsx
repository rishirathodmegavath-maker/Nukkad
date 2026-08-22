import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import type { KpiDetail as KpiDetailType } from '../lib/types'
import { StatusBadge, statusColor } from '../components/StatusBadge'
import { TimeseriesChart } from '../components/TimeseriesChart'
import { AnalysisPanel } from '../components/AnalysisPanel'

export function KpiDetail() {
  const { id } = useParams<{ id: string }>()
  const [kpi, setKpi] = useState<KpiDetailType | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setKpi(null)
    api
      .getKpi(id)
      .then(setKpi)
      .catch((e) => setError(e.message))
  }, [id])

  if (error) {
    return (
      <div className="text-sm" style={{ color: 'var(--critical)' }}>
        {error}
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
              <p className="text-xs text-[var(--text-muted)]">Last 90 days · daily</p>
            </div>
            <TimeseriesChart data={kpi.timeseries} unit={kpi.unit} color={statusColor(kpi.status)} />
            <p className="text-xs text-[var(--text-muted)] mt-2">
              Circled points are flagged by the rolling z-score anomaly detector (window = 14 days, threshold = 2.5σ).
            </p>
          </div>

          <div className="rounded-xl border p-5 text-xs text-[var(--text-secondary)] flex items-center justify-between" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
            <span>Data completeness for this metric</span>
            <span className="font-semibold tabular text-[var(--text-primary)]">{Math.round(kpi.data_completeness * 100)}%</span>
          </div>
        </div>

        <div>
          <AnalysisPanel kpi={kpi} />
        </div>
      </div>
    </div>
  )
}
