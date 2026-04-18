# Connapse YouTube Research Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code Routine that runs daily, compiles a Karpathy-style wiki of YouTube idea research into a Connapse container, drives free-beta signups on connapse.com.

**Architecture:** Small Python library (deterministic HTTP pulls, scoring math, manifest management) + Claude Code skills (LLM reasoning, MCP orchestration) + a public GitHub repo Claude Code Routines clones per run. Corpus lives in a single Connapse container with three layers: `/raw/` (immutable pulls), `/wiki/` (versioned LLM-compiled topic pages), `/daily/<date>/` (run digests). Delete+re-upload versioning works around Connapse's no-edit constraint.

**Tech Stack:** Python 3.11+, pytest, `pyproject.toml` build, `requests`/`httpx`, `pytrends`, `praw` (Reddit), Claude Code skills (markdown), `.mcp.json` for Connapse HTTP MCP, GitHub for routine code, Claude Code Routines (cloud, daily schedule).

**Spec:** `docs/superpowers/specs/2026-04-18-connapse-youtube-research-agent-design.md`

---

## Prerequisites (do before Task 1)

User must have:
- Python 3.11+ installed locally (for dev + tests)
- `gh` CLI authenticated (for repo creation + pushing)
- GitHub personal account, public-repo creation enabled
- Claude Code Pro/Max plan with "Claude Code on the web" enabled (for Routines)
- Anthropic/Connapse OAuth session already linked (verified in the current session)
- A YouTube Data API v3 key (create at https://console.cloud.google.com/apis/credentials). Stash value for Task 28.
- A Reddit app (create at https://reddit.com/prefs/apps → "create app" → "script" type). Stash client ID/secret for Task 28.

These are **setup prerequisites** that need human action — do not attempt to automate account creation.

---

## Phase 0 — Repo scaffolding

### Task 1: Create local package scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.gitignore`
- Create: `src/connapse_yt/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1.1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "connapse-yt-research"
version = "0.1.0"
description = "Daily YouTube idea research agent for Connapse"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27",
  "praw>=7.7",
  "pytrends>=4.9",
  "python-frontmatter>=1.1",
  "pydantic>=2.6",
  "tenacity>=8.2",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-httpx>=0.30", "responses>=0.25", "freezegun>=1.4"]

[tool.hatch.build.targets.wheel]
packages = ["src/connapse_yt"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 1.2: Write `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
.env
dist/
build/
*.egg-info/
.coverage
htmlcov/
/raw_local/
/daily_local/
```

- [ ] **Step 1.3: Write `README.md`**

```markdown
# connapse-yt-research

Daily YouTube idea research agent for Connapse. Runs on Claude Code Routines, compiles a Karpathy-style wiki into a Connapse container, drives free-beta signups on connapse.com.

See `docs/superpowers/specs/2026-04-18-connapse-youtube-research-agent-design.md` for the full design.

## Local dev

```bash
python -m venv .venv
.venv/Scripts/activate  # Windows; use .venv/bin/activate on Unix
pip install -e ".[dev]"
pytest
```
```

- [ ] **Step 1.4: Create `src/connapse_yt/__init__.py` and `tests/__init__.py`**

Both empty files:

```python
# src/connapse_yt/__init__.py
__version__ = "0.1.0"
```

```python
# tests/__init__.py
```

- [ ] **Step 1.5: Install locally and verify**

Run: `python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"`
Expected: `Successfully installed connapse-yt-research-0.1.0 ...`

Run: `.venv/Scripts/python -m pytest`
Expected: `no tests ran` (0 collected) — confirms pytest + pythonpath config works.

- [ ] **Step 1.6: Commit**

```bash
git add pyproject.toml README.md .gitignore src tests
git commit -m "feat: python package scaffold"
```

---

### Task 2: Create public GitHub repo and push

**Files:** none (GitHub ops only)

- [ ] **Step 2.1: Create public repo**

Run: `gh repo create connapse-yt-research --public --source=. --remote=origin --description "Daily YouTube research agent for Connapse"`
Expected: `https://github.com/<user>/connapse-yt-research` printed.

- [ ] **Step 2.2: Push initial commit**

Run: `git branch -M main && git push -u origin main`
Expected: branch tracked, all commits pushed.

- [ ] **Step 2.3: Verify**

Run: `gh repo view --web` (opens in browser) — confirm README renders, repo is public.

---

## Phase 1 — Scoring module (TDD)

### Task 3: Scoring composite math

**Files:**
- Create: `src/connapse_yt/scoring.py`
- Create: `tests/test_scoring.py`

- [ ] **Step 3.1: Write failing test for composite**

```python
# tests/test_scoring.py
from connapse_yt.scoring import composite_score

def test_composite_matches_spec_weights():
    score = composite_score(
        outlier_precedent=1.0,
        trend_slope=1.0,
        pain_density=1.0,
        audience_fit=1.0,
        signup_pull=1.0,
    )
    # Weights: 0.25 + 0.15 + 0.20 + 0.15 + 0.25 = 1.00
    assert score == 1.0

def test_composite_zero_when_all_zero():
    assert composite_score(0, 0, 0, 0, 0) == 0.0

def test_composite_weighted_mix():
    # Only outlier=1.0 → 0.25
    score = composite_score(1.0, 0, 0, 0, 0)
    assert score == 0.25

def test_composite_signup_pull_weight():
    # Only signup_pull=1.0 → 0.25
    assert composite_score(0, 0, 0, 0, 1.0) == 0.25

def test_composite_rejects_out_of_range():
    import pytest
    with pytest.raises(ValueError):
        composite_score(1.5, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        composite_score(-0.1, 0, 0, 0, 0)
```

- [ ] **Step 3.2: Run the test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_scoring.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'connapse_yt.scoring'`.

- [ ] **Step 3.3: Implement minimal scoring module**

```python
# src/connapse_yt/scoring.py
"""Deterministic scoring for candidate YouTube video ideas.

Weights (§5.3 of spec):
    outlier_precedent: 0.25
    trend_slope:       0.15
    pain_density:      0.20
    audience_fit:      0.15
    signup_pull:       0.25
Sum: 1.00
"""

WEIGHTS = {
    "outlier_precedent": 0.25,
    "trend_slope": 0.15,
    "pain_density": 0.20,
    "audience_fit": 0.15,
    "signup_pull": 0.25,
}


def composite_score(
    outlier_precedent: float,
    trend_slope: float,
    pain_density: float,
    audience_fit: float,
    signup_pull: float,
) -> float:
    """Compute weighted composite score. All axes must be in [0, 1]."""
    axes = {
        "outlier_precedent": outlier_precedent,
        "trend_slope": trend_slope,
        "pain_density": pain_density,
        "audience_fit": audience_fit,
        "signup_pull": signup_pull,
    }
    for name, value in axes.items():
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1], got {value}")
    return sum(WEIGHTS[k] * v for k, v in axes.items())
```

- [ ] **Step 3.4: Run tests, verify they pass**

Run: `.venv/Scripts/python -m pytest tests/test_scoring.py -v`
Expected: `5 passed`.

- [ ] **Step 3.5: Commit**

```bash
git add src/connapse_yt/scoring.py tests/test_scoring.py
git commit -m "feat: composite scoring with weighted axes"
```

---

### Task 4: Candidate dataclass + tag validation

**Files:**
- Modify: `src/connapse_yt/scoring.py`
- Modify: `tests/test_scoring.py`

- [ ] **Step 4.1: Write failing tests for Candidate**

Append to `tests/test_scoring.py`:

```python
import pytest
from connapse_yt.scoring import Candidate


def test_candidate_computes_composite_from_axes():
    c = Candidate(
        text="How I gave Claude permanent memory with Connapse",
        outlier_precedent=0.8,
        trend_slope=0.6,
        pain_density=0.7,
        audience_fit=0.9,
        signup_pull=0.85,
        pillar="P1",
        cloud_compatible=True,
        promotion_surface="hosted",
        sources=["/raw/youtube/2026-04-18/trending.json#video123"],
    )
    # 0.25*0.8 + 0.15*0.6 + 0.20*0.7 + 0.15*0.9 + 0.25*0.85
    # = 0.20 + 0.09 + 0.14 + 0.135 + 0.2125 = 0.7775
    assert abs(c.composite - 0.7775) < 1e-9


def test_candidate_rejects_unknown_pillar():
    with pytest.raises(ValueError, match="pillar"):
        Candidate(
            text="x", outlier_precedent=0.5, trend_slope=0.5,
            pain_density=0.5, audience_fit=0.5, signup_pull=0.5,
            pillar="P99", cloud_compatible=True,
            promotion_surface="hosted", sources=[],
        )


def test_candidate_rejects_unknown_surface():
    with pytest.raises(ValueError, match="promotion_surface"):
        Candidate(
            text="x", outlier_precedent=0.5, trend_slope=0.5,
            pain_density=0.5, audience_fit=0.5, signup_pull=0.5,
            pillar="P1", cloud_compatible=True,
            promotion_surface="facebook", sources=[],
        )


def test_candidate_with_cloud_incompatible_routes_oss():
    """Candidate promising BYO-storage must have cloud_compatible=False
    and the routing check should flag hosted surface as mismatched."""
    c = Candidate(
        text="Point Connapse at your S3 bucket",
        outlier_precedent=0.5, trend_slope=0.5,
        pain_density=0.5, audience_fit=0.5, signup_pull=0.5,
        pillar="P3", cloud_compatible=False,
        promotion_surface="oss", sources=[],
    )
    assert c.routing_ok is True


def test_candidate_rejects_oss_capability_routed_to_hosted():
    with pytest.raises(ValueError, match="cloud_compatible"):
        Candidate(
            text="Index your S3 bucket", outlier_precedent=0.5,
            trend_slope=0.5, pain_density=0.5, audience_fit=0.5,
            signup_pull=0.5, pillar="P3", cloud_compatible=False,
            promotion_surface="hosted", sources=[],
        )
```

- [ ] **Step 4.2: Run the tests to see them fail**

Run: `.venv/Scripts/python -m pytest tests/test_scoring.py -v`
Expected: 5 new tests FAIL with `ImportError: cannot import name 'Candidate'`.

- [ ] **Step 4.3: Implement `Candidate`**

Append to `src/connapse_yt/scoring.py`:

```python
from dataclasses import dataclass, field
from typing import Literal

Pillar = Literal["P1", "P2", "P3"]
Surface = Literal["hosted", "oss", "both"]
VALID_PILLARS = {"P1", "P2", "P3"}
VALID_SURFACES = {"hosted", "oss", "both"}


@dataclass
class Candidate:
    """A scored YouTube video idea candidate (§5.3).

    Validation rules enforced on construction:
    - pillar ∈ {P1, P2, P3} (null rejected — off-strategy is not a candidate).
    - promotion_surface ∈ {hosted, oss, both}.
    - cloud_compatible=False may not route to the hosted surface (spec §1 routing rule).
    """

    text: str
    outlier_precedent: float
    trend_slope: float
    pain_density: float
    audience_fit: float
    signup_pull: float
    pillar: Pillar
    cloud_compatible: bool
    promotion_surface: Surface
    sources: list[str] = field(default_factory=list)
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.pillar not in VALID_PILLARS:
            raise ValueError(
                f"pillar must be one of {sorted(VALID_PILLARS)}, got {self.pillar!r}"
            )
        if self.promotion_surface not in VALID_SURFACES:
            raise ValueError(
                f"promotion_surface must be one of {sorted(VALID_SURFACES)}, "
                f"got {self.promotion_surface!r}"
            )
        if not self.cloud_compatible and self.promotion_surface == "hosted":
            raise ValueError(
                "cloud_compatible=False cannot route to promotion_surface='hosted'; "
                "use 'oss' or 'both' (and 'both' only if you reframe the hook)"
            )

    @property
    def composite(self) -> float:
        return composite_score(
            self.outlier_precedent,
            self.trend_slope,
            self.pain_density,
            self.audience_fit,
            self.signup_pull,
        )

    @property
    def routing_ok(self) -> bool:
        """True if cloud/OSS routing is internally consistent."""
        if not self.cloud_compatible and self.promotion_surface == "hosted":
            return False
        return True
```

- [ ] **Step 4.4: Run tests, verify all pass**

Run: `.venv/Scripts/python -m pytest tests/test_scoring.py -v`
Expected: `10 passed`.

- [ ] **Step 4.5: Commit**

```bash
git add src/connapse_yt/scoring.py tests/test_scoring.py
git commit -m "feat: Candidate dataclass with pillar/surface/routing validation"
```

---

## Phase 2 — Data pull scripts (TDD)

### Task 5: YouTube Data API pull

**Files:**
- Create: `src/connapse_yt/pull/youtube.py`
- Create: `src/connapse_yt/pull/__init__.py`
- Create: `tests/test_pull_youtube.py`
- Create: `tests/fixtures/youtube_search_response.json`

- [ ] **Step 5.1: Create the fixture file**

Save this as `tests/fixtures/youtube_search_response.json`:

```json
{
  "kind": "youtube#searchListResponse",
  "etag": "abc",
  "items": [
    {
      "kind": "youtube#searchResult",
      "id": {"kind": "youtube#video", "videoId": "vid001"},
      "snippet": {
        "channelId": "UC_AIJ",
        "title": "I gave Claude persistent memory and it changed everything",
        "description": "Walkthrough of an MCP-backed memory system for agents.",
        "channelTitle": "AI Jason",
        "publishedAt": "2026-04-15T12:00:00Z",
        "thumbnails": {"default": {"url": "https://i.ytimg.com/vi/vid001/default.jpg"}}
      }
    },
    {
      "kind": "youtube#searchResult",
      "id": {"kind": "youtube#video", "videoId": "vid002"},
      "snippet": {
        "channelId": "UC_IDD",
        "title": "Your CLAUDE.md is costing you money",
        "description": "Why bloated repo wikis burn Claude tokens and how to fix it.",
        "channelTitle": "IndyDevDan",
        "publishedAt": "2026-04-14T08:00:00Z",
        "thumbnails": {"default": {"url": "https://i.ytimg.com/vi/vid002/default.jpg"}}
      }
    }
  ],
  "pageInfo": {"totalResults": 2, "resultsPerPage": 50}
}
```

- [ ] **Step 5.2: Write the failing test**

```python
# tests/test_pull_youtube.py
import json
from pathlib import Path
import httpx
import pytest
from connapse_yt.pull.youtube import search_videos, VideoSearchResult

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "youtube_search_response.json").read_text()
)


def test_search_videos_parses_items(httpx_mock):
    httpx_mock.add_response(
        url__contains="search",
        json=FIXTURE,
    )
    results = search_videos(api_key="TESTKEY", query="claude code", max_results=5)
    assert len(results) == 2
    assert isinstance(results[0], VideoSearchResult)
    assert results[0].video_id == "vid001"
    assert results[0].title.startswith("I gave Claude")
    assert results[0].channel_title == "AI Jason"


def test_search_videos_passes_api_key_and_query(httpx_mock):
    httpx_mock.add_response(json=FIXTURE)
    search_videos(api_key="TESTKEY", query="mcp server", max_results=10)
    request = httpx_mock.get_request()
    assert "key=TESTKEY" in str(request.url)
    assert "q=mcp+server" in str(request.url) or "q=mcp%20server" in str(request.url)
    assert "maxResults=10" in str(request.url)


def test_search_videos_raises_on_quota_exceeded(httpx_mock):
    httpx_mock.add_response(
        status_code=403,
        json={"error": {"code": 403, "message": "quotaExceeded"}},
    )
    with pytest.raises(httpx.HTTPStatusError):
        search_videos(api_key="TESTKEY", query="x", max_results=5)
```

- [ ] **Step 5.3: Run the test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_pull_youtube.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 5.4: Implement the pull module**

```python
# src/connapse_yt/pull/__init__.py
```

```python
# src/connapse_yt/pull/youtube.py
"""YouTube Data API v3 client — quota-aware, minimal surface.

Quota cost per spec §5.1:
    search.list  = 100 units
    videos.list  = 1 unit per page
    channels.list = 1 unit per page
"""

from dataclasses import dataclass
from typing import Any
import httpx

API_BASE = "https://www.googleapis.com/youtube/v3"


@dataclass
class VideoSearchResult:
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: str
    description: str


def search_videos(
    *,
    api_key: str,
    query: str,
    max_results: int = 25,
    client: httpx.Client | None = None,
) -> list[VideoSearchResult]:
    """Call YouTube Data API search.list. Costs 100 quota units per call."""
    close_after = client is None
    client = client or httpx.Client(timeout=30)
    try:
        resp = client.get(
            f"{API_BASE}/search",
            params={
                "key": api_key,
                "q": query,
                "part": "snippet",
                "type": "video",
                "maxResults": max_results,
            },
        )
        resp.raise_for_status()
        payload: dict[str, Any] = resp.json()
    finally:
        if close_after:
            client.close()

    results: list[VideoSearchResult] = []
    for item in payload.get("items", []):
        id_obj = item.get("id", {})
        snippet = item.get("snippet", {})
        if id_obj.get("kind") != "youtube#video":
            continue
        results.append(
            VideoSearchResult(
                video_id=id_obj["videoId"],
                title=snippet.get("title", ""),
                channel_id=snippet.get("channelId", ""),
                channel_title=snippet.get("channelTitle", ""),
                published_at=snippet.get("publishedAt", ""),
                description=snippet.get("description", ""),
            )
        )
    return results
```

- [ ] **Step 5.5: Run tests, verify they pass**

Run: `.venv/Scripts/python -m pytest tests/test_pull_youtube.py -v`
Expected: `3 passed`.

- [ ] **Step 5.6: Commit**

```bash
git add src/connapse_yt/pull tests/test_pull_youtube.py tests/fixtures/youtube_search_response.json
git commit -m "feat: YouTube search.list pull with typed results"
```

---

### Task 6: YouTube videos.list (stats for outlier detection)

**Files:**
- Modify: `src/connapse_yt/pull/youtube.py`
- Modify: `tests/test_pull_youtube.py`
- Create: `tests/fixtures/youtube_videos_response.json`

- [ ] **Step 6.1: Create fixture**

Save as `tests/fixtures/youtube_videos_response.json`:

```json
{
  "kind": "youtube#videoListResponse",
  "items": [
    {
      "id": "vid001",
      "snippet": {"channelId": "UC_AIJ", "title": "I gave Claude persistent memory"},
      "statistics": {"viewCount": "184250", "likeCount": "9312", "commentCount": "521"},
      "contentDetails": {"duration": "PT14M32S"}
    },
    {
      "id": "vid002",
      "snippet": {"channelId": "UC_IDD", "title": "Your CLAUDE.md is costing you money"},
      "statistics": {"viewCount": "98117", "likeCount": "5480", "commentCount": "312"},
      "contentDetails": {"duration": "PT9M02S"}
    }
  ]
}
```

- [ ] **Step 6.2: Write failing test**

Append to `tests/test_pull_youtube.py`:

```python
from connapse_yt.pull.youtube import get_video_stats, VideoStats

VIDEOS_FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "youtube_videos_response.json").read_text()
)


def test_get_video_stats_returns_typed(httpx_mock):
    httpx_mock.add_response(json=VIDEOS_FIXTURE)
    stats = get_video_stats(api_key="K", video_ids=["vid001", "vid002"])
    assert len(stats) == 2
    assert isinstance(stats[0], VideoStats)
    assert stats[0].video_id == "vid001"
    assert stats[0].view_count == 184250
    assert stats[0].duration_seconds == 14 * 60 + 32


def test_get_video_stats_batches_ids(httpx_mock):
    httpx_mock.add_response(json=VIDEOS_FIXTURE)
    get_video_stats(api_key="K", video_ids=["vid001", "vid002"])
    req = httpx_mock.get_request()
    assert "id=vid001%2Cvid002" in str(req.url) or "id=vid001,vid002" in str(req.url)
```

- [ ] **Step 6.3: Run to confirm fail**

Run: `.venv/Scripts/python -m pytest tests/test_pull_youtube.py::test_get_video_stats_returns_typed -v`
Expected: FAIL with `ImportError: cannot import name 'get_video_stats'`.

- [ ] **Step 6.4: Implement**

Append to `src/connapse_yt/pull/youtube.py`:

```python
import re


@dataclass
class VideoStats:
    video_id: str
    channel_id: str
    title: str
    view_count: int
    like_count: int
    comment_count: int
    duration_seconds: int


_ISO_DURATION = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def _parse_iso_duration(value: str) -> int:
    match = _ISO_DURATION.fullmatch(value or "")
    if not match:
        return 0
    h, m, s = (int(g) if g else 0 for g in match.groups())
    return h * 3600 + m * 60 + s


def get_video_stats(
    *,
    api_key: str,
    video_ids: list[str],
    client: httpx.Client | None = None,
) -> list[VideoStats]:
    """Batch-fetch video stats. Costs 1 quota unit per page (up to 50 ids)."""
    if not video_ids:
        return []
    close_after = client is None
    client = client or httpx.Client(timeout=30)
    try:
        resp = client.get(
            f"{API_BASE}/videos",
            params={
                "key": api_key,
                "id": ",".join(video_ids),
                "part": "snippet,statistics,contentDetails",
                "maxResults": 50,
            },
        )
        resp.raise_for_status()
        payload = resp.json()
    finally:
        if close_after:
            client.close()

    out: list[VideoStats] = []
    for item in payload.get("items", []):
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})
        out.append(
            VideoStats(
                video_id=item["id"],
                channel_id=snippet.get("channelId", ""),
                title=snippet.get("title", ""),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)),
                comment_count=int(stats.get("commentCount", 0)),
                duration_seconds=_parse_iso_duration(
                    item.get("contentDetails", {}).get("duration", "")
                ),
            )
        )
    return out
```

- [ ] **Step 6.5: Run tests, verify pass**

Run: `.venv/Scripts/python -m pytest tests/test_pull_youtube.py -v`
Expected: `5 passed`.

- [ ] **Step 6.6: Commit**

```bash
git add src/connapse_yt/pull/youtube.py tests/test_pull_youtube.py tests/fixtures/youtube_videos_response.json
git commit -m "feat: YouTube videos.list stats fetch with duration parsing"
```

---

### Task 7: Outlier-ratio computation

**Files:**
- Create: `src/connapse_yt/outlier.py`
- Create: `tests/test_outlier.py`

- [ ] **Step 7.1: Write failing test**

```python
# tests/test_outlier.py
from connapse_yt.outlier import outlier_ratio, score_from_ratio


def test_outlier_ratio_zero_baseline():
    assert outlier_ratio(views=1000, channel_median=0) == 0.0


def test_outlier_ratio_basic():
    assert outlier_ratio(views=100_000, channel_median=10_000) == 10.0


def test_score_from_ratio_is_clipped_and_scaled():
    # ratio = 1.0 → channel-average, low outlier → score ~0
    assert score_from_ratio(1.0) < 0.1
    # ratio = 10.0 → 10x channel-average, strong outlier → score ~0.7-0.9
    assert 0.6 <= score_from_ratio(10.0) <= 1.0
    # ratio = 100.0 → capped at 1.0
    assert score_from_ratio(100.0) == 1.0
    # ratio = 0 → 0
    assert score_from_ratio(0.0) == 0.0
```

- [ ] **Step 7.2: Run the test**

Run: `.venv/Scripts/python -m pytest tests/test_outlier.py -v`
Expected: FAIL (module missing).

- [ ] **Step 7.3: Implement**

```python
# src/connapse_yt/outlier.py
"""Outlier detection: view count vs. channel baseline."""

import math


def outlier_ratio(*, views: int, channel_median: float) -> float:
    if channel_median <= 0:
        return 0.0
    return views / channel_median


def score_from_ratio(ratio: float) -> float:
    """Map an outlier ratio to a [0, 1] score.

    Uses log2 so each doubling above the channel median adds roughly 0.1.
    - ratio ≤ 1 → near-zero score
    - ratio = 2 → 0.1
    - ratio = 10 → ~0.7-0.9
    - ratio ≥ 32 → 1.0 (capped)
    """
    if ratio <= 1.0:
        return 0.0
    score = math.log2(ratio) / 5.0  # log2(32) = 5 → score=1.0
    return min(1.0, score)
```

- [ ] **Step 7.4: Run tests, verify pass**

Run: `.venv/Scripts/python -m pytest tests/test_outlier.py -v`
Expected: `3 passed`.

- [ ] **Step 7.5: Commit**

```bash
git add src/connapse_yt/outlier.py tests/test_outlier.py
git commit -m "feat: outlier-ratio scoring with log2 scaling"
```

---

### Task 8: Reddit pull (praw)

**Files:**
- Create: `src/connapse_yt/pull/reddit.py`
- Create: `tests/test_pull_reddit.py`

- [ ] **Step 8.1: Write failing test with mock praw**

```python
# tests/test_pull_reddit.py
from unittest.mock import MagicMock
from connapse_yt.pull.reddit import fetch_top_submissions, RedditPost


def _fake_submission(
    id_="abc", title="Stop losing context", selftext="body", score=120, url="https://reddit.com/abc", num_comments=18, created_utc=1_744_905_600, subreddit_name="ClaudeAI"
):
    sub = MagicMock()
    sub.id = id_
    sub.title = title
    sub.selftext = selftext
    sub.score = score
    sub.url = url
    sub.num_comments = num_comments
    sub.created_utc = created_utc
    sub.subreddit.display_name = subreddit_name
    return sub


def test_fetch_top_submissions_maps_fields():
    fake_reddit = MagicMock()
    fake_sub = MagicMock()
    fake_sub.top.return_value = iter([_fake_submission(id_="a", title="t1"), _fake_submission(id_="b", title="t2")])
    fake_reddit.subreddit.return_value = fake_sub

    posts = fetch_top_submissions(
        reddit=fake_reddit, subreddits=["ClaudeAI"], limit=10, time_filter="day"
    )
    assert len(posts) == 2
    assert isinstance(posts[0], RedditPost)
    assert posts[0].post_id == "a"
    assert posts[0].subreddit == "ClaudeAI"


def test_fetch_top_submissions_iterates_multiple_subs():
    fake_reddit = MagicMock()
    fake_sub = MagicMock()
    fake_sub.top.return_value = iter([_fake_submission()])
    fake_reddit.subreddit.return_value = fake_sub

    posts = fetch_top_submissions(
        reddit=fake_reddit, subreddits=["ClaudeAI", "LLMDevs"], limit=5, time_filter="day"
    )
    # 1 submission per sub × 2 subs = 2
    assert fake_reddit.subreddit.call_count == 2
    assert len(posts) == 2
```

- [ ] **Step 8.2: Run to see it fail**

Run: `.venv/Scripts/python -m pytest tests/test_pull_reddit.py -v`
Expected: FAIL (module missing).

- [ ] **Step 8.3: Implement**

```python
# src/connapse_yt/pull/reddit.py
"""Reddit pull via praw. Non-commercial free tier: 100 req/min, 10k/month."""

from dataclasses import dataclass
from typing import Any


@dataclass
class RedditPost:
    post_id: str
    subreddit: str
    title: str
    selftext: str
    score: int
    num_comments: int
    url: str
    created_utc: float


def fetch_top_submissions(
    *,
    reddit: Any,  # praw.Reddit, accept Any for testability
    subreddits: list[str],
    limit: int = 25,
    time_filter: str = "day",
) -> list[RedditPost]:
    """Fetch `limit` top submissions from each subreddit."""
    out: list[RedditPost] = []
    for name in subreddits:
        sub = reddit.subreddit(name)
        for submission in sub.top(time_filter=time_filter, limit=limit):
            out.append(
                RedditPost(
                    post_id=submission.id,
                    subreddit=submission.subreddit.display_name,
                    title=submission.title,
                    selftext=submission.selftext,
                    score=submission.score,
                    num_comments=submission.num_comments,
                    url=submission.url,
                    created_utc=submission.created_utc,
                )
            )
    return out


def make_reddit_client(*, client_id: str, client_secret: str, user_agent: str):
    """Factory for a read-only praw client. Imports praw lazily."""
    import praw  # noqa: WPS433 — deferred import keeps praw optional for tests
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
```

- [ ] **Step 8.4: Run tests, verify pass**

Run: `.venv/Scripts/python -m pytest tests/test_pull_reddit.py -v`
Expected: `2 passed`.

- [ ] **Step 8.5: Commit**

```bash
git add src/connapse_yt/pull/reddit.py tests/test_pull_reddit.py
git commit -m "feat: Reddit top-submissions pull via praw"
```

---

### Task 9: Hacker News pull (Firebase)

**Files:**
- Create: `src/connapse_yt/pull/hn.py`
- Create: `tests/test_pull_hn.py`

- [ ] **Step 9.1: Write failing test**

```python
# tests/test_pull_hn.py
from connapse_yt.pull.hn import fetch_top_stories, HNStory


def test_fetch_top_stories_maps_fields(httpx_mock):
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/topstories.json",
        json=[11111, 22222, 33333],
    )
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/item/11111.json",
        json={
            "id": 11111, "type": "story", "title": "Show HN: Connapse",
            "by": "ana", "url": "https://github.com/Destrayon/Connapse",
            "score": 142, "time": 1_744_905_600, "descendants": 37,
        },
    )
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/item/22222.json",
        json={
            "id": 22222, "type": "story", "title": "Karpathy: LLM wikis",
            "by": "bob", "url": "https://x.com/karpathy/status/1", "score": 980,
            "time": 1_744_905_600, "descendants": 210,
        },
    )
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/item/33333.json",
        json={"id": 33333, "type": "job", "title": "Hiring"},
    )
    stories = fetch_top_stories(limit=3)
    # job items are filtered out
    assert len(stories) == 2
    assert isinstance(stories[0], HNStory)
    assert stories[0].id == 11111
    assert stories[0].title == "Show HN: Connapse"
```

- [ ] **Step 9.2: Run, confirm fail**

Run: `.venv/Scripts/python -m pytest tests/test_pull_hn.py -v`
Expected: FAIL.

- [ ] **Step 9.3: Implement**

```python
# src/connapse_yt/pull/hn.py
"""Hacker News pull via Firebase JSON API. Free, no auth."""

from dataclasses import dataclass
import httpx

API_BASE = "https://hacker-news.firebaseio.com/v0"


@dataclass
class HNStory:
    id: int
    title: str
    by: str
    url: str
    score: int
    time: int
    descendants: int


def fetch_top_stories(
    *, limit: int = 30, client: httpx.Client | None = None
) -> list[HNStory]:
    close_after = client is None
    client = client or httpx.Client(timeout=30)
    try:
        ids = client.get(f"{API_BASE}/topstories.json").json()[:limit]
        out: list[HNStory] = []
        for story_id in ids:
            item = client.get(f"{API_BASE}/item/{story_id}.json").json() or {}
            if item.get("type") != "story":
                continue
            out.append(
                HNStory(
                    id=item.get("id", 0),
                    title=item.get("title", ""),
                    by=item.get("by", ""),
                    url=item.get("url", ""),
                    score=item.get("score", 0),
                    time=item.get("time", 0),
                    descendants=item.get("descendants", 0),
                )
            )
        return out
    finally:
        if close_after:
            client.close()
```

- [ ] **Step 9.4: Run, verify pass**

Run: `.venv/Scripts/python -m pytest tests/test_pull_hn.py -v`
Expected: `1 passed`.

- [ ] **Step 9.5: Commit**

```bash
git add src/connapse_yt/pull/hn.py tests/test_pull_hn.py
git commit -m "feat: Hacker News top-stories pull via Firebase API"
```

---

### Task 10: pytrends wrapper

**Files:**
- Create: `src/connapse_yt/pull/trends.py`
- Create: `tests/test_pull_trends.py`

- [ ] **Step 10.1: Write failing test**

```python
# tests/test_pull_trends.py
from unittest.mock import MagicMock
import pandas as pd
from connapse_yt.pull.trends import compute_trend_slopes, TrendSlope


def test_compute_trend_slopes_computes_direction():
    fake_tr = MagicMock()
    df = pd.DataFrame(
        {
            "claude code": [10, 20, 30, 50, 80, 100, 140],
            "langchain": [100, 90, 80, 70, 60, 50, 40],
            "isPartial": [False] * 7,
        }
    )
    fake_tr.interest_over_time.return_value = df

    slopes = compute_trend_slopes(
        trends=fake_tr, keywords=["claude code", "langchain"], timeframe="today 3-m"
    )
    assert len(slopes) == 2
    by_kw = {s.keyword: s for s in slopes}
    assert isinstance(by_kw["claude code"], TrendSlope)
    assert by_kw["claude code"].direction == "rising"
    assert by_kw["langchain"].direction == "falling"


def test_compute_trend_slopes_handles_empty_df():
    fake_tr = MagicMock()
    fake_tr.interest_over_time.return_value = pd.DataFrame()
    slopes = compute_trend_slopes(trends=fake_tr, keywords=["x"], timeframe="today 1-m")
    assert slopes == []
```

- [ ] **Step 10.2: Run, confirm fail**

Run: `.venv/Scripts/python -m pytest tests/test_pull_trends.py -v`
Expected: FAIL.

- [ ] **Step 10.3: Implement**

```python
# src/connapse_yt/pull/trends.py
"""Google Trends slopes via pytrends."""

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

Direction = Literal["rising", "flat", "falling"]


@dataclass
class TrendSlope:
    keyword: str
    slope: float  # linear-regression slope across the timeframe
    direction: Direction
    score: float  # [0, 1], rising=positive slope mapped to higher score


def _direction(slope: float) -> Direction:
    if slope > 1.0:
        return "rising"
    if slope < -1.0:
        return "falling"
    return "flat"


def _score(slope: float) -> float:
    # Slopes in pytrends are noisy; clamp to +/- 10 → [0, 1].
    import math
    clipped = max(-10.0, min(10.0, slope))
    return (clipped + 10.0) / 20.0


def compute_trend_slopes(
    *,
    trends: Any,  # pytrends TrendReq, Any for testability
    keywords: list[str],
    timeframe: str = "today 3-m",
) -> list[TrendSlope]:
    if not keywords:
        return []
    trends.build_payload(keywords, timeframe=timeframe)
    df: pd.DataFrame = trends.interest_over_time()
    if df is None or df.empty:
        return []
    out: list[TrendSlope] = []
    x = list(range(len(df.index)))
    for kw in keywords:
        if kw not in df.columns:
            continue
        series = df[kw].astype(float).tolist()
        slope = _linear_slope(x, series)
        out.append(
            TrendSlope(
                keyword=kw,
                slope=slope,
                direction=_direction(slope),
                score=_score(slope),
            )
        )
    return out


def _linear_slope(xs: list[int], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    return num / den if den else 0.0


def make_trends_client(*, hl: str = "en-US", tz: int = 360):
    """Deferred import so pytrends stays optional for unit tests."""
    from pytrends.request import TrendReq  # noqa: WPS433
    return TrendReq(hl=hl, tz=tz)
```

- [ ] **Step 10.4: Run, verify pass**

Run: `.venv/Scripts/python -m pytest tests/test_pull_trends.py -v`
Expected: `2 passed`.

- [ ] **Step 10.5: Commit**

```bash
git add src/connapse_yt/pull/trends.py tests/test_pull_trends.py
git commit -m "feat: pytrends slope computation with direction scoring"
```

---

## Phase 3 — Wiki helpers (manifest, versioning)

### Task 11: Manifest read/write

**Files:**
- Create: `src/connapse_yt/manifest.py`
- Create: `tests/test_manifest.py`

- [ ] **Step 11.1: Write failing test**

```python
# tests/test_manifest.py
from connapse_yt.manifest import Manifest, ManifestEntry


def test_manifest_round_trips():
    m = Manifest(
        entries=[
            ManifestEntry(topic="hooks/p1-persistent-memory/cold-open-patterns",
                          current_version=3, current_path="wiki/hooks/p1-persistent-memory/cold-open-patterns.v3.md"),
            ManifestEntry(topic="strategy/positioning-theses",
                          current_version=5, current_path="wiki/strategy/positioning-theses.v5.md"),
        ]
    )
    rendered = m.to_markdown()
    parsed = Manifest.from_markdown(rendered)
    assert parsed == m


def test_manifest_bump_version():
    m = Manifest(entries=[
        ManifestEntry(topic="hooks/p1/cold-open",
                      current_version=2,
                      current_path="wiki/hooks/p1/cold-open.v2.md"),
    ])
    new_path = m.bump("hooks/p1/cold-open")
    assert new_path == "wiki/hooks/p1/cold-open.v3.md"
    assert m.entries[0].current_version == 3
    assert m.entries[0].current_path == "wiki/hooks/p1/cold-open.v3.md"


def test_manifest_add_new_topic_if_missing():
    m = Manifest(entries=[])
    path = m.bump("hooks/p1/new-pattern")
    assert path == "wiki/hooks/p1/new-pattern.v1.md"
    assert len(m.entries) == 1
    assert m.entries[0].current_version == 1
```

- [ ] **Step 11.2: Run, confirm fail**

Run: `.venv/Scripts/python -m pytest tests/test_manifest.py -v`
Expected: FAIL.

- [ ] **Step 11.3: Implement**

```python
# src/connapse_yt/manifest.py
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
```

- [ ] **Step 11.4: Run, verify pass**

Run: `.venv/Scripts/python -m pytest tests/test_manifest.py -v`
Expected: `3 passed`.

- [ ] **Step 11.5: Commit**

```bash
git add src/connapse_yt/manifest.py tests/test_manifest.py
git commit -m "feat: manifest tracker with markdown round-trip + bump"
```

---

### Task 12: Front-matter helpers

**Files:**
- Create: `src/connapse_yt/frontmatter.py`
- Create: `tests/test_frontmatter.py`

- [ ] **Step 12.1: Write failing test**

```python
# tests/test_frontmatter.py
from connapse_yt.frontmatter import write_page, read_page, PageMetadata


def test_round_trip():
    meta = PageMetadata(
        type="evergreen",
        topic="hooks/p1-persistent-memory/cold-open-patterns",
        date="evergreen",
        sources=["/raw/youtube/2026-04-18/trending.json"],
        source_ids=["vid001"],
        version=3,
        supersedes="wiki/hooks/p1-persistent-memory/cold-open-patterns.v2.md",
        session_url="https://claude.ai/code/sessions/abc",
        tags=["cold-open", "p1"],
    )
    text = write_page(meta, body="# Cold-open patterns\n\nFirst line.\n")
    parsed_meta, parsed_body = read_page(text)
    assert parsed_meta == meta
    assert parsed_body.strip() == "# Cold-open patterns\n\nFirst line.".strip()


def test_score_field_optional():
    meta = PageMetadata(
        type="daily-candidates",
        topic=None,
        date="2026-04-18",
        sources=[],
        source_ids=[],
        score=0.81,
    )
    text = write_page(meta, body="- candidate 1\n")
    parsed_meta, _ = read_page(text)
    assert parsed_meta.score == 0.81
```

- [ ] **Step 12.2: Run, confirm fail**

Run: `.venv/Scripts/python -m pytest tests/test_frontmatter.py -v`
Expected: FAIL.

- [ ] **Step 12.3: Implement**

```python
# src/connapse_yt/frontmatter.py
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
```

- [ ] **Step 12.4: Run, verify pass**

Run: `.venv/Scripts/python -m pytest tests/test_frontmatter.py -v`
Expected: `2 passed`.

- [ ] **Step 12.5: Commit**

```bash
git add src/connapse_yt/frontmatter.py tests/test_frontmatter.py
git commit -m "feat: YAML front-matter read/write with typed metadata"
```

---

### Task 13: Wiki update operation plan

**Files:**
- Create: `src/connapse_yt/wiki_update.py`
- Create: `tests/test_wiki_update.py`

- [ ] **Step 13.1: Write failing test**

```python
# tests/test_wiki_update.py
from connapse_yt.manifest import Manifest, ManifestEntry
from connapse_yt.wiki_update import plan_update, Operation


def test_plan_update_existing_topic_produces_four_ops():
    m = Manifest(entries=[
        ManifestEntry(
            topic="hooks/p1/cold-open",
            current_version=2,
            current_path="wiki/hooks/p1/cold-open.v2.md",
        ),
    ])
    ops = plan_update(
        manifest=m,
        topic="hooks/p1/cold-open",
        new_body="# v3\n\nUpdated body.\n",
        new_frontmatter={"type": "evergreen", "version": 3},
    )
    kinds = [op.kind for op in ops]
    # upload new, delete old, archive old (upload to /archive/), update manifest
    assert kinds == ["upload", "delete", "upload", "upload_manifest"]

    upload_new = ops[0]
    assert upload_new.path == "wiki/hooks/p1/cold-open.v3.md"
    assert "# v3" in upload_new.content

    delete_old = ops[1]
    assert delete_old.path == "wiki/hooks/p1/cold-open.v2.md"

    archive = ops[2]
    assert archive.path == "archive/wiki/hooks/p1/cold-open.v2.md"


def test_plan_update_new_topic_has_no_delete():
    m = Manifest(entries=[])
    ops = plan_update(
        manifest=m,
        topic="hooks/p2/token-cost",
        new_body="# v1\n",
        new_frontmatter={"type": "evergreen", "version": 1},
    )
    kinds = [op.kind for op in ops]
    assert "delete" not in kinds
    # new uploads new version + manifest, no archive step
    assert kinds == ["upload", "upload_manifest"]
```

- [ ] **Step 13.2: Run, confirm fail**

Run: `.venv/Scripts/python -m pytest tests/test_wiki_update.py -v`
Expected: FAIL.

- [ ] **Step 13.3: Implement**

```python
# src/connapse_yt/wiki_update.py
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
```

- [ ] **Step 13.4: Run tests, verify pass**

Run: `.venv/Scripts/python -m pytest tests/test_wiki_update.py -v`
Expected: `2 passed`.

- [ ] **Step 13.5: Commit**

```bash
git add src/connapse_yt/wiki_update.py tests/test_wiki_update.py
git commit -m "feat: delete+re-upload planner produces idempotent MCP op list"
```

---

### Task 14: CLI entry points (`pull` + `plan-update`)

**Files:**
- Create: `src/connapse_yt/cli.py`
- Modify: `pyproject.toml`
- Create: `tests/test_cli.py`

- [ ] **Step 14.1: Write failing test**

```python
# tests/test_cli.py
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
```

- [ ] **Step 14.2: Add `click` to dependencies**

Edit `pyproject.toml` — append to `[project].dependencies`:

```toml
  "click>=8.1",
```

Then: `.venv/Scripts/python -m pip install -e ".[dev]"`

- [ ] **Step 14.3: Run, confirm fail**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py -v`
Expected: FAIL (module missing).

- [ ] **Step 14.4: Implement CLI**

```python
# src/connapse_yt/cli.py
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
```

Edit `pyproject.toml` — add:

```toml
[project.scripts]
connapse-yt = "connapse_yt.cli:cli"
```

Reinstall: `.venv/Scripts/python -m pip install -e ".[dev]"`

- [ ] **Step 14.5: Run tests, verify pass**

Run: `.venv/Scripts/python -m pytest tests/test_cli.py -v`
Expected: `1 passed`.

- [ ] **Step 14.6: Commit**

```bash
git add src/connapse_yt/cli.py tests/test_cli.py pyproject.toml
git commit -m "feat: CLI entry with plan-update command"
```

---

## Phase 4 — Claude Code skills & MCP config

### Task 15: `.mcp.json` for Connapse

**Files:**
- Create: `.mcp.json`

- [ ] **Step 15.1: Write `.mcp.json`**

```json
{
  "mcpServers": {
    "connapse": {
      "type": "http",
      "url": "https://www.connapse.com/khastra/mcp"
    }
  }
}
```

- [ ] **Step 15.2: Commit**

```bash
git add .mcp.json
git commit -m "feat: declare Connapse HTTP MCP for routine"
```

---

### Task 16: Routine `CLAUDE.md`

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 16.1: Write `CLAUDE.md`**

```markdown
# connapse-yt-research — Routine Operating Manual

You are a daily research agent that compiles a Karpathy-style wiki into a Connapse container to drive free-beta signups at https://www.connapse.com/.

## Every invocation

1. Determine which skill to run based on the trigger context:
   - Daily schedule trigger → run `yt-research-daily` skill.
   - Weekly (Sunday) schedule trigger → run `positioning-synthesis` then `wiki-lint`.
   - Manual / API trigger with a passed prompt → follow the prompt; if it references a skill by name, invoke that skill.

2. The single Connapse container you write to is named `connapse-youtube-research`. Resolve its `containerId` via `mcp__connapse__container_list` on first use; cache it in `/tmp/container_id` for the rest of the session.

3. Before doing anything, verify Connapse connectivity with `mcp__connapse__container_list`. If it errors, abort with a stub `/daily/<date>/summary.md` noting the outage.

## Writing to Connapse

- Always use YAML front-matter per `src/connapse_yt/frontmatter.py` convention.
- For wiki-page updates, shell out to `connapse-yt plan-update ...` to get an ordered list of MCP operations, then execute each one: `upload` → `delete` → `upload` (archive) → `upload_manifest`.
- `/_manifest.md` is the canonical current-version tiebreaker. Always read it first; always rewrite it last.
- Stamp `$CLAUDE_CODE_REMOTE_SESSION_ID` into every uploaded file's `session_url:` front-matter field.

## Positioning pillars (§1.1 of spec)

Every candidate idea has a `pillar: P1 | P2 | P3` tag. Hooks lead with exactly one pillar:
- P1 = persistent memory across AI sessions
- P2 = context / token / cost optimization at scale
- P3 = file search for agents

Every candidate also has `cloud_compatible` and `promotion_surface`. If `cloud_compatible=False` and `promotion_surface=hosted` → reject (mis-routed). See §1 routing table.

## Audience + surface

Target audience v1: Claude Code users + agentic-dev power users. Primary CTA: connapse.com free-beta signup. Secondary: star / clone Destrayon/Connapse.

## Abort conditions

- Connapse unreachable → stub summary, exit 0 (not 1; routine must not look failed).
- 2+ data sources unreachable → stub, exit 0.
- YouTube quota ≥80% used → skip `search.list` this run; next run falls back to channel-ID cache.
```

- [ ] **Step 16.2: Commit**

```bash
git add CLAUDE.md
git commit -m "feat: routine operating manual"
```

---

### Task 17: `yt-research-daily` skill

**Files:**
- Create: `.claude/skills/yt-research-daily/SKILL.md`

- [ ] **Step 17.1: Write the skill**

```markdown
---
name: yt-research-daily
description: Daily YouTube idea research pipeline — pull free-tier signals, score, dedup, write daily folder, promote recurring ideas to wiki.
---

# Daily research pipeline

Work through these phases in order. Each phase commits its own artifacts.

## 0. Setup

- `export RUN_DATE=$(date -u +%Y-%m-%d)`
- Resolve and cache containerId (see CLAUDE.md §Every invocation).
- `mkdir -p /tmp/run/$RUN_DATE` and use this as the local staging area before uploading.

## 1. Pull

Shell out in this order (deterministic, no LLM reasoning):

```bash
python -m connapse_yt.pull.youtube_cli \
  --api-key "$YOUTUBE_API_KEY" \
  --query "claude code mcp" --query "agent memory rag" \
  --channel UC_AIJ --channel UC_IDD --channel UC_COLEMEDIN \
  --out /tmp/run/$RUN_DATE/youtube.json

python -m connapse_yt.pull.reddit_cli \
  --client-id "$REDDIT_CLIENT_ID" --client-secret "$REDDIT_CLIENT_SECRET" \
  --user-agent "$REDDIT_USER_AGENT" \
  --sub ClaudeAI --sub ClaudeCode --sub AI_Agents --sub LLMDevs \
  --sub LangChain --sub LocalLLaMA --sub mcp --sub cursor --sub SideProject \
  --out /tmp/run/$RUN_DATE/reddit.json

python -m connapse_yt.pull.hn_cli \
  --out /tmp/run/$RUN_DATE/hn.json

python -m connapse_yt.pull.trends_cli \
  --keyword "claude code" --keyword "mcp server" --keyword "rag" \
  --keyword "agent memory" --keyword "connapse" \
  --out /tmp/run/$RUN_DATE/trends.json
```

If any pull fails, log it to `/tmp/run/$RUN_DATE/errors.log` and continue with available sources. If ≥2 fail, abort per CLAUDE.md.

Then upload each raw JSON via `mcp__connapse__upload_file`:
- `/raw/youtube/$RUN_DATE/pull.json`
- `/raw/reddit/$RUN_DATE/pull.json`
- `/raw/hn/$RUN_DATE/pull.json`
- `/raw/trends/$RUN_DATE/pull.json`

## 2. Extract

Read each JSON locally. Produce `/tmp/run/$RUN_DATE/observations.md` — a markdown list of notable items:
- outlier videos (view ratio ≥10× channel median)
- Reddit threads with ≥100 upvotes in a target sub
- HN front-page stories about Claude/MCP/RAG/agent topics
- trend keywords with direction=rising

For each observation, include source path (e.g., `/raw/youtube/2026-04-18/pull.json#vid001`).

## 3. Candidates

From the observations, generate 8-15 candidate video ideas. For each:

1. Decide which **single pillar** (P1/P2/P3, per CLAUDE.md) the hook leads with.
2. Score the 3 deterministic axes using helpers:
   - `outlier_precedent`: `python -c "from connapse_yt.outlier import score_from_ratio; print(score_from_ratio(<ratio>))"`
   - `trend_slope`: from `trends.json` for the relevant keyword
   - `pain_density`: count distinct Reddit/HN threads citing the pain (integer → divide by 5, cap at 1.0)
3. Score `audience_fit` and `signup_pull` yourself (LLM judgment, with rationale).
4. Decide `cloud_compatible` (true unless the hook requires S3/Azure/FS connectors).
5. Decide `promotion_surface` (hosted | oss | both). Enforce the routing rule from §1.
6. If `cloud_compatible=False` and `promotion_surface=hosted` → reject or reframe before including.

Write `/tmp/run/$RUN_DATE/candidates.md` with a YAML header block per candidate.

## 4. Dedup vs. wiki

For each candidate, call `mcp__connapse__search_knowledge`:

```
search_knowledge(
  containerId=<cached>,
  query=<candidate text>,
  path="/wiki/",
  mode="hybrid",
  topK=3,
  minScore=0.05,
)
```

If top result has score ≥0.82, the candidate is a **dedup hit**:
- Read that wiki page via `mcp__connapse__get_document`.
- Append a dated observation to its `## Evidence` section.
- Shell out: `connapse-yt plan-update --manifest <local> --topic <topic> --body-file <updated> --frontmatter-json '{"type":"evergreen"}'`
- Execute the returned ops via MCP.

## 5. Promote recurring ideas

- Read the last 14 `/daily/*/candidates.md` files.
- For each candidate text appearing in ≥3 different days, promote to wiki:
  - Synthesize an evergreen page.
  - Use `connapse-yt plan-update` to produce ops, execute them.

## 6. Write daily digest

Upload:
- `/daily/$RUN_DATE/summary.md` — what changed, what's new, which candidates promoted.
- `/daily/$RUN_DATE/candidates.md` — full scored list.
- `/daily/$RUN_DATE/observations.md` — raw highlights.

## 7. Append to log

Read `/wiki/log.md`, append a line:

```
- 2026-04-18: sources=youtube,reddit,hn,trends; candidates=12; promoted=1; session=<URL>
```

Re-upload `/wiki/log.md` (delete+re-upload via `plan-update`).

## 8. Regenerate index

Read `/_manifest.md`. Generate a fresh `/wiki/index.md` TOC grouped by topic folder. Upload (delete+re-upload).

Exit 0.
```

- [ ] **Step 17.2: Commit**

```bash
git add .claude/skills/yt-research-daily/SKILL.md
git commit -m "feat: daily research skill orchestrating pull → score → dedup → write"
```

---

### Task 18: Add pull-script CLI wrappers

**Files:**
- Create: `src/connapse_yt/pull/youtube_cli.py`
- Create: `src/connapse_yt/pull/reddit_cli.py`
- Create: `src/connapse_yt/pull/hn_cli.py`
- Create: `src/connapse_yt/pull/trends_cli.py`

- [ ] **Step 18.1: Write `youtube_cli.py`**

```python
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
```

- [ ] **Step 18.2: Write `reddit_cli.py`**

```python
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
```

- [ ] **Step 18.3: Write `hn_cli.py`**

```python
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
```

- [ ] **Step 18.4: Write `trends_cli.py`**

```python
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
```

- [ ] **Step 18.5: Smoke-test the CLIs run (no network) by printing `--help`**

Run: `.venv/Scripts/python -m connapse_yt.pull.hn_cli --help`
Expected: click usage printout.

Run each: `youtube_cli --help`, `reddit_cli --help`, `trends_cli --help`. All should print help text (no crashes).

- [ ] **Step 18.6: Commit**

```bash
git add src/connapse_yt/pull/*_cli.py
git commit -m "feat: CLI wrappers for each data pull"
```

---

### Task 19: `positioning-synthesis` skill (weekly)

**Files:**
- Create: `.claude/skills/positioning-synthesis/SKILL.md`

- [ ] **Step 19.1: Write the skill**

```markdown
---
name: positioning-synthesis
description: Weekly positioning pass — read last 7 daily summaries and all /wiki/strategy/, produce a new positioning-theses page and a pillar-balance report.
---

# Weekly positioning synthesis

## 1. Inputs

Fetch via MCP:
- All files in `/wiki/strategy/` (hybrid search on `path="/wiki/strategy/"`, or list_files).
- The last 7 days of `/daily/<date>/summary.md` and `/daily/<date>/candidates.md`.

## 2. Pillar-balance report

Count candidates per pillar (P1/P2/P3) across the last 7 daily `candidates.md` files.

- If any pillar has ≥3× the volume of another → flag imbalance.
- Write `/tmp/pillar-balance.md` with counts + flag.
- Use `connapse-yt plan-update` with `--topic strategy/pillar-balance` to upload as a versioned wiki page.

## 3. Positioning-theses update

Synthesize 3-7 evidence-backed hypotheses in the form "Audience X responds to format Y because Z, evidenced by [sources]." Citations must reference specific daily files / raw paths.

- Read current `/wiki/strategy/positioning-theses.v<N>.md`.
- Draft `/tmp/positioning-theses.new.md`.
- Use `connapse-yt plan-update --topic strategy/positioning-theses ...` to version-bump and upload.

## 4. Append log

Append a line to `/wiki/log.md` noting the run: date, pillar counts, new theses version.

Exit 0.
```

- [ ] **Step 19.2: Commit**

```bash
git add .claude/skills/positioning-synthesis/SKILL.md
git commit -m "feat: weekly positioning-synthesis skill"
```

---

### Task 20: `wiki-lint` skill (weekly)

**Files:**
- Create: `.claude/skills/wiki-lint/SKILL.md`

- [ ] **Step 20.1: Write the skill**

```markdown
---
name: wiki-lint
description: Weekly corpus hygiene — orphans, stale claims, raw prune, daily archive.
---

# Weekly lint pass

## 1. Orphan + stale detection

- List all `/wiki/**` files.
- For each wiki page, search the corpus for inbound references (`search_knowledge` on its topic slug, path filter `/wiki/`).
- Pages with zero inbound references and no outbound links are **orphans** — flag in the log for human review, do not auto-delete.
- Pages whose most recent `## Evidence` entry is older than 90 days are **stale** — flag in the log, queue for next refresh.

## 2. Raw prune

- List `/raw/**`. For any file whose date prefix is older than 30 days, `mcp__connapse__delete_file`.
- Record deletions in `/wiki/log.md`.

## 3. Daily archive

- List `/daily/<YYYY-MM-DD>/` folders. For folders older than 180 days, move their `summary.md` to `/archive/daily/<YYYY-MM-DD>/summary.md` (upload then delete). Delete `candidates.md` and `observations.md` outright.

## 4. Index regenerate

Read `/_manifest.md` fresh. Regenerate `/wiki/index.md` TOC. Upload (delete + re-upload).

## 5. Log

Append one summary line to `/wiki/log.md` with: orphans_flagged, stale_flagged, raw_deleted, daily_archived.

Exit 0.
```

- [ ] **Step 20.2: Commit**

```bash
git add .claude/skills/wiki-lint/SKILL.md
git commit -m "feat: weekly wiki-lint skill (orphans, raw prune, archive)"
```

---

## Phase 5 — Integration & seed

### Task 21: End-to-end dry run

**Files:**
- Create: `tests/test_integration_dryrun.py`

- [ ] **Step 21.1: Write the test**

```python
# tests/test_integration_dryrun.py
"""Offline end-to-end: drive all four pull CLIs against fixtures and
verify they produce well-formed JSON the skill can consume."""

import json
import subprocess
import sys
from pathlib import Path


def test_hn_cli_produces_valid_json(tmp_path, httpx_mock):
    httpx_mock.add_response(
        url="https://hacker-news.firebaseio.com/v0/topstories.json", json=[]
    )
    out = tmp_path / "hn.json"
    result = subprocess.run(
        [sys.executable, "-m", "connapse_yt.pull.hn_cli", "--limit", "0", "--out", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    data = json.loads(out.read_text())
    assert data == []


def test_scoring_roundtrip_via_cli(tmp_path):
    from connapse_yt.scoring import Candidate
    c = Candidate(
        text="Give Claude persistent memory",
        outlier_precedent=0.8, trend_slope=0.6, pain_density=0.7,
        audience_fit=0.9, signup_pull=0.85,
        pillar="P1", cloud_compatible=True, promotion_surface="hosted",
        sources=["/raw/youtube/2026-04-18/pull.json#vid001"],
    )
    assert c.routing_ok
    assert 0 <= c.composite <= 1
```

- [ ] **Step 21.2: Run the tests**

Run: `.venv/Scripts/python -m pytest tests/test_integration_dryrun.py -v`
Expected: `2 passed`.

- [ ] **Step 21.3: Run the full suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all prior tests still pass, total count matches accumulated tasks.

- [ ] **Step 21.4: Commit**

```bash
git add tests/test_integration_dryrun.py
git commit -m "test: offline dry-run integration checks"
```

---

### Task 22: Create Connapse container

**Files:** none (MCP op only, recorded in commit message)

- [ ] **Step 22.1: List existing containers**

Invoke `mcp__connapse__container_list` from the current Claude Code session.
Expected: empty or existing names; confirm `connapse-youtube-research` doesn't exist yet.

- [ ] **Step 22.2: Create the container**

Invoke `mcp__connapse__container_create` with name `connapse-youtube-research`.
Expected: returns containerId. Record in a local note `deployment/container-id.txt` (add to `.gitignore` if it holds sensitive info; otherwise fine to commit).

- [ ] **Step 22.3: Verify with stats**

Invoke `mcp__connapse__container_stats` with the new containerId.
Expected: document_count=0.

- [ ] **Step 22.4: Commit the deployment note**

```bash
echo "containerName: connapse-youtube-research" > deployment/container.yaml
echo "createdAt: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> deployment/container.yaml
git add deployment/container.yaml
git commit -m "chore: record Connapse container name"
```

---

### Task 23: Seed the cold-start wiki

**Files:** uploaded via MCP to Connapse, also mirrored locally in `seed/` for provenance.

- [ ] **Step 23.1: Write six seed pages locally**

Create these under `seed/wiki/`:

- `strategy/positioning-theses.v1.md` — starter hypothesis: "Claude Code power-users have three acute pains (P1/P2/P3); each is promotable with single-pillar hooks; hosted CTA wins when the pain doesn't require BYO storage."
- `voice/connapse-brand-voice.v1.md` — lift tagline + pain phrasing from OSS README (§1 of spec).
- `audience/claude-code-power-user.v1.md` — initial persona sketch.
- `audience/agentic-dev-indie.v1.md` — adjacent persona.
- `topics/connapse-oss-landscape.v1.md` — snapshot of Destrayon/Connapse (stars, open issues count, latest release) pulled via `gh api repos/Destrayon/Connapse`.
- `strategy/pillar-balance.v1.md` — empty template (zero counts so far).

Each page starts with proper YAML front-matter (use `connapse_yt.frontmatter.write_page`). Write a script `seed/seed.py` that emits these:

```python
# seed/seed.py
"""One-shot seeding: writes seed/wiki/*.md so the skill can upload them via MCP."""

from pathlib import Path
from connapse_yt.frontmatter import PageMetadata, write_page

OUT = Path(__file__).parent / "wiki"
OUT.mkdir(parents=True, exist_ok=True)


def _meta(topic: str, version: int, tags: list[str]) -> PageMetadata:
    return PageMetadata(
        type="evergreen", topic=topic, date="evergreen",
        sources=["seed/seed.py"], version=version, tags=tags,
    )


def write(path: str, topic: str, body: str, tags: list[str]) -> None:
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(write_page(_meta(topic, 1, tags), body=body))


write(
    "strategy/positioning-theses.v1.md",
    "strategy/positioning-theses",
    "# Positioning theses (v1 — cold start)\n\n## Hypothesis T1\nClaude Code power-users have three acute pains: (P1) session amnesia, (P2) bloated-context cost, (P3) no file search over their documents. Each is promotable with single-pillar hooks per §1.1 of the design spec.\n\n## Hypothesis T2\nHosted CTA wins when the pain does not require BYO storage; OSS CTA wins when it does. Mis-routed videos produce low signup conversion.\n\n## Evidence\n- Seed (no live evidence yet). First real evidence appears after 7+ daily runs.\n",
    ["positioning", "cold-start"],
)

write(
    "voice/connapse-brand-voice.v1.md",
    "voice/connapse-brand-voice",
    "# Connapse brand voice (v1)\n\n**Canonical tagline** (from OSS README — lift verbatim for hooks):\n> Stop losing context between AI sessions. Give your agents persistent, searchable memory.\n\n**Pain phrasing**:\n> Your AI agents forget everything between sessions.\n\n**Surface-specific framings**:\n- Hosted: \"Drop your docs in, Claude reads them\"; \"60-second setup\"; \"free beta\".\n- OSS: \"Point it at your S3 bucket\"; \"Docker 60-second deploy\"; \"MIT, self-hosted\".\n\n**What we do not say (inaccurate on cloud)**:\n- \"Point Connapse at your S3 bucket\" (cloud has no BYO-storage connectors).\n- \"Index your Azure Blob container\" (same).\n- \"Connect your local filesystem\" (same).\n\n**Tone**: technical, direct, no hype adjectives. Show, don't tell.\n",
    ["voice", "cold-start"],
)

write(
    "audience/claude-code-power-user.v1.md",
    "audience/claude-code-power-user",
    "# Persona: Claude Code power-user (v1)\n\n**Who**: 2-10 years dev experience, uses Claude Code daily, builds MCP servers, follows Anthropic releases same-day.\n\n**Watches on YT**: AI Jason, IndyDevDan, Cole Medin, David Ondrej.\n\n**Active subs**: r/ClaudeAI, r/ClaudeCode, r/mcp, r/LLMDevs.\n\n**Pain signal words**: \"session amnesia\", \"context window\", \"my CLAUDE.md is huge\", \"re-explaining\", \"token cost\".\n\n**Evidence**: seed.\n",
    ["persona", "cold-start"],
)

write(
    "audience/agentic-dev-indie.v1.md",
    "audience/agentic-dev-indie",
    "# Persona: Agentic dev / indie (v1)\n\n**Who**: solo or small-team builder shipping an agent product, values OSS, self-hosts when possible, reads HN.\n\n**Watches on YT**: Matthew Berman, Matt Williams, Sam Witteveen, Mervin Praison.\n\n**Active subs**: r/LocalLLaMA, r/AI_Agents, r/LangChain, r/SideProject.\n\n**Pain signal words**: \"vector DB\", \"LangChain bloat\", \"self-host\", \"RAG that just works\", \"file upload\".\n\n**Evidence**: seed.\n",
    ["persona", "cold-start"],
)

write(
    "topics/connapse-oss-landscape.v1.md",
    "topics/connapse-oss-landscape",
    "# Connapse OSS landscape (v1)\n\nRepo: https://github.com/Destrayon/Connapse (MIT, .NET 10, 11 MCP tools)\nCompanion: https://github.com/Destrayon/connapse-cli\n\n**Tech hooks worth mentioning in content**:\n- 60-second Docker deploy\n- Hybrid vector + keyword search\n- S3 / Azure Blob / local FS connectors (OSS only — cloud has managed containers)\n- REST, CLI, and MCP surfaces\n- Glama-listed MCP server\n\nAgent updates this page with current star count + open-issue count weekly via `gh api repos/Destrayon/Connapse`.\n",
    ["oss", "cold-start"],
)

write(
    "strategy/pillar-balance.v1.md",
    "strategy/pillar-balance",
    "# Pillar balance (v1 — cold start)\n\n| Pillar | Candidates last 7 days | Flag |\n|---|---|---|\n| P1 (persistent memory) | 0 | — |\n| P2 (context/cost) | 0 | — |\n| P3 (file search) | 0 | — |\n\nUpdated weekly by `positioning-synthesis`.\n",
    ["pillar-balance", "cold-start"],
)
```

- [ ] **Step 23.2: Run the seeder locally**

Run: `.venv/Scripts/python seed/seed.py`
Expected: six files under `seed/wiki/**`.

- [ ] **Step 23.3: Upload seed pages to Connapse**

From this Claude Code session (not the routine), invoke `mcp__connapse__upload_file` for each of the six files into the container at the corresponding `/wiki/...` path.

Then build an initial `/_manifest.md` listing the six topics at version 1 and upload it.

- [ ] **Step 23.4: Verify**

Invoke `mcp__connapse__container_stats` → document_count should equal 7 (6 wiki pages + 1 manifest).

- [ ] **Step 23.5: Commit the seed script**

```bash
git add seed/
git commit -m "feat: cold-start corpus seeder for v1 wiki pages"
```

---

## Phase 6 — Routine deployment

### Task 24: Push repo to main

- [ ] **Step 24.1: Confirm green**

Run: `.venv/Scripts/python -m pytest`
Expected: all tests pass.

- [ ] **Step 24.2: Push**

Run: `git push origin main`
Expected: up-to-date with remote.

---

### Task 25: Configure the Routine in claude.ai

**Files:** none (UI action, record config in `deployment/routine.yaml`).

- [ ] **Step 25.1: Open `https://claude.ai/code/routines`**

Click **New Routine**.

- [ ] **Step 25.2: Set fields**

- Name: `connapse-yt-research-daily`
- Repository: `<your-handle>/connapse-yt-research` (default branch `main`)
- Environment: **Custom** — add network allowlist entries:
  - `connapse.com`
  - `www.connapse.com`
  - `youtube.googleapis.com`
  - `oauth.reddit.com`
  - `www.reddit.com`
  - `hacker-news.firebaseio.com`
  - `trends.google.com`
- Environment variables:
  - `YOUTUBE_API_KEY` = (your YT API key)
  - `REDDIT_CLIENT_ID` = (your Reddit app id)
  - `REDDIT_CLIENT_SECRET` = (your Reddit secret)
  - `REDDIT_USER_AGENT` = `connapse-yt-research/0.1 by <your-reddit-handle>`
- Trigger: **Schedule**, daily, 07:00 America/Chicago.
- Prompt: *"Run the yt-research-daily skill."*
- Connectors: keep the Connapse OAuth connector enabled; disable unrelated ones (Linear, GDrive, etc.) to minimize surface area unless needed.

Save the routine. Note the routine ID printed on the detail page.

- [ ] **Step 25.3: Record config**

```bash
cat > deployment/routine.yaml <<EOF
daily:
  name: connapse-yt-research-daily
  id: <paste routine id>
  schedule: "0 7 * * *"
  tz: America/Chicago
  network_env: custom
weekly:
  name: connapse-yt-research-weekly
  schedule: "0 8 * * 0"
  tz: America/Chicago
EOF
git add deployment/routine.yaml
git commit -m "chore: record daily routine config"
```

- [ ] **Step 25.4: Create the weekly routine**

Repeat Step 25.2 with:
- Name: `connapse-yt-research-weekly`
- Trigger: Schedule, Sundays 08:00 America/Chicago.
- Prompt: *"Run the positioning-synthesis skill, then the wiki-lint skill."*
- Same env + allowlist.

Add its ID to `deployment/routine.yaml`, commit.

- [ ] **Step 25.5: Push**

```bash
git push origin main
```

---

### Task 26: First manual run + verification

- [ ] **Step 26.1: Fire the daily routine manually**

On the routine detail page, click **Run now**.
Expected: a new session appears in the sessions list; status progresses "queued → running → completed".

- [ ] **Step 26.2: Wait for completion**

Once completed, open the session; scan the transcript for errors.
Expected: no red error blocks. Agent uploads ~6-10 files to Connapse.

- [ ] **Step 26.3: Verify via MCP in this Claude Code session**

- `mcp__connapse__list_files` on container, path `/daily/<today>/` → should show `summary.md`, `candidates.md`, `observations.md`.
- `mcp__connapse__list_files`, path `/raw/` → should show `youtube/<today>/`, `reddit/<today>/`, `hn/<today>/`, `trends/<today>/`.
- `mcp__connapse__get_document` on `/wiki/log.md` → last line is today's run with the routine's session URL.

- [ ] **Step 26.4: If something failed**

- Read the session transcript (click through on claude.ai).
- Fix the repo code locally, push to main, re-run.
- Do not proceed until a clean run exists.

- [ ] **Step 26.5: Enable the schedule**

On the routine page, confirm the schedule toggle is **on**.

---

## Phase 7 — Documentation

### Task 27: Update README with run/review flow

**Files:**
- Modify: `README.md`

- [ ] **Step 27.1: Append usage section**

Append to `README.md`:

```markdown

## Routine operations

**Daily routine:** runs at 07:00 America/Chicago. Output lands in the Connapse container `connapse-youtube-research` under `/raw/` and `/daily/<date>/`. See `deployment/routine.yaml` for IDs.

**Weekly routine:** runs Sundays at 08:00 CT. Runs positioning-synthesis then wiki-lint.

### How to query the corpus from another agent

Point your downstream query agent at the same Connapse MCP. The canonical retrieval patterns (§9 of the spec):

| Intent | Path filter |
|---|---|
| "Hooks that work for Claude Code devs" | `/wiki/hooks/` + `/wiki/audience/` |
| "What's trending this week" | `/daily/<last-7>/` |
| "Plan a video about X" | `/wiki/` + `/daily/<last-3>/` |
| "Our positioning thesis" | `/wiki/strategy/` |

### How to add a new Reddit sub

Edit `SKILL.md` for `yt-research-daily`, add `--sub <NewSub>` in the Reddit pull step, push to `main`.

### Troubleshooting

- **"quotaExceeded" on YouTube**: daily run caught it; the next day's run will fall back to cached channels. Raise the quota in Google Cloud Console if this recurs.
- **Connapse auth expired**: reconnect the connector on claude.ai and rerun.
- **Pillar imbalance flagged**: the weekly `pillar-balance.vN.md` called it out. Adjust the daily skill's `--query` list to favor the under-represented pillar for 1-2 weeks.
```

- [ ] **Step 27.2: Commit and push**

```bash
git add README.md
git commit -m "docs: routine operations + troubleshooting"
git push origin main
```

---

## Self-review checklist

Before declaring the plan complete, the implementer should verify:

1. **Spec coverage** — every section of `2026-04-18-connapse-youtube-research-agent-design.md` maps to at least one task:
   - §1 pillars → Tasks 16, 17, 19
   - §4 storage layout → Tasks 22, 23, 17
   - §5 pipeline → Tasks 5-10, 17
   - §6 delete+re-upload → Tasks 11-14
   - §7 repo → Tasks 1-2, 15-20
   - §8 routine config → Task 25
   - §9 retrieval → Task 27 (documented for downstream agent)
   - §10 operations → Task 25 (env + allowlist)
   - §11 failure modes → Tasks 16 (CLAUDE.md abort rules), 17 (error handling)
   - §12 testing → all TDD tasks + Task 21

2. **All tests green** — `pytest` passes from Phase 1 onward.

3. **First real daily run produced valid artifacts** — Task 26 verification complete.

4. **No TODO/TBD strings** anywhere in the committed repo.
