from fastapi import APIRouter, HTTPException

from ..data_generator import KPI_STORE
from ..schemas import KPIDetail, KPISummary

router = APIRouter(prefix="/api/kpis", tags=["kpis"])


@router.get("", response_model=list[KPISummary])
def list_kpis():
    return [
        KPISummary(**{k: v for k, v in kpi.model_dump().items() if k in KPISummary.model_fields})
        for kpi in KPI_STORE.values()
    ]


@router.get("/{kpi_id}", response_model=KPIDetail)
def get_kpi(kpi_id: str):
    kpi = KPI_STORE.get(kpi_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    return kpi
