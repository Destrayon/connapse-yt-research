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
  --sub ClaudeAI --sub ClaudeCode --sub AI_Agents --sub LLMDevs \
  --sub LangChain --sub LocalLLaMA --sub mcp --sub cursor --sub SideProject \
  --time-filter day --limit 25 \
  --out /tmp/run/$RUN_DATE/reddit.json
# Uses old.reddit.com public JSON; no auth. Optionally set REDDIT_USER_AGENT
# to identify this deployment (falls back to a generic project UA).

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
