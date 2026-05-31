#!/usr/bin/env python3
"""Print a plugin's current semver. Usage: python scripts/version.py <plugin>"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def plugin_json(name: str) -> Path:
    return ROOT / "plugins" / name / ".claude-plugin" / "plugin.json"


def read_version(name: str) -> str:
    return json.loads(plugin_json(name).read_text())["version"]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python scripts/version.py <plugin>", file=sys.stderr)
        raise SystemExit(2)
    print(read_version(sys.argv[1]))
