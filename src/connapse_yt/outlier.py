"""Outlier detection: view count vs. channel baseline."""

import math


def outlier_ratio(*, views: int, channel_median: float) -> float:
    if channel_median <= 0:
        return 0.0
    return views / channel_median


def score_from_ratio(ratio: float) -> float:
    """Map an outlier ratio to a [0, 1] score.

    Uses log2 so each doubling above the channel median adds roughly 0.1.
    - ratio ≤ 1 → near-zero score
    - ratio = 2 → 0.1
    - ratio = 10 → ~0.7-0.9
    - ratio ≥ 32 → 1.0 (capped)
    """
    if ratio <= 1.0:
        return 0.0
    score = math.log2(ratio) / 5.0  # log2(32) = 5 → score=1.0
    return min(1.0, score)
