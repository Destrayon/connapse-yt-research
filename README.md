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
