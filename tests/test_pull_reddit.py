"""Unit tests for the old.reddit.com-based Reddit pull."""
import re

import httpx
import pytest

from connapse_yt.pull.reddit import (
    DEFAULT_USER_AGENT,
    REDDIT_JSON_BASE,
    RedditPost,
    fetch_top_submissions,
)


def _listing(children: list[dict]) -> dict:
    """Wrap items in Reddit's listing envelope."""
    return {
        "kind": "Listing",
        "data": {"children": [{"kind": "t3", "data": c} for c in children]},
    }


def _item(id_="abc", subreddit="ClaudeAI", title="Stop losing context"):
    return {
        "id": id_,
        "subreddit": subreddit,
        "title": title,
        "selftext": "body",
        "score": 120,
        "num_comments": 18,
        "url": "https://reddit.com/abc",
        "created_utc": 1_744_905_600,
    }


def _url_for(sub: str) -> re.Pattern:
    # Match the /r/<sub>/top.json endpoint regardless of query string ordering
    return re.compile(rf"^{re.escape(REDDIT_JSON_BASE)}/r/{sub}/top\.json(\?.*)?$")


# Tests use inter_request_delay=0 to keep the suite fast — the production
# 2s delay exists to avoid Reddit's burst bot-detection, which tests bypass
# via pytest-httpx.
_NO_DELAY = {"inter_request_delay": 0}


def test_fetch_top_submissions_maps_fields(httpx_mock):
    httpx_mock.add_response(
        url=_url_for("ClaudeAI"),
        json=_listing([_item(id_="a", title="t1"), _item(id_="b", title="t2")]),
    )
    with httpx.Client() as http:
        posts = fetch_top_submissions(
            http=http, subreddits=["ClaudeAI"], limit=10, time_filter="day",
            **_NO_DELAY,
        )
    assert len(posts) == 2
    assert isinstance(posts[0], RedditPost)
    assert posts[0].post_id == "a"
    assert posts[0].subreddit == "ClaudeAI"
    assert posts[0].score == 120
    assert posts[0].num_comments == 18


def test_fetch_top_submissions_iterates_multiple_subs(httpx_mock):
    for sub in ["ClaudeAI", "LLMDevs"]:
        httpx_mock.add_response(
            url=_url_for(sub),
            json=_listing([_item(id_=f"{sub}-1", subreddit=sub)]),
        )
    with httpx.Client() as http:
        posts = fetch_top_submissions(
            http=http,
            subreddits=["ClaudeAI", "LLMDevs"],
            limit=5,
            time_filter="day",
            **_NO_DELAY,
        )
    assert len(posts) == 2
    assert {p.subreddit for p in posts} == {"ClaudeAI", "LLMDevs"}


def test_fetch_top_submissions_sends_time_filter_and_limit(httpx_mock):
    httpx_mock.add_response(url=_url_for("ClaudeAI"), json=_listing([]))
    with httpx.Client() as http:
        fetch_top_submissions(
            http=http, subreddits=["ClaudeAI"], limit=7, time_filter="week",
            **_NO_DELAY,
        )
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    params = dict(requests[0].url.params)
    assert params["t"] == "week"
    assert params["limit"] == "7"


def test_fetch_top_submissions_sends_user_agent_header(httpx_mock):
    httpx_mock.add_response(url=_url_for("ClaudeAI"), json=_listing([]))
    with httpx.Client() as http:
        fetch_top_submissions(
            http=http,
            subreddits=["ClaudeAI"],
            user_agent="custom-ua/1.0 by u/somebody",
            **_NO_DELAY,
        )
    req = httpx_mock.get_requests()[0]
    assert req.headers["user-agent"] == "custom-ua/1.0 by u/somebody"


def test_fetch_top_submissions_default_user_agent(httpx_mock):
    httpx_mock.add_response(url=_url_for("ClaudeAI"), json=_listing([]))
    with httpx.Client() as http:
        fetch_top_submissions(http=http, subreddits=["ClaudeAI"], **_NO_DELAY)
    req = httpx_mock.get_requests()[0]
    assert req.headers["user-agent"] == DEFAULT_USER_AGENT


def test_fetch_top_submissions_rejects_bad_time_filter():
    with pytest.raises(ValueError, match="time_filter must be one of"):
        fetch_top_submissions(subreddits=["ClaudeAI"], time_filter="bogus")


def test_fetch_top_submissions_rejects_bad_limit():
    with pytest.raises(ValueError, match=r"limit must be in \[1, 100\]"):
        fetch_top_submissions(subreddits=["ClaudeAI"], limit=0)
    with pytest.raises(ValueError, match=r"limit must be in \[1, 100\]"):
        fetch_top_submissions(subreddits=["ClaudeAI"], limit=101)


def test_fetch_top_submissions_coerces_missing_fields(httpx_mock):
    """Reddit occasionally returns items with null fields (deleted posts etc)."""
    httpx_mock.add_response(
        url=_url_for("ClaudeAI"),
        json=_listing([{
            "id": "x",
            "subreddit": "ClaudeAI",
            "title": "t",
            "selftext": None,
            "score": None,
            "num_comments": None,
            "url": None,
        }]),
    )
    with httpx.Client() as http:
        posts = fetch_top_submissions(
            http=http, subreddits=["ClaudeAI"], limit=1, time_filter="day",
            **_NO_DELAY,
        )
    assert len(posts) == 1
    assert posts[0].selftext == ""
    assert posts[0].score == 0
    assert posts[0].num_comments == 0
    assert posts[0].url == ""
    assert posts[0].created_utc == 0.0


def test_fetch_top_submissions_empty_listing(httpx_mock):
    httpx_mock.add_response(url=_url_for("ClaudeAI"), json=_listing([]))
    with httpx.Client() as http:
        posts = fetch_top_submissions(
            http=http, subreddits=["ClaudeAI"], **_NO_DELAY,
        )
    assert posts == []


def test_fetch_top_submissions_skips_403_sub_and_continues(httpx_mock, caplog):
    """One sub being bot-blocked shouldn't kill the entire daily pull."""
    # 403 short-circuits retries — one mocked response is enough.
    httpx_mock.add_response(url=_url_for("LocalLLaMA"), status_code=403)
    httpx_mock.add_response(
        url=_url_for("ClaudeAI"),
        json=_listing([_item(id_="a", subreddit="ClaudeAI")]),
    )

    with httpx.Client() as http, caplog.at_level("WARNING"):
        posts = fetch_top_submissions(
            http=http,
            subreddits=["LocalLLaMA", "ClaudeAI"],
            **_NO_DELAY,
        )
    assert len(posts) == 1
    assert posts[0].subreddit == "ClaudeAI"
    assert any("403" in rec.message and "LocalLLaMA" in rec.message
               for rec in caplog.records)


def test_fetch_top_submissions_retries_429_with_backoff(httpx_mock, monkeypatch):
    """429 is transient rate-limiting — worth retrying with backoff."""
    monkeypatch.setattr(
        "connapse_yt.pull.reddit.wait_exponential",
        lambda **kw: __import__("tenacity").wait_none(),
    )

    httpx_mock.add_response(url=_url_for("ClaudeAI"), status_code=429)
    httpx_mock.add_response(
        url=_url_for("ClaudeAI"),
        json=_listing([_item(id_="a")]),
    )

    with httpx.Client() as http:
        posts = fetch_top_submissions(
            http=http, subreddits=["ClaudeAI"], **_NO_DELAY,
        )
    assert len(posts) == 1


def test_fetch_top_submissions_retries_transient_failure(
    httpx_mock, monkeypatch
):
    """Transient 502 → retry succeeds on second attempt."""
    monkeypatch.setattr(
        "connapse_yt.pull.reddit.wait_exponential",
        lambda **kw: __import__("tenacity").wait_none(),
    )

    # First call: 502; second call: 200
    httpx_mock.add_response(url=_url_for("ClaudeAI"), status_code=502)
    httpx_mock.add_response(
        url=_url_for("ClaudeAI"),
        json=_listing([_item(id_="a")]),
    )

    with httpx.Client() as http:
        posts = fetch_top_submissions(
            http=http, subreddits=["ClaudeAI"], **_NO_DELAY,
        )
    assert len(posts) == 1
    assert posts[0].post_id == "a"
