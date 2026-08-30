import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { AuditLogEntry } from '../lib/types'

export function AuditLog() {
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getAuditLog()
      .then(setEntries)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight mb-1">Audit Log</h1>
      <p className="text-sm text-[var(--text-secondary)] mb-6 max-w-2xl">
        Every AI analysis is logged for auditability — what was asked, what was concluded, how confident the
        system was, and whether the narrative came from the LLM or the deterministic fallback template.
      </p>

      {error && (
        <div className="rounded-lg border p-4 text-sm" style={{ borderColor: 'var(--critical)', background: 'var(--critical-bg)', color: 'var(--critical)' }}>
          {error}
        </div>
      )}

      {!entries && !error && <div className="h-40 rounded-xl border animate-pulse" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }} />}

      {entries && entries.length === 0 && (
        <div className="rounded-xl border p-8 text-center text-sm text-[var(--text-muted)]" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
          No analyses run yet. Open a KPI and click "Explain this KPI" to generate the first audit entry.
        </div>
      )}

      {entries && entries.length > 0 && (
        <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-[var(--text-muted)] uppercase tracking-wide border-b" style={{ borderColor: 'var(--border)' }}>
                <th className="px-4 py-2.5 font-medium">Time</th>
                <th className="px-4 py-2.5 font-medium">KPI</th>
                <th className="px-4 py-2.5 font-medium">Summary</th>
                <th className="px-4 py-2.5 font-medium">Persona</th>
                <th className="px-4 py-2.5 font-medium">Role</th>
                <th className="px-4 py-2.5 font-medium">Confidence</th>
                <th className="px-4 py-2.5 font-medium">Source</th>
                <th className="px-4 py-2.5 font-medium">Latency</th>
                <th className="px-4 py-2.5 font-medium">Est. cost</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                  <td className="px-4 py-3 text-xs text-[var(--text-muted)] whitespace-nowrap tabular">
                    {new Date(e.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-medium whitespace-nowrap">{e.kpi_name}</td>
                  <td className="px-4 py-3 text-[var(--text-secondary)]">{e.summary}</td>
                  <td className="px-4 py-3 text-xs text-[var(--text-secondary)] whitespace-nowrap">{e.persona}</td>
                  <td className="px-4 py-3 text-xs text-[var(--text-secondary)] whitespace-nowrap">{e.role}</td>
                  <td className="px-4 py-3 tabular">{Math.round(e.confidence * 100)}%</td>
                  <td className="px-4 py-3">
                    <span
                      className="text-xs rounded-full px-2 py-0.5 font-medium"
                      style={{
                        color: e.narrative_source === 'llm' ? 'var(--brand)' : 'var(--text-secondary)',
                        background: e.narrative_source === 'llm' ? 'var(--brand-bg)' : 'var(--border)',
                      }}
                    >
                      {e.narrative_source}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs tabular text-[var(--text-muted)] whitespace-nowrap">{e.total_latency_ms.toFixed(1)}ms</td>
                  <td className="px-4 py-3 text-xs tabular text-[var(--text-muted)] whitespace-nowrap">
                    {e.model_calls > 0 ? `$${e.estimated_cost_usd.toFixed(6)}` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
