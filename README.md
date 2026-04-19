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

### Reddit data source

As of Nov 2025 Reddit's Responsible Builder Policy (RBP) requires manual pre-approval for all new API keys. Until approval lands we pull from **`old.reddit.com/r/<sub>/top.json`**, the public unauthenticated JSON view. Real data, fresh scores, no third-party service in the loop. Our daily volume (~8 requests/day across 8 subs) is well below Reddit's unauthenticated rate ceiling (~60 req/min per IP).

Set `REDDIT_USER_AGENT` in the cloud environment to identify this deployment (e.g. `connapse-yt-research/0.1 by u/<handle>`). Reddit throttles requests without descriptive UAs. If unset we fall back to a generic project UA.

If Reddit tightens unauthenticated access and starts 429'ing this path, apply for RBP at https://support.reddithelp.com/hc/en-us/requests/new and switch `src/connapse_yt/pull/reddit.py` back to a praw client once approved.

### Troubleshooting

- **"quotaExceeded" on YouTube**: daily run caught it; the next day's run will fall back to cached channels. Raise the quota in Google Cloud Console if this recurs.
- **Connapse auth expired**: reconnect the connector on claude.ai and rerun.
- **Pillar imbalance flagged**: the weekly `pillar-balance.vN.md` called it out. Adjust the daily skill's `--query` list to favor the under-represented pillar for 1-2 weeks.
- **Reddit 429 / 403 / 502**: unauthenticated `old.reddit.com` path got throttled. Short-term: set a unique `REDDIT_USER_AGENT` and retry the next day. Long-term: apply for Reddit RBP approval.
