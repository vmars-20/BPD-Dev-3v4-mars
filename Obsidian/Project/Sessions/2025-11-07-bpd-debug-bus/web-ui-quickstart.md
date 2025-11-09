---
created: 2025-11-07
type: web-ui-quickstart
commit: 4d94b1c
---

# 🚀 WEB UI QUICK START - Phase 1

## Copy This Entire Message to Claude Code Web UI:

```
I need to implement Phase 1 of a development plan. The handoff point is at commit 4d94b1c on main branch.

TASK: Migrate wip/moku_go.py → scripts/moku-deploy.py with YAML support

Please start by:
1. Confirming you can see wip/moku_go.py (should be 361 lines)
2. Reading Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/phase1-handoff.md for detailed instructions
3. Checking that test configs exist: bpd-deployment-setup1-dummy-dut.yaml

Main requirements:
- Copy wip/moku_go.py to scripts/moku-deploy.py
- Add YAML support (currently JSON only)
- Fix imports to use libs/moku-models
- Add --dry-run flag for safe testing
- Rename app from "moku-go" to "moku-deploy"

Test your work with:
uv run python scripts/moku-deploy.py discover --timeout 2
uv run python scripts/moku-deploy.py deploy --config bpd-deployment-setup1-dummy-dut.yaml --device 192.168.73.1 --dry-run

Note: You'll be on an auto-generated branch (claude/...). This is expected and correct.

Time budget: 90 minutes
```

## What Web UI Should See

After starting, Web UI should confirm:
- ✅ File exists: `wip/moku_go.py`
- ✅ Test configs exist at root
- ✅ Documentation in `Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/`
- ✅ On branch `claude/[some-id]` at commit 4d94b1c or later

## Expected Deliverables

Web UI will create:
1. `scripts/moku-deploy.py` - Main tool
2. `scripts/lib/__init__.py` - Package marker
3. Commits with clear messages

## After Web UI Completes

1. Get commit hashes from Web UI
2. In your local terminal:
```bash
# Fetch their work
git fetch origin

# See their branch
git branch -r | grep claude

# Cherry-pick their commits
git cherry-pick [hash1] [hash2] ...
```

## Success Criteria

- Tool renamed to moku-deploy.py
- YAML files load successfully
- Discovery command works
- Deploy command supports YAML
- Dry-run mode implemented
- Tests pass with example configs