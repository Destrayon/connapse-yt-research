---
name: video-brief
description: Browse the research corpus for video ideas or generate a single-file HTML planning brief for a chosen idea. Browse mode prints a table in chat; brief mode writes ./briefs/<slug>.html to the local working directory. Pulls everything from the Connapse container via MCP.
---

# Video idea browser + brief generator (local tool)

Two modes, selected from the user's prompt:

- **Browse mode** — answers "what should I film?" in chat. Reads the research corpus, prints a table, writes nothing to disk.
- **Brief mode** — resolves to a single candidate and produces a self-contained HTML page at `./briefs/<slug>.html` for the human to open in a browser and plan a shoot from.

This skill runs **locally in Claude Code**, invoked on-demand by the human. It is not called by the cloud routines. The daily/weekly routines produce the research corpus; this skill consumes that corpus.

Briefs are **personal planning artifacts, not part of the research corpus** — they are never uploaded to the Connapse container. Do not call `mcp__connapse__upload_file` from this skill.

## Invocation dispatch

Match the user's prompt to one bucket. If ambiguous between modes, or if a brief-mode prompt resolves to multiple candidates, ask before proceeding. Write no files until confirmed.

### Browse mode triggers

Print a table (and a short follow-up) in chat. Write no files.

| Prompt pattern | Reads | Output |
|---|---|---|
| "show me today's ideas" / "what should I film today" / "today's menu" / "give me ideas from today's research" | `/daily/<latest>/candidates.md` | Today's menu table |
| "show me this week's ideas" / "this week's menu" / "what's in the last 7 days" / "ideas this week" | last 7 `/daily/*/candidates.md` | Weekly menu table |
| "what trends this week" / "what's hot" / "weekly themes" / "what should I lean into" | latest `/wiki/strategy/positioning-theses.md` + `/wiki/strategy/pillar-balance.md` | Trends summary |

### Brief mode triggers

Resolve to exactly one candidate, then run §0–§6.

| Prompt pattern | Resolver |
|---|---|
| "brief me on <slug>" / "brief <slug>" | Exact slug match in latest daily |
| "brief <C-number>" (legacy IDs, pre-slug dailies) | Exact C-number match in latest daily |
| "brief today's top pick" / "brief #1" | Rank 1 in latest daily |
| "brief #<n>" / "brief the <nth>-ranked" | Rank n in latest daily |
| "brief this week's top" | Highest weighted across last 7 dailies |
| "brief the top P<n>" / "brief the P<n> one" | Rank 1 filtered to pillar P<n> in latest daily |
| "brief the undersupplied pillar" | Rank 1 in the pillar flagged UNDERSUPPLIED in latest pillar-balance |
| "brief the <keywords> one" (e.g., "brief the token-diet one") | Fuzzy keyword match across hooks in latest daily |
| Free-text topic ("brief a video about X") | `mcp__connapse__search_knowledge(path="/daily/", query=<text>, topK=3, mode="Hybrid")` |

If the request is ambiguous or multiple candidates match, return the top 3 and ask. Do not fall through to a different day silently.

---

## Browse mode

### Today's menu

Resolve containerId and read `/daily/<latest>/candidates.md` via `mcp__connapse__get_document`. Print a Markdown table:

| # | Pillar | ID | Hook | Why it's live |
|---|---|---|---|---|

- `#` — rank from the bottom-of-file ranking table (1 = highest weighted).
- `Pillar` — P1, P2, or P3.
- `ID` — slug for new dailies, C-number for legacy.
- `Hook` — the candidate's hook, verbatim from YAML.
- `Why it's live` — one sentence distilled from the candidate's `rationale` field.

Sort rows by rank (1 first). Include every candidate in that day's file.

After the table, add exactly ONE pro-tip line choosing the highest-leverage pick in this priority order:
1. **News-cycle decay**: if a news-reaction candidate (HN-cited in rationale) sits at rank ≤3, flag it: "News-cycle window closes ~<date+2d>; `<id>` decays fastest."
2. **Undersupplied pillar**: if pillar-balance flags a pillar as UNDERSUPPLIED and a candidate in that pillar exists in the file, flag it: "`<id>` is the P<n> pick — filming it corrects the pillar imbalance."
3. **Fallback**: flag the rank-1 candidate: "`<id>` is the strongest weighted pick this cycle."

End the response with: `Say "brief me on <id>" to generate a full HTML planning brief.`

### This week's menu

List `/daily/` via `mcp__connapse__list_files`, take the 7 most recent date folders. For each, read `candidates.md`. Aggregate all candidates into one ranked list by weighted score.

If two candidates share a slug (recurring topic across days), merge into one row and annotate the Hook column with `[recurring N×]`.

Columns: same as today's menu, with an added `Date` column (or "recurring" for merged rows).

If fewer than 2 dailies have run in the 7-day window, say so explicitly and fall through to the today's-menu view.

### Weekly trends

Read `/_manifest.md` first to resolve the latest versions of `strategy/positioning-theses` and `strategy/pillar-balance`. Read both files.

Print each hypothesis as:

**T<n> — <one-line headline>**
- <two-sentence summary of the hypothesis body>
- **Actionable:** <what this means for filming this week — be specific about which candidates or pillars benefit>

Below the hypotheses, append one line citing the undersupplied pillar from pillar-balance: `This week's undersupplied pillar is P<n>: filming a P<n> video is the highest-leverage move.`

End the response with: `Want me to brief one of these? Say something like "brief the P3 one" or "brief today's top pick."`

Write no files in any browse-mode path. The response ends at the in-chat output.

---

## Brief mode

(Only enter §0 onward if brief mode was dispatched AND exactly one candidate was resolved.)

## 0. Setup

- Resolve and cache containerId via `mcp__connapse__container_list` (name: `connapse-youtube-research`).
- Verify Connapse connectivity. If the MCP is unreachable, abort and tell the user — do not write a stub HTML.

## 1. Resolve the candidate

Record for the resolved candidate:
- `id` — the candidate's ID (slug for new dailies, C-number for legacy)
- `source_daily_date` — the date folder the candidate came from
- The full YAML block (pillar, hook, angle, five score axes, rationale, cloud_compatible, promotion_surface)
- Weighted rank and score from the ranking table at the bottom of that day's `candidates.md`

Output path: `./briefs/<id>.html`. Re-running for the same ID overwrites (intended — briefs reflect the latest research state).

**Fuzzy keyword resolution**: when the user asks for "the token-diet one" or similar, search hook texts (and slugs if present) for the keyword(s). If zero matches, list the available IDs and ask. If multiple matches, list them and ask.

**By free text** (`"brief a video about X"`): `mcp__connapse__search_knowledge(path="/daily/", query="<user text>", topK=3, mode="Hybrid")`. Pick the candidate in the highest-ranked chunk. Confirm the interpretation in the return message.

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

1. **Header** — `<h1>` = `<id>: <hook>`; subtitle with pillar badge (P1 blue, P2 red, P3 green), `promotion_surface`, weighted score, source daily date.

2. **Angle** — one paragraph verbatim from the candidate YAML.

3. **Score breakdown** — five rows (outlier_precedent, trend_slope, pain_density, audience_fit, signup_pull) + weighted composite. Each row: numeric score and horizontal bar (`<span>` with inline `width: <score*200>px`, solid color background).

4. **Reference videos** — table: Title (linked to youtube.com/watch?v=…), Channel, Views (formatted with thousands separators), Published (date only). 5 rows.

5. **HN discussions** — table if the rationale cited HN: Title (linked), Points, Comments, Age. Omit the section entirely if no HN citations.

6. **Trend tailwind** — short paragraph: which keyword is rising (if any) with slope value, or "No trend tailwind this cycle — all direction=flat."

7. **Lead with these pain words** — bullet list from the matching persona's pain signal words. Two labeled sub-lists if both personas were included.

8. **Brand voice** — canonical tagline in a `<blockquote>`; pain phrasing below.

9. **DON'T say** — red-accented list, verbatim from the brand-voice don't-say.

10. **Positioning frame** — "This candidate maps to **T<n>**: <quoted hypothesis>".

11. **Pillar balance context** — one sentence: current count + flag.
    - If this candidate's pillar is UNDERSUPPLIED → "→ filming this corrects the imbalance."
    - If this candidate's pillar is NOT the undersupplied one → "→ P<n> is the undersupplied pillar this week; consider whether a P<n> candidate should jump the queue."
    - If no pillar is flagged → "→ pillar mix looks balanced; proceed on weighted-score merits."

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

Create `./briefs/` relative to cwd if it doesn't exist. Write the HTML to `./briefs/<id>.html`. Use standard file writing tools (Write); do not call MCP upload.

`/briefs/` is already in the repo `.gitignore`. If the cwd is a different git repo that doesn't already ignore it, suggest (don't auto-apply) adding `briefs/` to `.gitignore`.

## 6. Return

Report to the user:
- The local path: `./briefs/<id>.html` (absolute path also fine)
- One-line summary: `"Briefed <id> '<hook>' — <pillar> <surface>, ranked #<rank> score <score>. Open in your browser."`
- If the pillar was UNDERSUPPLIED, mention it as a pro-filming signal.
- If you short-circuited on ambiguity in §1, no file was written — list the candidate options and ask which to brief.

## Abort conditions

- Connapse MCP unreachable → abort, no stub file. Clear error to user.
- Requested candidate not found in the most recent `/daily/<date>/candidates.md` → list the available IDs and ask for a retry. Do not fall through to a different day silently.
- No `/daily/<date>/candidates.md` exists at all → tell the user the research routine hasn't run yet; point them at the cloud routine to produce a daily first.
