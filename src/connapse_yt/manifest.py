"""Canonical current-version tracker for the wiki.

The manifest is the tiebreaker if a delete+re-upload fails mid-flight
and both versions of a page are briefly live. Stored as a markdown
table for human readability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass
class ManifestEntry:
    topic: str
    current_version: int
    current_path: str


@dataclass
class Manifest:
    entries: list[ManifestEntry] = field(default_factory=list)

    HEADER = "| Topic | Version | Path |\n|---|---|---|"

    def _find(self, topic: str) -> ManifestEntry | None:
        return next((e for e in self.entries if e.topic == topic), None)

    def bump(self, topic: str) -> str:
        """Bump (or create) a topic and return its new versioned path."""
        entry = self._find(topic)
        if entry is None:
            entry = ManifestEntry(
                topic=topic,
                current_version=1,
                current_path=f"wiki/{topic}.v1.md",
            )
            self.entries.append(entry)
            return entry.current_path
        entry.current_version += 1
        entry.current_path = f"wiki/{topic}.v{entry.current_version}.md"
        return entry.current_path

    def to_markdown(self) -> str:
        rows = [self.HEADER]
        for e in sorted(self.entries, key=lambda x: x.topic):
            rows.append(f"| {e.topic} | {e.current_version} | {e.current_path} |")
        return "\n".join(rows) + "\n"

    @classmethod
    def from_markdown(cls, text: str) -> "Manifest":
        entries: list[ManifestEntry] = []
        row_re = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*$")
        for line in text.splitlines():
            if line.startswith("| Topic ") or line.startswith("|---"):
                continue
            match = row_re.match(line)
            if match:
                entries.append(
                    ManifestEntry(
                        topic=match.group(1),
                        current_version=int(match.group(2)),
                        current_path=match.group(3),
                    )
                )
        return cls(entries=entries)
