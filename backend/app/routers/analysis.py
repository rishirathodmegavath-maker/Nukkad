import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..analysis.actions import check_decision_authority, recommend_actions
from ..analysis.confidence import score_confidence
from ..analysis.evidence_retrieval import INDEX
from ..analysis.materiality import score_materiality
from ..analysis.narrative import generate_narrative
from ..analysis.root_cause import find_primary_driver
from ..analysis.stats_engine import classify_significance, expected_value
from ..data_generator import KPI_STORE
from ..database import get_db
from ..models import AuditLog, Feedback
from ..schemas import AnalysisResult, DecisionAuthority, FeedbackSignal, Materiality, Persona, ProcessingStep, Telemetry
from ..security import secure_evidence
from ..security import secure_kpi

router = APIRouter(prefix="/api/kpis", tags=["analysis"])

VALID_PERSONAS = {"executive", "analyst", "ops_manager"}
RECALIBRATION_MIN_SAMPLES = 3
RECALIBRATION_USEFUL_THRESHOLD = 0.5


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
    interactions = sorted(kpi.interaction_effects, key=lambda item: abs(item.contribution_pct), reverse=True)
    query = " ".join([kpi.name, kpi.category, *kpi.known_drivers, *(item.segment for item in kpi.breakdown)])
    retrieved_evidence = INDEX.search(query, limit=2) or kpi.evidence
    evidence, _redacted = secure_evidence(retrieved_evidence, role)

    feedback_rows = db.query(Feedback).filter(Feedback.kpi_id == kpi_id).all()
    fb_total = len(feedback_rows)
    fb_useful = sum(1 for r in feedback_rows if r.useful)
    fb_rate = round(fb_useful / fb_total, 2) if fb_total else None
    recalibration_flag = bool(
        fb_total >= RECALIBRATION_MIN_SAMPLES and fb_rate is not None and fb_rate < RECALIBRATION_USEFUL_THRESHOLD
    )
    if fb_total == 0:
        fb_note = "No prior feedback recorded for this KPI yet."
    elif recalibration_flag:
        fb_note = (
            f"{fb_useful}/{fb_total} past analyses on this KPI were marked useful ({fb_rate * 100:.0f}%) — "
            "below the recalibration threshold, so confidence for this run was trimmed."
        )
    else:
        fb_note = f"{fb_useful}/{fb_total} past analyses on this KPI were marked useful ({fb_rate * 100:.0f}%)."
    feedback_signal = FeedbackSignal(
        sample_size=fb_total, useful_rate=fb_rate, recalibration_flag=recalibration_flag, note=fb_note
    )

    confidence, confidence_reasoning = score_confidence(
        significance=significance,
        data_completeness=kpi.data_completeness,
        has_primary_driver=not is_ambiguous,
        top_contribution_pct=primary_driver.contribution_pct if primary_driver else 0.0,
        evidence_count=len(evidence),
        history_days=history_days,
        refresh_cadence=kpi.refresh_cadence,
        recalibration_flag=recalibration_flag,
    )

    expected = expected_value(values)
    expected_deviation_pct = ((kpi.current_value - expected) / expected * 100) if expected else 0.0

    recommended_actions = recommend_actions(
        status=kpi.status,
        is_ambiguous=is_ambiguous,
        dimension=kpi.dimension_label,
        driver_segment=primary_driver.segment if primary_driver else None,
        owner=kpi.owner,
        confidence=confidence,
    )

    mat_score, mat_stat, mat_impact, mat_estimate, mat_reasoning = score_materiality(
        significance=significance,
        pct_change=pct_change,
        current_value=kpi.current_value,
        prior_value=kpi.prior_value,
        unit=kpi.unit,
        business_impact_per_unit_usd=kpi.business_impact_per_unit_usd,
        business_impact_basis=kpi.business_impact_basis,
    )
    materiality = Materiality(
        score=mat_score,
        statistical_component=mat_stat,
        business_impact_component=mat_impact,
        estimated_impact=mat_estimate,
        reasoning=mat_reasoning,
    )

    can_authorize, authority_note = check_decision_authority(role=role, owner=kpi.owner, access_roles=kpi.access_roles)
    decision_authority = DecisionAuthority(role=role, owner=kpi.owner, can_authorize=can_authorize, note=authority_note)

    narrative, narrative_source, llm_telemetry = generate_narrative(
        kpi=kpi,
        persona=persona,
        significance=significance,
        pct_change=pct_change,
        primary_driver=primary_driver,
        breakdown=kpi.breakdown,
        evidence=evidence,
        confidence=confidence,
        confidence_reasoning=confidence_reasoning,
        recommended_actions=recommended_actions,
    )

    what_changed = (
        f"{kpi.name} moved {pct_change:+.1f}% "
        f"({kpi.prior_value:.2f} → {kpi.current_value:.2f} {kpi.unit})"
    )
    likely_cause = (
        f"{interactions[0].segments[0]} x {interactions[0].segments[1]} ({interactions[0].contribution_pct:.0f}% interaction contribution)"
        if interactions
        else f"{primary_driver.segment} ({primary_driver.dimension})"
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
            detail="Contribution-share ranking plus two-dimensional interaction-effect ranking (for example traffic source x device)",
        ),
        ProcessingStep(
            step="Evidence retrieval",
            method="retrieval",
            detail="TF-IDF cosine vector retrieval over an indexed evidence corpus with document ID, freshness, score and lineage",
        ),
        ProcessingStep(
            step="Confidence scoring",
            method="deterministic",
            detail="Weighted formula: significance + data completeness + attribution clarity + evidence count + history sufficiency",
        ),
        ProcessingStep(
            step="Recommended actions",
            method="deterministic",
            detail="Rules playbook keyed by status/ambiguity, structured as driver -> lever -> action -> owner -> monitoring plan — not left to the LLM",
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
        llm_error=llm_telemetry["llm_error"],
    )

    result = AnalysisResult(
        kpi_id=kpi.id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        persona=persona,
        what_changed=what_changed,
        likely_cause=likely_cause,
        evidence=evidence,
        contributing_factors=sorted(kpi.breakdown, key=lambda b: abs(b.contribution_pct), reverse=True),
        interaction_effects=interactions,
        known_drivers=kpi.known_drivers,
        significance=significance,
        confidence=confidence,
        confidence_reasoning=confidence_reasoning,
        is_ambiguous=is_ambiguous,
        recommended_actions=recommended_actions,
        materiality=materiality,
        decision_authority=decision_authority,
        expected_value=round(expected, 2),
        expected_deviation_pct=round(expected_deviation_pct, 2),
        cohort_benchmark=kpi.cohort_benchmark,
        feedback_signal=feedback_signal,
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
