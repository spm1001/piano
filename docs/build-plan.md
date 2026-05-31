# Cross-agent tool skeleton — build plan & research brief (Code handoff)

**For:** a Claude Code session starting cold (no memory of the chat that produced this). **Human:** Sameer.
**Status:** decisions made, nothing built yet. This note is self-contained — you should not need the originating conversation.

**Desired Outcome:** Stood up a cross-agent tool that installs once and appears in Claude, Codex, and Antigravity, with a template that makes the next tool a one-command add and makes the "stale plugin / greyed-out Update button" failure structurally impossible.

---

## PART 1 — What you need to know (research distilled, May 2026)

This domain moved in the last fortnight. Re-verify paths/versions against current vendor changelogs before trusting any of it.

**Three artefact types, three convergence states:**
- **Skills** — converged on **format**, diverged on **path**. `SKILL.md` is an open standard (agentskills.io, Anthropic-originated, Apache-2.0, ~32 tools reading it). A skill = a folder with `SKILL.md` (YAML frontmatter: `name` + `description` minimum) plus optional `scripts/ references/ assets/`. Discovery paths differ: **Claude** `.claude/skills/` only; **Codex** `.agents/skills/` (project) or `~/.codex/skills/`; **Antigravity** `.agents/skills/`. Codex + Antigravity share `.agents/`; **Claude is the outlier and does NOT read `.agents/skills/` or `AGENTS.md` natively** (it reads `CLAUDE.md`). Native-AGENTS.md support is an open Anthropic request, unresolved as of late May 2026.
- **Callable tools** — converged on **MCP** across all three: stdio + streamable-HTTP. **Remote/HTTP MCP is the ONLY way to reach claude.ai web chat** (stdio is CLI/desktop only). Config files differ: Codex TOML, Antigravity `mcp_config.json`, Claude `.mcp.json`.
- **CLIs** — don't distribute bare; **wrap as an MCP server** (stdio local, HTTP for chat). Codex can even run itself as an MCP server.

**The named enemy: VENDOR DRIFT.** A tool maintained in a source repo but hand-copied ("vendored") into a monorepo silently lags. Live example that triggered this work: Mise was 0.7.3 in `spm1001/mise-en-space` but the vendored copy in `spm1001/batterie/plugins/mise` still read 0.7.2 — so every client served stale truth and the Desktop "Update" button greyed out ("On latest version") because installed-version == stale-source-version. **Design imperative: one canonical copy is the only human-edited copy; every per-agent view is generated.**

**Anthropic org plugin marketplace (Team/Enterprise, Claude-only) — verified from support.claude.com/en/articles/13837433:**
- Repo must be **private or internal, github.com only** (public repos NOT allowed for org marketplaces). The *public* test repo proves the local 3-agent loop; it can never be the org marketplace — those are two different proofs on two different repos.
- `marketplace.json` supports **relative paths** (`"source": "./plugins/x"`) fully. `github`/`url`/`git-subdir` sources work **only if the target repo is public**. `npm`/`pip` not supported.
- Doc literally says: *"If your plugin code lives in separate private repositories, copy those plugin folders into the marketplace repository (a git submodule, git subtree, or a CI step works well) and reference them with relative paths."*
- Sync: initial sync on connect; "Sync automatically" re-syncs **when a PR is merged / on push**; manual "Update" otherwise. Compares latest-vs-last-synced commit; **reads manifest, validates each plugin, REPLACES ALL plugins with current repo state**; up to **30 min**; **a failed sync can temporarily remove plugins for members** and may reset install preferences. Uses the Cowork GitHub App installation token (the App must be installed on the repo).

**Loose ends, with current verdicts (don't re-litigate these):**
- The submodule advice above is *real and correctly attributed* — but "doc blesses it" ≠ "server recurses it." The Claude CLI had a documented history of NOT recursing submodules (empty placeholder dirs). **Prefer `git subtree` or a CI-flatten step** (both put real file content in the tree, no recursion dependency). Use submodule only if Stage-0 testing proves the sync recurses.
- Intra-repo relative **symlinks** DO resolve after a plain clone (target is in-repo, unlike a submodule) — but they're fragile through the per-plugin validate step, Windows checkout, and zip packaging. So: **symlinks are fine for local agents reading the working tree; for org-synced plugin content, flatten to real files.**
- Ignore any claim about a "v1.8555.2 Desktop regression" — unverified and superseded (current Desktop is 1.9659.2, 2026-05-28).

**The cross-agent install matrix (compact):**
- Claude Code (CLI): `.claude/skills/`; `.mcp.json` (project, committable) via `claude mcp add`; stdio or `--transport http`.
- Claude Desktop / claude.ai chat: skills via installed plugin or org marketplace; **MCP into chat = remote HTTPS connector only**, brokered from Anthropic cloud (must be publicly reachable).
- Codex (CLI/IDE): `.agents/skills/` or `~/.codex/skills/` (follows symlinks); `~/.codex/config.toml` `[mcp_servers.<n>]`.
- Antigravity (CLI/IDE/desktop): `.agents/skills/` or `~/.gemini/...`; shared `~/.gemini/config/mcp_config.json`; OAuth re-authenticated per surface.

**The update mechanism per vendor (what defeats the greyed-button trap):**
- Claude: compares `plugin.json` `version` → **you MUST bump semver on every change** (and ideally cut a `<plugin>--vX.Y.Z` tag). `claude plugin marketplace update` refreshes the local clone (install does NOT auto-refresh it).
- Codex/Antigravity: skills read live from the folder (restart to refresh); MCP re-read from config on launch. No version button.
- `npx skills`: keeps a `skills-lock.json` of GitHub tree SHAs; `npx skills update`/`check` compares SHAs — drift-proof and vendor-independent.

---

## PART 2 — The plan (walking skeleton)

**Iron rule:** canonical `skills/<n>/` and `mcp/<n>/` are the ONLY files a human edits. Everything in `.claude/`, `.agents/`, rendered configs, and `plugins/*/skills/` is generated. If you ever hand-copy a tool between agent dirs, stop — that's the drift.

**Build FRESH and public first, do NOT refactor the live `batterie` monorepo** (it has the org marketplace wired and members depending on it). The clean skeleton becomes the reusable template afterwards.

- **Stage 0 — public repo, closes the local loop + resolves the unknowns.** 1 skill (`couvert`) + 1 trivial MCP (`ping`). `npx skills` projects skills into `.claude/skills/` + `.agents/skills/`; `render-configs.py` turns `servers.yaml` into the 3 MCP configs. **Benchmark:** fresh clone + one `make sync` → tool appears in Claude, Codex, Antigravity. **Run the two experiments here (private throwaway clone):** (a) does a *symlinked* skill survive an org sync, or arrive empty? (b) does a *submodule* plugin folder recurse server-side, or arrive empty? The answers pick subtree vs CI-flatten for Stage 2.
- **Stage 1 — web reach.** Deploy `ping` as public-HTTPS streamable-HTTP, add as a claude.ai custom connector. **Benchmark:** `ping` callable in chat. Proves the stdio→HTTP split is the only gate to the chat surface.
- **Stage 2 — private org propagation.** Private repo + `marketplace.json` with `./plugins/x` relative sources + "Sync automatically" on. Use subtree/CI-flatten (not submodule unless Stage 0 proved recursion). **Benchmark:** a semver bump + merge reaches all 8 members on next session — the Mise bug made structurally impossible.
- **Stage 3 — make it reusable.** GitHub **template repo** + a `new-tool` scaffold command (use `trousse:scaffold`). Adding a tool becomes one command; updating becomes `make sync && make release` (CI bumps semver + tags). **This is where the recursive "skill that maintains the skeleton" belongs** — deferred from Stage 0 because a smoke-test tool must be orthogonal to the plumbing it tests.

---

## PART 3 — The first tools

**`couvert`** — lightweight session open/close ritual, no work-tracker. Description-triggered (NOT slash-commands or hooks — those are the divergent layer, added per-agent later). Genuinely useful to Sameer; simple enough to keep the smoke test clean. (Name is a brigade nod — the cover laid before service and cleared after — rename freely.)

**`ping`** — deliberately trivial diagnostic MCP. One tool, deterministic output. Its only job is to prove transport (stdio local + HTTP into chat). Do NOT make it useful; make it certain.

---

## PART 4 — Snippets (starting points — test, don't trust)

### Repo layout
```
mit-skeleton/                      # public test repo first; pattern → mit-tools later
├── AGENTS.md                      # canonical standing instructions (Codex + Antigravity native)
├── CLAUDE.md                      # thin: "@AGENTS.md" + Claude-only lines
├── skills/                        # CANONICAL — edit here only
│   └── couvert/SKILL.md
├── mcp/                           # CANONICAL — edit here only
│   └── ping/  (uv project: pyproject.toml, src/, server.py)
├── plugins/                       # Claude wrappers — generated content, relative sources only
│   └── couvert/
│       ├── .claude-plugin/plugin.json
│       ├── skills/couvert/SKILL.md   # CI-FLATTENED real file (not a symlink for org sync)
│       └── .mcp.json
├── .claude-plugin/marketplace.json
├── servers.yaml                   # ONE source for MCP invocations
├── scripts/{render-configs.py, flatten.py, bump.py}
├── Makefile
└── .github/workflows/{release.yml, flatten.yml}
```

### skills/couvert/SKILL.md
```markdown
---
name: couvert
description: >
  Lightweight session open/close ritual — top-and-tail a work session without a
  full work-tracker. Use when the user says open/start a session ("/open", "let's
  start") or close/wrap one ("/close", "wrap up"). Orients at the start; reflects,
  captures a short note, and commits at the end.
---

# Couvert — session lifecycle (no work-tracker)

## Open
1. Orient: read the latest session note (if any) and `git status`; summarise in 2–3 lines where things stand.
2. Surface obvious open loops / unfinished edits.
3. State the session's intent in one sentence (ask once if unclear). Orientation, not interrogation.

## Close
1. Reflect: what changed this session, 3–5 past-tense bullets.
2. Name the single Next Action to resume with.
3. Capture: append a short note (date, intent, what-changed, next-action) to the session log.
4. Commit staged work with a concise message. Closing seals; it does not open new threads.
```

### mcp/ping/server.py  (FastMCP — wire entrypoint/layout via trousse:scaffold)
```python
from mcp.server.fastmcp import FastMCP
import datetime, os

mcp = FastMCP("ping")

@mcp.tool()
def ping() -> str:
    """Deterministic pong — proves the transport works."""
    return f"pong @ {datetime.datetime.utcnow().isoformat()}Z pid={os.getpid()}"

def main():
    mcp.run()  # stdio by default; for chat: mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
```
```toml
# mcp/ping/pyproject.toml  (so `uvx --from ./mcp/ping ping-server` works)
[project]
name = "ping-server"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["mcp>=1.2"]
[project.scripts]
ping-server = "ping_server.server:main"
```

### servers.yaml  (single source → all three configs)
```yaml
servers:
  ping:
    description: Trivial diagnostic — proves transport.
    transport: stdio          # 'http' for the claude.ai chat deployment
    command: uvx
    args: ["--from", "./mcp/ping", "ping-server"]
    env: []                   # names of env vars to pass through
```

### scripts/render-configs.py  (sketch — Code to harden; TOML via tomli-w)
```python
"""servers.yaml -> Claude .mcp.json + Antigravity mcp_config.json + Codex config.toml."""
import sys, yaml, json
spec = yaml.safe_load(open(sys.argv[1]))["servers"]
mcp_json = {"mcpServers": {n: {"command": s["command"], "args": s["args"]} for n, s in spec.items()}}
json.dump(mcp_json, open(".mcp.json", "w"), indent=2)        # Claude (project)
# Antigravity: same JSON shape, different path (~/.gemini/config/mcp_config.json)
# Codex: write [mcp_servers.<n>] command/args via tomli_w to .codex/config.toml
```

### plugins/couvert/.claude-plugin/plugin.json  (bump version on EVERY change)
```json
{
  "name": "couvert",
  "version": "0.1.0",
  "description": "Session lifecycle skill + ping diagnostic MCP",
  "mcpServers": {
    "ping": { "command": "uvx", "args": ["--from", "${CLAUDE_PLUGIN_ROOT}/mcp/ping", "ping-server"] }
  }
}
```

### .claude-plugin/marketplace.json  (relative source = org-sync-safe)
```json
{
  "name": "mit-skeleton",
  "owner": { "name": "Sameer Modha" },
  "plugins": [
    { "name": "couvert", "source": "./plugins/couvert",
      "description": "Session lifecycle + ping diagnostic." }
  ]
}
```

### Makefile
```make
sync:        ## project canonical skills/mcp into every agent
	npx skills add . -a claude-code -a codex -a antigravity
	python scripts/render-configs.py servers.yaml

flatten:     ## copy canonical skills into plugin dirs as REAL files (org-sync safe)
	python scripts/flatten.py        # skills/<n> -> plugins/<n>/skills/<n>

release:     ## bump plugin semver + tag (CI normally does this)
	python scripts/bump.py $(PLUGIN) $(LEVEL)   # patch|minor|major
	git tag $(PLUGIN)--v$$(python scripts/version.py $(PLUGIN))
```

---

## Caveats
- Re-verify every discovery path / config location against current changelogs (Antigravity 2.0 replaced Gemini CLI; Gemini CLI consumer-tier sunsets ~June 18 2026).
- `npx skills` (skills.sh, Vercel-led) is community-maintained with some experimental subcommands — pin a version in CI.
- Highest-leverage unknown: if Claude ships native `.agents/skills/` + `AGENTS.md`, collapse to a single `.agents/` layout and drop the Claude projection. Watch the changelog.
- The two Stage-0 experiments (symlink survival, submodule recursion) are unresolved by Sameer's existing repos — answer them empirically, don't infer.

## Next Action
Initialise the public `mit-skeleton` repo with the layout above; author `couvert` + `ping`; wire `make sync`; clone fresh and confirm both appear in all three agents.
