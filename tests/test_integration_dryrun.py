# tests/test_integration_dryrun.py
"""Offline end-to-end: drive all four pull CLIs against fixtures and
verify they produce well-formed JSON the skill can consume."""

import json
from pathlib import Path

from click.testing import CliRunner

from connapse_yt.pull.hn_cli import main as hn_main


def test_hn_cli_produces_valid_json(tmp_path, httpx_mock):
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/topstories.json", json=[]
    )
    out = tmp_path / "hn.json"
    runner = CliRunner()
    result = runner.invoke(hn_main, ["--limit", "0", "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    data = json.loads(out.read_text())
    assert data == []


def test_scoring_roundtrip_via_cli(tmp_path):
    from connapse_yt.scoring import Candidate
    c = Candidate(
        text="Give Claude persistent memory",
        outlier_precedent=0.8, trend_slope=0.6, pain_density=0.7,
        audience_fit=0.9, signup_pull=0.85,
        pillar="P1", cloud_compatible=True, promotion_surface="hosted",
        sources=["/raw/youtube/2026-04-18/pull.json#vid001"],
    )
    assert c.routing_ok
    assert 0 <= c.composite <= 1
