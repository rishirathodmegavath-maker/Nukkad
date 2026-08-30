"""Materiality scoring: how much does this movement actually matter?
Statistical significance alone answers "is this unusual" — it says nothing
about whether the dollars involved are worth an executive's attention. A KPI
can be statistically loud but financially trivial, or a quiet trend that's
worth millions. This blends both, weighted toward business impact.
"""
from __future__ import annotations

SIGNIFICANCE_SCORE = {"severe": 1.0, "meaningful": 0.6, "noise": 0.15}

# Illustrative impact scale for $-denominated KPIs: a swing at or above this
# magnitude is treated as maximally material on the business-impact axis.
BUSINESS_IMPACT_CEILING_USD = 250_000.0

# For non-dollar (rate/count) KPIs there's no direct $ conversion available in
# this prototype, so business impact falls back to the magnitude of relative
# change — a smaller, explicitly-flagged proxy rather than a silent guess.

STATISTICAL_WEIGHT = 0.4
BUSINESS_IMPACT_WEIGHT = 0.6


def score_materiality(
    significance: str,
    pct_change: float,
    current_value: float,
    prior_value: float,
    unit: str,
    business_impact_per_unit_usd: float,
    business_impact_basis: str,
) -> tuple[float, float, float, str, str]:
    statistical_component = SIGNIFICANCE_SCORE[significance]

    unit_delta = abs(current_value - prior_value)
    impact_usd = unit_delta * max(0.0, business_impact_per_unit_usd)
    business_impact_component = min(1.0, impact_usd / BUSINESS_IMPACT_CEILING_USD)
    estimated_impact = f"~${impact_usd:,.0f} modeled business impact"
    impact_basis = (
        f"{unit_delta:.2f} {unit} movement x ${business_impact_per_unit_usd:,.0f} per unit; "
        f"{business_impact_basis}"
    )

    score = STATISTICAL_WEIGHT * statistical_component + BUSINESS_IMPACT_WEIGHT * business_impact_component
    score = round(max(0.0, min(1.0, score)), 2)

    reasoning = (
        f"statistical component {statistical_component:.2f} (signal '{significance}', weight {STATISTICAL_WEIGHT}); "
        f"business-impact component {business_impact_component:.2f} ({impact_basis}, weight {BUSINESS_IMPACT_WEIGHT})."
    )

    return score, round(statistical_component, 2), round(business_impact_component, 2), estimated_impact, reasoning
