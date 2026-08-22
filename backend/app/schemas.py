from datetime import date
from typing import Literal

from pydantic import BaseModel

Status = Literal["normal", "watch", "critical", "recovered"]


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


class EvidenceItem(BaseModel):
    source: str  # e.g. "CRM note", "Support tickets", "Marketing calendar"
    text: str
    relevance: Literal["supporting", "contextual"]


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


class KPIDetail(KPISummary):
    timeseries: list[TimeseriesPoint]
    breakdown: list[BreakdownItem]
    evidence: list[EvidenceItem]
    data_completeness: float  # 0-1, drives confidence
    dimension_label: str


class AnalysisResult(BaseModel):
    kpi_id: str
    generated_at: str
    what_changed: str
    likely_cause: str
    evidence: list[EvidenceItem]
    contributing_factors: list[BreakdownItem]
    significance: Literal["noise", "meaningful", "severe"]
    confidence: float  # 0-1
    confidence_reasoning: str
    is_ambiguous: bool
    recommended_actions: list[str]
    narrative: str
    narrative_source: Literal["llm", "template"]


class AuditLogEntry(BaseModel):
    id: int
    timestamp: str
    kpi_id: str
    kpi_name: str
    action: str
    confidence: float
    narrative_source: str
    summary: str

    class Config:
        from_attributes = True
