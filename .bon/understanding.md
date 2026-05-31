# piano — cross-agent tool skeleton

## What this is

A walking skeleton for **one tool that installs once and appears in Claude,
Codex, and Antigravity** — with a structure that makes the next tool a
one-command add and makes the "stale plugin / greyed-out Update button"
failure *structurally impossible*.

Full research brief: [`docs/build-plan.md`](../docs/build-plan.md). Read it
before extending this — it carries the May-2026 vendor landscape and the
reasoning behind every decision below.

This repo (`piano`) is the **fresh, public** skeleton the plan calls
`mit-skeleton`. We deliberately do **not** refactor the live `batterie`
monorepo (it has the org marketplace wired and members depending on it); the
clean skeleton becomes the reusable template afterwards.

## The iron rule (the whole point)

> Canonical `skills/<n>/` and `mcp/<n>/` are the **only** files a human edits.
> Everything in `.claude/`, `.agents/`, rendered MCP configs, and
> `plugins/*/skills/` is **generated**. If you ever hand-copy a tool between
> agent dirs, stop — that is the drift.

The named enemy is **VENDOR DRIFT**: a tool maintained in a source repo but
hand-copied ("vendored") into a monorepo silently lags. The live trigger was
Mise 0.7.3 in `mise-en-space` vs a vendored 0.7.2 in `batterie` — stale truth
served to every client, and Desktop's "Update" greyed out because
installed-version == stale-source-version.

## The three artefact types (convergence map, May 2026)

| Type | Format | Path divergence |
|---|---|---|
| **Skills** | `SKILL.md` open standard (agentskills.io, Apache-2.0) | Claude `.claude/skills/` only; Codex `.agents/skills/` or `~/.codex/skills/`; Antigravity `.agents/skills/`. **Claude is the outlier — does NOT read `.agents/` or `AGENTS.md` natively.** |
| **Callable tools** | **MCP** (stdio + streamable-HTTP), converged across all three | Config files differ: Claude `.mcp.json`, Codex TOML, Antigravity `mcp_config.json`. **Remote/HTTP MCP is the ONLY way to reach claude.ai web chat.** |
| **CLIs** | wrap as an MCP server | — |

## Architectural decisions

- **One canonical copy, every view generated.** `skills/` and `mcp/` are
  edited by hand; `npx skills` projects skills into agent dirs and
  `render-configs.py` turns `servers.yaml` into the three MCP configs.
- **For org-synced plugin content, flatten to real files — not symlinks, not
  submodules.** Symlinks resolve after a plain clone but are fragile through
  the per-plugin validate step, Windows checkout, and zip packaging.
  Submodules are *doc-blessed* but the Claude CLI has a history of NOT
  recursing them (empty placeholder dirs). Prefer `git subtree` or a
  CI-flatten step — both put real content in the tree. (Symlinks remain fine
  for *local* agents reading the working tree.)
- **Semver discipline is the anti-drift mechanism for Claude.** Claude
  compares `plugin.json` `version`; every change MUST bump semver (ideally cut
  a `<plugin>--vX.Y.Z` tag). Codex/Antigravity read skills live from the
  folder (no version button); MCP re-read from config on launch.

## Scope boundaries (what we are NOT doing)

- **Not refactoring `batterie`.** This is greenfield.
- **No slash-commands or hooks in the smoke-test tools.** Those are the
  *divergent* per-agent layer — added later, not part of the skeleton proof.
- **`ping` must stay trivial.** Its only job is to prove transport. Do NOT
  make it useful; make it certain.
- **The recursive "skill that maintains the skeleton" is Stage 3**, not Stage
  0 — a smoke-test tool must be orthogonal to the plumbing it tests.

## Gotchas / live unknowns

- **Codex is not installed on this machine (hezza).** We can *project* files
  into `.agents/skills/` (which Codex would read) and verify them, but cannot
  run a live Codex smoke-test here. Antigravity ships as `gemini` at
  `~/.local/bin/gemini`.
- **The two org-sync experiments need real org-marketplace infrastructure.**
  (a) does a symlinked skill survive an org sync, or arrive empty? (b) does a
  submodule plugin folder recurse server-side? Both require a private repo +
  the Cowork GitHub App (Team/Enterprise) — that is Stage-2 plumbing. They are
  slated in Stage 0 by the plan but are **blocked on org access** and cannot
  run purely locally. Until then, the flatten-to-real-files decision stands as
  the safe default.
- **`npx skills`** is community-maintained (skills.sh, Vercel-led) with some
  experimental subcommands — **pin a version in CI**. It auto-detects
  `claude-code` and validates the local path.
- **`uvx --from <local-path>` caches the built wheel by version — editing the
  source without bumping the version silently serves STALE code.** This is the
  project's own vendor-drift theme one layer down. Therefore the *local*
  working-tree launcher is **`uv run --directory ./mcp/<name> <script>`**
  (editable, always fresh), not `uvx`. Discovered 2026-05-31 while smoke-testing
  ping: an old stdio-only wheel kept running after the transport switch was
  added, exiting instantly on EOF (empty log, no port).
- **FastMCP ignores `FASTMCP_PORT`/`FASTMCP_HOST` env** when its constructor
  sets explicit defaults (kwargs win over env in pydantic-settings). A
  deployable MCP must read the bind address itself: `ping`'s `main()` honours
  `$PORT`/`$HOST` (PaaS convention) with `FASTMCP_*` as fallback. Matters for
  Stage 1 deployment, not just the smoke.
- **Transport is one runtime switch on one source.** `ping`'s `main()` reads
  `PING_TRANSPORT` (`stdio` default, `http` → streamable-HTTP). Two smokes prove
  both locally: `scripts/smoke_ping.py` (stdio) and `scripts/smoke_ping_http.py`
  (HTTP loopback on a dedicated port). Stage 1 is only public HTTPS + the
  claude.ai connector — no new ping code.
- **Re-verify discovery paths against current changelogs.** Antigravity 2.0
  replaced Gemini CLI; Gemini CLI consumer-tier sunsets ~18 Jun 2026. If
  Claude ships native `.agents/skills/` + `AGENTS.md`, collapse to a single
  `.agents/` layout and drop the Claude projection.

## The first two tools

- **`couvert`** — lightweight session open/close ritual, no work-tracker.
  Description-triggered (not slash-commands/hooks). Genuinely useful, simple
  enough to keep the smoke test clean.
- **`ping`** — deliberately trivial diagnostic MCP. One tool, deterministic
  output. Proves transport (stdio local + HTTP into chat).
