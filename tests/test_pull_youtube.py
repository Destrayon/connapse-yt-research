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
