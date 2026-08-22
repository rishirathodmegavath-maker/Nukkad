from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from .database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    kpi_id = Column(String, index=True)
    kpi_name = Column(String)
    action = Column(String)
    confidence = Column(Float)
    narrative_source = Column(String)
    summary = Column(Text)
