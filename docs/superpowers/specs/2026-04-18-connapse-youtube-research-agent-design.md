# Connapse YouTube Idea Research Agent — Design Spec

**Date:** 2026-04-18
**Status:** Draft, pending user sign-off
**Author:** brainstorming session (Claude + Diviel)

## 1. Purpose

Build a Claude Code Routine that runs daily, researches YouTube video ideas for promoting Connapse, and persists findings into a Connapse knowledge container so a downstream query agent can later pull ideas, evidence, audience insights, and positioning theses on demand.

The channel does not yet exist. Positioning is a first-class output of the agent, not an input — the corpus doubles as an evidence base for deciding the channel's niche.

**Business goal (v1):** drive **free-tier signups** at `https://www.connapse.com/` during the public-beta phase. Connapse is free with no subscription today; a paid tier is planned but a free tier will always exist. Every video idea is evaluated partly on how naturally it creates a path to "try Connapse free" as a CTA. Long-term goal is paid conversion, but v1 agent optimizes only for signup volume + signup quality (users in the target segment).

**Promotion surfaces** (dual):

- **Hosted product** — `https://www.connapse.com/` — managed RAG / knowledge-container SaaS, free beta. Content angle: "managed RAG in 2 minutes", "replace X with Connapse", workflow demos. **Primary CTA path.**
- **OSS repo** — public GitHub repository. Content angle: "self-host your RAG", "contribute to an AI knowledge tool", architecture deep-dives. **Secondary / top-of-funnel** — lower-intent traffic but builds credibility and attracts dev-segment signups who then use hosted.

**Target audience (v1):** Claude Code users + agentic-AI developers and power users. This is the primary audience the channel will speak to; the corpus should weight signals from this segment.

## 2. Goals & non-goals

**Goals**

- Persistent, compounding corpus of YouTube-relevant research anchored in Connapse.
- Daily autonomous runs with zero-to-low recurring API cost at steady state.
- Temporal separation: daily observations distinct from curated topic pages.
- Dedup + promotion flow so recurring signals consolidate into evergreen wiki pages.
- Positioning theses that a human (or another agent) can query for strategic decisions.
- Works around Connapse's current no-edit constraint via delete + re-upload versioning.

**Non-goals (v1)**

- Script generation, thumbnail generation, or final production artifacts.
- Video upload automation.
- Multi-channel support.
- Paid data sources (Exploding Topics, X API Basic, Reddit commercial tier).
- Vector infra outside Connapse's built-in hybrid search.

## 3. Context

- **Connapse MCP**: remote HTTP MCP at `https://www.connapse.com/khastra/mcp`. Tools: `container_create/list/delete/stats`, `upload_file`, `delete_file`, `get_document`, `list_files`, `search_knowledge` (semantic/keyword/hybrid, filterable by path), `bulk_upload`, `bulk_delete`, plus auth flows. **No in-place edit** — files are immutable; editing means delete + re-upload.
- **Claude Code Routines**: Anthropic-managed cloud automation. Fresh sandboxed VM per run, repo-cloned from GitHub, no persistent memory across runs. Min interval 1 hour. Pro cap 5 runs/day. Default Trusted network allowlist does **not** include connapse.com; a Custom network env is required.
- **User**: Windows local dev environment, existing Connapse OAuth session tested and working.
- **Karpathy LLM-wiki pattern** (Apr 2026): compile raw sources into a topic-aggregated, interlinked markdown wiki; the wiki is the compiled artifact, raw is the source. Periodic lint passes maintain coherence.

## 4. Architecture

### 4.1 Storage layout (Connapse container `connapse-youtube-research`)

```
/raw/                                 immutable source pulls (dated)
  youtube/2026-04-18/trending-ai-dev.json
  youtube/2026-04-18/niche-search-rag.json
  reddit/2026-04-18/r-localllama-top.json
  hn/2026-04-18/frontpage.json
  trends/2026-04-18/slopes.json
  transcripts/<video_id>.md          on-demand, only for outliers
/wiki/                                LLM-compiled; versioned
  strategy/positioning-theses.vN.md   primary F-mode deliverable
  audience/<persona>.vN.md            discovered personas, evolve
  hooks/<pattern>.vN.md
  competitors/<channel>-teardown.vN.md
  voice/connapse-brand-voice.vN.md
  topics/<niche>-landscape.vN.md
  index.md                            TOC, regenerated each run
  log.md                              append-only run log
/daily/
  2026-04-18/
    summary.md                        digest — what changed, what's new
    candidates.md                     scored ideas w/ source citations
    observations.md                   raw highlights, no filtering
/archive/                             superseded wiki versions
  wiki/hooks/cold-open-patterns.v2.md
/_manifest.md                         canonical current-version list
```

### 4.2 File front-matter convention

Every markdown file starts with YAML:

```yaml
---
type: evergreen | daily-summary | daily-candidates | daily-observations | transcript | raw-extract
topic: hooks | audience | competitors | voice | strategy | topics | null
date: 2026-04-18                  # run date, or "evergreen"
sources: [youtube-api, reddit, hn, pytrends, llm-synthesis]
source_ids: [videoId123, t3_abc, 12345678]    # where applicable
score: 0.87                       # for candidates
version: 3                        # for wiki pages
supersedes: hooks/cold-open-patterns.v2.md
session_url: https://claude.ai/code/sessions/<id>
tags: [shorts, cold-open, connapse-fit]
---
```

Path and filename carry the fast-filter signals (`type`, `date`, `topic` via folder). Body carries the hybrid-search content.

### 4.3 Chunking

Content-type-aware, per RAG research:

- Wiki topic pages: 400-600 token chunks, 15% overlap, split on H2/H3.
- Transcripts: 200-300 token chunks, 20% overlap, split on speaker/timestamp.
- Raw API pulls: one chunk per record (one video, one post, one thread).
- Candidates: one line per candidate, bundled with score + rationale.

## 5. Data pipeline (per daily run)

1. **Pull** (free tier only at v1)
   - YouTube Data API v3 — 10k units/day. Budget: ≤3 `search.list` calls (300u), ~20 `videos.list` calls (20u), ~5 `channels.list` (5u), `commentThreads` cheap. Keep under 500u/day.
     - **Seed channel list** (cold start, agent refines after week 1 via Reddit/HN mentions and YT recommended-channel graph):
       - AI Jason (agentic workflows, LangChain/Claude)
       - IndyDevDan (Claude Code power-user content)
       - Cole Medin (agent builders, n8n + LLMs)
       - David Ondrej (Claude Code tutorials, no-code AI)
       - All About AI (agentic experiments, tool walkthroughs)
       - Matthew Berman (LLM/agent news + demos)
       - Sam Witteveen (LangChain/LangGraph deep-dives)
       - Matt Williams (ex-Ollama, local + agentic)
       - Mervin Praison (agent tutorials, MCP content)
       - AI Search (tool comparisons)
       - Anthropic (official, for model/product news baselines)
       - Fireship (general AI news pulse; engagement benchmark)
   - Reddit — OAuth, non-commercial, 100 req/min, 10k req/month. Targets (Claude-Code-and-agentic-focused):
     `r/ClaudeAI`, `r/ClaudeCode`, `r/AI_Agents`, `r/LLMDevs`, `r/LangChain`,
     `r/LocalLLaMA`, `r/AgentDevelopmentKit`, `r/mcp`, `r/cursor` (adjacent tooling),
     `r/SideProject` (indie-dev discovery). Configurable; pruned/expanded based on signal density after week 4.
   - Hacker News — Firebase JSON API, no auth, free.
   - Google Trends — `pytrends`, conservative pacing (60s spacing if rate-limited).
   - Raw JSON written to `/raw/<source>/<date>/`.

2. **Extract** — LLM distills each raw artifact into observations: title patterns, pain points, emerging keywords, competitor moves, outlier videos (≥10x channel avg views).

3. **Score** candidates on 5 axes, each 0-1:
   - `outlier_precedent` — views vs. channel baseline (YT data)
   - `trend_slope` — pytrends rise + cross-platform mention velocity
   - `pain_density` — count of distinct Reddit/HN threads voicing the problem
   - `audience_fit` — LLM-judged fit to **Claude Code / agentic-dev** audience (v1 target segment)
   - `signup_pull` — LLM-judged likelihood the video produces a natural "try Connapse free" CTA, scoring how directly Connapse solves the pain/workflow shown. Distinguished from `audience_fit`: a video can match the audience (high audience_fit) without being a good signup driver (low signup_pull), e.g. a general "state of AI" recap.
   - Composite: `0.25·outlier + 0.15·trend + 0.20·pain + 0.15·audience + 0.25·signup_pull`
   - Each candidate tagged `promotion_surface: hosted | oss | both` so downstream filtering can pick content type. Hosted-surface candidates with `signup_pull ≥ 0.7` are the primary v1 output.
   - Rationale written alongside score, citing source paths.

4. **Dedup vs. wiki** — for each candidate,
   `search_knowledge(candidate_text, containerId, path="/wiki/", mode="hybrid", topK=3, minScore=0.05)`.
   Cosine ≥ 0.82 → append dated observation to that wiki page (delete + re-upload, version bump). Else → leave in `candidates.md`.

5. **Promote** — any candidate appearing in ≥3 daily runs within a 14-day window → new wiki page, or merge into an existing wiki page in an adjacent topic. Evidence links back to the originating daily folders.

6. **Positioning pass** (weekly, Sunday) — read last 7 days of `/daily/*/summary.md` and all `/wiki/strategy/` pages. Produce a new `positioning-theses.vN+1.md` listing evidence-backed hypotheses ("audience X responds to format Y because Z"). Archive previous.

7. **Lint pass** (weekly) — orphan pages, stale claims, missing cross-refs, contradictions. Prune `/raw/` older than 30 days (re-fetchable). Archive `/daily/*/summary.md` older than 180 days.

8. **Log** — append a run-metadata line to `/wiki/log.md`: date, sources pulled, wiki pages touched, promotions, session URL.

## 6. Wiki-edit workaround (delete + re-upload)

Connapse cannot edit files. Every wiki-page update follows:

1. `get_document(<page>.vN.md)`.
2. LLM produces updated body.
3. `upload_file(<page>.v(N+1).md)` — new version with `supersedes: <page>.vN.md`, bumped `## Changelog` section.
4. `delete_file(<page>.vN.md)` — remove old from live path.
5. `upload_file(archive/wiki/<page>.vN.md)` — preserve history.
6. Regenerate `/_manifest.md` listing current-version filenames per topic. Single source of truth for "canonical".

Failure modes:

- Step 4 fails → both versions live. `/_manifest.md` breaks the tie; next run cleans up. No data loss.
- Step 5 fails → history gap, logged in `/wiki/log.md` as `archive-orphan` for manual recovery.
- Step 6 fails → previous manifest still correct; next run re-runs step 6 idempotently.

All operations are idempotent on rerun.

## 7. Routine repo structure (`connapse-yt-research` on GitHub)

```
CLAUDE.md                       agent operating manual + routing rules
.mcp.json                       Connapse HTTP MCP declaration
.claude/
  settings.json                 skills + hooks
  skills/
    yt-research-daily/SKILL.md  main daily pipeline
    wiki-compile/SKILL.md       Karpathy compile pattern
    wiki-lint/SKILL.md          weekly hygiene
    positioning-synthesis/SKILL.md  weekly positioning pass
scripts/
  pull_youtube.py               quota-aware YT Data API wrapper
  pull_reddit.py                non-commercial OAuth
  pull_hn.py                    Firebase, no auth
  pull_trends.py                pytrends
  score.py                      deterministic composite scoring
  wiki_update.py                delete+re-upload helper
prompts/
  extract.md
  score-rationale.md
  positioning.md
tests/
  test_score.py                 scoring math is deterministic; test it
  test_wiki_update.py           delete+re-upload state machine
README.md
```

Scripts are Python; deterministic work (math, HTTP) lives here, LLM reasoning lives in skills.

## 8. Routine configuration (Claude Code Routines)

- **Daily trigger:** schedule, 07:00 America/Chicago (user local), invokes `yt-research-daily` skill.
- **Weekly trigger:** schedule, Sunday 08:00, invokes `positioning-synthesis` then `wiki-lint` skills sequentially.
- **Environment:** Custom network env with allowlist:
  `connapse.com`, `youtube.googleapis.com`, `oauth.reddit.com`, `www.reddit.com`,
  `hacker-news.firebaseio.com`, `trends.google.com`.
- **Secrets (env vars on environment):**
  `YOUTUBE_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`,
  `CONNAPSE_CONTAINER_ID`.
- **Connapse auth:** OAuth linked via claude.ai connectors (already verified in this session).
- **Output channels:**
  - Connapse uploads (primary data path).
  - Session URL (`$CLAUDE_CODE_REMOTE_SESSION_ID`) stamped into each upload's front-matter for provenance.
  - Optional git PR to `claude/*` branch if the agent proposes prompt/skill edits (self-improvement).

## 9. Downstream query-agent retrieval patterns

| User intent                         | Path filter                           | Mode     | k  |
|-------------------------------------|---------------------------------------|----------|----|
| "What hooks work for devs?"         | `/wiki/hooks/` + `/wiki/audience/`    | hybrid   | 8  |
| "What's trending this week?"        | `/daily/<last-7>/`                    | hybrid   | 12 |
| "Has this idea been covered?"       | `/wiki/` + `/daily/<last-30>/`        | semantic | 6  |
| "Plan a video about X"              | `/wiki/` + `/daily/<last-3>/`         | hybrid   | 12 |
| "What's our positioning thesis?"    | `/wiki/strategy/`                     | keyword  | 4  |
| "Show me the run log"               | `/wiki/log.md`                        | get_doc  | —  |

Default composite: k=8 from wiki, k=4 from `/daily/last-7`, client-side rerank.

## 10. Operations & cost

- Runs: 1 daily + 1 weekly ≈ 35/mo; within Pro 5/day cap.
- API $/mo at v1: ~$0. Free tiers cover everything.
- Token $/mo: ~50-150k context + 20-40k output per run × 30 = within Pro pool; no overflow expected.
- Degraded mode: if YouTube quota ≥80% by 18:00, skip `search.list` next day, fall back to cached channel IDs.
- Corpus growth estimate: `/raw/` ~5-15MB/day → pruned at 30d → steady state ~450MB. `/wiki/` ~2-10MB total after 90 days.

## 11. Failure modes & recovery

- **API outage (YouTube/Reddit/HN):** skill catches, logs to `/wiki/log.md`, proceeds with available sources. If ≥2 sources down, abort and leave a stub `/daily/<date>/summary.md` noting the outage.
- **Connapse MCP auth expired:** routine cannot proceed; surface via Linear ticket creation via user's Linear connector (already configured). Human rotates OAuth.
- **Quota exceeded mid-run:** partial `/raw/` pull is acceptable; `/daily/<date>/summary.md` notes the limit.
- **Delete+re-upload partial failure:** see Section 6. `/_manifest.md` tiebreaker + next-run idempotency.
- **Duplicate daily runs** (user triggers manual + scheduled same day): idempotent writes — second run notices existing `/daily/<date>/summary.md`, appends an `_run2` file instead of overwriting.

## 12. Testing

- `test_score.py` — scoring math fixed on synthetic inputs (regression-guard).
- `test_wiki_update.py` — state-machine test of delete+re-upload transitions, including each failure mode.
- `test_dedup.py` — dedup threshold behavior against a small fixture wiki.
- **Integration test:** mock MCP with recorded Connapse responses; assert an end-to-end run produces expected `/daily/<date>/` files.
- **Smoke test in real Routines env:** dry-run flag in skill that pulls data but writes to `/dryrun/<date>/` only.

## 13. Open questions (resolve before implementation plan)

**Resolved:**

- ~~YT channel seed list~~ — seeded in §5 with Claude-Code / agentic-dev-focused channels. Agent refines after week 1.
- ~~Reddit sub list~~ — defaults in §5, Claude-Code / agentic-focused.
- ~~Business goal~~ — free-tier signups at connapse.com (see §1).
- ~~Target audience~~ — Claude Code users + agentic-dev power users.

**Still open:**

- **Local time zone** for the 07:00 daily trigger — default America/Chicago unless user specifies otherwise.
- **GitHub repo location** for the routine code — user's personal GitHub account vs. a Connapse org. Private visibility.
- **Container naming** — `connapse-youtube-research` proposed, or does user prefer another convention matching existing Connapse container names?
- **Connapse OSS repo URL** — need the actual GitHub URL to seed a `/wiki/topics/connapse-oss-landscape.md` page and to let the agent cite issues/PRs as content fodder.

## 14. Out of scope for v1 (explicit deferrals)

- Native Connapse edit (when shipped, replaces Section 6 workaround cleanly).
- Paid trend sources (Exploding Topics, Glimpse).
- X/Twitter API integration ($0.005/read is feasible but not essential at v1).
- Thumbnail/title A/B ideation.
- Multi-channel / multi-persona containers.
- Analytics ingestion from an actual YouTube channel (no channel yet).

## 15. References

- [Claude Code Routines docs](https://code.claude.com/docs/en/routines)
- [Karpathy LLM-wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Astro-Han/karpathy-llm-wiki skill](https://github.com/Astro-Han/karpathy-llm-wiki)
- [YouTube Data API quota](https://developers.google.com/youtube/v3/determine_quota_cost)
- [Reddit API pricing](https://painonsocial.com/blog/how-much-does-reddit-api-cost)
- [LlamaIndex chunking guide](https://docs.llamaindex.ai/en/stable/optimizing/production_rag/)
- [Anthropic contextual retrieval cookbook](https://www.anthropic.com/news/contextual-retrieval)
