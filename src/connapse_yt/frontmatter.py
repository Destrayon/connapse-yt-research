"""YAML front-matter convention for wiki / daily files (§4.2)."""

from dataclasses import dataclass, field
from typing import Optional

import frontmatter


@dataclass
class PageMetadata:
    type: str
    topic: Optional[str]
    date: str                       # ISO date or "evergreen"
    sources: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    score: Optional[float] = None
    version: Optional[int] = None
    supersedes: Optional[str] = None
    session_url: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = {
            "type": self.type,
            "topic": self.topic,
            "date": self.date,
            "sources": self.sources,
            "source_ids": self.source_ids,
            "tags": self.tags,
        }
        for k in ("score", "version", "supersedes", "session_url"):
            v = getattr(self, k)
            if v is not None:
                data[k] = v
        return data


def write_page(meta: PageMetadata, *, body: str) -> str:
    post = frontmatter.Post(body, **meta.to_dict())
    return frontmatter.dumps(post) + "\n"


def read_page(text: str) -> tuple[PageMetadata, str]:
    post = frontmatter.loads(text)
    meta = PageMetadata(
        type=post.get("type", ""),
        topic=post.get("topic"),
        date=post.get("date", ""),
        sources=list(post.get("sources", [])),
        source_ids=list(post.get("source_ids", [])),
        score=post.get("score"),
        version=post.get("version"),
        supersedes=post.get("supersedes"),
        session_url=post.get("session_url"),
        tags=list(post.get("tags", [])),
    )
    return meta, post.content
