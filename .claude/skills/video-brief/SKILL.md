---
name: video-brief
description: Generate a single-file HTML video-planning brief for a candidate idea and drop it in the local working directory. Pulls hook, evidence, reference videos, pain vocabulary, brand voice, and positioning frame from the Connapse container via MCP; writes the HTML locally — not back to the container.
---

# Video brief generator (local tool)

Produce one self-contained HTML page per invocation, written to the **local filesystem** so the human can open it in a browser and plan a shoot from it.

This skill runs **locally in Claude Code**, invoked on-demand by the human. It is not called by the cloud routines. The daily/weekly routines produce the research corpus; this skill consumes that corpus to produce a personal planning artifact.

Invoke with a prompt like:

- `"brief me on C2"` — by candidate ID from the most recent `/daily/<date>/candidates.md`
- `"brief today's top pick"` — the rank-1 candidate from the most recent daily
- `"brief this week's top"` — the highest-weighted candidate across the last 7 daily folders
- `"brief the top P3 candidate this week"` — highest-weighted candidate filtered to one pillar
- Free-text topic (`"brief a video about token cost"`) — resolve via `mcp__connapse__search_knowledge`

**Output:** `./briefs/<candidate_id>.html` relative to the current working directory. The skill creates `./briefs/` if missing. Re-running for the same candidate overwrites (intended — briefs reflect the latest research state).

**Does not upload to the Connapse container.** Briefs are private planning artifacts, not part of the research corpus. Do not call `mcp__connapse__upload_file` from this skill.

## 0. Setup

- Resolve and cache containerId via `mcp__connapse__container_list` (name: `connapse-youtube-research`).
- Verify Connapse connectivity. If the MCP is unreachable, abort and tell the user — do not write a stub HTML.

## 1. Resolve the candidate

Find the target and record:
- `candidate_id` (e.g., `C2`)
- `source_daily_date` (the date folder the candidate came from, e.g., `2026-04-19`)
- the full candidate YAML block (pillar, hook, angle, five score axes, rationale, cloud_compatible, promotion_surface)
- its weighted rank / score from the ranking table at the bottom of that day's `candidates.md`

**By ID** (`"brief me on C2"`): `mcp__connapse__list_files('/daily/')`, pick the newest date folder, `mcp__connapse__get_document` on `/daily/<latest>/candidates.md`, extract the YAML for the requested ID.

**By "today's top pick"**: same, take rank 1 from the table.

**By "this week's top"**: list `/daily/`, take the 7 most recent dates. For each, extract the rank-1 candidate. Pick the highest weighted score. On ties, prefer the more recent date.

**By pillar filter** (`"brief the top P3 candidate this week"`): like "this week's top" but filter by `pillar=P<N>` before ranking.

**By free text**: `mcp__connapse__search_knowledge(path="/daily/", query="<user text>", topK=3, mode="Hybrid")`. Pick the candidate in the highest-ranked chunk. Confirm the interpretation in the return message.

If the request is ambiguous, **do not guess** — return the top 3 matches and ask which to brief. Write no files until confirmed.

## 2. Pull evidence

The candidate's `rationale` cites concrete sources. Resolve them:

- **YouTube references**: `mcp__connapse__get_document('/raw/youtube/<source_daily_date>/pull.json')`. For each video ID or channel+title phrase in the rationale, capture `video_id`, `title`, `channel_title`, `view_count`, `published_at`. Keep the 5 most relevant. Video URL: `https://www.youtube.com/watch?v=<video_id>`.
- **HN references**: if the rationale cites `HN #<id>` or "Hacker News", fetch `/raw/hn/<source_daily_date>/pull.json` and match thread IDs or titles. Capture `id`, `title`, `score`, `descendants`, `url`. Thread URL: `https://news.ycombinator.com/item?id=<id>`.
- **Trends**: fetch `/raw/trends/<source_daily_date>/pull.json` entirely. Note the keyword with the highest positive slope relevant to the pillar; flag explicitly if all direction=flat.

## 3. Pull wiki context

Use `/_manifest.md` to find the current version for each topic, then `mcp__connapse__get_document`:

- `/wiki/strategy/positioning-theses.v<latest>.md` — find the hypothesis (T1–T5) matching this candidate's pillar + angle. Quote verbatim; cite by T-number.
- `/wiki/strategy/pillar-balance.v<latest>.md` — note the current count and whether the pillar is flagged UNDERSUPPLIED.
- `/wiki/audience/<persona>.v<latest>.md` — pick by pillar + surface:
  - P1, P2, any surface → `claude-code-power-user`
  - P3 or `promotion_surface=oss|both` → `agentic-dev-indie`
  - Ambiguous → include both.
- `/wiki/voice/connapse-brand-voice.v<latest>.md` — tagline, pain phrasing, hosted-vs-OSS framings, complete don't-say list.

## 4. Render HTML

Produce one self-contained HTML file — all CSS inline, no scripts, no CDN, no external images. Opens correctly offline. Print-friendly (max-width ~860px, system font stack, decent line height).

**Required sections, in this order:**

1. **Header** — `<h1>` = `<candidate_id>: <hook>`; subtitle with pillar badge (P1 blue, P2 red, P3 green), `promotion_surface`, weighted score, source daily date.

2. **Angle** — one paragraph verbatim from the candidate YAML.

3. **Score breakdown** — five rows (outlier_precedent, trend_slope, pain_density, audience_fit, signup_pull) + weighted composite. Each row: numeric score and horizontal bar (`<span>` with inline `width: <score*200>px`, solid color background).

4. **Reference videos** — table: Title (linked to youtube.com/watch?v=…), Channel, Views (formatted with thousands separators), Published (date only). 5 rows.

5. **HN discussions** — table if the rationale cited HN: Title (linked), Points, Comments, Age. Omit the section entirely if no HN citations.

6. **Trend tailwind** — short paragraph: which keyword is rising (if any) with slope value, or "No trend tailwind this cycle — all direction=flat."

7. **Lead with these pain words** — bullet list from the matching persona's pain signal words. Two labeled sub-lists if both personas were included.

8. **Brand voice** — canonical tagline in a `<blockquote>`; pain phrasing below.

9. **DON'T say** — red-accented list, verbatim from the brand-voice don't-say.

10. **Positioning frame** — "This candidate maps to **T<n>**: <quoted hypothesis>".

11. **Pillar balance context** — one sentence: current count + flag. If UNDERSUPPLIED, add "→ filming this corrects the imbalance."

12. **CTA copy** — pick by `promotion_surface`:
    - `hosted` → "60-second setup", "free beta", connapse.com
    - `oss` → "Docker 60-second deploy", "MIT, self-hosted", GitHub link
    - `both` → both stacked, hosted first
    Suggest ≤20 seconds of end-screen copy.

13. **Script outline scaffold** — four slots, rendered as dashed-border `<div>` with grey italic placeholder text:
    - **Hook (0–15s)** — "Use the tagline verbatim or the pain phrasing — don't warm up, cut straight in."
    - **Problem (15s–1:30)** — "Show the pain on screen. One concrete metric visible."
    - **Solution demo (1:30–7:00)** — "Before/after with the same metric. Show Connapse doing the work."
    - **CTA (last 30s)** — "Per the CTA section above. Under 20 seconds. No outro music filler."

14. **Footer** — generation date, candidate source path (`/daily/<source_daily_date>/candidates.md`). Small grey text. No session URL needed — this is local.

**CSS target**: under ~120 lines, no vendor prefixes, system font stack, light theme, readable at A4 print.

## 5. Write locally

Create `./briefs/` relative to cwd if it doesn't exist. Write the HTML to `./briefs/<candidate_id>.html`. Use standard file writing tools (Write); do not call MCP upload.

If `./briefs/` is in a git repo that doesn't already ignore it, suggest (don't auto-apply) adding `briefs/` to `.gitignore` — these are personal planning artifacts, not repo content.

## 6. Return

Report to the user:
- The local path: `./briefs/<candidate_id>.html` (absolute path also fine)
- One-line summary: `"Briefed <candidate_id> '<hook>' — <pillar> <surface>, ranked #<rank> score <score>. Open in your browser."`
- If the pillar was UNDERSUPPLIED, mention it as a pro-filming signal.
- If you short-circuited on ambiguity in §1, no file was written — list the candidate options and ask which to brief.

## Abort conditions

- Connapse MCP unreachable → abort, no stub file. Clear error to user.
- Requested candidate ID not found in the most recent `/daily/<date>/candidates.md` → list the available IDs and ask for a retry. Do not fall through to a different day silently.
- No `/daily/<date>/candidates.md` exists at all → tell the user the research routine hasn't run yet; point them at the cloud routine to produce a daily first.
