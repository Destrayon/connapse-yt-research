from connapse_yt.scoring import composite_score

def test_composite_matches_spec_weights():
    score = composite_score(
        outlier_precedent=1.0,
        trend_slope=1.0,
        pain_density=1.0,
        audience_fit=1.0,
        signup_pull=1.0,
    )
    # Weights: 0.25 + 0.15 + 0.20 + 0.15 + 0.25 = 1.00
    assert score == 1.0

def test_composite_zero_when_all_zero():
    assert composite_score(0, 0, 0, 0, 0) == 0.0

def test_composite_weighted_mix():
    # Only outlier=1.0 → 0.25
    score = composite_score(1.0, 0, 0, 0, 0)
    assert score == 0.25

def test_composite_signup_pull_weight():
    # Only signup_pull=1.0 → 0.25
    assert composite_score(0, 0, 0, 0, 1.0) == 0.25

def test_composite_rejects_out_of_range():
    import pytest
    with pytest.raises(ValueError):
        composite_score(1.5, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        composite_score(-0.1, 0, 0, 0, 0)
