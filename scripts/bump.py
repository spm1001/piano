#!/usr/bin/env python3
"""Bump a plugin's semver. Usage: python scripts/bump.py <plugin> <patch|minor|major>

Bumping the plugin.json version on every change is the anti-drift mechanism for
Claude: it compares this version to decide whether the Desktop "Update" button is
live. A skipped bump is what greys it out ("On latest version").

Uses a targeted regex replace of just the version field, so the diff is one line
and other formatting (e.g. multi-line arg arrays) is untouched.
"""

import re
import sys
from pathlib import Path

from version import plugin_json, read_version

LEVELS = ("patch", "minor", "major")


def bump(name: str, level: str) -> str:
    if level not in LEVELS:
        raise SystemExit(f"unknown level {level!r}; choose one of {LEVELS}")
    cur = read_version(name)
    major, minor, patch = (int(x) for x in cur.split("."))
    if level == "major":
        major, minor, patch = major + 1, 0, 0
    elif level == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    new = f"{major}.{minor}.{patch}"

    path = plugin_json(name)
    text = path.read_text()
    pattern = r'("version"\s*:\s*")' + re.escape(cur) + r'(")'
    new_text, n = re.subn(pattern, r"\g<1>" + new + r"\g<2>", text, count=1)
    if n != 1:
        raise SystemExit(f"could not find version {cur!r} in {path}")
    path.write_text(new_text)
    return new


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python scripts/bump.py <plugin> <patch|minor|major>", file=sys.stderr)
        raise SystemExit(2)
    print(bump(sys.argv[1], sys.argv[2]))
