#!/usr/bin/env python3
"""Flatten canonical sources into plugin dirs as REAL files (no symlinks).

For every plugin `plugins/<name>/`:
  - copy the matching canonical skill `skills/<name>/` (if any) to
    `plugins/<name>/skills/<name>/`
  - copy every canonical MCP server the plugin references in its
    `plugin.json` mcpServers args (a `${CLAUDE_PLUGIN_ROOT}/mcp/<server>` token)
    to `plugins/<name>/mcp/<server>/`

Why real files, not symlinks or submodules: org-marketplace sync, Windows
checkout, and zip packaging are all hostile to symlinks, and the Claude CLI has
a history of not recursing submodules. Real files in the tree are the only form
that survives all three, AND they make the plugin self-contained — its
${CLAUDE_PLUGIN_ROOT}/mcp/... reference resolves wherever it is installed.
See .bon/understanding.md.

Usage: python scripts/flatten.py
"""

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
MCP = ROOT / "mcp"
PLUGINS = ROOT / "plugins"

MCP_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/mcp/([^/\"]+)")

# Never bundle build/venv cruft into a plugin.
IGNORE = shutil.ignore_patterns(".venv", "__pycache__", "*.pyc", "*.egg-info", ".pytest_cache")


def copy_real(src: Path, dest: Path, label: str) -> None:
    if dest.is_symlink():
        dest.unlink()  # never leave a symlink where real files must go
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=IGNORE)
    assert not dest.is_symlink(), f"{dest} must be real, not a symlink"
    print(f"  {label}: {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)} (real files)")


def referenced_mcp_servers(plugin_dir: Path) -> set[str]:
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return set()
    data = json.loads(manifest.read_text())
    names: set[str] = set()
    for server in (data.get("mcpServers") or {}).values():
        for arg in server.get("args", []):
            names.update(MCP_REF.findall(str(arg)))
    return names


def main() -> int:
    if not PLUGINS.is_dir():
        print(f"No plugins/ dir at {PLUGINS}", file=sys.stderr)
        return 1

    did = 0
    for plugin in sorted(p for p in PLUGINS.iterdir() if p.is_dir()):
        name = plugin.name
        # 1. the matching skill (by convention plugins/<name> bundles skills/<name>)
        skill = SKILLS / name
        if skill.is_dir():
            copy_real(skill, plugin / "skills" / name, f"skill {name}")
            did += 1
        # 2. every MCP server the plugin references
        for server in sorted(referenced_mcp_servers(plugin)):
            src = MCP / server
            if not src.is_dir():
                print(f"  WARN {name}: references mcp/{server} but {src} is missing", file=sys.stderr)
                continue
            copy_real(src, plugin / "mcp" / server, f"mcp {server}")
            did += 1

    if did == 0:
        print("Nothing flattened.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
