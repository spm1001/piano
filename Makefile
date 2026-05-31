# piano — regenerate every per-agent view from canonical sources.
#
# The iron rule: skills/<n>/ and mcp/<n>/ are the ONLY human-edited files.
# Everything these targets touch is generated.

# Pin the community `skills` CLI (skills.sh) so CI is reproducible.
SKILLS_VERSION ?= 1.5.9
PLUGIN ?= couvert
LEVEL  ?= patch

.PHONY: help sync flatten release smoke

help:  ## show this help
	@grep -E '^[a-z.]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

sync:  ## project canonical skills into every agent dir + render the 3 MCP configs
	# Split the call: skills@1.5.9 consolidates a combined multi-agent install
	# into .agents/ only and SKIPS the Claude copy, so claude-code must run on
	# its own to produce .claude/skills/. (Verified 2026-05-31; re-check on bumps.)
	npx --yes skills@$(SKILLS_VERSION) add . -a claude-code -y
	npx --yes skills@$(SKILLS_VERSION) add . -a codex -a antigravity -y
	uv run scripts/render-configs.py servers.yaml

flatten:  ## copy canonical skills into plugin dirs as REAL files (org-sync safe)
	python3 scripts/flatten.py

release:  ## bump a plugin's semver + tag it (CI normally does this). PLUGIN=, LEVEL=
	$(eval NEW := $(shell python3 scripts/bump.py $(PLUGIN) $(LEVEL)))
	git tag $(PLUGIN)--v$(NEW)
	@echo "bumped $(PLUGIN) -> $(NEW) and tagged $(PLUGIN)--v$(NEW)"

smoke:  ## prove the ping transport both ways (stdio + HTTP loopback)
	uv run scripts/smoke_ping.py
	uv run scripts/smoke_ping_http.py
