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


import pytest
from connapse_yt.scoring import Candidate


def test_candidate_computes_composite_from_axes():
    c = Candidate(
        text="How I gave Claude permanent memory with Connapse",
        outlier_precedent=0.8,
        trend_slope=0.6,
        pain_density=0.7,
        audience_fit=0.9,
        signup_pull=0.85,
        pillar="P1",
        cloud_compatible=True,
        promotion_surface="hosted",
        sources=["/raw/youtube/2026-04-18/trending.json#video123"],
    )
    # 0.25*0.8 + 0.15*0.6 + 0.20*0.7 + 0.15*0.9 + 0.25*0.85
    # = 0.20 + 0.09 + 0.14 + 0.135 + 0.2125 = 0.7775
    assert abs(c.composite - 0.7775) < 1e-9


def test_candidate_rejects_unknown_pillar():
    with pytest.raises(ValueError, match="pillar"):
        Candidate(
            text="x", outlier_precedent=0.5, trend_slope=0.5,
            pain_density=0.5, audience_fit=0.5, signup_pull=0.5,
            pillar="P99", cloud_compatible=True,
            promotion_surface="hosted", sources=[],
        )


def test_candidate_rejects_unknown_surface():
    with pytest.raises(ValueError, match="promotion_surface"):
        Candidate(
            text="x", outlier_precedent=0.5, trend_slope=0.5,
            pain_density=0.5, audience_fit=0.5, signup_pull=0.5,
            pillar="P1", cloud_compatible=True,
            promotion_surface="facebook", sources=[],
        )


def test_candidate_with_cloud_incompatible_routes_oss():
    """Candidate promising BYO-storage must have cloud_compatible=False
    and the routing check should flag hosted surface as mismatched."""
    c = Candidate(
        text="Point Connapse at your S3 bucket",
        outlier_precedent=0.5, trend_slope=0.5,
        pain_density=0.5, audience_fit=0.5, signup_pull=0.5,
        pillar="P3", cloud_compatible=False,
        promotion_surface="oss", sources=[],
    )
    assert c.routing_ok is True


def test_candidate_rejects_oss_capability_routed_to_hosted():
    with pytest.raises(ValueError, match="cloud_compatible"):
        Candidate(
            text="Index your S3 bucket", outlier_precedent=0.5,
            trend_slope=0.5, pain_density=0.5, audience_fit=0.5,
            signup_pull=0.5, pillar="P3", cloud_compatible=False,
            promotion_surface="hosted", sources=[],
        )
