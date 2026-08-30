"""Server-side row/domain and field-level authorization.

The API never relies on client-side hiding.  Entitled roles may still receive
different fields: analysts can inspect calculation/lineage and raw evidence;
business roles receive governed summaries with sensitive evidence redacted.
"""
from __future__ import annotations

from .schemas import EvidenceItem, KPIDetail

FIELD_ACCESS = {
    "calculation": ["global_exec", "analyst"],
    "lineage": ["global_exec", "analyst"],
    "evidence.text": ["analyst"],
}


def can_view_field(role: str, field: str) -> bool:
    return role in FIELD_ACCESS.get(field, [])


def secure_evidence(items: list[EvidenceItem], role: str) -> tuple[list[EvidenceItem], list[str]]:
    if can_view_field(role, "evidence.text"):
        return items, []
    secured = [
        item.model_copy(update={"text": "[REDACTED: raw evidence is restricted to the analyst role]"})
        for item in items
    ]
    return secured, ["evidence.text"] if items else []


def secure_kpi(kpi: KPIDetail, role: str) -> KPIDetail:
    updates: dict[str, object] = {}
    redacted: list[str] = []
    for field in ("calculation", "lineage"):
        if not can_view_field(role, field):
            updates[field] = "[REDACTED: restricted field]"
            redacted.append(field)
    evidence, evidence_redactions = secure_evidence(kpi.evidence, role)
    updates["evidence"] = evidence
    redacted.extend(evidence_redactions)
    updates["redacted_fields"] = redacted
    return kpi.model_copy(update=updates)
