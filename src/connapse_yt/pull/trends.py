"""Google Trends slopes via pytrends."""

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

Direction = Literal["rising", "flat", "falling"]


@dataclass
class TrendSlope:
    keyword: str
    slope: float  # linear-regression slope across the timeframe
    direction: Direction
    score: float  # [0, 1], rising=positive slope mapped to higher score


def _direction(slope: float) -> Direction:
    if slope > 1.0:
        return "rising"
    if slope < -1.0:
        return "falling"
    return "flat"


def _score(slope: float) -> float:
    # Slopes in pytrends are noisy; clamp to +/- 10 → [0, 1].
    import math
    clipped = max(-10.0, min(10.0, slope))
    return (clipped + 10.0) / 20.0


def compute_trend_slopes(
    *,
    trends: Any,  # pytrends TrendReq, Any for testability
    keywords: list[str],
    timeframe: str = "today 3-m",
) -> list[TrendSlope]:
    if not keywords:
        return []
    trends.build_payload(keywords, timeframe=timeframe)
    df: pd.DataFrame = trends.interest_over_time()
    if df is None or df.empty:
        return []
    out: list[TrendSlope] = []
    x = list(range(len(df.index)))
    for kw in keywords:
        if kw not in df.columns:
            continue
        series = df[kw].astype(float).tolist()
        slope = _linear_slope(x, series)
        out.append(
            TrendSlope(
                keyword=kw,
                slope=slope,
                direction=_direction(slope),
                score=_score(slope),
            )
        )
    return out


def _linear_slope(xs: list[int], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    return num / den if den else 0.0


def make_trends_client(*, hl: str = "en-US", tz: int = 360):
    """Deferred import so pytrends stays optional for unit tests."""
    from pytrends.request import TrendReq  # noqa: WPS433
    return TrendReq(hl=hl, tz=tz)
