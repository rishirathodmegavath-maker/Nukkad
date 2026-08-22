"""Deterministic statistical layer: rolling z-score anomaly detection,
trend comparison, and recovery detection. No ML training required —
this is the "rules + statistics" half of Clarity's hybrid AI stack.
"""
from __future__ import annotations

import numpy as np


def rolling_anomaly_flags(values: list[float], window: int = 14, z_threshold: float = 2.5) -> list[bool]:
    arr = np.array(values, dtype=float)
    flags = [False] * len(arr)
    for i in range(len(arr)):
        start = max(0, i - window)
        hist = arr[start:i]
        if len(hist) < 5:
            continue
        mu, sigma = hist.mean(), hist.std()
        if sigma < 1e-9:
            continue
        z = (arr[i] - mu) / sigma
        if abs(z) >= z_threshold:
            flags[i] = True
    return flags


def detect_recovery(values: list[float]) -> bool:
    arr = np.array(values, dtype=float)
    if len(arr) < 40:
        return False
    pre_baseline = arr[:20].mean()
    mid_window = arr[20:85] if len(arr) >= 85 else arr[20:-3]
    if len(mid_window) == 0:
        return False
    dip_min = mid_window.min()
    current = arr[-3:].mean()
    return bool(dip_min < pre_baseline * 0.85 and current >= pre_baseline * 0.95)


def classify_significance(values: list[float]) -> tuple[str, float, float]:
    """Returns (significance, pct_change, trend_pct) using a short-term
    z-score (shock detection) combined with a medium-term trend comparison
    (gradual decline detection) — two different failure modes need two
    different lenses.
    """
    arr = np.array(values, dtype=float)
    current = arr[-3:].mean()
    recent_baseline = arr[-17:-7].mean() if len(arr) >= 17 else arr[:-3].mean()
    pct_change = (current - recent_baseline) / recent_baseline * 100 if recent_baseline else 0.0

    window = arr[-15:-1] if len(arr) >= 16 else arr[:-1]
    mu, sigma = window.mean(), window.std()
    last_z = (arr[-1] - mu) / sigma if sigma > 1e-9 else 0.0

    if len(arr) >= 44:
        trend_recent = arr[-14:].mean()
        trend_past = arr[-44:-30].mean()
        trend_pct = (trend_recent - trend_past) / trend_past * 100 if trend_past else 0.0
    else:
        trend_pct = pct_change

    if abs(last_z) > 3 or abs(pct_change) > 15:
        significance = "severe"
    elif abs(last_z) > 1.8 or abs(trend_pct) > 8:
        significance = "meaningful"
    else:
        significance = "noise"

    return significance, round(pct_change, 2), round(trend_pct, 2)


def determine_status(significance: str, pct_change: float, higher_is_better: bool, recovered: bool) -> str:
    if recovered:
        return "recovered"
    bad_direction = (pct_change < 0) if higher_is_better else (pct_change > 0)
    if significance == "severe" and bad_direction:
        return "critical"
    if significance in ("meaningful", "severe") and bad_direction:
        return "watch"
    return "normal"
