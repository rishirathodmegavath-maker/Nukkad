import type { Status } from '../lib/types'

const STATUS_CONFIG: Record<Status, { label: string; color: string; bg: string; icon: string }> = {
  critical: { label: 'Critical', color: 'var(--critical)', bg: 'var(--critical-bg)', icon: '▲' },
  watch: { label: 'Watch', color: 'var(--warning)', bg: 'var(--warning-bg)', icon: '●' },
  recovered: { label: 'Recovered', color: 'var(--good)', bg: 'var(--good-bg)', icon: '✓' },
  normal: { label: 'Normal', color: 'var(--text-secondary)', bg: 'var(--border)', icon: '–' },
}

export function StatusBadge({ status }: { status: Status }) {
  const cfg = STATUS_CONFIG[status]
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{ color: cfg.color, background: cfg.bg }}
    >
      <span aria-hidden="true">{cfg.icon}</span>
      {cfg.label}
    </span>
  )
}

export function statusColor(status: Status): string {
  return STATUS_CONFIG[status].color
}
