---
session_id: 2025-11-07-bpd-debug-bus
phase: 1
created: 2025-11-07
type: phase-handoff
---

# Phase 1 Handoff: Build moku-deploy.py

## Quick Context

**Session:** Building BPD deployment toolchain
**Current Phase:** Phase 1 of 4
**Time Budget:** 90 minutes + 15 min testing
**Branch:** sessions/2025-11-07-bpd-debug-bus

## Starting Point

**Phase 0 Complete ✅:**
- PLAN.md created in session directory
- Workspace clean, ready for development
- Found existing `wip/moku_go.py` with core functionality

## Phase 1 Objectives

### Primary Task
Migrate and enhance `wip/moku_go.py` → `scripts/moku-deploy.py`

### Key Changes Needed

1. **Rename and relocate:**
   - Copy `wip/moku_go.py` → `scripts/moku-deploy.py`
   - Update app name from "moku-go" to "moku-deploy"
   - Update all documentation strings

2. **Add YAML support:**
   ```python
   # Current: JSON only
   deployment_config = MokuConfig.model_validate_json(config.read_text())

   # Needed: JSON or YAML
   if config.suffix in ['.yaml', '.yml']:
       data = yaml.safe_load(config.read_text())
       deployment_config = MokuConfig.model_validate(data)
   else:
       deployment_config = MokuConfig.model_validate_json(config.read_text())
   ```

3. **Fix imports:**
   ```python
   # Current:
   from moku_models import (...)

   # Fix to:
   sys.path.insert(0, str(PROJECT_ROOT / "libs" / "moku-models"))
   from moku_models import (...)
   ```

4. **Fix platform resolution:**
   ```python
   # Remove MOKU_GO_PLATFORM import
   # Instead, load from YAML config or use default
   ```

## Test Files Available

Test against these existing YAML configs:
- `bpd-deployment-setup1-dummy-dut.yaml` - Self-contained testing
- `bpd-deployment-setup2-real-dut.yaml` - Live FI campaign

## Quick Test Plan

```bash
# Test discovery (dry-run safe)
uv run python scripts/moku-deploy.py discover --timeout 2

# Test list (uses cache)
uv run python scripts/moku-deploy.py list

# Test YAML loading (dry-run with --dry-run flag to add)
uv run python scripts/moku-deploy.py deploy \
  --device 192.168.73.1 \
  --config bpd-deployment-setup1-dummy-dut.yaml \
  --dry-run
```

## Success Criteria

- [ ] Tool renamed to moku-deploy.py
- [ ] YAML configs load successfully
- [ ] Discovery command works
- [ ] List command works
- [ ] Deploy command accepts YAML
- [ ] Dry-run mode added for safe testing
- [ ] Import paths corrected

## Files to Create/Modify

1. `scripts/moku-deploy.py` (main tool)
2. `scripts/lib/__init__.py` (empty, for package)
3. Optional: `scripts/lib/moku_discovery.py` (if refactoring)

## Git Commits

Suggested commit when done:
```bash
git add scripts/moku-deploy.py scripts/lib/
git commit -m "feat: Add moku-deploy.py deployment tool with YAML support

Migrate and enhance wip/moku_go.py to production tool with:
- YAML configuration support (in addition to JSON)
- Corrected import paths for monorepo structure
- Renamed to avoid collision with Moku:Go product name
- Added dry-run mode for safe testing without hardware"
```

## Commands to Start

```bash
# 1. Start fresh context
/obsd_continue_session 2025-11-07-bpd-debug-bus

# 2. Load this handoff
cat Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/phase1-handoff.md

# 3. Load the PLAN for reference
cat Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/PLAN.md

# 4. Begin implementation
cp wip/moku_go.py scripts/moku-deploy.py
```

## Notes

- Focus on core functionality only (90 min budget)
- Defer advanced features if time runs short
- Test with dry-run mode to avoid hardware requirements
- Phase 2 (bpd-debug.py) should start in another fresh context