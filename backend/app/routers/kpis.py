from fastapi import APIRouter, HTTPException

from ..data_generator import KPI_STORE
from ..schemas import KPIContract, KPIDetail, KPISummary

router = APIRouter(prefix="/api/kpis", tags=["kpis"])

# Global materiality thresholds — same rule set applied to every KPI, kept
# here (not per-KPI) since the underlying detector is a single shared
# algorithm. Part of the semantic contract's "thresholds" section.
THRESHOLDS = {
    "watch": "|z-score| > 1.8 over a 14-day rolling window, OR medium-term trend move > 8%, in the adverse direction",
    "critical": "|z-score| > 3.0, OR short-term change > 15%, in the adverse direction",
    "recovered": "prior dip >15% below baseline AND current 3-day window back within 5% of baseline",
}


def _visible_kpis(role: str):
    return [k for k in KPI_STORE.values() if role in k.access_roles]


def _require_access(kpi_id: str, role: str) -> KPIDetail:
    kpi = KPI_STORE.get(kpi_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    if role not in kpi.access_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role}' is not entitled to view '{kpi.name}' (row/domain-level access control).",
        )
    return kpi


@router.get("", response_model=list[KPISummary])
def list_kpis(role: str = "global_exec"):
    return [
        KPISummary(**{k: v for k, v in kpi.model_dump().items() if k in KPISummary.model_fields})
        for kpi in _visible_kpis(role)
    ]


@router.get("/{kpi_id}", response_model=KPIDetail)
def get_kpi(kpi_id: str, role: str = "global_exec"):
    return _require_access(kpi_id, role)


@router.get("/{kpi_id}/contract", response_model=KPIContract)
def get_kpi_contract(kpi_id: str, role: str = "global_exec"):
    kpi = _require_access(kpi_id, role)
    return KPIContract(
        kpi_id=kpi.id,
        name=kpi.name,
        unit=kpi.unit,
        definition=kpi.definition,
        calculation=kpi.calculation,
        dimension_label=kpi.dimension_label,
        drivers=[b.segment for b in kpi.breakdown],
        thresholds=THRESHOLDS,
        source_system=kpi.source_system,
        refresh_cadence=kpi.refresh_cadence,
        lineage=kpi.lineage,
        access_roles=kpi.access_roles,
        owner=kpi.owner,
        history_days=len(kpi.timeseries),
    )
