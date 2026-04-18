from connapse_yt.pull.hn import fetch_top_stories, HNStory


def test_fetch_top_stories_maps_fields(httpx_mock):
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/topstories.json",
        json=[11111, 22222, 33333],
    )
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/item/11111.json",
        json={
            "id": 11111, "type": "story", "title": "Show HN: Connapse",
            "by": "ana", "url": "https://github.com/Destrayon/Connapse",
            "score": 142, "time": 1_744_905_600, "descendants": 37,
        },
    )
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/item/22222.json",
        json={
            "id": 22222, "type": "story", "title": "Karpathy: LLM wikis",
            "by": "bob", "url": "https://x.com/karpathy/status/1", "score": 980,
            "time": 1_744_905_600, "descendants": 210,
        },
    )
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/item/33333.json",
        json={"id": 33333, "type": "job", "title": "Hiring"},
    )
    stories = fetch_top_stories(limit=3)
    # job items are filtered out
    assert len(stories) == 2
    assert isinstance(stories[0], HNStory)
    assert stories[0].id == 11111
    assert stories[0].title == "Show HN: Connapse"
