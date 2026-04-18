from connapse_yt.outlier import outlier_ratio, score_from_ratio


def test_outlier_ratio_zero_baseline():
    assert outlier_ratio(views=1000, channel_median=0) == 0.0


def test_outlier_ratio_basic():
    assert outlier_ratio(views=100_000, channel_median=10_000) == 10.0


def test_score_from_ratio_is_clipped_and_scaled():
    # ratio = 1.0 → channel-average, low outlier → score ~0
    assert score_from_ratio(1.0) < 0.1
    # ratio = 10.0 → 10x channel-average, strong outlier → score ~0.7-0.9
    assert 0.6 <= score_from_ratio(10.0) <= 1.0
    # ratio = 100.0 → capped at 1.0
    assert score_from_ratio(100.0) == 1.0
    # ratio = 0 → 0
    assert score_from_ratio(0.0) == 0.0
