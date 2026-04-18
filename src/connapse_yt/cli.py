"""CLI entry points for Claude Code skills to shell out to."""

import json
import sys
from pathlib import Path

import click

from .manifest import Manifest
from .wiki_update import plan_update


@click.group()
def cli() -> None:
    """connapse-yt — helper CLI for the YouTube research agent."""


@cli.command("plan-update")
@click.option("--manifest", "manifest_path", type=click.Path(exists=True), required=True)
@click.option("--topic", required=True)
@click.option("--body-file", type=click.Path(exists=True), required=True)
@click.option("--frontmatter-json", required=True, help="JSON object of metadata fields")
def plan_update_cmd(manifest_path: str, topic: str, body_file: str, frontmatter_json: str):
    """Print the ordered list of MCP operations to update a wiki topic."""
    manifest = Manifest.from_markdown(Path(manifest_path).read_text())
    body = Path(body_file).read_text()
    fm = json.loads(frontmatter_json)
    ops = plan_update(
        manifest=manifest, topic=topic, new_body=body, new_frontmatter=fm
    )
    payload = [
        {"kind": op.kind, "path": op.path, "content": op.content} for op in ops
    ]
    click.echo(json.dumps(payload, indent=2))


if __name__ == "__main__":  # pragma: no cover
    cli()
