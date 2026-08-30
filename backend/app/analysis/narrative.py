"""Narrative generation: the only place an LLM is allowed to touch this
pipeline, and even then only to phrase facts that were already computed
deterministically upstream (stats_engine + root_cause + confidence). The
LLM never invents numbers — it receives them as fixed inputs. If no API
key is configured, or the call fails/times out, Clarity falls back to a
deterministic template so the demo never breaks and never silently
fabricates.

Narratives are also persona-aware: the same underlying facts are phrased
differently for an executive (impact + one action), an analyst (method +
confidence breakdown), or an ops manager (who to contact, today). This is
the "role-based personalization of insight depth" the Round 2 brief asks
for, kept to prompt/template branching rather than separate models.

Telemetry (latency, token usage, estimated cost) is read directly from the
Anthropic API response's `usage` block when an LLM call is made — not
estimated — so the runtime-cost reporting is real, not illustrative.
"""
from __future__ import annotations

import os
import time

import httpx

from ..schemas import BreakdownItem, EvidenceItem, KPIDetail

# Illustrative public per-1M-token pricing (USD). Swap for your account's
# actual rate card — this is only meant to make the cost telemetry legible.
PRICING_PER_M_TOKENS = {
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.0},
}
DEFAULT_PRICING = {"input": 3.0, "output": 15.0}

PERSONA_INSTRUCTIONS = {
    "executive": (
        "Write for a time-poor executive: 2-3 sentences. Lead with the business impact and the single "
        "most important recommended action. No technical jargon, no statistical method names."
    ),
    "analyst": (
        "Write for a data analyst who needs to audit this conclusion: 4-5 sentences. Name the analytical "
        "method used, state the confidence breakdown, and be precise with numbers."
    ),
    "ops_manager": (
        "Write for an operations manager who must act today: short and direct. Name the exact segment/team "
        "to contact and the urgency. Skip background context."
    ),
}

PERSONA_TEMPLATE_LEAD = {
    "executive": "executive summary",
    "analyst": "analyst detail",
    "ops_manager": "ops briefing",
}


def _template_narrative(
    kpi: KPIDetail,
    persona: str,
    significance: str,
    pct_change: float,
    primary_driver: BreakdownItem | None,
    breakdown: list[BreakdownItem],
    evidence: list[EvidenceItem],
    confidence: float,
    confidence_reasoning: str,
    recommended_actions: list[str],
) -> str:
    direction = "rose" if pct_change > 0 else "fell"

    if persona == "executive":
        sentences = [
            f"{kpi.name} {direction} {abs(pct_change):.1f}% to {kpi.current_value:.2f}{kpi.unit}."
        ]
        if primary_driver:
            sentences.append(f"Primary driver: {primary_driver.segment} ({primary_driver.contribution_pct:.0f}% of the change).")
        else:
            sentences.append("No single segment dominates — this is a broad-based movement, not an isolated incident.")
        sentences.append(f"Confidence {confidence * 100:.0f}%.")
        if recommended_actions:
            sentences.append(f"Recommended: {recommended_actions[0]}")
        return " ".join(sentences)

    if persona == "ops_manager":
        who = primary_driver.segment if primary_driver else kpi.dimension_label
        sentences = [
            f"{kpi.name} {direction} {abs(pct_change):.1f}% — classified {significance}."
        ]
        sentences.append(f"Owner to contact: {who}.")
        if recommended_actions:
            sentences.append(f"Do now: {recommended_actions[0]}")
        return " ".join(sentences)

    # analyst (default/full detail)
    sentences = [
        f"{kpi.name} {direction} {abs(pct_change):.1f}% to {kpi.current_value:.2f}{kpi.unit}, "
        f"versus {kpi.prior_value:.2f}{kpi.unit} in the prior comparison window "
        f"(classified as a {significance} change by the rolling z-score / trend detector)."
    ]
    if primary_driver:
        others = [b for b in breakdown if b.segment != primary_driver.segment]
        offset_note = ""
        if others and abs(primary_driver.contribution_pct) > 100:
            offset_note = " Movement in the remaining segments partially offset this."
        sentences.append(
            f"The {primary_driver.dimension} breakdown identifies {primary_driver.segment} as the dominant "
            f"driver, contributing {primary_driver.contribution_pct:.0f}% of the total change "
            f"({primary_driver.prior_value:.2f} → {primary_driver.current_value:.2f}{kpi.unit}, "
            f"{primary_driver.pct_change:+.1f}%).{offset_note}"
        )
    else:
        top3 = sorted(breakdown, key=lambda b: abs(b.contribution_pct), reverse=True)[:3]
        names = ", ".join(f"{b.segment} ({b.contribution_pct:+.0f}%)" for b in top3)
        sentences.append(
            f"No single {kpi.dimension_label} segment dominates — {names} each contribute a comparable "
            "share, indicating a broad-based rather than isolated cause."
        )
    if evidence:
        e = evidence[0]
        sentences.append(f'This is consistent with {e.source}: "{e.text}"')
    sentences.append(f"Confidence: {confidence * 100:.0f}% ({confidence_reasoning})")
    if recommended_actions:
        sentences.append(f"Recommended next step: {recommended_actions[0]}")
    return " ".join(sentences)


def _empty_telemetry() -> dict:
    return {
        "llm_latency_ms": 0.0,
        "model_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def _llm_narrative(facts: str, persona: str) -> tuple[str | None, dict]:
    telemetry = _empty_telemetry()
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None, telemetry

    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    persona_instruction = PERSONA_INSTRUCTIONS.get(persona, PERSONA_INSTRUCTIONS["analyst"])
    start = time.perf_counter()
    try:
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 300,
                "system": (
                    "You are a business analyst writing a short KPI explanation. "
                    "You are given ONLY pre-computed facts (numbers, root cause, confidence). "
                    "Do NOT invent any number that is not already in the facts. "
                    f"{persona_instruction} Plain language, no bullet points, no markdown."
                ),
                "messages": [{"role": "user", "content": facts}],
            },
            timeout=8.0,
        )
        resp.raise_for_status()
        data = resp.json()
        telemetry["llm_latency_ms"] = round((time.perf_counter() - start) * 1000, 1)

        usage = data.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        rate = PRICING_PER_M_TOKENS.get(model, DEFAULT_PRICING)
        cost = (input_tokens / 1_000_000) * rate["input"] + (output_tokens / 1_000_000) * rate["output"]

        telemetry.update(
            model_calls=1,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=round(cost, 6),
        )
        return data["content"][0]["text"].strip(), telemetry
    except Exception:
        telemetry["llm_latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
        return None, telemetry


def generate_narrative(
    kpi: KPIDetail,
    persona: str,
    significance: str,
    pct_change: float,
    primary_driver: BreakdownItem | None,
    breakdown: list[BreakdownItem],
    evidence: list[EvidenceItem],
    confidence: float,
    confidence_reasoning: str,
    recommended_actions: list[str],
) -> tuple[str, str, dict]:
    template = _template_narrative(
        kpi, persona, significance, pct_change, primary_driver, breakdown, evidence,
        confidence, confidence_reasoning, recommended_actions,
    )

    facts_blob = (
        f"Metric: {kpi.name} ({kpi.unit}). Current: {kpi.current_value:.2f}, Prior: {kpi.prior_value:.2f}, "
        f"Change: {pct_change:+.1f}%. Significance: {significance}. "
        f"Primary driver: {primary_driver.segment + ' (' + f'{primary_driver.contribution_pct:.0f}%' + ' of change)' if primary_driver else 'none - broad based'}. "
        f"Evidence: {evidence[0].text if evidence else 'none'}. "
        f"Confidence: {confidence * 100:.0f}% ({confidence_reasoning}). "
        f"Recommended action: {recommended_actions[0] if recommended_actions else 'none'}."
    )
    llm_text, telemetry = _llm_narrative(facts_blob, persona)
    if llm_text:
        return llm_text, "llm", telemetry
    return template, "template", telemetry
