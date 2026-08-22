"""Root-cause attribution: ranks dimensional segments by their share of
the total metric change and decides whether a single dominant driver
exists or the change is genuinely ambiguous (broad-based).
"""
from __future__ import annotations

from ..schemas import BreakdownItem


def find_primary_driver(breakdown: list[BreakdownItem]) -> BreakdownItem | None:
    if not breakdown:
        return None
    ranked = sorted(breakdown, key=lambda b: abs(b.contribution_pct), reverse=True)
    top = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None

    dominant_by_share = abs(top.contribution_pct) >= 50
    dominant_by_margin = runner_up is None or abs(top.contribution_pct) >= 1.6 * abs(runner_up.contribution_pct)

    if dominant_by_share and dominant_by_margin:
        return top
    return None
