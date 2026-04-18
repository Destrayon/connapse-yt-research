"""Delete+re-upload state machine (§6).

Produces an ordered list of Connapse MCP operations. The caller
(Claude Code skill) executes them via `mcp__connapse__upload_file`,
`mcp__connapse__delete_file`, etc. The plan is deterministic and
idempotent on rerun.
"""

from dataclasses import dataclass
from typing import Literal, Any

from .manifest import Manifest
from .frontmatter import PageMetadata, write_page

OpKind = Literal["upload", "delete", "upload_manifest"]


@dataclass
class Operation:
    kind: OpKind
    path: str
    content: str = ""


def plan_update(
    *,
    manifest: Manifest,
    topic: str,
    new_body: str,
    new_frontmatter: dict[str, Any],
) -> list[Operation]:
    """Return ordered MCP operations to land a new wiki page version."""
    ops: list[Operation] = []
    existing = next((e for e in manifest.entries if e.topic == topic), None)
    new_version = (existing.current_version + 1) if existing else 1

    # Build the new file content with frontmatter
    meta_dict = dict(new_frontmatter)
    meta_dict.setdefault("version", new_version)
    if existing:
        meta_dict["supersedes"] = existing.current_path
    meta = _dict_to_metadata(meta_dict, topic=topic)
    file_text = write_page(meta, body=new_body)

    new_path = f"wiki/{topic}.v{new_version}.md"
    ops.append(Operation(kind="upload", path=new_path, content=file_text))

    if existing:
        ops.append(Operation(kind="delete", path=existing.current_path))
        archive_path = f"archive/{existing.current_path}"
        # Archived version preserves its original bytes as the skill reads them
        ops.append(Operation(kind="upload", path=archive_path, content=""))

    # Update manifest last — used as tiebreaker if preceding ops are partial
    manifest_after = _clone_and_bump(manifest, topic, new_version, new_path)
    ops.append(
        Operation(
            kind="upload_manifest",
            path="_manifest.md",
            content=manifest_after.to_markdown(),
        )
    )
    return ops


def _clone_and_bump(manifest: Manifest, topic: str, version: int, path: str) -> Manifest:
    from copy import deepcopy
    from .manifest import ManifestEntry

    cloned = deepcopy(manifest)
    entry = next((e for e in cloned.entries if e.topic == topic), None)
    if entry is None:
        cloned.entries.append(
            ManifestEntry(topic=topic, current_version=version, current_path=path)
        )
    else:
        entry.current_version = version
        entry.current_path = path
    return cloned


def _dict_to_metadata(data: dict, *, topic: str) -> PageMetadata:
    return PageMetadata(
        type=data.get("type", "evergreen"),
        topic=topic,
        date=data.get("date", "evergreen"),
        sources=data.get("sources", []),
        source_ids=data.get("source_ids", []),
        score=data.get("score"),
        version=data.get("version"),
        supersedes=data.get("supersedes"),
        session_url=data.get("session_url"),
        tags=data.get("tags", []),
    )
