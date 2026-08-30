"""Configurable warehouse and BI REST connectors.

Credentials stay in environment variables; no secrets are accepted from or
returned to the browser.  The adapters execute a real SQL probe or HTTP health
request when explicitly tested, while the seeded adapter keeps the demo usable
without enterprise credentials.
"""
from __future__ import annotations

import os
import time

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text

router = APIRouter(prefix="/api/connectors", tags=["connectors"])


class ConnectorStatus(BaseModel):
    id: str
    kind: str
    configured: bool
    state: str
    latency_ms: float | None = None
    detail: str


def _catalog() -> dict[str, dict[str, str]]:
    return {
        "seeded_demo": {"kind": "sample", "value": "built-in"},
        "warehouse": {"kind": "sql", "value": os.getenv("WAREHOUSE_DATABASE_URL", "").strip()},
        "bi_tool": {"kind": "rest", "value": os.getenv("BI_API_URL", "").strip()},
    }


@router.get("", response_model=list[ConnectorStatus])
def list_connectors():
    result = []
    for connector_id, config in _catalog().items():
        configured = bool(config["value"])
        result.append(ConnectorStatus(
            id=connector_id,
            kind=config["kind"],
            configured=configured,
            state="ready" if configured else "awaiting_credentials",
            detail=("Connector is configured and can be tested." if configured else "Set its server-side environment variable; sample mode remains active."),
        ))
    return result


@router.post("/{connector_id}/test", response_model=ConnectorStatus)
def test_connector(connector_id: str):
    config = _catalog().get(connector_id)
    if not config:
        raise HTTPException(status_code=404, detail="Connector not found")
    if not config["value"]:
        raise HTTPException(status_code=409, detail="Connector is not configured")
    started = time.perf_counter()
    try:
        if config["kind"] == "sql":
            engine = create_engine(config["value"], pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            detail = "SQL connection and query probe succeeded."
        elif config["kind"] == "rest":
            headers = {}
            token = os.getenv("BI_API_TOKEN", "").strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
            response = httpx.get(config["value"], headers=headers, timeout=5.0)
            response.raise_for_status()
            detail = f"BI REST endpoint returned HTTP {response.status_code}."
        else:
            detail = "Built-in sample connector is ready."
        return ConnectorStatus(id=connector_id, kind=config["kind"], configured=True, state="connected", latency_ms=round((time.perf_counter()-started)*1000, 1), detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Connector probe failed: {type(exc).__name__}") from exc
