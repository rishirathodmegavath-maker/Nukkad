from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog
from ..schemas import AuditLogEntry

router = APIRouter(prefix="/api/audit-log", tags=["audit"])


@router.get("", response_model=list[AuditLogEntry])
def get_audit_log(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
    return [
        AuditLogEntry(
            id=r.id,
            timestamp=r.timestamp.isoformat() if r.timestamp else "",
            kpi_id=r.kpi_id,
            kpi_name=r.kpi_name,
            action=r.action,
            persona=r.persona or "executive",
            role=r.role or "global_exec",
            confidence=r.confidence,
            narrative_source=r.narrative_source,
            total_latency_ms=r.total_latency_ms or 0.0,
            model_calls=r.model_calls or 0,
            estimated_cost_usd=r.estimated_cost_usd or 0.0,
            summary=r.summary,
        )
        for r in rows
    ]
