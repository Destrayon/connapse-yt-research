"""Reddit pull via praw. Non-commercial free tier: 100 req/min, 10k/month."""

from dataclasses import dataclass
from typing import Any


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


def fetch_top_submissions(
    *,
    reddit: Any,  # praw.Reddit, accept Any for testability
    subreddits: list[str],
    limit: int = 25,
    time_filter: str = "day",
) -> list[RedditPost]:
    """Fetch `limit` top submissions from each subreddit."""
    out: list[RedditPost] = []
    for name in subreddits:
        sub = reddit.subreddit(name)
        for submission in sub.top(time_filter=time_filter, limit=limit):
            out.append(
                RedditPost(
                    post_id=submission.id,
                    subreddit=submission.subreddit.display_name,
                    title=submission.title,
                    selftext=submission.selftext,
                    score=submission.score,
                    num_comments=submission.num_comments,
                    url=submission.url,
                    created_utc=submission.created_utc,
                )
            )
    return out


def make_reddit_client(*, client_id: str, client_secret: str, user_agent: str):
    """Factory for a read-only praw client. Imports praw lazily."""
    import praw  # noqa: WPS433 — deferred import keeps praw optional for tests
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
