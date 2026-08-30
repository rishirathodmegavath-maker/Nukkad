from datetime import date
from typing import Literal

from pydantic import BaseModel

Status = Literal["normal", "watch", "critical", "recovered"]
Persona = Literal["executive", "analyst", "ops_manager"]


class TimeseriesPoint(BaseModel):
    date: date
    value: float
    is_anomaly: bool = False


class BreakdownItem(BaseModel):
    segment: str
    dimension: str  # e.g. "channel", "region", "cohort"
    prior_value: float
    current_value: float
    pct_change: float
    contribution_pct: float  # share of the TOTAL metric change explained by this segment


class InteractionEffect(BaseModel):
    """Ranked two-dimensional segment interaction (for example channel x device)."""

    dimensions: list[str]
    segments: list[str]
    contribution_pct: float
    pct_change: float
    sample_size: int


class EvidenceItem(BaseModel):
    source: str  # e.g. "CRM note", "Support tickets", "Marketing calendar"
    text: str
    relevance: Literal["supporting", "contextual"]
    document_id: str | None = None
    retrieval_score: float | None = None
    freshness: str | None = None
    lineage: str | None = None


class KPISummary(BaseModel):
    id: str
    name: str
    unit: str
    category: str
    current_value: float
    prior_value: float
    pct_change: float
    status: Status
    sparkline: list[float]
    source_system: str  # simulated upstream system(s) this KPI is reconciled from
    refresh_cadence: str  # e.g. "real-time (streaming)", "hourly batch", "daily batch", "weekly batch"
    access_roles: list[str]  # roles entitled to view this KPI (row/domain-level access control)
    owner: str  # accountable owner for this KPI — the decision-rights anchor


class KPIDetail(KPISummary):
    timeseries: list[TimeseriesPoint]
    breakdown: list[BreakdownItem]
    evidence: list[EvidenceItem]
    data_completeness: float  # 0-1, drives confidence
    dimension_label: str
    definition: str  # plain-language KPI definition (semantic contract)
    calculation: str  # calculation / SQL-ish lineage description
    lineage: str  # source-to-metric data lineage
    known_drivers: list[str] = []  # simulated known/likely contributing factors, for multi-factor scenarios
    cohort_benchmark: str | None = None  # comparable-cohort baseline, for sparse-history KPIs
    interaction_effects: list[InteractionEffect] = []
    business_impact_per_unit_usd: float = 0.0
    business_impact_basis: str = ""
    redacted_fields: list[str] = []


class KPIContract(BaseModel):
    """Lightweight KPI / semantic contract: definition, calculation, drivers,
    thresholds, lineage and access restrictions — governed metadata a BI
    platform would keep so every downstream consumer agrees on what the
    number means."""

    kpi_id: str
    name: str
    unit: str
    definition: str
    calculation: str
    dimension_label: str
    drivers: list[str]
    thresholds: dict[str, str]
    source_system: str
    refresh_cadence: str
    lineage: str
    access_roles: list[str]
    owner: str
    history_days: int
    business_impact_per_unit_usd: float
    business_impact_basis: str
    field_access: dict[str, list[str]]
    redacted_fields: list[str] = []


class ProcessingStep(BaseModel):
    step: str
    method: str  # "deterministic" | "llm" | "retrieval"
    detail: str


class Materiality(BaseModel):
    """Materiality = statistical significance blended with estimated $ business
    impact, not statistical significance alone — a movement can be
    statistically loud but financially small, or vice versa."""

    score: float  # 0-1
    statistical_component: float  # 0-1
    business_impact_component: float  # 0-1
    estimated_impact: str  # human-readable $ or magnitude estimate
    reasoning: str


class DecisionAuthority(BaseModel):
    """Decision rights: does the *viewing* role actually own this KPI's
    domain (can authorize the recommended actions), or are they read/
    diagnostic-only and must escalate to the owner?"""

    role: str
    owner: str
    can_authorize: bool
    note: str


class ActionItem(BaseModel):
    """One recommended action, structured as the Round 2 brief specifies:
    driver -> controllable lever -> action -> owner -> confidence ->
    monitoring plan. Not just a sentence — a governed, auditable unit."""

    driver: str
    lever: str
    action: str
    owner: str
    confidence: float
    monitoring_plan: str


class FeedbackSignal(BaseModel):
    """What past human feedback on this KPI says, and whether it actually
    moved this run's confidence score (see score_confidence's
    recalibration_flag) — the loop is real, not just captured-and-ignored."""

    sample_size: int
    useful_rate: float | None
    recalibration_flag: bool
    note: str


class Telemetry(BaseModel):
    model_config = {"protected_namespaces": ()}

    total_latency_ms: float
    llm_latency_ms: float
    model_calls: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    llm_error: str | None = None  # e.g. "no_api_key_configured", "timeout", "http_529", "call_failed"


class AnalysisResult(BaseModel):
    kpi_id: str
    generated_at: str
    persona: Persona
    what_changed: str
    likely_cause: str
    evidence: list[EvidenceItem]
    contributing_factors: list[BreakdownItem]
    interaction_effects: list[InteractionEffect]
    known_drivers: list[str]
    significance: Literal["noise", "meaningful", "severe"]
    confidence: float  # 0-1
    confidence_reasoning: str
    is_ambiguous: bool
    recommended_actions: list[ActionItem]
    materiality: Materiality
    decision_authority: DecisionAuthority
    expected_value: float  # simple trend-line forecast baseline ("what we'd expect")
    expected_deviation_pct: float  # actual vs. expected_value, distinct from vs.-prior-period pct_change
    cohort_benchmark: str | None = None
    feedback_signal: FeedbackSignal
    narrative: str
    narrative_source: Literal["llm", "template"]
    processing_steps: list[ProcessingStep]
    telemetry: Telemetry


class AuditLogEntry(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}

    id: int
    timestamp: str
    kpi_id: str
    kpi_name: str
    action: str
    persona: str
    role: str
    confidence: float
    narrative_source: str
    total_latency_ms: float
    model_calls: int
    estimated_cost_usd: float
    summary: str


class FeedbackCreate(BaseModel):
    kpi_id: str
    persona: Persona = "executive"
    useful: bool
    comment: str | None = None


class FeedbackEntry(BaseModel):
    id: int
    timestamp: str
    kpi_id: str
    persona: str
    useful: bool
    comment: str | None

    class Config:
        from_attributes = True


class FeedbackSummary(BaseModel):
    """Aggregated feedback for one KPI. Also consumed live: analyze_kpi
    queries this same aggregate and passes a recalibration flag into
    score_confidence, so an unfavorable feedback trend actually trims the
    next run's confidence — see FeedbackSignal on AnalysisResult."""

    kpi_id: str
    total_feedback: int
    useful_count: int
    not_useful_count: int
    useful_rate: float | None
    note: str
