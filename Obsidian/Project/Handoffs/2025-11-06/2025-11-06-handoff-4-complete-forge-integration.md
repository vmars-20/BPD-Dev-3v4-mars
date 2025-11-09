---
created: 2025-11-06
type: handoff
priority: P2
status: completed
completed: 2025-11-06
depends_on:
  - handoff-3-apply-template-to-bpd
---

# Handoff 4: Complete FORGE Integration & Test Infrastructure

**Date:** 2025-11-06 23:30
**Session:** Post-FORGE Template Application
**Owner:** @claude
**Dependencies:** Handoff 3 complete
**Estimated Time:** 30-60 minutes

---

## Context: What Was Just Completed

### Handoff 3 Results ✅
1. **FORGE 3-layer pattern applied:**
   - Main: `BPD_forge_main` with `bpd_*` ports
   - Shim: `app_reg_*` signals with `ready_for_updates` handshaking
   - Wrapper: FORGE control scheme (CR0[31:29])

2. **forge_cocotb package created:**
   - Reusable test infrastructure for all workspace members
   - Progressive testing preserved (P1/P2/P3/P4)
   - Proper Python imports (`from forge_cocotb import ...`)

3. **Test wrapper updated:**
   - Uses `BPD_forge_main` entity
   - Compiles cleanly
   - ⚠️ FSM state hardcoded to IDLE (workaround)

### Commits (pushed to BPD-Dev-main):
- `36e4276` - FORGE pattern implementation
- `49f3110` - forge_cocotb package
- `2c9abaa` - Test wrapper fix

---

## Outstanding Issues

### Issue 1: FSM State Not Exported
**Problem:** `BPD_forge_main` no longer exports test status ports:
```vhdl
-- Old (removed):
trig_out_active_port      : out std_logic;
intensity_out_active_port : out std_logic;
current_state_port        : out std_logic_vector(5 downto 0);

-- New: Only physical outputs
OutputA : out signed(15 downto 0);  -- DAC output
```

**Impact:**
- Test wrapper can decode trig/intensity active from OutputA/B
- Cannot decode FSM state (needed for `fsm_observer` tests)
- Currently hardcoded: `current_state_port <= "000000"` (IDLE)

**Solution Options:**
1. Add status register (SR0) to export FSM state (proper FORGE way)
2. Add test-only status ports (quick fix, bypasses production architecture)
3. Accept test limitation (fsm_observer tests won't work)

### Issue 2: Directory Naming Clarity ✅ RESOLVED
**Previous:**
```
libs/forge-vhdl/tests/          # CocoTB HDL tests
examples/.../vhdl/tests/        # CocoTB HDL tests
```

**Current (2025-11-06):**
```
libs/forge-vhdl/cocotb_test/    # Clear: CocoTB tests
examples/.../vhdl/cocotb_test/  # Won't conflict with Python unit tests
```

**Reason:** Future Python unit tests would also live in `tests/`, causing confusion.

---

## Next Steps

### Task 4.1: Implement FSM State Status Register (Recommended)

**File:** `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`

**Add status output port:**
```vhdl
entity BPD_forge_main is
    port (
        -- ... existing ports ...

        -- Status outputs (NEW)
        status_fsm_state : out std_logic_vector(5 downto 0);
    );
end entity;
```

**Implementation:**
```vhdl
-- Drive status output
status_fsm_state <= state;
```

**Update shim** (`BPD_forge_shim.vhd`):
```vhdl
signal status_fsm_state : std_logic_vector(5 downto 0);

-- In main instantiation:
status_fsm_state => status_fsm_state,

-- Pack into Status Register 0
Status0 <= x"000000" & "00" & status_fsm_state;
```

**Update test wrapper** (`CustomWrapper_bpd_with_observer.vhd`):
```vhdl
-- Remove hardcoded IDLE:
-- current_state_port <= "000000";

-- Extract from Control0[5:0] or add status signal from shim
current_state_port <= status_fsm_state;
```

### Task 4.2: Rename tests/ → cocotb_test/ ✅ COMPLETED (2025-11-06)

**Changes needed:**
```bash
# In forge-vhdl
mv libs/forge-vhdl/tests libs/forge-vhdl/cocotb_test

# In BPD
mv examples/basic-probe-driver/vhdl/tests examples/basic-probe-driver/vhdl/cocotb_test

# Update pyproject.toml testpaths
testpaths = [
    "libs/forge-vhdl/cocotb_test",
    # ... other test paths
]
```

**Impact:** Low risk, high clarity gain.

### Task 4.3: Update FORGE_ARCHITECTURE.md

**File:** `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md`

**Sections to update:**
1. Entity names (`basic_probe_driver_custom_inst_main` → `BPD_forge_main`)
2. Port naming (`arm_enable` → `bpd_arm_enable`)
3. Signal flow diagram (app_reg_* → bpd_*)
4. `ready_for_updates` handshaking
5. Status register section (if Task 4.1 done)

### Task 4.4: Run CocoTB Tests (Validation)

**Command:**
```bash
cd examples/basic-probe-driver/vhdl
uv run python cocotb_test/run.py bpd_fsm_observer
```

**Expected:**
- If Task 4.1 done: Tests should pass
- If Task 4.1 skipped: FSM state tests will fail (expected)

---

## Files Modified (Handoff 3)

1. `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`
   - Entity renamed, ports renamed, ready_for_updates logic

2. `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd`
   - app_reg_* signals, synchronization, ready_for_updates

3. `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_forge.vhd`
   - Already compliant (no changes)

4. `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_with_observer.vhd`
   - Test wrapper updated for new entity/ports

5. `libs/forge-vhdl/forge_cocotb/*`
   - New package (conftest, test_base, ghdl_filter)

---

## Success Criteria

- [ ] FSM state exported via status register or test port (DEFERRED to Handoff 5)
- [ ] Test wrapper can observe FSM state transitions (DEFERRED to Handoff 5)
- [ ] CocoTB tests run successfully (or known failures documented) (DEFERRED to Handoff 5)
- [x] Directory names clarified (tests → cocotb_test) ✅ COMPLETED
- [x] Documentation updated with new directory names ✅ COMPLETED
- [x] cocotb-integration-test agent updated for FORGE changes ✅ COMPLETED

---

## Resources

**Current Implementation:**
- Main: `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`
- Shim: `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd`
- Test wrapper: `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_with_observer.vhd`

**Test Infrastructure:**
- Package: `libs/forge-vhdl/forge_cocotb/`
- BPD tests: `examples/basic-probe-driver/vhdl/cocotb_test/`
- Runner: `cocotb_test/run.py` (uses forge_cocotb)

**Documentation:**
- Architecture: `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md`
- Testing guide: `libs/forge-vhdl/docs/COCOTB_TROUBLESHOOTING.md`

---

## Blockers

@human
- None expected
- Task 4.1 is optional (test wrapper compiles, but FSM tests limited)
- Task 4.2 is purely organizational (no functional impact)

---

**Created:** 2025-11-06 23:30
**Completed:** 2025-11-06 (partial - infrastructure tasks only)
**Status:** Completed (FSM debugging deferred to Handoff 5)
**Priority:** P2 (polish/validation)
**Dependencies:** Handoff 3 complete

---

## Completion Notes (2025-11-06)

**Completed in this session:**
- ✅ Task 4.2: Renamed `tests/` → `cocotb_test/` across workspace
- ✅ Updated pyproject.toml testpaths configuration
- ✅ Updated all documentation references (CLAUDE.md, Handoff docs, agent docs)
- ✅ Updated cocotb-integration-test agent for FORGE changes
- ✅ Created Handoff 5 for FSM debugging (future session)

**Deferred to Handoff 5:**
- Task 4.1: FSM state status register implementation
- Task 4.3: FORGE_ARCHITECTURE.md updates
- Task 4.4: CocoTB test validation

**Rationale:** Infrastructure improvements (directory reorganization, documentation) were separated from FSM debugging to keep concerns isolated. The testing infrastructure is now ready for future FSM debugging work.
