"""Reddit pull via the public `old.reddit.com/.json` endpoint.

No authentication required — just a descriptive User-Agent. Reddit
rate-limits unauthenticated requests to roughly 60 req/min per IP and
its bot-detection layer will 403 bursty sequential requests even under
the stated limit, so we space requests out and retry with backoff.

Why not the official API? In Nov 2025 Reddit introduced the Responsible
Builder Policy (RBP) requiring manual pre-approval for all new API keys
(see https://support.reddithelp.com/hc/en-us/articles/42728983564564).
Until approval lands we scrape the public JSON view, which has served
hobby projects since 2008. Our daily volume (~8 requests/day across 8
subs) is far below any real throttling threshold.

When RBP approval arrives, swap back to praw by restoring the `praw`
dep and a `make_reddit_client(...)` factory; the `RedditPost` dataclass
and `fetch_top_submissions` signature are stable.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger(__name__)

REDDIT_JSON_BASE = "https://old.reddit.com"

DEFAULT_USER_AGENT = (
    "connapse-yt-research/0.1 "
    "(+https://github.com/Destrayon/connapse-yt-research)"
)

# Reddit's unauthenticated bot-detection 403s anything faster than ~1 req /
# 6s from a single IP. Empirically 10s between subreddits is reliable; 2s
# gets blocked by the second or third sub. For a 9-sub daily pull this
# costs ~90s, which is acceptable for a daily routine.
INTER_REQUEST_DELAY_SEC = 10.0

_VALID_TIME_FILTERS = {"hour", "day", "week", "month", "year", "all"}


@dataclass
class RedditPost:
    post_id: str
    subreddit: str
    title: str
    selftext: str
    score: int
    num_comments: int
    url: str
    created_utc: float


class RedditBlockedError(RuntimeError):
    """Reddit returned 403/429 — transient rate-limiting or bot-block."""


def _is_retryable(exc: BaseException) -> bool:
    # Retry on transient server errors and 429 rate-limiting. Do NOT retry
    # on 403 — that means Reddit's bot-detection has already decided about
    # this IP, and hammering them further only makes the block worse.
    # A 403'd sub is skipped by the outer loop.
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return isinstance(exc, (httpx.TransportError, httpx.TimeoutException))


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    reraise=True,
)
def _fetch_one(
    client: httpx.Client,
    sub: str,
    time_filter: str,
    limit: int,
    user_agent: str,
) -> list[RedditPost]:
    url = f"{REDDIT_JSON_BASE}/r/{sub}/top.json"
    params: dict[str, Any] = {"t": time_filter, "limit": limit}
    r = client.get(url, params=params, headers={"User-Agent": user_agent})
    if r.status_code in (403, 429):
        # tenacity needs an HTTPError to retry; wrap it
        r.raise_for_status()
    r.raise_for_status()

    posts: list[RedditPost] = []
    payload = r.json()
    children = (payload.get("data") or {}).get("children") or []
    for c in children:
        d = c.get("data") or {}
        posts.append(
            RedditPost(
                post_id=str(d.get("id", "")),
                subreddit=str(d.get("subreddit", sub)),
                title=str(d.get("title", "")),
                selftext=str(d.get("selftext") or ""),
                score=int(d.get("score") or 0),
                num_comments=int(d.get("num_comments") or 0),
                url=str(d.get("url") or ""),
                created_utc=float(d.get("created_utc") or 0),
            )
        )
    return posts


def fetch_top_submissions(
    *,
    http: httpx.Client | None = None,
    subreddits: list[str],
    limit: int = 25,
    time_filter: str = "day",
    user_agent: str = DEFAULT_USER_AGENT,
    inter_request_delay: float = INTER_REQUEST_DELAY_SEC,
) -> list[RedditPost]:
    """Fetch `limit` top submissions from each subreddit.

    `http` is injectable for tests so pytest-httpx can intercept. If omitted,
    a default client with a 30s timeout is created and closed per call.

    Reddit requires a descriptive User-Agent; requests without one get
    throttled aggressively or 429'd outright.

    A per-subreddit 403/429/5xx is logged and skipped so one blocked sub
    doesn't kill the whole run — the daily skill treats missing subs as
    a partial outage, not a total failure.
    """
    if time_filter not in _VALID_TIME_FILTERS:
        raise ValueError(
            f"time_filter must be one of {sorted(_VALID_TIME_FILTERS)}, "
            f"got {time_filter!r}"
        )
    if not 1 <= limit <= 100:
        raise ValueError(f"limit must be in [1, 100], got {limit}")

    owns_client = http is None
    client = http or httpx.Client(timeout=30.0, follow_redirects=True)

    out: list[RedditPost] = []
    try:
        for i, name in enumerate(subreddits):
            if i > 0 and inter_request_delay > 0:
                time.sleep(inter_request_delay)
            try:
                out.extend(_fetch_one(client, name, time_filter, limit, user_agent))
            except httpx.HTTPStatusError as e:
                log.warning(
                    "reddit pull for r/%s failed with HTTP %s; skipping",
                    name, e.response.status_code,
                )
            except httpx.HTTPError as e:
                log.warning("reddit pull for r/%s failed: %s; skipping", name, e)
    finally:
        if owns_client:
            client.close()
    return out
