"""YouTube Data API v3 client — quota-aware, minimal surface.

Quota cost per spec §5.1:
    search.list  = 100 units
    videos.list  = 1 unit per page
    channels.list = 1 unit per page
"""

from dataclasses import dataclass
from typing import Any
import re

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


@dataclass
class VideoStats:
    video_id: str
    channel_id: str
    title: str
    view_count: int
    like_count: int
    comment_count: int
    duration_seconds: int


_ISO_DURATION = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def _parse_iso_duration(value: str) -> int:
    match = _ISO_DURATION.fullmatch(value or "")
    if not match:
        return 0
    h, m, s = (int(g) if g else 0 for g in match.groups())
    return h * 3600 + m * 60 + s


def get_video_stats(
    *,
    api_key: str,
    video_ids: list[str],
    client: httpx.Client | None = None,
) -> list[VideoStats]:
    """Batch-fetch video stats. Costs 1 quota unit per page (up to 50 ids)."""
    if not video_ids:
        return []
    close_after = client is None
    client = client or httpx.Client(timeout=30)
    try:
        resp = client.get(
            f"{API_BASE}/videos",
            params={
                "key": api_key,
                "id": ",".join(video_ids),
                "part": "snippet,statistics,contentDetails",
                "maxResults": 50,
            },
        )
        resp.raise_for_status()
        payload = resp.json()
    finally:
        if close_after:
            client.close()

    out: list[VideoStats] = []
    for item in payload.get("items", []):
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        out.append(
            VideoStats(
                video_id=item["id"],
                channel_id=snippet.get("channelId", ""),
                title=snippet.get("title", ""),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)),
                comment_count=int(stats.get("commentCount", 0)),
                duration_seconds=_parse_iso_duration(
                    item.get("contentDetails", {}).get("duration", "")
                ),
            )
        )
    return out
