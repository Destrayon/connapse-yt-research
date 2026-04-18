"""YouTube Data API v3 client — quota-aware, minimal surface.

Quota cost per spec §5.1:
    search.list  = 100 units
    videos.list  = 1 unit per page
    channels.list = 1 unit per page
"""

from dataclasses import dataclass
from typing import Any
import httpx

API_BASE = "https://www.googleapis.com/youtube/v3"


@dataclass
class VideoSearchResult:
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: str
    description: str


def search_videos(
    *,
    api_key: str,
    query: str,
    max_results: int = 25,
    client: httpx.Client | None = None,
) -> list[VideoSearchResult]:
    """Call YouTube Data API search.list. Costs 100 quota units per call."""
    close_after = client is None
    client = client or httpx.Client(timeout=30)
    try:
        resp = client.get(
            f"{API_BASE}/search",
            params={
                "key": api_key,
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": max_results,
            },
        )
        resp.raise_for_status()
        payload: dict[str, Any] = resp.json()
    finally:
        if close_after:
            client.close()

    results: list[VideoSearchResult] = []
    for item in payload.get("items", []):
        id_obj = item.get("id", {})
        snippet = item.get("snippet", {})
        if id_obj.get("kind") != "youtube#video":
            continue
        results.append(
            VideoSearchResult(
                video_id=id_obj["videoId"],
                title=snippet.get("title", ""),
                channel_id=snippet.get("channelId", ""),
                channel_title=snippet.get("channelTitle", ""),
                published_at=snippet.get("publishedAt", ""),
                description=snippet.get("description", ""),
            )
        )
    return results
