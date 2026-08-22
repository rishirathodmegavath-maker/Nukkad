"""Narrative generation: the only place an LLM is allowed to touch this
pipeline, and even then only to phrase facts that were already computed
deterministically upstream (stats_engine + root_cause + confidence). The
LLM never invents numbers — it receives them as fixed inputs. If no API
key is configured, or the call fails/times out, Clarity falls back to a
deterministic template so the demo never breaks and never silently
fabricates.
"""
from __future__ import annotations

import os

import httpx

from ..schemas import BreakdownItem, EvidenceItem, KPIDetail


def _template_narrative(
    kpi: KPIDetail,
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
    sentences = [
        f"{kpi.name} {direction} {abs(pct_change):.1f}% to {kpi.current_value:.2f}{kpi.unit}, "
        f"versus {kpi.prior_value:.2f}{kpi.unit} in the prior comparison window "
        f"(classified as a {significance} change by the anomaly detector)."
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


def _llm_narrative(facts: str) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
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
                    "You are a business analyst writing a short KPI explanation for an executive. "
                    "You are given ONLY pre-computed facts (numbers, root cause, confidence). "
                    "Do NOT invent any number that is not already in the facts. "
                    "Write 3-4 tight sentences: what changed, why, and the recommended next step. "
                    "Plain business language, no bullet points, no markdown."
                ),
                "messages": [{"role": "user", "content": facts}],
            },
            timeout=8.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"].strip()
    except Exception:
        return None


def generate_narrative(
    kpi: KPIDetail,
    significance: str,
    pct_change: float,
    primary_driver: BreakdownItem | None,
    breakdown: list[BreakdownItem],
    evidence: list[EvidenceItem],
    confidence: float,
    confidence_reasoning: str,
    recommended_actions: list[str],
) -> tuple[str, str]:
    template = _template_narrative(
        kpi, significance, pct_change, primary_driver, breakdown, evidence,
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
    llm_text = _llm_narrative(facts_blob)
    if llm_text:
        return llm_text, "llm"
    return template, "template"
