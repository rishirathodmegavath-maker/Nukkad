"""Confidence scoring: how much should a business leader trust this
explanation? Combines statistical strength, data completeness, and
clarity of root-cause attribution. Always returns the reasoning behind
the number — a bare score with no explanation is not explainable AI.
"""
from __future__ import annotations

SIGNIFICANCE_BASE = {"severe": 0.88, "meaningful": 0.68, "noise": 0.35}


def score_confidence(
    significance: str,
    data_completeness: float,
    has_primary_driver: bool,
    top_contribution_pct: float,
    evidence_count: int,
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

    score = max(0.05, min(0.98, score))
    reasoning = "; ".join(reasons) + "."
    return round(score, 2), reasoning
