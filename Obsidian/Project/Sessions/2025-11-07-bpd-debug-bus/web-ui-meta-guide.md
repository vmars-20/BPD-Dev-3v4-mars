---
session_id: 2025-11-07-bpd-debug-bus
type: web-ui-coordination-guide
created: 2025-11-07
---

# Claude Code Web UI Coordination Guide for Phase 1

## 🚨 Critical Context: Branch Translation

**Your Local Branch:** `sessions/2025-11-07-bpd-debug-bus`
**Web UI Branch:** `claude/[unique-session-id]` (auto-generated)

The Claude Code web UI will create its own branch for safety. This guide helps you coordinate between the two contexts.

---

## Initial Setup for Web UI

### 1. Opening Message to Web UI Claude

Copy and paste this initial context:

```
I'm working on Phase 1 of a session plan. The work is documented in my local branch sessions/2025-11-07-bpd-debug-bus, but you'll be working on your own branch.

Please read these files to understand the context:
1. Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/PLAN.md - Full implementation plan
2. Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/phase1-handoff.md - Specific Phase 1 tasks
3. wip/moku_go.py - Existing code to migrate

Phase 1 Goal: Migrate wip/moku_go.py → scripts/moku-deploy.py with YAML support

Key tasks:
- Copy wip/moku_go.py to scripts/moku-deploy.py
- Add YAML loading support
- Fix import paths for monorepo structure
- Test with existing YAML configs

Test files available:
- bpd-deployment-setup1-dummy-dut.yaml
- bpd-deployment-setup2-real-dut.yaml

Time budget: 90 minutes
```

### 2. Branch Awareness Command

After the Web UI loads, ask it to check its branch:

```
What branch are you on? Please run: git status

Note: You're on a temporary branch, but the work you do will be merged back to my sessions/2025-11-07-bpd-debug-bus branch later.
```

---

## Working in Web UI Context

### Key Reminders for Web UI

1. **Ignore branch differences** - Focus on the file changes, not branch names
2. **Use relative paths** - All paths relative to repo root work the same
3. **Test with dry-run** - Add --dry-run flag to avoid hardware dependencies
4. **Commit frequently** - Make atomic commits that can be cherry-picked

### Files Web UI Will Create/Modify

```
scripts/
├── moku-deploy.py          # Main tool (from wip/moku_go.py)
├── lib/
│   ├── __init__.py         # Package marker
│   └── moku_discovery.py   # Optional: refactored discovery
```

### Testing Commands for Web UI

These work regardless of branch:

```bash
# Test YAML loading
uv run python scripts/validate_moku_config.py bpd-deployment-setup1-dummy-dut.yaml

# Test discovery (safe, no hardware)
uv run python scripts/moku-deploy.py discover --timeout 2

# Test deployment with dry-run
uv run python scripts/moku-deploy.py deploy \
  --device 192.168.73.1 \
  --config bpd-deployment-setup1-dummy-dut.yaml \
  --dry-run  # ADD THIS FLAG!
```

---

## Syncing Changes Back

### After Web UI Completes Phase 1

1. **In Web UI, get the commit hashes:**
```bash
git log --oneline -5
```

2. **Note the branch name:**
```bash
git branch --show-current
```

3. **In your local terminal:**
```bash
# Fetch the Web UI branch
git fetch origin claude/[unique-id]:temp-phase1

# Cherry-pick the commits (use hashes from step 1)
git cherry-pick [commit1] [commit2] ...

# Or merge the whole branch
git merge temp-phase1 --no-ff

# Clean up
git branch -d temp-phase1
```

---

## Key Differences to Remember

| Aspect | Local CLI | Web UI |
|--------|-----------|---------|
| Branch | sessions/2025-11-07-bpd-debug-bus | claude/[auto-generated] |
| Session tracking | Obsidian/Project/Sessions/... | Must reference by path |
| Git workflow | Direct commits | Will need cherry-pick/merge |
| Testing | Can use hardware | Use --dry-run flag |
| Context persistence | /obsd_continue_session | Must reload from files |

---

## Communication Protocol

### From Local → Web UI
1. Create handoff files in Obsidian/Project/Sessions/
2. Reference files by full path
3. Explicitly state which files to read

### From Web UI → Local
1. Web UI makes commits with clear messages
2. Web UI provides commit hashes
3. Local cherry-picks or merges changes

---

## Phase 1 Specific Instructions for Web UI

### Must Do:
1. ✅ Migrate wip/moku_go.py → scripts/moku-deploy.py
2. ✅ Add YAML support (import yaml, handle .yaml/.yml files)
3. ✅ Fix import paths (add libs/moku-models to path)
4. ✅ Test with both YAML configs
5. ✅ Add --dry-run flag for safe testing

### Nice to Have (if time):
- Refactor discovery into scripts/lib/moku_discovery.py
- Add more comprehensive error handling
- Add progress bars with Rich

### Don't Do (save for Phase 2):
- Don't implement bpd-debug.py yet
- Don't create BPD-specific logic
- Don't add hardware-specific features

---

## Success Criteria for Web UI

The Web UI session is successful if:

1. **File exists:** `scripts/moku-deploy.py`
2. **YAML loads:** Tool can read both test YAML files
3. **Imports work:** Correct paths to libs/moku-models
4. **Tests pass:** Dry-run mode executes without errors
5. **Commits made:** Clean commits with descriptive messages

---

## Troubleshooting

### If Web UI gets confused about branches:
"Focus on creating scripts/moku-deploy.py. The branch name doesn't matter - I'll handle merging your changes back to my session branch."

### If Web UI can't find files:
"The files are at these paths relative to repo root:
- Source: wip/moku_go.py
- Target: scripts/moku-deploy.py
- Tests: bpd-deployment-setup1-dummy-dut.yaml"

### If Web UI worries about hardware:
"Add a --dry-run flag that skips actual hardware connection. Just validate the config and print what would be deployed."

---

## Final Handoff from Web UI

Ask Web UI to create a summary:

```
Please create a Phase 1 completion summary with:
1. Files created/modified
2. Key changes made
3. Test results
4. Commit hashes
5. Any issues encountered
6. Suggestions for Phase 2
```

Save this as: `Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/phase1-complete.md`

---

## Ready to Start!

1. Open Claude Code Web UI
2. Copy the initial context message above
3. Let it read the PLAN and handoff files
4. Work through Phase 1 tasks
5. Use this guide to handle branch coordination

Remember: The Web UI branch is temporary, but the work is real. Focus on the code, not the branch!