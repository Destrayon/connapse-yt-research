# src/connapse_yt/pull/trends_cli.py
import json
from dataclasses import asdict
from pathlib import Path

import click

from . import trends


@click.command()
@click.option("--keyword", "keywords", multiple=True, required=True)
@click.option("--timeframe", default="today 3-m")
@click.option("--out", "out_path", type=click.Path(), required=True)
def main(keywords, timeframe, out_path):
    client = trends.make_trends_client()
    slopes = trends.compute_trend_slopes(
        trends=client, keywords=list(keywords), timeframe=timeframe
    )
    Path(out_path).write_text(json.dumps([asdict(s) for s in slopes], indent=2))
    click.echo(f"wrote {out_path}: {len(slopes)} slopes")


if __name__ == "__main__":
    main()
