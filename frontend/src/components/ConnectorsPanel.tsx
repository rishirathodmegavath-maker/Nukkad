import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { ConnectorStatus } from '../lib/types'

function StateBadge({ state }: { state: string }) {
  const color = state === 'connected' ? 'var(--good)' : state === 'ready' ? 'var(--brand)' : 'var(--text-muted)'
  const bg = state === 'connected' ? 'var(--good-bg)' : state === 'ready' ? 'var(--brand-bg)' : 'var(--border)'
  return (
    <span className="text-[10px] rounded-full px-2 py-0.5 font-medium" style={{ color, background: bg }}>
      {state.replace('_', ' ')}
    </span>
  )
}

export function ConnectorsPanel() {
  const [connectors, setConnectors] = useState<ConnectorStatus[] | null>(null)
  const [testing, setTesting] = useState<string | null>(null)

  useEffect(() => {
    api.listConnectors().then(setConnectors).catch(() => setConnectors([]))
  }, [])

  const runTest = async (id: string) => {
    setTesting(id)
    try {
      const result = await api.testConnector(id)
      setConnectors((prev) => (prev ? prev.map((c) => (c.id === id ? result : c)) : prev))
    } catch {
      setConnectors((prev) =>
        prev ? prev.map((c) => (c.id === id ? { ...c, state: 'error', detail: 'Test failed — see backend logs.' } : c)) : prev,
      )
    } finally {
      setTesting(null)
    }
  }

  if (!connectors || connectors.length === 0) return null

  return (
    <div className="rounded-xl border p-4 mb-6" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
      <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-3">
        Data source connectors
      </p>
      <div className="grid sm:grid-cols-3 gap-3">
        {connectors.map((c) => (
          <div key={c.id} className="rounded-lg border p-3 text-xs" style={{ borderColor: 'var(--border)' }}>
            <div className="flex items-center justify-between mb-1">
              <span className="font-medium">{c.id.replace('_', ' ')}</span>
              <StateBadge state={c.state} />
            </div>
            <p className="text-[var(--text-muted)] mb-2">
              {c.kind} · {c.detail}
              {c.latency_ms != null && ` · ${c.latency_ms.toFixed(0)}ms`}
            </p>
            <button
              onClick={() => runTest(c.id)}
              disabled={!c.configured || testing === c.id}
              className="text-[10px] rounded-md border px-2 py-1 disabled:opacity-40"
              style={{ borderColor: 'var(--border)' }}
              title={c.configured ? 'Run a live connection probe' : 'Set the server-side credentials to enable this'}
            >
              {testing === c.id ? 'Testing…' : 'Test connection'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
