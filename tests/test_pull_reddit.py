from unittest.mock import MagicMock
from connapse_yt.pull.reddit import fetch_top_submissions, RedditPost


def _fake_submission(
    id_="abc", title="Stop losing context", selftext="body", score=120, url="https://reddit.com/abc", num_comments=18, created_utc=1_744_905_600, subreddit_name="ClaudeAI"
):
    sub = MagicMock()
    sub.id = id_
    sub.title = title
    sub.selftext = selftext
    sub.score = score
    sub.url = url
    sub.num_comments = num_comments
    sub.created_utc = created_utc
    sub.subreddit.display_name = subreddit_name
    return sub


def test_fetch_top_submissions_maps_fields():
    fake_reddit = MagicMock()
    fake_sub = MagicMock()
    fake_sub.top.return_value = iter([_fake_submission(id_="a", title="t1"), _fake_submission(id_="b", title="t2")])
    fake_reddit.subreddit.return_value = fake_sub

    posts = fetch_top_submissions(
        reddit=fake_reddit, subreddits=["ClaudeAI"], limit=10, time_filter="day"
    )
    assert len(posts) == 2
    assert isinstance(posts[0], RedditPost)
    assert posts[0].post_id == "a"
    assert posts[0].subreddit == "ClaudeAI"


def test_fetch_top_submissions_iterates_multiple_subs():
    fake_reddit = MagicMock()
    fake_sub = MagicMock()
    # Use side_effect so each call to .top() returns a fresh iter (otherwise
    # the single iter is exhausted after the first subreddit).
    fake_sub.top.side_effect = lambda **kw: iter([_fake_submission()])
    fake_reddit.subreddit.return_value = fake_sub

    posts = fetch_top_submissions(
        reddit=fake_reddit, subreddits=["ClaudeAI", "LLMDevs"], limit=5, time_filter="day"
    )
    # 1 submission per sub × 2 subs = 2
    assert fake_reddit.subreddit.call_count == 2
    assert len(posts) == 2
