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
DOLLAR_IMPACT_CEILING = {"$K": 60.0}

# For non-dollar (rate/count) KPIs there's no direct $ conversion available in
# this prototype, so business impact falls back to the magnitude of relative
# change — a smaller, explicitly-flagged proxy rather than a silent guess.
RELATIVE_IMPACT_CEILING_PCT = 20.0

STATISTICAL_WEIGHT = 0.4
BUSINESS_IMPACT_WEIGHT = 0.6


def score_materiality(
    significance: str,
    pct_change: float,
    current_value: float,
    prior_value: float,
    unit: str,
) -> tuple[float, float, float, str, str]:
    statistical_component = SIGNIFICANCE_SCORE[significance]

    dollar_ceiling = DOLLAR_IMPACT_CEILING.get(unit)
    if dollar_ceiling:
        impact_magnitude = abs(current_value - prior_value)
        business_impact_component = min(1.0, impact_magnitude / dollar_ceiling)
        magnitude_unit = unit[1:] if unit.startswith("$") else unit
        estimated_impact = f"~${impact_magnitude:.1f}{magnitude_unit} swing"
        impact_basis = f"${impact_magnitude:.1f}{magnitude_unit} magnitude vs a ${dollar_ceiling:.0f}{magnitude_unit} full-materiality reference"
    else:
        business_impact_component = min(1.0, abs(pct_change) / RELATIVE_IMPACT_CEILING_PCT)
        estimated_impact = f"~{abs(pct_change):.1f}% relative move (no direct $ conversion available for this unit)"
        impact_basis = f"{abs(pct_change):.1f}% relative change vs a {RELATIVE_IMPACT_CEILING_PCT:.0f}% full-materiality reference (proxy, not a real $ estimate)"

    score = STATISTICAL_WEIGHT * statistical_component + BUSINESS_IMPACT_WEIGHT * business_impact_component
    score = round(max(0.0, min(1.0, score)), 2)

    reasoning = (
        f"statistical component {statistical_component:.2f} (signal '{significance}', weight {STATISTICAL_WEIGHT}); "
        f"business-impact component {business_impact_component:.2f} ({impact_basis}, weight {BUSINESS_IMPACT_WEIGHT})."
    )

    return score, round(statistical_component, 2), round(business_impact_component, 2), estimated_impact, reasoning
