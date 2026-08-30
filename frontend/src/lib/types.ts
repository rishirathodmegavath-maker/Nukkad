export type Status = 'normal' | 'watch' | 'critical' | 'recovered'
export type Significance = 'noise' | 'meaningful' | 'severe'
export type Persona = 'executive' | 'analyst' | 'ops_manager'

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
  source_system: string
  refresh_cadence: string
  access_roles: string[]
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
  definition: string
  calculation: string
  lineage: string
  known_drivers: string[]
  owner: string
}

export interface KpiContract {
  kpi_id: string
  name: string
  unit: string
  definition: string
  calculation: string
  dimension_label: string
  drivers: string[]
  thresholds: Record<string, string>
  source_system: string
  refresh_cadence: string
  lineage: string
  access_roles: string[]
  owner: string
  history_days: number
}

export interface Materiality {
  score: number
  statistical_component: number
  business_impact_component: number
  estimated_impact: string
  reasoning: string
}

export interface DecisionAuthority {
  role: string
  owner: string
  can_authorize: boolean
  note: string
}

export interface ProcessingStep {
  step: string
  method: string
  detail: string
}

export interface Telemetry {
  total_latency_ms: number
  llm_latency_ms: number
  model_calls: number
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
}

export interface AnalysisResult {
  kpi_id: string
  generated_at: string
  persona: Persona
  what_changed: string
  likely_cause: string
  evidence: EvidenceItem[]
  contributing_factors: BreakdownItem[]
  known_drivers: string[]
  significance: Significance
  confidence: number
  confidence_reasoning: string
  is_ambiguous: boolean
  recommended_actions: string[]
  materiality: Materiality
  decision_authority: DecisionAuthority
  narrative: string
  narrative_source: 'llm' | 'template'
  processing_steps: ProcessingStep[]
  telemetry: Telemetry
}

export interface AuditLogEntry {
  id: number
  timestamp: string
  kpi_id: string
  kpi_name: string
  action: string
  persona: string
  role: string
  confidence: number
  narrative_source: string
  total_latency_ms: number
  model_calls: number
  estimated_cost_usd: number
  summary: string
}

export interface RoleOption {
  id: string
  label: string
}

export interface FeedbackEntry {
  id: number
  timestamp: string
  kpi_id: string
  persona: string
  useful: boolean
  comment: string | null
}
