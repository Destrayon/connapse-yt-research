"""Deterministic scoring for candidate YouTube video ideas.

Weights (§5.3 of spec):
    outlier_precedent: 0.25
    trend_slope:       0.15
    pain_density:      0.20
    audience_fit:      0.15
    signup_pull:       0.25
Sum: 1.00
"""

from dataclasses import dataclass, field
from typing import Literal

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


Pillar = Literal["P1", "P2", "P3"]
Surface = Literal["hosted", "oss", "both"]
VALID_PILLARS = {"P1", "P2", "P3"}
VALID_SURFACES = {"hosted", "oss", "both"}


@dataclass
class Candidate:
    """A scored YouTube video idea candidate (§5.3).

    Validation rules enforced on construction:
    - pillar ∈ {P1, P2, P3} (null rejected — off-strategy is not a candidate).
    - promotion_surface ∈ {hosted, oss, both}.
    - cloud_compatible=False may not route to the hosted surface (spec §1 routing rule).
    """

    text: str
    outlier_precedent: float
    trend_slope: float
    pain_density: float
    audience_fit: float
    signup_pull: float
    pillar: Pillar
    cloud_compatible: bool
    promotion_surface: Surface
    sources: list[str] = field(default_factory=list)
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.pillar not in VALID_PILLARS:
            raise ValueError(
                f"pillar must be one of {sorted(VALID_PILLARS)}, got {self.pillar!r}"
            )
        if self.promotion_surface not in VALID_SURFACES:
            raise ValueError(
                f"promotion_surface must be one of {sorted(VALID_SURFACES)}, "
                f"got {self.promotion_surface!r}"
            )
        if not self.cloud_compatible and self.promotion_surface == "hosted":
            raise ValueError(
                "cloud_compatible=False cannot route to promotion_surface='hosted'; "
                "use 'oss' or 'both' (and 'both' only if you reframe the hook)"
            )

    @property
    def composite(self) -> float:
        return composite_score(
            self.outlier_precedent,
            self.trend_slope,
            self.pain_density,
            self.audience_fit,
            self.signup_pull,
        )

    @property
    def routing_ok(self) -> bool:
        """True if cloud/OSS routing is internally consistent."""
        if not self.cloud_compatible and self.promotion_surface == "hosted":
            return False
        return True
