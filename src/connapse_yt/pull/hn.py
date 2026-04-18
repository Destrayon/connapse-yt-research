"""Hacker News pull via Firebase JSON API. Free, no auth."""

from dataclasses import dataclass
import httpx

API_BASE = "https://hacker-news.firebaseio.com/v0"


@dataclass
class HNStory:
    id: int
    title: str
    by: str
    url: str
    score: int
    time: int
    descendants: int


def fetch_top_stories(
    *, limit: int = 30, client: httpx.Client | None = None
) -> list[HNStory]:
    close_after = client is None
    client = client or httpx.Client(timeout=30)
    try:
        ids = client.get(f"{API_BASE}/topstories.json").json()[:limit]
        out: list[HNStory] = []
        for story_id in ids:
            item = client.get(f"{API_BASE}/item/{story_id}.json").json() or {}
            if item.get("type") != "story":
                continue
            out.append(
                HNStory(
                    id=item.get("id", 0),
                    title=item.get("title", ""),
                    by=item.get("by", ""),
                    url=item.get("url", ""),
                    score=item.get("score", 0),
                    time=item.get("time", 0),
                    descendants=item.get("descendants", 0),
                )
            )
        return out
    finally:
        if close_after:
            client.close()
