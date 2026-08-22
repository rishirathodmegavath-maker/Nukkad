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
from ..schemas import AnalysisResult

router = APIRouter(prefix="/api/kpis", tags=["analysis"])


@router.post("/{kpi_id}/analyze", response_model=AnalysisResult)
def analyze_kpi(kpi_id: str, db: Session = Depends(get_db)):
    kpi = KPI_STORE.get(kpi_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")

    values = [p.value for p in kpi.timeseries]
    significance, pct_change, _trend = classify_significance(values)

    primary_driver = find_primary_driver(kpi.breakdown)
    is_ambiguous = primary_driver is None

    confidence, confidence_reasoning = score_confidence(
        significance=significance,
        data_completeness=kpi.data_completeness,
        has_primary_driver=not is_ambiguous,
        top_contribution_pct=primary_driver.contribution_pct if primary_driver else 0.0,
        evidence_count=len(kpi.evidence),
    )

    recommended_actions = recommend_actions(
        status=kpi.status,
        is_ambiguous=is_ambiguous,
        dimension=kpi.dimension_label,
        driver_segment=primary_driver.segment if primary_driver else None,
    )

    narrative, narrative_source = generate_narrative(
        kpi=kpi,
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

    result = AnalysisResult(
        kpi_id=kpi.id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        what_changed=what_changed,
        likely_cause=likely_cause,
        evidence=kpi.evidence,
        contributing_factors=sorted(kpi.breakdown, key=lambda b: abs(b.contribution_pct), reverse=True),
        significance=significance,
        confidence=confidence,
        confidence_reasoning=confidence_reasoning,
        is_ambiguous=is_ambiguous,
        recommended_actions=recommended_actions,
        narrative=narrative,
        narrative_source=narrative_source,
    )

    log = AuditLog(
        kpi_id=kpi.id,
        kpi_name=kpi.name,
        action="analyze",
        confidence=confidence,
        narrative_source=narrative_source,
        summary=what_changed + " | " + likely_cause,
    )
    db.add(log)
    db.commit()

    return result
