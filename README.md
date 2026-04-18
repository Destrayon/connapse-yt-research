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
