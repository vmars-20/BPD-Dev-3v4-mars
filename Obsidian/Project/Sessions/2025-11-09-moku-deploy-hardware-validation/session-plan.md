---
session_id: 2025-11-09-moku-deploy-hardware-validation
created: 2025-11-09 15:30
git_branch: 3v3Out-branch (worktree: /Users/vmars20/20251109/3v3Out-Dev)
git_worktree_main: /Users/vmars20/20251109/BPD-Dev-3v4-mars
---

# Session Plan - 2025-11-09-moku-deploy-hardware-validation

## Session Scope
**Goal:** Make scripts/moku-deploy.py rock-solid for real-life hardware testing

**Context:** Transitioning from simulation/CocoTB testing to real Moku hardware deployment and validation. The moku-deploy.py script needs hardening for production hardware workflows.

**Worktree Note:** This session runs in a git worktree (`3v3Out-Dev` on `3v3Out-branch`), managed by ccmanager. Session docs commit to this branch only.

---

## Primary Objectives

- [ ] Review moku-deploy.py current capabilities and limitations
- [ ] Identify hardware-specific edge cases and failure modes
- [ ] Implement robust error handling for network/connection issues
- [ ] Add hardware state validation and safety checks
- [ ] Test deployment workflow with real Moku hardware (if available)
- [ ] Document hardware validation workflow and best practices

---

## Expected Tasks

### Phase 1: Code Review & Analysis (30-45 min)
1. Read and analyze `scripts/moku-deploy.py` implementation
2. Review moku-models integration (Pydantic validation)
3. Check FORGE control scheme handling (CR0[31:29])
4. Identify TODOs, warnings, or known limitations in code

### Phase 2: Hardware Edge Case Identification (30 min)
1. Map hardware failure scenarios:
   - Network connectivity loss mid-deployment
   - Device busy/locked by another session
   - Bitstream upload failures
   - Control register access errors
   - Platform mismatch (Go vs Lab vs Pro)
2. Review existing error handling patterns
3. Identify gaps in failure recovery

### Phase 3: Robustness Improvements (60-90 min)
1. Add connection retry logic with exponential backoff
2. Implement deployment state checkpointing
3. Add rollback capability for failed deployments
4. Enhance logging for hardware debugging
5. Add pre-deployment validation checks
6. Implement graceful degradation where possible

### Phase 4: Hardware Testing (if available) (60 min)
1. Test deployment to real Moku platform
2. Verify FORGE control scheme initialization
3. Test error recovery scenarios
4. Capture real-world edge cases
5. Document hardware-specific quirks

### Phase 5: Documentation (30 min)
1. Update moku-deploy.py docstrings
2. Create hardware deployment troubleshooting guide
3. Document tested hardware configurations
4. Add usage examples for common scenarios

---

## Active Handoffs

**Previous session context (2025-11-07):**
- Handoff 9: Hardware validation with oscilloscope (deferred)
- Focus was on hierarchical encoder testing
- This session shifts focus to deployment tooling

**Current session:** No active handoffs at start - creating fresh scope

---

## Context to Load (Tier 1)

**Always load first:**
- [x] Root llms.txt (navigation)
- [x] scripts/moku-deploy.py (primary target)
- [x] libs/moku-models/llms.txt (platform specs)
- [ ] CLAUDE.md (FORGE architecture - reference only)

**Tier 2 (if needed):**
- [ ] libs/moku-models/moku_models/*.py (Pydantic models)
- [ ] examples/basic-probe-driver/BPD-RTL.yaml (register spec example)
- [ ] Previous session handoffs (if cross-session context needed)

---

## Success Criteria

### Code Quality
- [ ] moku-deploy.py handles all identified failure modes gracefully
- [ ] Error messages are actionable (tell user what to do)
- [ ] Logging provides sufficient debug info without noise
- [ ] Code follows existing patterns (Pydantic, Typer, Rich)

### Hardware Validation
- [ ] Successfully deploys to Moku hardware without errors
- [ ] Handles connection interruptions gracefully
- [ ] Recovers from common failures (busy device, network issues)
- [ ] FORGE control scheme initialization verified on hardware

### Documentation
- [ ] Troubleshooting guide created
- [ ] Usage examples cover common scenarios
- [ ] Hardware quirks documented
- [ ] Code comments updated

---

## Known Issues & Constraints

### From moku-deploy.py code review (to be conducted):
- [ ] TODO: Identify current TODOs in code
- [ ] TODO: Check BRAM loader integration status (Layer 1 FORGE)
- [ ] TODO: Verify forge_ready flag handling
- [ ] TODO: Check platform_id detection logic

### Hardware Constraints:
- [ ] Moku hardware availability TBD
- [ ] Network latency/reliability in test environment
- [ ] Platform-specific limitations (Go vs Lab vs Pro)

---

## Notes

### Worktree Architecture Notes
- Main repo: `/Users/vmars20/20251109/BPD-Dev-3v4-mars` (on `main`)
- This worktree: `/Users/vmars20/20251109/3v3Out-Dev` (on `3v3Out-branch`)
- Session commits stay on `3v3Out-branch` (worktree-local)
- No dual-commit to main needed (standard obsd workflow modified)

### Session Management
- This session created with worktree-adapted `/obsd_new_session` workflow
- Commit strategy: Single branch (3v3Out-branch), no session branch needed
- Session docs are workspace-specific

### Related Work
- Previous focus: CocoTB simulation testing
- Current focus: Hardware deployment tooling
- Future work: Hardware validation testing (may resume Handoff 9)

---

## Risk Assessment

**High Priority Risks:**
1. **Hardware unavailability** - Can still harden code, defer testing
2. **Platform API changes** - Moku library version mismatches
3. **Network issues** - May not be testable in current environment

**Mitigation:**
- Focus on code robustness first (testable without hardware)
- Add simulation/dry-run modes for offline testing
- Document hardware assumptions clearly

---

**Created:** 2025-11-09 15:30
**Status:** Active
**Estimated Duration:** 3-4 hours
**Priority:** P1 (Hardware tooling is critical path)
