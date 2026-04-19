# src/connapse_yt/pull/reddit_cli.py
"""CLI wrapper for the Reddit pull. No auth — uses old.reddit.com public JSON.

Set REDDIT_USER_AGENT env var to identify your deployment (recommended); if
unset we fall back to a generic project user-agent.
"""
import json
from dataclasses import asdict
from pathlib import Path

import click

from . import reddit


@click.command()
@click.option("--sub", "subs", multiple=True, required=True)
@click.option("--limit", default=25, type=int)
@click.option(
    "--time-filter",
    default="day",
    type=click.Choice(["hour", "day", "week", "month", "year", "all"]),
)
@click.option(
    "--user-agent",
    envvar="REDDIT_USER_AGENT",
    default=reddit.DEFAULT_USER_AGENT,
    show_default=True,
    help="Required by Reddit; identifies your deployment in request logs.",
)
@click.option("--out", "out_path", type=click.Path(), required=True)
def main(subs, limit, time_filter, user_agent, out_path):
    posts = reddit.fetch_top_submissions(
        subreddits=list(subs),
        limit=limit,
        time_filter=time_filter,
        user_agent=user_agent,
    )
    Path(out_path).write_text(
        json.dumps([asdict(p) for p in posts], indent=2),
        encoding="utf-8",
    )
    click.echo(f"wrote {out_path}: {len(posts)} posts")


if __name__ == "__main__":
    main()
