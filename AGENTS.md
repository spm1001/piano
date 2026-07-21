# piano — standing instructions for agents

`piano` is a **cross-agent tool skeleton**: one canonical copy of each tool that
fans out to Claude, Codex, and Antigravity. It exists to make vendor drift
structurally impossible.

## The iron rule

> Canonical `skills/<name>/` and `mcp/<name>/` are the **only** files a human
> edits. Everything in `.claude/`, `.agents/`, the rendered MCP configs, and
> `plugins/*/skills/` is **generated**.
>
> If you ever hand-copy a tool between agent directories, stop — that is the
> drift this repo exists to prevent.

## Layout

| Path | Role | Edit by hand? |
|---|---|---|
| `skills/<name>/SKILL.md` | Canonical skill | **Yes** |
| `mcp/<name>/` | Canonical MCP server (uv project) | **Yes** |
| `servers.yaml` | One source for every MCP invocation | **Yes** |
| `.claude/skills/`, `.agents/skills/` | Projected skills | No — generated |
| `.mcp.json`, `mcp_config.json`, `.codex/config.toml` | Rendered MCP configs | No — generated |
| `plugins/*/` | Claude plugin wrappers (flattened real files) | No — generated |

## How to regenerate

```sh
make sync      # project skills into every agent dir + render the 3 MCP configs
make flatten   # copy canonical skills into plugins/*/ as REAL files (org-sync safe)
make release   # bump a plugin's semver + tag (CI normally does this)
```

`make sync` runs `npx skills add .` (skills → `.claude/skills/` + `.agents/skills/`)
and `scripts/render-configs.py` (`servers.yaml` → the three MCP configs).

## Adding a tool

1. Author it once under `skills/<name>/` and/or `mcp/<name>/`.
2. Add an entry to `servers.yaml` if it's an MCP server.
3. For Claude distribution, add a `plugins/<name>/` wrapper and a
   `marketplace.json` entry (relative `./plugins/<name>` source only).
4. `make sync && make flatten`.

## Hard rules

- **Bump `plugin.json` `version` on every change to a Claude plugin.** Claude
  compares this; skipping it is what greys out the Desktop "Update" button.
- **Plugin skill content must be flattened real files** — not symlinks, not
  submodules — so it survives org-marketplace sync, Windows checkout, and zip
  packaging.
- **Keep `ping` trivial.** It is the transport smoke test; do not make it useful.

Work is tracked on a bon board in `.bon/` — read `.bon/README.md` before reading or changing anything there.
