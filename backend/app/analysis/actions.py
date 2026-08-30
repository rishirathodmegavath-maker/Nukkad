"""Deterministic recommendation playbook. Action selection is a rules
lookup, not an LLM decision — recommending a business action is exactly
the kind of deterministic, auditable step that should NOT be left to a
non-deterministic model.

Each action is returned as a structured driver -> lever -> action -> owner
-> confidence -> monitoring-plan record, per the Round 2 brief's own
solutioning spec, rather than a bare sentence.
"""
from __future__ import annotations

from ..schemas import ActionItem


def recommend_actions(
    status: str,
    is_ambiguous: bool,
    dimension: str,
    driver_segment: str | None,
    owner: str,
    confidence: float,
) -> list[ActionItem]:
    driver = driver_segment or (f"No dominant {dimension} segment" if is_ambiguous else dimension)

    if status == "recovered":
        return [
            ActionItem(
                driver=driver,
                lever="Playbook capture",
                action="Document the intervention that drove the recovery as a reusable playbook.",
                owner=owner,
                confidence=confidence,
                monitoring_plan="Re-check in 2 more reporting cycles to confirm the recovery is durable, not a rebound blip.",
            ),
            ActionItem(
                driver=driver,
                lever="Monitoring cadence",
                action="Continue routine monitoring before formally closing this incident out.",
                owner=owner,
                confidence=confidence,
                monitoring_plan="Auto-flag again if the metric dips more than 5% below the recovered baseline.",
            ),
        ]

    if is_ambiguous:
        return [
            ActionItem(
                driver=driver,
                lever="Manual investigation",
                action=f"Assign an analyst for a manual deep-dive — no single {dimension} segment explains the change.",
                owner=owner,
                confidence=confidence,
                monitoring_plan="Re-run this automated analysis in 3-5 days once more data has accumulated.",
            ),
            ActionItem(
                driver=driver,
                lever="Instrumentation",
                action="Increase data instrumentation for this metric before the next automated review.",
                owner=owner,
                confidence=confidence,
                monitoring_plan="Confirm data completeness has improved before trusting the next automated read.",
            ),
        ]

    if status == "critical":
        return [
            ActionItem(
                driver=driver,
                lever="Escalation",
                action=f"Escalate to the {driver_segment} segment owner within 24 hours.",
                owner=owner,
                confidence=confidence,
                monitoring_plan="Confirm root-cause acknowledgment from the segment owner within 24h.",
            ),
            ActionItem(
                driver=driver,
                lever="Incident review",
                action="Open an incident review to confirm root cause before customer/investor communication.",
                owner=owner,
                confidence=confidence,
                monitoring_plan="Track incident-review completion; confirm no external comms went out prematurely.",
            ),
            ActionItem(
                driver=driver,
                lever="Exposure sizing",
                action="Quantify revenue-at-risk from similar accounts/segments to size the exposure.",
                owner=owner,
                confidence=confidence,
                monitoring_plan="Compare the sized exposure estimate against next period's actuals.",
            ),
        ]

    if status == "watch":
        return [
            ActionItem(
                driver=driver,
                lever="Investigation",
                action=f"Investigate the {driver_segment or dimension} trend with the responsible team this week.",
                owner=owner,
                confidence=confidence,
                monitoring_plan="Set an automated alert if the trend continues for 5 more consecutive days.",
            ),
            ActionItem(
                driver=driver,
                lever="Experimentation",
                action="Consider a controlled experiment (A/B test) to test a corrective intervention.",
                owner=owner,
                confidence=confidence,
                monitoring_plan="Compare experiment vs. control on this KPI over the following reporting cycle.",
            ),
        ]

    return [
        ActionItem(
            driver="none",
            lever="Routine monitoring",
            action="No action required — metric is within normal operating range.",
            owner=owner,
            confidence=confidence,
            monitoring_plan="Continue routine monitoring; no special follow-up needed.",
        ),
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
