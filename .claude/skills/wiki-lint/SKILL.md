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
