"""Synthetic-but-deliberate demo data. Six KPIs, six distinct storylines
(normal / critical anomaly / gradual high-risk trend / recovered after
intervention / genuinely ambiguous / sparse-history new launch), so the
product demonstrates its full range rather than one lucky scenario.
Generated once at import time with fixed RNG seeds so every run of the demo
is stable and reproducible.

Each KPI also carries simulated multi-source lineage (source_system,
refresh_cadence), a lightweight semantic contract (definition, calculation,
lineage), and access_roles for the row/domain-level access-control demo —
these are the "governed KPI semantics" and "heterogeneous sources" the
Round 2 brief asks for, kept intentionally simple for a single-hour prototype.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from .analysis.stats_engine import classify_significance, detect_recovery, determine_status, rolling_anomaly_flags
from .schemas import BreakdownItem, EvidenceItem, KPIDetail, TimeseriesPoint

DAYS = 90
TODAY = date.today()


def _dates(n: int = DAYS) -> list[date]:
    return [TODAY - timedelta(days=(n - 1 - i)) for i in range(n)]


def _base_series(mean: float, noise_pct: float, seed: int, weekly_season_pct: float = 0.0, days: int = DAYS) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, mean * noise_pct, days)
    season = np.zeros(days)
    if weekly_season_pct:
        for i in range(days):
            dow = (TODAY - timedelta(days=(days - 1 - i))).weekday()
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
    source_system: str,
    refresh_cadence: str,
    definition: str,
    calculation: str,
    lineage: str,
    access_roles: list[str],
    known_drivers: list[str] | None = None,
) -> KPIDetail:
    dates = _dates(len(series))
    values = series.tolist()
    anomaly_flags = rolling_anomaly_flags(values)
    significance, pct_change, _trend = classify_significance(values)
    recovered = detect_recovery(values)
    status = determine_status(significance, pct_change, higher_is_better, recovered)

    current_value = float(np.mean(values[-3:]))
    prior_value = float(np.mean(values[-17:-7])) if len(values) >= 17 else float(np.mean(values[: max(1, len(values) - 3)]))
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
        source_system=source_system,
        refresh_cadence=refresh_cadence,
        definition=definition,
        calculation=calculation,
        lineage=lineage,
        access_roles=access_roles,
        known_drivers=known_drivers or [],
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
        source_system="Billing Platform (Stripe) + Salesforce CRM",
        refresh_cadence="daily batch",
        definition="Total recognized revenue for the APAC region across all sales channels, in $K/day.",
        calculation="SUM(invoice_amount) WHERE region='APAC', reconciled daily against Salesforce opportunity close events.",
        lineage="Stripe invoices -> nightly finance ETL -> revenue_daily fact table, joined to Salesforce account/channel dims.",
        access_roles=["global_exec", "apac_manager", "analyst"],
        known_drivers=["Single dominant driver: Enterprise segment account churn (TitanCorp cancellation)"],
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
        source_system="Order Management System (event stream)",
        refresh_cadence="real-time (streaming)",
        definition="Count of completed NA online orders per day, across all devices.",
        calculation="COUNT(DISTINCT order_id) WHERE market='NA' AND channel='online', streamed and rolled up to daily grain.",
        lineage="OMS Kafka topic -> stream aggregator -> orders_daily materialized view.",
        access_roles=["global_exec", "na_manager", "analyst"],
    )

    # 3. WATCH: slow gradual decline across the whole window, broad-based.
    # Deliberately tagged as the multi-factor scenario: a technical driver
    # (checkout latency) overlays a broad-based channel decline — two
    # different kinds of "cause" acting at once, not a single isolated one.
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
        source_system="Product Analytics (Amplitude) + Web Server Logs",
        refresh_cadence="hourly batch",
        definition="Share of EMEA site sessions that complete checkout, in %/day.",
        calculation="COUNT(sessions with completed order) / COUNT(sessions) WHERE region='EMEA', aggregated hourly then rolled to daily.",
        lineage="Amplitude events + nginx access logs -> hourly Spark job -> conversion_hourly -> daily rollup.",
        access_roles=["global_exec", "emea_manager", "analyst"],
        known_drivers=[
            "Checkout latency regression (+600ms) affecting all traffic sources equally",
            "Broad-based decline across channels — no single traffic-source outlier",
        ],
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
        source_system="Billing Platform (Stripe) + Ops Incident Log (PagerDuty)",
        refresh_cadence="daily batch",
        definition="Total recognized revenue for the LATAM region across all sales channels, in $K/day.",
        calculation="SUM(invoice_amount) WHERE region='LATAM', reconciled daily against PagerDuty incident windows.",
        lineage="Stripe invoices -> nightly finance ETL -> revenue_daily fact table, annotated with PagerDuty incident overlays.",
        access_roles=["global_exec", "latam_manager", "analyst"],
        known_drivers=["Payment gateway outage (13 days) — resolved, recovery attributable to the fix"],
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
        source_system="CRM (Salesforce) + Support Tickets (Zendesk)",
        refresh_cadence="weekly batch",
        definition="Share of global SMB accounts that cancel in a given period, in %/week, by tenure cohort.",
        calculation="COUNT(cancelled accounts) / COUNT(active accounts at period start), grouped by tenure cohort.",
        lineage="Salesforce account status + Zendesk cancellation surveys -> weekly batch join -> churn_weekly.",
        access_roles=["global_exec", "analyst"],
    )

    # 6. SPARSE-HISTORY: newly launched feature, only 12 days of data — not
    # enough to establish a reliable trend baseline. Confidence must reflect
    # that honestly rather than pretending 90 days of history exist.
    sparse_days = 12
    rng = np.random.default_rng(6)
    trend6 = np.linspace(18.0, 21.5, sparse_days)
    s6 = trend6 + rng.normal(0, 0.8, sparse_days)
    kpis["activation_ai_copilot"] = _make_kpi(
        "activation_ai_copilot", "Activation Rate — AI Copilot (New Feature)", "%", "Growth", True, s6, "cohort",
        shares={"Beta users": 0.60, "GA rollout": 0.40},
        contributions={"Beta users": 58, "GA rollout": 42},
        evidence=[
            EvidenceItem(source="Product analytics", text="Feature launched 12 days ago; GA rollout is still ramping in batches.", relevance="contextual"),
        ],
        data_completeness=0.35,
        source_system="Product Analytics (Amplitude)",
        refresh_cadence="daily batch",
        definition="Share of exposed users who complete a first meaningful action with the AI Copilot within 7 days of exposure.",
        calculation="COUNT(users with >=1 copilot action in 7d) / COUNT(users exposed to copilot), grouped daily.",
        lineage="Amplitude event stream -> nightly ETL -> activation_daily table (feature launched 12 days ago).",
        access_roles=["global_exec", "product_lead", "analyst"],
        known_drivers=[
            "Only 12 days of history available — no reliable trend baseline yet",
            "GA rollout still ramping in batches, not yet at steady state",
        ],
    )

    return kpis


KPI_STORE: dict[str, KPIDetail] = _generate_all()
