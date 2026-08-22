import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { BreakdownItem } from '../lib/types'

function BreakdownTooltip({ active, payload }: { active?: boolean; payload?: { payload: BreakdownItem }[] }) {
  if (!active || !payload?.length) return null
  const item = payload[0].payload
  return (
    <div className="rounded-lg border px-3 py-2 text-xs shadow-sm" style={{ background: 'var(--surface-raised)', borderColor: 'var(--border)' }}>
      <p className="font-semibold">{item.segment}</p>
      <p className="tabular mt-0.5">
        {item.prior_value.toLocaleString()} → {item.current_value.toLocaleString()} ({item.pct_change > 0 ? '+' : ''}
        {item.pct_change.toFixed(1)}%)
      </p>
      <p className="text-[var(--text-muted)] mt-0.5">Contributes {item.contribution_pct.toFixed(0)}% of total change</p>
    </div>
  )
}

export function BreakdownChart({ data }: { data: BreakdownItem[] }) {
  const sorted = [...data].sort((a, b) => Math.abs(b.contribution_pct) - Math.abs(a.contribution_pct))
  return (
    <ResponsiveContainer width="100%" height={Math.max(160, sorted.length * 42)}>
      <BarChart data={sorted} layout="vertical" margin={{ top: 4, right: 24, bottom: 4, left: 4 }} barCategoryGap={10}>
        <CartesianGrid stroke="var(--border)" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickLine={false} axisLine={{ stroke: 'var(--border-strong)' }} unit="%" />
        <YAxis type="category" dataKey="segment" tick={{ fontSize: 12, fill: 'var(--text-primary)' }} tickLine={false} axisLine={false} width={110} />
        <ReferenceLine x={0} stroke="var(--border-strong)" />
        <Tooltip content={<BreakdownTooltip />} cursor={{ fill: 'var(--brand-bg)' }} />
        <Bar dataKey="contribution_pct" radius={4} maxBarSize={22}>
          {sorted.map((entry) => (
            <Cell key={entry.segment} fill={entry.contribution_pct >= 0 ? 'var(--series-blue)' : 'var(--series-red)'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
