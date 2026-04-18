# seed/seed.py
"""One-shot seeding: writes seed/wiki/*.md so the skill can upload them via MCP."""

from pathlib import Path
from connapse_yt.frontmatter import PageMetadata, write_page

OUT = Path(__file__).parent / "wiki"
OUT.mkdir(parents=True, exist_ok=True)


def _meta(topic: str, version: int, tags: list[str]) -> PageMetadata:
    return PageMetadata(
        type="evergreen", topic=topic, date="evergreen",
        sources=["seed/seed.py"], version=version, tags=tags,
    )


def write(path: str, topic: str, body: str, tags: list[str]) -> None:
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(write_page(_meta(topic, 1, tags), body=body), encoding="utf-8")


write(
    "strategy/positioning-theses.v1.md",
    "strategy/positioning-theses",
    "# Positioning theses (v1 — cold start)\n\n## Hypothesis T1\nClaude Code power-users have three acute pains: (P1) session amnesia, (P2) bloated-context cost, (P3) no file search over their documents. Each is promotable with single-pillar hooks per §1.1 of the design spec.\n\n## Hypothesis T2\nHosted CTA wins when the pain does not require BYO storage; OSS CTA wins when it does. Mis-routed videos produce low signup conversion.\n\n## Evidence\n- Seed (no live evidence yet). First real evidence appears after 7+ daily runs.\n",
    ["positioning", "cold-start"],
)

write(
    "voice/connapse-brand-voice.v1.md",
    "voice/connapse-brand-voice",
    "# Connapse brand voice (v1)\n\n**Canonical tagline** (from OSS README — lift verbatim for hooks):\n> Stop losing context between AI sessions. Give your agents persistent, searchable memory.\n\n**Pain phrasing**:\n> Your AI agents forget everything between sessions.\n\n**Surface-specific framings**:\n- Hosted: \"Drop your docs in, Claude reads them\"; \"60-second setup\"; \"free beta\".\n- OSS: \"Point it at your S3 bucket\"; \"Docker 60-second deploy\"; \"MIT, self-hosted\".\n\n**What we do not say (inaccurate on cloud)**:\n- \"Point Connapse at your S3 bucket\" (cloud has no BYO-storage connectors).\n- \"Index your Azure Blob container\" (same).\n- \"Connect your local filesystem\" (same).\n\n**Tone**: technical, direct, no hype adjectives. Show, don't tell.\n",
    ["voice", "cold-start"],
)

write(
    "audience/claude-code-power-user.v1.md",
    "audience/claude-code-power-user",
    "# Persona: Claude Code power-user (v1)\n\n**Who**: 2-10 years dev experience, uses Claude Code daily, builds MCP servers, follows Anthropic releases same-day.\n\n**Watches on YT**: AI Jason, IndyDevDan, Cole Medin, David Ondrej.\n\n**Active subs**: r/ClaudeAI, r/ClaudeCode, r/mcp, r/LLMDevs.\n\n**Pain signal words**: \"session amnesia\", \"context window\", \"my CLAUDE.md is huge\", \"re-explaining\", \"token cost\".\n\n**Evidence**: seed.\n",
    ["persona", "cold-start"],
)

write(
    "audience/agentic-dev-indie.v1.md",
    "audience/agentic-dev-indie",
    "# Persona: Agentic dev / indie (v1)\n\n**Who**: solo or small-team builder shipping an agent product, values OSS, self-hosts when possible, reads HN.\n\n**Watches on YT**: Matthew Berman, Matt Williams, Sam Witteveen, Mervin Praison.\n\n**Active subs**: r/LocalLLaMA, r/AI_Agents, r/LangChain, r/SideProject.\n\n**Pain signal words**: \"vector DB\", \"LangChain bloat\", \"self-host\", \"RAG that just works\", \"file upload\".\n\n**Evidence**: seed.\n",
    ["persona", "cold-start"],
)

write(
    "topics/connapse-oss-landscape.v1.md",
    "topics/connapse-oss-landscape",
    "# Connapse OSS landscape (v1)\n\nRepo: https://github.com/Destrayon/Connapse (MIT, .NET 10, 11 MCP tools)\nCompanion: https://github.com/Destrayon/connapse-cli\n\n**Tech hooks worth mentioning in content**:\n- 60-second Docker deploy\n- Hybrid vector + keyword search\n- S3 / Azure Blob / local FS connectors (OSS only — cloud has managed containers)\n- REST, CLI, and MCP surfaces\n- Glama-listed MCP server\n\nAgent updates this page with current star count + open-issue count weekly via `gh api repos/Destrayon/Connapse`.\n",
    ["oss", "cold-start"],
)

write(
    "strategy/pillar-balance.v1.md",
    "strategy/pillar-balance",
    "# Pillar balance (v1 — cold start)\n\n| Pillar | Candidates last 7 days | Flag |\n|---|---|---|\n| P1 (persistent memory) | 0 | — |\n| P2 (context/cost) | 0 | — |\n| P3 (file search) | 0 | — |\n\nUpdated weekly by `positioning-synthesis`.\n",
    ["pillar-balance", "cold-start"],
)
