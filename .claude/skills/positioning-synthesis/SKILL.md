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
