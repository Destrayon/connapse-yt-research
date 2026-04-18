# tests/test_pull_youtube.py
import json
import re
from pathlib import Path
import httpx
import pytest
from connapse_yt.pull.youtube import search_videos, VideoSearchResult

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "youtube_search_response.json").read_text()
)


def test_search_videos_parses_items(httpx_mock):
    httpx_mock.add_response(
        url=re.compile(r".*search.*"),
        json=FIXTURE,
    )
    results = search_videos(api_key="TESTKEY", query="claude code", max_results=5)
    assert len(results) == 2
    assert isinstance(results[0], VideoSearchResult)
    assert results[0].video_id == "vid001"
    assert results[0].title.startswith("I gave Claude")
    assert results[0].channel_title == "AI Jason"


def test_search_videos_passes_api_key_and_query(httpx_mock):
    httpx_mock.add_response(json=FIXTURE)
    search_videos(api_key="TESTKEY", query="mcp server", max_results=10)
    request = httpx_mock.get_request()
    assert "key=TESTKEY" in str(request.url)
    assert "q=mcp+server" in str(request.url) or "q=mcp%20server" in str(request.url)
    assert "maxResults=10" in str(request.url)


def test_search_videos_raises_on_quota_exceeded(httpx_mock):
    httpx_mock.add_response(
        status_code=403,
        json={"error": {"code": 403, "message": "quotaExceeded"}},
    )
    with pytest.raises(httpx.HTTPStatusError):
        search_videos(api_key="TESTKEY", query="x", max_results=5)


from connapse_yt.pull.youtube import get_video_stats, VideoStats

VIDEOS_FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "youtube_videos_response.json").read_text()
)


def test_get_video_stats_returns_typed(httpx_mock):
    httpx_mock.add_response(json=VIDEOS_FIXTURE)
    stats = get_video_stats(api_key="K", video_ids=["vid001", "vid002"])
    assert len(stats) == 2
    assert isinstance(stats[0], VideoStats)
    assert stats[0].video_id == "vid001"
    assert stats[0].view_count == 184250
    assert stats[0].duration_seconds == 14 * 60 + 32


def test_get_video_stats_batches_ids(httpx_mock):
    httpx_mock.add_response(json=VIDEOS_FIXTURE)
    get_video_stats(api_key="K", video_ids=["vid001", "vid002"])
    req = httpx_mock.get_request()
    assert "id=vid001%2Cvid002" in str(req.url) or "id=vid001,vid002" in str(req.url)
