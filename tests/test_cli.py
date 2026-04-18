import json
from pathlib import Path
from click.testing import CliRunner
import pytest

pytest.importorskip("click")

from connapse_yt.cli import cli


def test_cli_plan_update_prints_ops(tmp_path):
    manifest_file = tmp_path / "_manifest.md"
    manifest_file.write_text(
        "| Topic | Version | Path |\n|---|---|---|\n"
        "| hooks/p1/cold-open | 2 | wiki/hooks/p1/cold-open.v2.md |\n"
    )
    body_file = tmp_path / "body.md"
    body_file.write_text("# new\n")

    runner = CliRunner()
    result = runner.invoke(cli, [
        "plan-update",
        "--manifest", str(manifest_file),
        "--topic", "hooks/p1/cold-open",
        "--body-file", str(body_file),
        "--frontmatter-json", '{"type": "evergreen"}',
    ])
    assert result.exit_code == 0, result.output
    ops = json.loads(result.output)
    assert ops[0]["kind"] == "upload"
    assert ops[0]["path"] == "wiki/hooks/p1/cold-open.v3.md"
