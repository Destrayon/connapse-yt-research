from connapse_yt.frontmatter import write_page, read_page, PageMetadata


def test_round_trip():
    meta = PageMetadata(
        type="evergreen",
        topic="hooks/p1-persistent-memory/cold-open-patterns",
        date="evergreen",
        sources=["/raw/youtube/2026-04-18/trending.json"],
        source_ids=["vid001"],
        version=3,
        supersedes="wiki/hooks/p1-persistent-memory/cold-open-patterns.v2.md",
        session_url="https://claude.ai/code/sessions/abc",
        tags=["cold-open", "p1"],
    )
    text = write_page(meta, body="# Cold-open patterns\n\nFirst line.\n")
    parsed_meta, parsed_body = read_page(text)
    assert parsed_meta == meta
    assert parsed_body.strip() == "# Cold-open patterns\n\nFirst line.".strip()


def test_score_field_optional():
    meta = PageMetadata(
        type="daily-candidates",
        topic=None,
        date="2026-04-18",
        sources=[],
        source_ids=[],
        score=0.81,
    )
    text = write_page(meta, body="- candidate 1\n")
    parsed_meta, _ = read_page(text)
    assert parsed_meta.score == 0.81
