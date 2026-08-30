from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, func

from .database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    kpi_id = Column(String, index=True)
    kpi_name = Column(String)
    action = Column(String)
    persona = Column(String, default="executive")
    role = Column(String, default="global_exec")
    confidence = Column(Float)
    narrative_source = Column(String)
    total_latency_ms = Column(Float, default=0.0)
    model_calls = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    summary = Column(Text)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    kpi_id = Column(String, index=True)
    persona = Column(String, default="executive")
    useful = Column(Boolean)
    comment = Column(Text, nullable=True)
