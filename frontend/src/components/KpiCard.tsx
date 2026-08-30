import { Link } from 'react-router-dom'
import type { KpiSummary } from '../lib/types'
import { StatusBadge, statusColor } from './StatusBadge'
import { Sparkline } from './Sparkline'

export function KpiCard({ kpi }: { kpi: KpiSummary }) {
  const positive = kpi.pct_change >= 0
  const arrow = positive ? '↑' : '↓'
  const deltaColor = kpi.status === 'critical' ? 'var(--critical)' : kpi.status === 'watch' ? 'var(--warning)' : kpi.status === 'recovered' ? 'var(--good)' : 'var(--text-secondary)'

  return (
    <Link
      to={`/kpi/${kpi.id}`}
      className="block rounded-xl border p-4 transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2"
      style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs text-[var(--text-muted)]">{kpi.category}</p>
          <h3 className="font-semibold text-sm mt-0.5">{kpi.name}</h3>
        </div>
        <StatusBadge status={kpi.status} />
      </div>

      <div className="mt-3 flex items-end justify-between">
        <div>
          <p className="text-2xl font-semibold tabular tracking-tight">
            {kpi.current_value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            <span className="text-sm text-[var(--text-muted)] ml-1">{kpi.unit}</span>
          </p>
          <p className="text-xs mt-1 tabular font-medium" style={{ color: deltaColor }}>
            {arrow} {Math.abs(kpi.pct_change).toFixed(1)}% vs prior period
          </p>
        </div>
        <div className="w-24">
          <Sparkline data={kpi.sparkline} color={statusColor(kpi.status)} />
        </div>
      </div>

      <p className="text-[10px] text-[var(--text-muted)] mt-3 truncate" title={`${kpi.source_system} · ${kpi.refresh_cadence}`}>
        {kpi.source_system} · {kpi.refresh_cadence}
      </p>
    </Link>
  )
}
