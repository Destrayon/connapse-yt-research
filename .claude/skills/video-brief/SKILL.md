---
name: video-brief
description: On-demand HTML brief for a candidate video idea — pulls hook, evidence, reference videos, pain vocabulary, brand voice, and positioning frame into one single-file HTML you open in a browser and plan a shoot from.
---

# Video brief generator

Produce one self-contained HTML page per invocation, uploaded to `/briefs/<date>/<candidate_id>.html` in the container. The point is to give a human something printable/readable while filming — not another markdown file to cross-reference.

This skill is **manual, on-demand**. The daily/weekly routines do not call it. Invoke it with a prompt like:

- `"brief me on C2"` — by candidate ID from the most recent `/daily/<date>/candidates.md`
- `"brief today's top pick"` — the rank-1 candidate from the most recent daily
- `"brief this week's top"` — the highest-weighted candidate across the last 7 daily folders
- `"brief the top P3 candidate this week"` — highest-weighted candidate filtered to one pillar
- Free-text topic (`"brief a video about token cost"`) — agent resolves via `search_knowledge`

## 0. Setup

- `export RUN_DATE=$(date -u +%Y-%m-%d)` — the brief's generation date. Distinct from the candidate's source date.
- Resolve and cache containerId (see CLAUDE.md §Every invocation).
- Verify Connapse connectivity with `mcp__connapse__container_list`. If unreachable, abort and tell the user; no stub.

## 1. Resolve the candidate

Find the target candidate by one of these paths. Record:
- `candidate_id` (e.g., `C2`)
- `source_daily_date` (the date folder the candidate came from, e.g., `2026-04-19`)
- the full candidate YAML block (pillar, hook, angle, five score axes, rationale, cloud_compatible, promotion_surface)
- its weighted rank / score from the ranking table at the bottom of that day's `candidates.md`

**By ID** (`"brief me on C2"`): list `/daily/` via `mcp__connapse__list_files`, pick the newest date folder, `mcp__connapse__get_document` on `/daily/<latest>/candidates.md`, extract the YAML for the requested ID.

**By "today's top pick"** (`"brief today's top pick"`): same as above, take rank 1 from the table.

**By "this week's top"**: list `/daily/`, take the 7 most recent dates. For each, extract the rank-1 candidate. Pick the one with the highest weighted score. If a candidate tied across dates, prefer the one from the most recent date.

**By pillar filter** (`"brief the top P3 candidate this week"`): same as "this week's top" but filter candidates where `pillar=P<N>` before ranking.

**By free text**: `mcp__connapse__search_knowledge(path="/daily/", query="<user text>", topK=3, mode="Hybrid")`. Pick the candidate in the highest-ranked chunk. Confirm the match to the user in the return message ("Interpreted as C5 …").

If the user's request is ambiguous, **do not guess** — respond with the top 3 matches and ask which to brief. No uploads until disambiguated.

## 2. Pull evidence

The candidate's `rationale` field cites concrete sources — video IDs, channel names, HN thread IDs, view counts. Extract and resolve them:

- **YouTube references**: `mcp__connapse__get_document('/raw/youtube/<source_daily_date>/pull.json')` and parse. For each video ID or channel+title phrase in the rationale, capture `video_id`, `title`, `channel_title`, `view_count`, `published_at`. Keep the 5 most relevant to the hook (the ones the rationale directly names + the highest-viewcount matches on the pillar). Video URL format: `https://www.youtube.com/watch?v=<video_id>`.
- **HN references**: if rationale cites `HN #<id>` or "Hacker News", fetch `/raw/hn/<source_daily_date>/pull.json` and match thread IDs or titles. Capture `id`, `title`, `score`, `descendants` (comment count), `url`. HN thread URL: `https://news.ycombinator.com/item?id=<id>`.
- **Trends**: fetch `/raw/trends/<source_daily_date>/pull.json` in its entirety — it's small. Call out the keyword(s) with the highest positive slope relevant to the pillar; explicitly flag if all direction=flat ("no trend tailwind").

## 3. Pull wiki context

Use `/_manifest.md` first to find the current version for each topic. Then `mcp__connapse__get_document` the following:

- `/wiki/strategy/positioning-theses.v<latest>.md` — find the hypothesis (T1–T5) whose framing best matches this candidate's pillar + angle. Quote the hypothesis text verbatim in the brief; cite by its T-number.
- `/wiki/strategy/pillar-balance.v<latest>.md` — note the current count for this candidate's pillar and whether it's flagged UNDERSUPPLIED. If it is, that's a pro-filming signal (correcting imbalance); surface it.
- `/wiki/audience/<persona>.v<latest>.md` — pick the persona by pillar + promotion_surface:
  - P1, P2, any surface → `claude-code-power-user`
  - P3 or `promotion_surface=oss|both` → `agentic-dev-indie`
  - If ambiguous, include both personas' pain-word lists.
- `/wiki/voice/connapse-brand-voice.v<latest>.md` — lift the canonical tagline verbatim, the pain phrasing, the hosted-vs-OSS framings, and the complete don't-say list.

## 4. Render HTML

Produce one self-contained HTML file — all CSS inline, no scripts, no CDN, no external images. Opens correctly offline. Print-friendly (max-width ~860px, system font stack, decent line height).

**Required sections, in this order:**

1. **Header** — `<h1>` = `<candidate_id>: <hook>`; subtitle line with pillar badge (color-coded: P1 blue, P2 red, P3 green), `promotion_surface`, weighted score, source daily date.

2. **Angle** — one paragraph verbatim from the candidate YAML.

3. **Score breakdown** — five rows (outlier_precedent, trend_slope, pain_density, audience_fit, signup_pull), each with the numeric score and a simple horizontal bar (`<span>` with inline `width: <score*200>px`, solid color background). Final row: weighted composite score.

4. **Reference videos** — table: Title (linked to youtube.com/watch?v=…), Channel, Views (formatted with thousands separators), Published (date only). 5 rows.

5. **HN discussions** — table if the rationale cited HN: Title (linked), Points, Comments, Age. Omit the section if no HN citations.

6. **Trend tailwind** — one short paragraph: which keyword is rising (if any), with slope value; or "No trend tailwind this cycle — all direction=flat" if flat.

7. **Lead with these pain words** — bullet list from the matching persona's pain signal words. If both personas were included, two labeled sub-lists.

8. **Brand voice** — canonical tagline in a `<blockquote>`; pain phrasing below.

9. **DON'T say** — red-accented list, verbatim from brand-voice don't-say.

10. **Positioning frame** — "This candidate maps to **T<n>**: <quoted hypothesis>" with a link anchor to `/wiki/strategy/positioning-theses.v<n>.md`.

11. **Pillar balance context** — one sentence: current count, flag status. If UNDERSUPPLIED, add a short "→ filming this corrects the imbalance" call-out.

12. **CTA copy** — pick one of the brand-voice framings by `promotion_surface`:
    - `hosted` → "60-second setup", "free beta", connapse.com link
    - `oss` → "Docker 60-second deploy", "MIT, self-hosted", GitHub link
    - `both` → both stacked, with hosted first
    Suggest ≤20 seconds of end-screen copy.

13. **Script outline scaffold** — four empty slotted sections for the human to fill in:
    - **Hook (0–15s)** — placeholder: "Use the tagline verbatim or the pain phrasing — don't warm up, cut straight in."
    - **Problem (15s–1:30)** — placeholder: "Show the pain on screen. One concrete metric visible (token count, response time, etc)."
    - **Solution demo (1:30–7:00)** — placeholder: "Before/after with the same metric. Show Connapse doing the work."
    - **CTA (last 30s)** — placeholder: "Per the CTA section above. Under 20 seconds. No outro music filler."
    Render each slot as a dashed-border `<div>` with grey italic placeholder text.

14. **Footer** — generation metadata: date, session URL (`$CLAUDE_CODE_REMOTE_SESSION_ID`), candidate source path. Small grey text.

**CSS target**: under ~120 lines, no vendor prefixes needed (target modern browsers only), system font stack, light theme, readable at A4 print.

Write the HTML locally to `/tmp/run/<RUN_DATE>/brief-<candidate_id>.html` first so it can be re-read/debugged without an upload round-trip.

## 5. Upload

Upload via `mcp__connapse__upload_file`:
- `containerId`: cached
- `path`: `/briefs/<RUN_DATE>/<candidate_id>.html`
- content: the rendered HTML
- description: `"Brief for <candidate_id>: <hook> (pillar <pillar>, surface <promotion_surface>)"`
- tags (if supported): `["brief", "video-plan", "<pillar>"]`

Stamp `$CLAUDE_CODE_REMOTE_SESSION_ID` into the footer of the HTML before uploading.

Do **not** update `_manifest.md`. Briefs are per-day ephemeral artifacts, not versioned evergreens. `wiki-lint` has no brief-specific rules today; briefs under `/briefs/` are out of its scope.

## 6. Return

Report back to the invoker with:
- The canonical path (`/briefs/<RUN_DATE>/<candidate_id>.html`)
- A one-line summary: `"Briefed <candidate_id> '<hook>' — <pillar> <surface>, ranked #<rank> score <score>. Open in Connapse UI."`
- If the candidate's pillar was UNDERSUPPLIED, mention it: `"Pillar <P> is currently undersupplied — filming this helps correct the imbalance."`
- If you short-circuited on ambiguity in §1, no upload happened — report the options and ask which to brief.

Exit 0.

## Abort conditions

- Connapse unreachable → abort, no stub. User gets a clear error; re-run later.
- Requested candidate ID not found in the most recent `/daily/<date>/candidates.md` → report the available IDs (from the ranking table) and ask for a retry. Do not fall through to a different day silently.
- No `/daily/<date>/candidates.md` exists at all → the research routine hasn't run yet. Tell the user to run `yt-research-daily` first.
