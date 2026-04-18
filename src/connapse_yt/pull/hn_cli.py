# src/connapse_yt/pull/hn_cli.py
import json
from dataclasses import asdict
from pathlib import Path

import click

from . import hn


@click.command()
@click.option("--limit", default=30)
@click.option("--out", "out_path", type=click.Path(), required=True)
def main(limit, out_path):
    stories = hn.fetch_top_stories(limit=limit)
    Path(out_path).write_text(json.dumps([asdict(s) for s in stories], indent=2))
    click.echo(f"wrote {out_path}: {len(stories)} stories")


if __name__ == "__main__":
    main()
