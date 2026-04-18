from unittest.mock import MagicMock
import pandas as pd
from connapse_yt.pull.trends import compute_trend_slopes, TrendSlope


def test_compute_trend_slopes_computes_direction():
    fake_tr = MagicMock()
    df = pd.DataFrame(
        {
            "claude code": [10, 20, 30, 50, 80, 100, 140],
            "langchain": [100, 90, 80, 70, 60, 50, 40],
            "isPartial": [False] * 7,
        }
    )
    fake_tr.interest_over_time.return_value = df

    slopes = compute_trend_slopes(
        trends=fake_tr, keywords=["claude code", "langchain"], timeframe="today 3-m"
    )
    assert len(slopes) == 2
    by_kw = {s.keyword: s for s in slopes}
    assert isinstance(by_kw["claude code"], TrendSlope)
    assert by_kw["claude code"].direction == "rising"
    assert by_kw["langchain"].direction == "falling"


def test_compute_trend_slopes_handles_empty_df():
    fake_tr = MagicMock()
    fake_tr.interest_over_time.return_value = pd.DataFrame()
    slopes = compute_trend_slopes(trends=fake_tr, keywords=["x"], timeframe="today 1-m")
    assert slopes == []
