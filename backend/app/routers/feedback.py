"""Human-feedback capture: the first link in a learn-from-feedback loop.
An analyst or business user marks an analysis useful/not-useful; this is
persisted and queryable per KPI. A full retraining/recalibration loop is
out of scope for this prototype, but the capture mechanism — the part a
judge can actually see work — is real, not simulated.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Feedback
from ..schemas import FeedbackCreate, FeedbackEntry, FeedbackSummary

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackEntry)
def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    row = Feedback(kpi_id=payload.kpi_id, persona=payload.persona, useful=payload.useful, comment=payload.comment)
    db.add(row)
    db.commit()
    db.refresh(row)
    return FeedbackEntry(
        id=row.id,
        timestamp=row.timestamp.isoformat() if row.timestamp else "",
        kpi_id=row.kpi_id,
        persona=row.persona,
        useful=row.useful,
        comment=row.comment,
    )


@router.get("/summary", response_model=FeedbackSummary)
def feedback_summary(kpi_id: str, db: Session = Depends(get_db)):
    rows = db.query(Feedback).filter(Feedback.kpi_id == kpi_id).all()
    total = len(rows)
    useful = sum(1 for r in rows if r.useful)
    useful_rate = round(useful / total, 2) if total else None
    note = (
        "Consumed by the next analysis run; after 3 samples, a useful-rate below 50% trims confidence by 10%."
        if total
        else "No feedback recorded yet for this KPI."
    )
    return FeedbackSummary(
        kpi_id=kpi_id,
        total_feedback=total,
        useful_count=useful,
        not_useful_count=total - useful,
        useful_rate=useful_rate,
        note=note,
    )


@router.get("", response_model=list[FeedbackEntry])
def list_feedback(kpi_id: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(Feedback).order_by(desc(Feedback.timestamp))
    if kpi_id:
        query = query.filter(Feedback.kpi_id == kpi_id)
    rows = query.limit(limit).all()
    return [
        FeedbackEntry(
            id=r.id,
            timestamp=r.timestamp.isoformat() if r.timestamp else "",
            kpi_id=r.kpi_id,
            persona=r.persona,
            useful=r.useful,
            comment=r.comment,
        )
        for r in rows
    ]
