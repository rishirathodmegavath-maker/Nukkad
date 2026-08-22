import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TimeseriesPoint } from '../lib/types'

function AnomalyDot(props: { cx?: number; cy?: number; payload?: TimeseriesPoint }) {
  const { cx, cy, payload } = props
  if (!payload?.is_anomaly || cx === undefined || cy === undefined) return null
  return (
    <circle cx={cx} cy={cy} r={4.5} fill="var(--surface)" stroke="var(--critical)" strokeWidth={2} />
  )
}

function ChartTooltip({ active, payload, unit }: { active?: boolean; payload?: { payload: TimeseriesPoint }[]; unit: string }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs shadow-sm"
      style={{ background: 'var(--surface-raised)', borderColor: 'var(--border)' }}
    >
      <p className="text-[var(--text-muted)]">{point.date}</p>
      <p className="font-semibold tabular mt-0.5">
        {point.value.toLocaleString(undefined, { maximumFractionDigits: 2 })} {unit}
      </p>
      {point.is_anomaly && (
        <p className="mt-1 font-medium" style={{ color: 'var(--critical)' }}>
          ▲ Flagged anomaly
        </p>
      )}
    </div>
  )
}

export function TimeseriesChart({ data, unit, color }: { data: TimeseriesPoint[]; unit: string; color: string }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          tickLine={false}
          axisLine={{ stroke: 'var(--border-strong)' }}
          interval={13}
        />
        <YAxis
          tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
          tickLine={false}
          axisLine={false}
          width={48}
          domain={['auto', 'auto']}
        />
        <Tooltip content={<ChartTooltip unit={unit} />} />
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={<AnomalyDot />}
          activeDot={{ r: 5 }}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
