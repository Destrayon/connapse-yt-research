# src/connapse_yt/pull/reddit_cli.py
import json
from dataclasses import asdict
from pathlib import Path

import click

from . import reddit


@click.command()
@click.option("--client-id", envvar="REDDIT_CLIENT_ID", required=True)
@click.option("--client-secret", envvar="REDDIT_CLIENT_SECRET", required=True)
@click.option("--user-agent", envvar="REDDIT_USER_AGENT", required=True)
@click.option("--sub", "subs", multiple=True, required=True)
@click.option("--limit", default=25)
@click.option("--time-filter", default="day")
@click.option("--out", "out_path", type=click.Path(), required=True)
def main(client_id, client_secret, user_agent, subs, limit, time_filter, out_path):
    client = reddit.make_reddit_client(
        client_id=client_id, client_secret=client_secret, user_agent=user_agent
    )
    posts = reddit.fetch_top_submissions(
        reddit=client, subreddits=list(subs), limit=limit, time_filter=time_filter
    )
    Path(out_path).write_text(json.dumps([asdict(p) for p in posts], indent=2))
    click.echo(f"wrote {out_path}: {len(posts)} posts")


if __name__ == "__main__":
    main()
