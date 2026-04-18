# src/connapse_yt/pull/youtube_cli.py
"""CLI shim so the daily skill can shell out to YouTube pulls."""

import json
import sys
from dataclasses import asdict
from pathlib import Path

import click

from . import youtube


@click.command()
@click.option("--api-key", envvar="YOUTUBE_API_KEY", required=True)
@click.option("--query", multiple=True)
@click.option("--channel", "channel_ids", multiple=True)
@click.option("--max-results", default=25)
@click.option("--out", "out_path", type=click.Path(), required=True)
def main(api_key, query, channel_ids, max_results, out_path):
    results = {"search": [], "videos": []}
    seen_ids: set[str] = set()

    for q in query:
        for r in youtube.search_videos(api_key=api_key, query=q, max_results=max_results):
            if r.video_id in seen_ids:
                continue
            seen_ids.add(r.video_id)
            results["search"].append(asdict(r))

    # Channel baseline fetch (batched) — if we had channel_ids we'd pull recent uploads
    # For v1 the outlier baseline is computed from the pooled search results; channel_ids
    # are reserved for future enrichment.

    if seen_ids:
        stats = youtube.get_video_stats(api_key=api_key, video_ids=list(seen_ids))
        results["videos"] = [asdict(s) for s in stats]

    Path(out_path).write_text(json.dumps(results, indent=2))
    click.echo(f"wrote {out_path}: {len(results['search'])} search, {len(results['videos'])} videos")


if __name__ == "__main__":
    main()
