# piano (Claude)

Claude does not read `AGENTS.md` natively, so import the canonical standing
instructions here:

@AGENTS.md

## Claude-only notes

- Claude reads skills from `.claude/skills/` only (not `.agents/skills/`). Run
  `make sync` to (re)project them.
- Claude distribution goes through the **plugin** wrapper in `plugins/couvert/`
  and `.claude-plugin/marketplace.json`. Bump `plugin.json` `version` on every
  change — Claude compares it, and a skipped bump is what greys out the Desktop
  "Update" button.

Work is tracked on a bon board in `.bon/` — read `.bon/README.md` before reading or changing anything there.
