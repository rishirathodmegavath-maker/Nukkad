import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..analysis.actions import recommend_actions
from ..analysis.confidence import score_confidence
from ..analysis.narrative import generate_narrative
from ..analysis.root_cause import find_primary_driver
from ..analysis.stats_engine import classify_significance
from ..data_generator import KPI_STORE
from ..database import get_db
from ..models import AuditLog
from ..schemas import AnalysisResult, Persona, ProcessingStep, Telemetry

router = APIRouter(prefix="/api/kpis", tags=["analysis"])

VALID_PERSONAS = {"executive", "analyst", "ops_manager"}


@router.post("/{kpi_id}/analyze", response_model=AnalysisResult)
def analyze_kpi(kpi_id: str, persona: Persona = "executive", role: str = "global_exec", db: Session = Depends(get_db)):
    request_start = time.perf_counter()

    kpi = KPI_STORE.get(kpi_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    if role not in kpi.access_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role}' is not entitled to view '{kpi.name}' (row/domain-level access control).",
        )
    if persona not in VALID_PERSONAS:
        raise HTTPException(status_code=400, detail=f"Unknown persona '{persona}'")

    values = [p.value for p in kpi.timeseries]
    history_days = len(values)
    significance, pct_change, _trend = classify_significance(values)

    primary_driver = find_primary_driver(kpi.breakdown)
    is_ambiguous = primary_driver is None

    confidence, confidence_reasoning = score_confidence(
        significance=significance,
        data_completeness=kpi.data_completeness,
        has_primary_driver=not is_ambiguous,
        top_contribution_pct=primary_driver.contribution_pct if primary_driver else 0.0,
        evidence_count=len(kpi.evidence),
        history_days=history_days,
    )

    recommended_actions = recommend_actions(
        status=kpi.status,
        is_ambiguous=is_ambiguous,
        dimension=kpi.dimension_label,
        driver_segment=primary_driver.segment if primary_driver else None,
    )

    narrative, narrative_source, llm_telemetry = generate_narrative(
        kpi=kpi,
        persona=persona,
        significance=significance,
        pct_change=pct_change,
        primary_driver=primary_driver,
        breakdown=kpi.breakdown,
        evidence=kpi.evidence,
        confidence=confidence,
        confidence_reasoning=confidence_reasoning,
        recommended_actions=recommended_actions,
    )

    what_changed = (
        f"{kpi.name} moved {pct_change:+.1f}% "
        f"({kpi.prior_value:.2f} → {kpi.current_value:.2f} {kpi.unit})"
    )
    likely_cause = (
        f"{primary_driver.segment} ({primary_driver.dimension})"
        if primary_driver
        else f"No dominant {kpi.dimension_label} segment — broad-based movement"
    )

    processing_steps = [
        ProcessingStep(
            step="Anomaly & trend detection",
            method="deterministic",
            detail="Rolling z-score (window=14, threshold=2.5) + medium-term trend comparison — numpy",
        ),
        ProcessingStep(
            step="Root-cause attribution",
            method="deterministic",
            detail="Contribution-share ranking across breakdown segments (rule-based dominance test: >=50% share and >=1.6x runner-up)",
        ),
        ProcessingStep(
            step="Evidence retrieval",
            method="retrieval",
            detail="Lookup against curated evidence store (simulated CRM/support/ops corpus)",
        ),
        ProcessingStep(
            step="Confidence scoring",
            method="deterministic",
            detail="Weighted formula: significance + data completeness + attribution clarity + evidence count + history sufficiency",
        ),
        ProcessingStep(
            step="Recommended actions",
            method="deterministic",
            detail="Rules playbook keyed by status/ambiguity — not left to the LLM",
        ),
        ProcessingStep(
            step="Narrative phrasing",
            method=narrative_source,
            detail=(
                f"Anthropic {os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-5')}, persona-tuned prompt"
                if narrative_source == "llm"
                else "Deterministic persona-specific sentence template (LLM unavailable, not configured, or timed out)"
            ),
        ),
    ]

    total_latency_ms = round((time.perf_counter() - request_start) * 1000, 1)
    telemetry = Telemetry(
        total_latency_ms=total_latency_ms,
        llm_latency_ms=llm_telemetry["llm_latency_ms"],
        model_calls=llm_telemetry["model_calls"],
        input_tokens=llm_telemetry["input_tokens"],
        output_tokens=llm_telemetry["output_tokens"],
        estimated_cost_usd=llm_telemetry["estimated_cost_usd"],
    )

    result = AnalysisResult(
        kpi_id=kpi.id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        persona=persona,
        what_changed=what_changed,
        likely_cause=likely_cause,
        evidence=kpi.evidence,
        contributing_factors=sorted(kpi.breakdown, key=lambda b: abs(b.contribution_pct), reverse=True),
        known_drivers=kpi.known_drivers,
        significance=significance,
        confidence=confidence,
        confidence_reasoning=confidence_reasoning,
        is_ambiguous=is_ambiguous,
        recommended_actions=recommended_actions,
        narrative=narrative,
        narrative_source=narrative_source,
        processing_steps=processing_steps,
        telemetry=telemetry,
    )

    log = AuditLog(
        kpi_id=kpi.id,
        kpi_name=kpi.name,
        action="analyze",
        persona=persona,
        role=role,
        confidence=confidence,
        narrative_source=narrative_source,
        total_latency_ms=total_latency_ms,
        model_calls=llm_telemetry["model_calls"],
        estimated_cost_usd=llm_telemetry["estimated_cost_usd"],
        summary=what_changed + " | " + likely_cause,
    )
    db.add(log)
    db.commit()

    return result
