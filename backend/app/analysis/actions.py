"""Deterministic recommendation playbook. Action selection is a rules
lookup, not an LLM decision — recommending a business action is exactly
the kind of deterministic, auditable step that should NOT be left to a
non-deterministic model.
"""
from __future__ import annotations


def recommend_actions(status: str, is_ambiguous: bool, dimension: str, driver_segment: str | None) -> list[str]:
    if status == "recovered":
        return [
            "Document the intervention that drove the recovery as a reusable playbook.",
            "Monitor for 2 more cycles to confirm the recovery is durable, not a rebound blip.",
        ]

    if is_ambiguous:
        return [
            f"Assign an analyst for a manual deep-dive — no single {dimension} segment explains the change.",
            "Increase data instrumentation for this metric before the next automated review.",
            "Re-run this analysis in 3-5 days once more data has accumulated.",
        ]

    if status == "critical":
        return [
            f"Escalate to the {driver_segment} segment owner within 24 hours.",
            "Open an incident review to confirm root cause before customer/investor communication.",
            "Quantify revenue-at-risk from similar accounts/segments to size the exposure.",
        ]

    if status == "watch":
        return [
            f"Investigate the {driver_segment or dimension} trend with the responsible team this week.",
            "Set an automated alert if the trend continues for 5 more consecutive days.",
            "Consider a controlled experiment (A/B test) to test a corrective intervention.",
        ]

    return [
        "No action required — metric is within normal operating range.",
        "Continue routine monitoring.",
    ]


def check_decision_authority(role: str, owner: str, access_roles: list[str]) -> tuple[bool, str]:
    """Decision rights: does the viewing role actually own this KPI's domain
    and can therefore authorize the recommended actions, or are they
    read/diagnostic-only and must escalate to the owner instead?

    global_exec always has authority (cross-domain executive). "analyst" is
    always advisory-only, regardless of which KPIs they can read — broad
    visibility is not the same as authority to act. Any other role is treated
    as the domain owner only if it's in this KPI's access_roles (i.e. it was
    specifically entitled to this KPI's domain).
    """
    if role == "global_exec":
        return True, f"Global Executive has cross-domain authority to act. Nominal owner: {owner}."
    if role == "analyst":
        return False, f"Analysts have diagnostic access only — recommend and escalate to the owner ({owner})."
    if role in access_roles:
        return True, f"'{role}' owns this KPI's domain and can authorize these actions directly."
    return False, f"'{role}' is not the owner of this KPI — escalate to {owner} before acting."
