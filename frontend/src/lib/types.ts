export type Status = 'normal' | 'watch' | 'critical' | 'recovered'
export type Significance = 'noise' | 'meaningful' | 'severe'

export interface KpiSummary {
  id: string
  name: string
  unit: string
  category: string
  current_value: number
  prior_value: number
  pct_change: number
  status: Status
  sparkline: number[]
}

export interface TimeseriesPoint {
  date: string
  value: number
  is_anomaly: boolean
}

export interface BreakdownItem {
  segment: string
  dimension: string
  prior_value: number
  current_value: number
  pct_change: number
  contribution_pct: number
}

export interface EvidenceItem {
  source: string
  text: string
  relevance: 'supporting' | 'contextual'
}

export interface KpiDetail extends KpiSummary {
  timeseries: TimeseriesPoint[]
  breakdown: BreakdownItem[]
  evidence: EvidenceItem[]
  data_completeness: number
  dimension_label: string
}

export interface AnalysisResult {
  kpi_id: string
  generated_at: string
  what_changed: string
  likely_cause: string
  evidence: EvidenceItem[]
  contributing_factors: BreakdownItem[]
  significance: Significance
  confidence: number
  confidence_reasoning: string
  is_ambiguous: boolean
  recommended_actions: string[]
  narrative: string
  narrative_source: 'llm' | 'template'
}

export interface AuditLogEntry {
  id: number
  timestamp: string
  kpi_id: string
  kpi_name: string
  action: string
  confidence: number
  narrative_source: string
  summary: string
}
