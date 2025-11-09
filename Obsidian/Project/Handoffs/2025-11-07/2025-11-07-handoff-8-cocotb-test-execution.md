---
created: 2025-11-07
type: handoff
priority: P1
status: complete
completed: 2025-11-07
depends_on:
  - handoff-7-cocotb-test-design
test_report: Test-Reports/2025-11-07-handoff-8-test-results.md
---

# Handoff 8: CocoTB Test Execution and Validation

**Date:** 2025-11-07
**Session:** FORGE Hierarchical Voltage Encoding Testing
**Owner:** @claude
**Dependencies:** Handoff 7 complete (tests designed)
**Estimated Time:** 1-2 hours

---

## Executive Summary

Execute the CocoTB tests designed in Handoff 7 for the hierarchical encoder, validate test output quality, and iterate if needed to meet progressive testing standards.

**Scope:**
1. Run P1 tests for `forge_hierarchical_encoder.vhd`
2. Validate test output quality (<20 lines for P1)
3. Fix any test failures or VHDL bugs discovered
4. Run updated BPD FSM observer tests
5. Document test results

**Success Criteria:**
- P1 tests pass with <20 line output
- All assertions pass (green output)
- Test output is LLM-friendly (<100 tokens)
- BPD FSM observer tests still pass with new decoder

---

## Task 1: Run forge_hierarchical_encoder P1 Tests

### Execution Command

```bash
# Navigate to forge-vhdl tests directory
cd libs/forge-vhdl

# Run P1 tests (default, LLM-optimized)
uv run python tests/run.py forge_hierarchical_encoder

# Expected output: <20 lines, all green
```

### Expected Output Format

```
Running CocoTB tests for forge_hierarchical_encoder (P1_BASIC)...

forge_hierarchical_encoder.forge_hierarchical_encoder_tb
  ✓ Reset behavior                                    PASS
  ✓ State progression                                 PASS
  ✓ Status offset encoding                            PASS
  ✓ Fault detection (sign flip)                       PASS

4/4 tests passed (0 failed)
Runtime: 2.3s

PASS: forge_hierarchical_encoder P1 tests
```

### Success Criteria

**P1 Output Quality:**
- [x] Total lines: <20 (ideally 8-12)
- [x] Token count: <100
- [x] All tests pass (green)
- [x] No GHDL warnings or errors
- [x] Runtime: <5 seconds

**If output >20 lines:**
1. Check GHDL filter level (should be AGGRESSIVE for P1)
2. Reduce number of tests (3-4 tests, not 5+)
3. Simplify test assertions (fewer print statements)
4. Use `self.log()` instead of `print()` for debug info

---

## Task 2: Debug and Fix Test Failures

### Common Issues and Solutions

**Issue 1: Signed Integer Access**
```python
# WRONG: Loses sign bit
output = int(dut.voltage_out.value)

# CORRECT: Preserves sign
output = int(dut.voltage_out.value.signed_integer)
```

**Issue 2: Integer Division Rounding**
```python
# VHDL uses integer division (truncates):
status_offset <= (status_lower * 100) / 128;

# Python must match:
offset = (status_lower * 100) // 128  # Use // not /
```

**Issue 3: Reset Polarity**
```vhdl
-- Encoder uses active-high reset
if reset = '1' then
```

```python
# Test must use active-high reset
await reset_active_high(dut)  # NOT reset_active_low!
```

**Issue 4: Clock Setup**
```python
# Must setup clock before any tests
await setup_clock(dut)  # Starts clock at 10ns period
```

### Debugging Workflow

**Step 1: Run test with verbose output**
```bash
COCOTB_VERBOSITY=DEBUG uv run python tests/run.py forge_hierarchical_encoder
```

**Step 2: Inspect waveforms (if needed)**
```bash
# GHDL generates waveform files
gtkwave dump.vcd &
```

**Step 3: Add temporary debug logging**
```python
async def test_state_progression(self):
    for state in TestValues.P1_STATES:
        self.dut.state_vector.value = state
        self.dut.status_vector.value = 0x00
        await ClockCycles(self.dut.clk, 1)

        expected = TestValues.calculate_expected_digital(state, 0x00)
        actual = int(self.dut.voltage_out.value.signed_integer)

        # Temporary debug (remove after fixing)
        self.log(f"State={state}, expected={expected}, actual={actual}")

        assert actual == expected
```

**Step 4: Fix and re-run**
```bash
# Edit test or VHDL
# Re-run P1 tests
uv run python tests/run.py forge_hierarchical_encoder
```

---

## Task 3: Run P2 Tests (Optional)

### When to Run P2

**Run P2 if:**
- P1 tests all pass
- You want comprehensive validation
- Time permits (adds ~20 seconds runtime)

**Skip P2 if:**
- P1 tests reveal bugs (fix first)
- Time is limited (P1 is sufficient for basic validation)

### Execution Command

```bash
TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py forge_hierarchical_encoder

# Expected output: <50 lines, 10-15 tests
```

### P2 Success Criteria

- [x] Total lines: <50
- [x] Token count: <200
- [x] All tests pass (green)
- [x] Runtime: <30 seconds
- [x] Edge cases covered (state=31, state=63, status=0xFF)

---

## Task 4: Run Updated BPD FSM Observer Tests

### Execution Command

```bash
# Navigate to BPD test directory
cd examples/basic-probe-driver/vhdl

# Run BPD CocoTB tests
make LEVEL=P1

# Or using run.py (if registered)
uv run python cocotb_test/run.py test_bpd_fsm_observer
```

### Expected Outcome

**If decoder was updated correctly:**
- All existing tests should still pass
- New decoder extracts state + status correctly
- Fault flag tests pass (if added)

**If tests fail:**
1. Check decoder function logic (matches VHDL arithmetic)
2. Verify BPD main entity exports state/status correctly
3. Verify BPD shim instantiates encoder correctly
4. Check OutputD wiring in CustomWrapper

### Validation Steps

**Step 1: Verify state extraction**
```python
# BPD states: 0=IDLE, 1=ARMED, 2=FIRING, 3=COOLDOWN, 63=FAULT
digital_value = int(dut.OutputD.value.signed_integer)
decoded = decode_hierarchical_voltage(digital_value)

assert decoded['state'] == expected_state
```

**Step 2: Verify status extraction**
```python
# BPD status pattern: fault_flag & state[5:0] & '0'
# So status[7] = fault, status[6:1] = state copy, status[0] = 0

decoded = decode_hierarchical_voltage(digital_value)

if expected_fault:
    assert decoded['fault'] == True
    assert digital_value < 0  # Negative voltage
else:
    assert decoded['fault'] == False
    assert digital_value >= 0  # Positive voltage
```

**Step 3: Verify magnitude preservation**
```python
# When fault occurs, magnitude should preserve last normal state
# E.g., STATE=2 (normal) → FAULT should show -400 (not -12600)

normal_state = 2
fault_state = 63

# Record normal output
dut.force_state(normal_state)  # Implementation-dependent
await ClockCycles(dut.clk, 1)
normal_output = int(dut.OutputD.value.signed_integer)

# Trigger fault
dut.force_state(fault_state)
await ClockCycles(dut.clk, 1)
fault_output = int(dut.OutputD.value.signed_integer)

# Fault should be negative with same magnitude
assert fault_output == -normal_output
```

---

## Task 5: Document Test Results

### Test Report Template

Create: `Obsidian/Project/Test-Reports/2025-11-07-handoff-8-test-results.md`

```markdown
# Handoff 8 Test Results: Hierarchical Encoder

**Date:** 2025-11-07
**Tester:** @claude
**Component:** forge_hierarchical_encoder.vhd

---

## P1 Test Results

**Command:** `uv run python tests/run.py forge_hierarchical_encoder`

**Output:**
```
[Paste P1 test output here - should be <20 lines]
```

**Metrics:**
- Total tests: X
- Passed: X
- Failed: 0
- Output lines: X (<20 ✓)
- Runtime: X seconds (<5 ✓)

**Issues found:** None / [List any issues]

---

## P2 Test Results (Optional)

**Command:** `TEST_LEVEL=P2_INTERMEDIATE uv run python tests/run.py forge_hierarchical_encoder`

**Output:**
```
[Paste P2 test output here - should be <50 lines]
```

**Metrics:**
- Total tests: X
- Passed: X
- Failed: 0
- Output lines: X (<50 ✓)
- Runtime: X seconds (<30 ✓)

---

## BPD FSM Observer Test Results

**Command:** `make LEVEL=P1` (in examples/basic-probe-driver/vhdl)

**Output:**
```
[Paste BPD test output here]
```

**Decoder validation:**
- State extraction: ✓ / ✗
- Status extraction: ✓ / ✗
- Fault flag: ✓ / ✗
- Magnitude preservation: ✓ / ✗

---

## Issues and Resolutions

### Issue 1: [Description]
**Symptom:** [What went wrong]
**Root cause:** [Why it happened]
**Fix:** [How it was resolved]
**Commit:** [Git commit hash if fixed in code]

### Issue 2: ...

---

## Conclusion

**Status:** PASS / FAIL
**Next steps:** Proceed to Handoff 9 (hardware validation)
```

---

## Task 6: Commit Test Code

### Git Workflow

```bash
# Stage all test files
git add libs/forge-vhdl/tests/forge_hierarchical_encoder_tests/
git add examples/basic-probe-driver/vhdl/cocotb_test/test_bpd_fsm_observer.py
git add libs/forge-vhdl/tests/test_configs.py  # If modified

# Check status
git status

# Commit with descriptive message
git commit -m "$(cat <<'EOF'
test: Add CocoTB P1 tests for hierarchical encoder (Handoff 7-8)

Implement progressive CocoTB tests following forge-vhdl standards.

## Tests Added
- forge_hierarchical_encoder P1 tests (4 tests, <20 line output)
- Test reset behavior, state progression, status offset, fault sign flip
- BPD FSM observer decoder updated for hierarchical encoding

## Test Results
- P1 tests: X/X passed, <20 line output, <5s runtime
- BPD FSM observer: X/X passed with new decoder
- All tests green (PASS)

## Validation
- Digital domain testing (not voltages)
- Signed integer access (.signed_integer)
- Integer division matches VHDL truncation
- Active-high reset polarity

Reference: Handoff 7 (test design), Handoff 8 (execution)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push to remote
git push origin BPD-Dev-main
```

---

## Success Criteria

### P1 Tests
- [x] All tests pass (green output)
- [x] Output <20 lines
- [x] Token count <100
- [x] Runtime <5 seconds
- [x] No GHDL errors or warnings
- [x] Test code committed to git

### P2 Tests (Optional)
- [ ] All tests pass
- [ ] Output <50 lines
- [ ] Edge cases validated

### BPD Tests
- [x] FSM observer tests pass with new decoder
- [x] State extraction works
- [x] Status extraction works
- [x] Fault flag behavior correct

### Documentation
- [x] Test results documented
- [x] Issues logged and resolved
- [x] Commit message descriptive

---

## Troubleshooting Guide

### Problem: Test output >20 lines

**Diagnosis:**
```bash
# Count output lines
uv run python tests/run.py forge_hierarchical_encoder | wc -l
```

**Solutions:**
1. Reduce test count (4 tests, not 5+)
2. Check GHDL filter level:
   ```bash
   GHDL_FILTER_LEVEL=aggressive uv run python tests/run.py forge_hierarchical_encoder
   ```
3. Remove print statements (use `self.log()` for debug only)
4. Simplify assertions (don't print intermediate values)

---

### Problem: Signed integer reads as unsigned

**Symptom:**
```
Expected: -400
Actual: 65136  (0xFF70 interpreted as unsigned)
```

**Solution:**
```python
# WRONG:
output = int(dut.voltage_out.value)

# CORRECT:
output = int(dut.voltage_out.value.signed_integer)
```

---

### Problem: Integer division mismatch

**Symptom:**
```
Expected: 78 (from (127 * 100) // 128)
Actual: 78.125 (from (127 * 100) / 128)
```

**Solution:**
```python
# VHDL truncates, so Python must use //
offset = (status_lower * 100) // 128  # Integer division
```

---

### Problem: Reset doesn't clear output

**Check reset polarity:**
```vhdl
-- Encoder uses active-high reset
if reset = '1' then
```

```python
# Test must match
await reset_active_high(dut)  # NOT reset_active_low!
```

---

## Reference Documentation

### forge-vhdl Testing Docs
- `libs/forge-vhdl/CLAUDE.md` - Progressive testing standard
- `libs/forge-vhdl/tests/test_base.py` - Base class API
- `libs/forge-vhdl/tests/conftest.py` - Setup utilities

### CocoTB Documentation
- CocoTB triggers: `ClockCycles`, `RisingEdge`, etc.
- Signal access: `.value`, `.value.signed_integer`
- Assertions: Standard Python `assert`

### GHDL Documentation
- GHDL simulation: Waveform output, filtering
- GHDL filter levels: aggressive, normal, minimal, none

---

## Next Steps

**After Handoff 8 (test execution):**
1. Proceed to **Handoff 9** - Hardware validation with Moku oscilloscope
2. Create Python decoder utility for real voltage data
3. Validate on hardware (if available)

**If tests fail:**
1. Debug and fix (use troubleshooting guide)
2. Re-run tests
3. Update test report
4. Commit fixes

---

**Created:** 2025-11-07
**Status:** Pending
**Priority:** P1 (Testing)
**Dependencies:** Handoff 7 complete (tests designed)
**Estimated Completion:** 1-2 hours active work

---

**END OF HANDOFF 8**
