"""Synthetic-but-deliberate demo data. Five KPIs, five distinct storylines
(normal / critical anomaly / gradual high-risk trend / recovered after
intervention / genuinely ambiguous), so the product demonstrates its full
range rather than one lucky scenario. Generated once at import time with
fixed RNG seeds so every run of the demo is stable and reproducible.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from .analysis.stats_engine import classify_significance, detect_recovery, determine_status, rolling_anomaly_flags
from .schemas import BreakdownItem, EvidenceItem, KPIDetail, TimeseriesPoint

DAYS = 90
TODAY = date.today()


def _dates() -> list[date]:
    return [TODAY - timedelta(days=(DAYS - 1 - i)) for i in range(DAYS)]


def _base_series(mean: float, noise_pct: float, seed: int, weekly_season_pct: float = 0.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, mean * noise_pct, DAYS)
    season = np.zeros(DAYS)
    if weekly_season_pct:
        for i in range(DAYS):
            dow = (TODAY - timedelta(days=(DAYS - 1 - i))).weekday()
            season[i] = mean * weekly_season_pct * (1 if dow < 5 else -1)
    return mean + noise + season


def _build_breakdown(
    dimension: str,
    shares: dict[str, float],
    contributions: dict[str, float],
    prior_total: float,
    total_change: float,
) -> list[BreakdownItem]:
    items = []
    for segment, share in shares.items():
        seg_prior = share * prior_total
        seg_change = (contributions[segment] / 100.0) * total_change
        seg_current = seg_prior + seg_change
        seg_pct = (seg_change / seg_prior * 100) if seg_prior else 0.0
        items.append(
            BreakdownItem(
                segment=segment,
                dimension=dimension,
                prior_value=round(seg_prior, 2),
                current_value=round(seg_current, 2),
                pct_change=round(seg_pct, 2),
                contribution_pct=round(contributions[segment], 1),
            )
        )
    return items


def _make_kpi(
    kpi_id: str,
    name: str,
    unit: str,
    category: str,
    higher_is_better: bool,
    series: np.ndarray,
    dimension_label: str,
    shares: dict[str, float],
    contributions: dict[str, float],
    evidence: list[EvidenceItem],
    data_completeness: float,
) -> KPIDetail:
    dates = _dates()
    values = series.tolist()
    anomaly_flags = rolling_anomaly_flags(values)
    significance, pct_change, _trend = classify_significance(values)
    recovered = detect_recovery(values)
    status = determine_status(significance, pct_change, higher_is_better, recovered)

    current_value = float(np.mean(values[-3:]))
    prior_value = float(np.mean(values[-17:-7]))
    total_change = current_value - prior_value

    breakdown = _build_breakdown(dimension_label, shares, contributions, prior_value, total_change)

    timeseries = [
        TimeseriesPoint(date=d, value=round(v, 2), is_anomaly=a)
        for d, v, a in zip(dates, values, anomaly_flags)
    ]

    return KPIDetail(
        id=kpi_id,
        name=name,
        unit=unit,
        category=category,
        current_value=round(current_value, 2),
        prior_value=round(prior_value, 2),
        pct_change=round(pct_change, 2),
        status=status,
        sparkline=[round(v, 2) for v in values[-21:]],
        timeseries=timeseries,
        breakdown=breakdown,
        evidence=evidence,
        data_completeness=data_completeness,
        dimension_label=dimension_label,
    )


def _generate_all() -> dict[str, KPIDetail]:
    kpis: dict[str, KPIDetail] = {}

    # 1. CRITICAL: sudden step-down driven by one dominant segment (enterprise churn)
    # Shock starts at index 83 so the prior comparison window (days 73-82) stays
    # entirely pre-shock and the current window (last 3 days) is entirely post-shock.
    s = _base_series(mean=420, noise_pct=0.025, seed=1)
    s[83:] = s[83:] * 0.78 - np.random.default_rng(11).normal(0, 4, DAYS - 83)
    kpis["rev_apac"] = _make_kpi(
        "rev_apac", "Revenue — APAC", "$K", "Revenue", True, s, "channel",
        shares={"Enterprise": 0.40, "Online": 0.30, "Retail": 0.20, "Partner": 0.10},
        contributions={"Enterprise": 150, "Online": -25, "Retail": -13, "Partner": -12},
        evidence=[
            EvidenceItem(source="CRM note (2 days ago)", text="Largest APAC enterprise account (TitanCorp) cancelled renewal, citing budget freeze.", relevance="supporting"),
            EvidenceItem(source="Support tickets", text="No increase in churn-related tickets from Online/Retail customers this period.", relevance="contextual"),
        ],
        data_completeness=0.93,
    )

    # 2. NORMAL: stable, low-noise series with no shock or trend.
    # (Weekday seasonality was tried here but its phase misaligns with the
    # fixed 10/3-day comparison windows and produces a spurious "watch" signal —
    # a real reminder that naive rolling stats need seasonality-awareness,
    # noted in the README limitations.)
    s = _base_series(mean=1500, noise_pct=0.015, seed=2)
    kpis["orders_na_online"] = _make_kpi(
        "orders_na_online", "Orders — NA Online", "orders/day", "Growth", True, s, "device",
        shares={"Desktop": 0.45, "Mobile": 0.40, "Tablet": 0.15},
        contributions={"Desktop": 40, "Mobile": 45, "Tablet": 15},
        evidence=[
            EvidenceItem(source="Marketing calendar", text="No major campaigns launched or ended in this window.", relevance="contextual"),
        ],
        data_completeness=0.97,
    )

    # 3. WATCH: slow gradual decline across the whole window, broad-based
    rng = np.random.default_rng(3)
    trend = np.linspace(3.8, 3.2, DAYS)
    s = trend + rng.normal(0, 0.05, DAYS)
    kpis["conv_emea"] = _make_kpi(
        "conv_emea", "Conversion Rate — EMEA", "%", "Growth", True, s, "traffic source",
        shares={"Paid Search": 0.35, "Organic": 0.30, "Direct": 0.20, "Referral": 0.15},
        contributions={"Paid Search": 34, "Organic": 27, "Direct": 22, "Referral": 17},
        evidence=[
            EvidenceItem(source="Product analytics", text="Checkout page load time increased ~600ms over the same period across all traffic sources.", relevance="supporting"),
            EvidenceItem(source="Support tickets", text="Small uptick in 'payment step failed' complaints, not isolated to one channel.", relevance="supporting"),
        ],
        data_completeness=0.88,
    )

    # 4. RECOVERED: dip then recovery after an intervention
    rng = np.random.default_rng(4)
    s = _base_series(mean=300, noise_pct=0.02, seed=4)
    s[70:83] = s[70:83] * 0.75
    s[83:] = np.linspace(s[82], 315, DAYS - 83) + rng.normal(0, 5, DAYS - 83)
    kpis["rev_latam"] = _make_kpi(
        "rev_latam", "Revenue — LATAM", "$K", "Revenue", True, s, "channel",
        shares={"Online": 0.55, "Retail": 0.30, "Partner": 0.15},
        contributions={"Online": 70, "Retail": 20, "Partner": 10},
        evidence=[
            EvidenceItem(source="Ops incident log", text="Payment gateway outage (13 days, now resolved) blocked ~20% of LATAM checkout attempts.", relevance="supporting"),
            EvidenceItem(source="Ops incident log", text="Gateway failover fix deployed; checkout success rate back to baseline since.", relevance="supporting"),
        ],
        data_completeness=0.95,
    )

    # 5. AMBIGUOUS: noisy, broad-based increase in a "lower is better" metric, low data completeness
    rng = np.random.default_rng(5)
    trend = np.linspace(2.1, 2.6, DAYS)
    s = trend + rng.normal(0, 0.15, DAYS)
    kpis["churn_smb"] = _make_kpi(
        "churn_smb", "Churn Rate — Global SMB", "%", "Retention", False, s, "cohort",
        shares={"0-6mo tenure": 0.30, "6-12mo tenure": 0.28, "12-24mo tenure": 0.24, "24mo+ tenure": 0.18},
        contributions={"0-6mo tenure": 29, "6-12mo tenure": 26, "12-24mo tenure": 24, "24mo+ tenure": 21},
        evidence=[
            EvidenceItem(source="Support tickets", text="No dominant complaint theme identified across cancellation surveys this period.", relevance="contextual"),
        ],
        data_completeness=0.55,
    )

    return kpis


KPI_STORE: dict[str, KPIDetail] = _generate_all()
