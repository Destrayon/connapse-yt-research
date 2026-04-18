"""Deterministic scoring for candidate YouTube video ideas.

Weights (§5.3 of spec):
    outlier_precedent: 0.25
    trend_slope:       0.15
    pain_density:      0.20
    audience_fit:      0.15
    signup_pull:       0.25
Sum: 1.00
"""

WEIGHTS = {
    "outlier_precedent": 0.25,
    "trend_slope": 0.15,
    "pain_density": 0.20,
    "audience_fit": 0.15,
    "signup_pull": 0.25,
}


def composite_score(
    outlier_precedent: float,
    trend_slope: float,
    pain_density: float,
    audience_fit: float,
    signup_pull: float,
) -> float:
    """Compute weighted composite score. All axes must be in [0, 1]."""
    axes = {
        "outlier_precedent": outlier_precedent,
        "trend_slope": trend_slope,
        "pain_density": pain_density,
        "audience_fit": audience_fit,
        "signup_pull": signup_pull,
    }
    for name, value in axes.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1], got {value}")
    return sum(WEIGHTS[k] * v for k, v in axes.items())
