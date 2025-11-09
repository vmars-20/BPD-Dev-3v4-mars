---
created: 2025-11-06
type: handoff
priority: P1
status: pending
depends_on:
  - handoff-4-complete-forge-integration
---

# Handoff 5: FSM Debugging & Standards Validation

**Date:** 2025-11-06 (created)
**Session:** Post-Infrastructure Improvements
**Owner:** @claude
**Dependencies:** Handoff 4 complete
**Estimated Time:** 2-4 hours

---

## Context: Why This Handoff Exists

Handoff 4 completed the FORGE infrastructure integration (3-layer pattern, forge_cocotb package, directory reorganization). However, **FSM debugging was intentionally deferred** to keep infrastructure and debugging concerns separated.

This handoff focuses on:
1. **Diagnosing actual FSM bugs** in BPD implementation
2. **Validating FSM implementations** against project coding standards
3. **Ensuring consistency** across templates and BPD

---

## Scope

### In Scope
- ✅ BPD FSM implementation debugging (known bug exists)
- ✅ FSM coding standards validation
- ✅ Template FSM validation (ensure consistency with standards)
- ✅ FSM state export mechanisms (if needed for debugging)
- ✅ CocoTB FSM observer tests

### Out of Scope
- ❌ Infrastructure changes (completed in Handoff 4)
- ❌ FORGE control scheme modifications (stable)
- ❌ New feature development

---

## Background: Known FSM Issues

### Issue 1: BPD FSM Has Known Bug
**Status:** Deferred from earlier development phase

**What We Know:**
- BPD FSM implemented in `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`
- Entity renamed to `BPD_forge_main` (Handoff 3)
- Has known behavioral bug (exact nature TBD during debugging)
- FSM observer infrastructure exists for debugging

**What We Don't Know:**
- Exact nature of the bug (needs diagnosis)
- Which states/transitions affected
- Whether bug is logic error or timing issue

### Issue 2: FSM Coding Standards Compliance
**Reference:** Project has FSM coding guidelines (exact location TBD)

**Need to validate:**
- State encoding conventions
- Reset behavior (active-high vs active-low)
- ready_for_updates handshaking correctness
- Clock domain crossing safety
- Timeout counter implementations

### Issue 3: Template vs BPD Consistency
**Question:** Do template FSMs follow same patterns as BPD?

**Files to check:**
- `libs/platform/FORGE_App_Wrapper.vhd` (template)
- `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd` (BPD implementation)
- Any other FSM examples in forge-vhdl

---

## Tasks

### Task 5.1: Locate FSM Coding Standards
**Goal:** Find and review project FSM coding guidelines

**Likely locations:**
- `libs/forge-vhdl/docs/VHDL_CODING_STANDARDS.md`
- `libs/forge-vhdl/CLAUDE.md`
- `.claude/shared/` architecture docs
- Root `CLAUDE.md`

**Deliverable:** List of FSM coding standards to validate against

---

### Task 5.2: Diagnose BPD FSM Bug
**Goal:** Identify root cause of known FSM bug

**Approach:**
1. **Review FSM implementation:**
   - State encoding
   - Transition logic
   - Counter implementations
   - Output assignments

2. **Run CocoTB tests:**
   ```bash
   cd examples/basic-probe-driver/vhdl
   make LEVEL=P1  # Quick validation
   make LEVEL=P2  # Standard coverage
   ```

3. **Analyze FSM observer outputs:**
   - State transition sequences
   - Timing violations
   - Unexpected states

4. **Check common FSM bugs:**
   - Off-by-one errors in counters
   - Missing state transitions
   - Incorrect reset behavior
   - Race conditions

**Deliverable:** Root cause analysis + fix plan

---

### Task 5.3: Validate FSM Against Coding Standards
**Goal:** Ensure BPD FSM follows project guidelines

**Checklist (TBD based on Task 5.1):**
- [ ] State encoding style (gray code? one-hot? binary?)
- [ ] Reset behavior (active-high, synchronous)
- [ ] ready_for_updates handshaking (proper FSM states)
- [ ] Counter overflow protection
- [ ] Default case handling (`when others => FAULT`)
- [ ] Clock domain crossing (if any)
- [ ] Output glitch prevention

**Deliverable:** Compliance report + required fixes

---

### Task 5.4: Validate Template FSM Consistency
**Goal:** Ensure template FSMs match BPD patterns

**Files to review:**
- `libs/platform/FORGE_App_Wrapper.vhd`
- Any example FSMs in forge-vhdl

**Questions:**
- Do templates use same state encoding as BPD?
- Do templates implement ready_for_updates correctly?
- Are reset behaviors consistent?

**Deliverable:** Template updates (if needed)

---

### Task 5.5: Fix FSM Bug(s)
**Goal:** Implement fixes from diagnosis

**Steps:**
1. Apply fix to `BPD_forge_main`
2. Re-run CocoTB tests (P1 → P2 → P3)
3. Validate with FSM observer
4. Update documentation if behavior changed

**Deliverable:** Working FSM implementation

---

### Task 5.6: Document FSM State Export (If Needed)
**Context:** Handoff 4 deferred FSM state export to status register

**If needed for debugging:**
- Add `status_fsm_state` output port to `BPD_forge_main`
- Wire through shim to Status Register 0
- Update test wrapper to use status register (remove hardcoded IDLE)
- Document pattern in FORGE_ARCHITECTURE.md

**If NOT needed:**
- Document that test wrapper workaround is sufficient
- Keep FSM state internal to main entity

**Deliverable:** Decision + implementation (if chosen)

---

## Success Criteria

- [ ] BPD FSM bug diagnosed and fixed
- [ ] All CocoTB tests pass (P1, P2, P3)
- [ ] FSM implementation validated against coding standards
- [ ] Template FSMs consistent with BPD patterns
- [ ] FSM observer tests working (if state export implemented)
- [ ] Documentation updated with FSM patterns

---

## Files to Modify

**FSM Implementation:**
- `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`

**Testing:**
- `examples/basic-probe-driver/vhdl/cocotb_test/test_bpd_fsm_observer.py`
- `examples/basic-probe-driver/vhdl/cocotb_test/run.py`

**Templates (if needed):**
- `libs/platform/FORGE_App_Wrapper.vhd`

**Documentation:**
- `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md`
- `libs/forge-vhdl/docs/VHDL_CODING_STANDARDS.md` (if exists)

**Shim/Wrapper (if state export needed):**
- `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd`
- `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_with_observer.vhd`

---

## Resources

**FSM Implementation:**
- Main: `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`
- Shim: `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd`

**Testing Infrastructure:**
- Tests: `examples/basic-probe-driver/vhdl/cocotb_test/`
- forge_cocotb package: `libs/forge-vhdl/forge_cocotb/`

**Documentation:**
- Architecture: `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md`
- Testing guide: `libs/forge-vhdl/docs/COCOTB_TROUBLESHOOTING.md`

**Standards:**
- TBD: VHDL coding standards document

---

## Blockers

@human
- None expected
- FSM state export decision (can work around with test wrapper)
- Coding standards location (can infer from existing code if doc missing)

---

**Created:** 2025-11-06
**Status:** Pending
**Priority:** P1 (functional correctness)
**Dependencies:** Handoff 4 complete
