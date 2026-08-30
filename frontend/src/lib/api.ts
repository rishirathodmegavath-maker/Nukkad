import type {
  AnalysisResult,
  AuditLogEntry,
  FeedbackEntry,
  FeedbackSummary,
  KpiContract,
  KpiDetail,
  KpiSummary,
  Persona,
  RoleOption,
} from './types'

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
  listKpis: (role: string = 'global_exec') => request<KpiSummary[]>(`/api/kpis?role=${encodeURIComponent(role)}`),
  getKpi: (id: string, role: string = 'global_exec') =>
    request<KpiDetail>(`/api/kpis/${id}?role=${encodeURIComponent(role)}`),
  getKpiContract: (id: string, role: string = 'global_exec') =>
    request<KpiContract>(`/api/kpis/${id}/contract?role=${encodeURIComponent(role)}`),
  analyzeKpi: (id: string, persona: Persona = 'executive', role: string = 'global_exec') =>
    request<AnalysisResult>(
      `/api/kpis/${id}/analyze?persona=${encodeURIComponent(persona)}&role=${encodeURIComponent(role)}`,
      { method: 'POST' },
    ),
  getAuditLog: () => request<AuditLogEntry[]>('/api/audit-log'),
  listRoles: () => request<RoleOption[]>('/api/roles'),
  submitFeedback: (payload: { kpi_id: string; persona: Persona; useful: boolean; comment?: string }) =>
    request<FeedbackEntry>('/api/feedback', { method: 'POST', body: JSON.stringify(payload) }),
  getFeedbackSummary: (kpiId: string) =>
    request<FeedbackSummary>(`/api/feedback/summary?kpi_id=${encodeURIComponent(kpiId)}`),
  health: () => request<{ status: string }>('/api/health'),
}
