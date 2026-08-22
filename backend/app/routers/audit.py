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
            confidence=r.confidence,
            narrative_source=r.narrative_source,
            summary=r.summary,
        )
        for r in rows
    ]
