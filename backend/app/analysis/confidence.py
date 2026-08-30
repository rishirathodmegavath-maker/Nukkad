"""Confidence scoring: how much should a business leader trust this
explanation? Combines statistical strength, data completeness, and
clarity of root-cause attribution. Always returns the reasoning behind
the number — a bare score with no explanation is not explainable AI.
"""
from __future__ import annotations

SIGNIFICANCE_BASE = {"severe": 0.88, "meaningful": 0.68, "noise": 0.35}


SPARSE_HISTORY_THRESHOLD_DAYS = 30

# Illustrative hours-since-last-refresh implied by each cadence — a stand-in
# for a real "data as of" timestamp, since this prototype has no live
# ingestion clock. Used only as a staleness signal on confidence.
FRESHNESS_HOURS = {
    "real-time (streaming)": 0.25,
    "hourly batch": 1.5,
    "daily batch": 20.0,
    "weekly batch": 140.0,
}
STALE_THRESHOLD_HOURS = 96.0


def score_confidence(
    significance: str,
    data_completeness: float,
    has_primary_driver: bool,
    top_contribution_pct: float,
    evidence_count: int,
    history_days: int = 90,
    refresh_cadence: str = "daily batch",
) -> tuple[float, str]:
    base = SIGNIFICANCE_BASE[significance]
    reasons = [f"statistical signal is '{significance}' (base {base:.2f})"]

    score = base * (0.55 + 0.45 * data_completeness)
    reasons.append(f"data completeness {data_completeness * 100:.0f}%")

    if has_primary_driver:
        score += 0.08
        reasons.append(f"a single segment explains {abs(top_contribution_pct):.0f}% of the change")
    else:
        score -= 0.12
        reasons.append("no single segment dominates the change (broad-based / ambiguous)")

    if evidence_count > 0:
        score += 0.05
        reasons.append(f"{evidence_count} corroborating evidence item(s) found")
    else:
        reasons.append("no corroborating qualitative evidence found")

    freshness_hours = FRESHNESS_HOURS.get(refresh_cadence, 20.0)
    if freshness_hours > STALE_THRESHOLD_HOURS:
        score *= 0.92
        reasons.append(
            f"source refreshes {refresh_cadence} (~{freshness_hours:.0f}h since last update) — "
            "confidence trimmed for staleness risk"
        )

    if history_days < SPARSE_HISTORY_THRESHOLD_DAYS:
        score = min(score, 0.45) * (0.5 + 0.5 * history_days / SPARSE_HISTORY_THRESHOLD_DAYS)
        reasons.append(
            f"only {history_days} day(s) of history available — insufficient for a reliable trend "
            "baseline, so confidence is deliberately capped regardless of the raw signal"
        )

    score = max(0.05, min(0.98, score))
    reasoning = "; ".join(reasons) + "."
    return round(score, 2), reasoning
