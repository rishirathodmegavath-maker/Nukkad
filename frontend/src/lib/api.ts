import type { AnalysisResult, AuditLogEntry, KpiDetail, KpiSummary } from './types'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`)
  }
  return res.json()
}

export const api = {
  listKpis: () => request<KpiSummary[]>('/api/kpis'),
  getKpi: (id: string) => request<KpiDetail>(`/api/kpis/${id}`),
  analyzeKpi: (id: string) => request<AnalysisResult>(`/api/kpis/${id}/analyze`, { method: 'POST' }),
  getAuditLog: () => request<AuditLogEntry[]>('/api/audit-log'),
  health: () => request<{ status: string }>('/api/health'),
}
