# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6", "tomli-w>=1.0"]
# ///
"""Render servers.yaml into the three per-agent MCP configs.

  Claude       -> .mcp.json           ({"mcpServers": {...}})        project-level
  Antigravity  -> mcp_config.json     (same JSON shape)              -> ~/.gemini/config/
  Codex        -> .codex/config.toml  ([mcp_servers.<name>])         -> ~/.codex/

This writes repo-local artifacts only. It deliberately does NOT overwrite the
user's global Antigravity/Codex configs — those must be merged, not clobbered.
The printed install paths say where each rendered file belongs.

Usage: uv run scripts/render-configs.py [servers.yaml]
"""

import json
import sys
from pathlib import Path

import tomli_w
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_servers(spec_path: Path) -> dict:
    spec = yaml.safe_load(spec_path.read_text())
    return spec.get("servers", {})


def server_entry(s: dict) -> dict:
    """Common {command, args[, env]} entry shared by all three configs."""
    entry = {"command": s["command"], "args": list(s.get("args", []))}
    # servers.yaml lists env var *names* to pass through; render as {NAME: ${NAME}}
    env_names = s.get("env") or []
    if env_names:
        entry["env"] = {name: f"${{{name}}}" for name in env_names}
    return entry


def render_json(servers: dict, out: Path) -> None:
    payload = {"mcpServers": {n: server_entry(s) for n, s in servers.items()}}
    out.write_text(json.dumps(payload, indent=2) + "\n")


def render_codex_toml(servers: dict, out: Path) -> None:
    payload = {"mcp_servers": {n: server_entry(s) for n, s in servers.items()}}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(tomli_w.dumps(payload).encode())


def main() -> int:
    spec_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "servers.yaml"
    servers = load_servers(spec_path)
    if not servers:
        print(f"No servers in {spec_path}", file=sys.stderr)
        return 1

    claude = ROOT / ".mcp.json"
    antigravity = ROOT / "mcp_config.json"
    codex = ROOT / ".codex" / "config.toml"

    render_json(servers, claude)
    render_json(servers, antigravity)
    render_codex_toml(servers, codex)

    names = ", ".join(servers)
    print(f"Rendered {len(servers)} server(s): {names}")
    print(f"  Claude       {claude.relative_to(ROOT)}   (read directly — project MCP)")
    print(f"  Antigravity  {antigravity.relative_to(ROOT)}   -> install to ~/.gemini/config/mcp_config.json")
    print(f"  Codex        {codex.relative_to(ROOT)}   -> merge into ~/.codex/config.toml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
