---
created: 2025-11-07
type: handoff
priority: P1
status: superseded
superseded_by: Test architecture redesign (commit 207949d)
depends_on:
  - handoff-6-hierarchical-voltage-encoding
completed: 2025-11-07
revision: 2025-11-07 (redesigned with specialized agents)
---

# Handoff 7: CocoTB Test Design for Hierarchical Encoder

**Date:** 2025-11-07
**Session:** FORGE Hierarchical Voltage Encoding Testing
**Owner:** @claude
**Dependencies:** Handoff 6 complete
**Estimated Time:** 2-3 hours

---

## Executive Summary

Design and implement CocoTB progressive tests for the new `forge_hierarchical_encoder.vhd` component following the forge-vhdl progressive testing standard (P1/P2/P3/P4).

**Scope:**
1. Create CocoTB tests for `forge_hierarchical_encoder.vhd` (new component)
2. Update existing BPD FSM observer tests to use new hierarchical scheme
3. Follow progressive testing standard (<20 line P1 output)

**Success Criteria:**
- P1 tests designed and implemented (<10 tests, <20 line output)
- P2 tests designed (optional, 10-15 tests)
- Test structure follows forge-vhdl standards
- Tests validate digital encoding (not voltage!)

---

## Context: forge-vhdl Progressive Testing Standard

### The Golden Rule

> **"If your P1 test output exceeds 20 lines, you're doing it wrong."**

### Test Levels

**P1 - BASIC** (Required, LLM-optimized)
- 3-5 essential tests only
- Small test values (cycles=20)
- <20 line output, <100 tokens
- <5 second runtime
- **Environment:** `TEST_LEVEL=P1_BASIC` (default)

**P2 - INTERMEDIATE** (Optional, standard validation)
- 5-10 tests with edge cases
- Realistic test values
- <50 line output
- <30 second runtime
- **Environment:** `TEST_LEVEL=P2_INTERMEDIATE`

### Test Structure (Mandatory)

```
libs/forge-vhdl/tests/
├── test_base.py                                    # Base class (DO NOT MODIFY)
├── forge_hierarchical_encoder_tests/               # NEW: Per-module directory
│   ├── forge_hierarchical_encoder_constants.py     # Shared constants
│   ├── P1_forge_hierarchical_encoder_basic.py      # Minimal tests (REQUIRED)
│   └── P2_forge_hierarchical_encoder_intermediate.py # Standard tests (OPTIONAL)
└── run.py                                           # Test runner
```

### Reference Implementation

**Existing test to reference:**
- `libs/forge-vhdl/tests/forge_util_clk_divider_tests/` (complete example)
- `libs/forge-vhdl/tests/test_base.py` (base class with verbosity control)
- `libs/forge-vhdl/tests/conftest.py` (setup utilities)

**Documentation:**
- `libs/forge-vhdl/CLAUDE.md` - Section: "CocoTB Progressive Testing Standard"
- `libs/forge-vhdl/docs/PROGRESSIVE_TESTING_GUIDE.md` (if exists)

---

## Task 1: Create forge_hierarchical_encoder CocoTB Tests

### Test Module Structure

**Location:** `libs/forge-vhdl/tests/forge_hierarchical_encoder_tests/`

**Files to create:**
1. `forge_hierarchical_encoder_constants.py` - HDL sources, test values
2. `P1_forge_hierarchical_encoder_basic.py` - Minimal tests (3-5 tests)
3. `P2_forge_hierarchical_encoder_intermediate.py` - Standard tests (optional)

### Constants File Template

```python
# forge_hierarchical_encoder_tests/forge_hierarchical_encoder_constants.py
from pathlib import Path

MODULE_NAME = "forge_hierarchical_encoder"
HDL_SOURCES = [Path("../vhdl/debugging/forge_hierarchical_encoder.vhd")]
HDL_TOPLEVEL = "forge_hierarchical_encoder"  # lowercase!

class TestValues:
    """Test values for hierarchical encoder (DIGITAL DOMAIN!)"""

    # P1: Small values for fast tests
    P1_STATES = [0, 1, 2, 3]                    # 4 states (IDLE, ARMED, FIRING, COOLDOWN)
    P1_STATUS = [0x00, 0x40, 0x7F, 0x80, 0xC0]  # Normal, mid, max, fault, fault+mid

    # P2: Comprehensive values
    P2_STATES = [0, 1, 2, 3, 4, 5, 31, 63]      # Normal + edge cases
    P2_STATUS = [0x00, 0x01, 0x7F, 0x80, 0xFF]  # Full range

    # Expected digital outputs (NOT voltages!)
    # Formula: base = state * 200, offset = (status & 0x7F) * 100 / 128
    # Output = (base + offset) if status[7]==0 else -(base + offset)

    @staticmethod
    def calculate_expected_digital(state: int, status: int) -> int:
        """Calculate expected digital output value."""
        base = state * 200
        status_lower = status & 0x7F  # Lower 7 bits
        offset = (status_lower * 100) // 128
        combined = base + offset

        fault_flag = (status >> 7) & 1
        return -combined if fault_flag else combined
```

### P1 Test Cases (3-5 tests only!)

**Test 1: Reset Behavior**
- Set state=0, status=0x00
- Assert reset drives output to 0

**Test 2: State Progression (Normal)**
- State 0→1→2→3, status=0x00
- Assert outputs: 0 → 200 → 400 → 600 digital units

**Test 3: Status Offset Encoding**
- State=2 (fixed), status=0x00 vs 0x7F
- Assert outputs: 400 vs ~478 digital units (50 unit offset)

**Test 4: Fault Detection (Sign Flip)**
- State=2, status=0x00 (normal) → +400
- State=2, status=0x80 (fault) → -400

**Test 5: Fault Magnitude Preservation** (optional for P1)
- State=3, status=0xC0 (fault + offset)
- Assert negative output with correct magnitude

### P1 Test Template

```python
# forge_hierarchical_encoder_tests/P1_forge_hierarchical_encoder_basic.py
import cocotb
from cocotb.triggers import ClockCycles
from conftest import setup_clock, reset_active_high
from test_base import TestBase
from forge_hierarchical_encoder_tests.forge_hierarchical_encoder_constants import *

class ForgeHierarchicalEncoderTests(TestBase):
    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def run_p1_basic(self):
        # P1: 3-5 ESSENTIAL tests only
        await self.test("Reset behavior", self.test_reset)
        await self.test("State progression", self.test_state_progression)
        await self.test("Status offset encoding", self.test_status_offset)
        await self.test("Fault detection (sign flip)", self.test_fault_sign_flip)

    async def test_reset(self):
        """Test reset drives output to 0."""
        await reset_active_high(self.dut)
        await ClockCycles(self.dut.clk, 1)

        actual = int(self.dut.voltage_out.value.signed_integer)
        assert actual == 0, f"Expected 0 after reset, got {actual}"

    async def test_state_progression(self):
        """Test state 0→1→2→3 produces 0→200→400→600 digital units."""
        for state in TestValues.P1_STATES:
            self.dut.state_vector.value = state
            self.dut.status_vector.value = 0x00
            await ClockCycles(self.dut.clk, 1)

            expected = TestValues.calculate_expected_digital(state, 0x00)
            actual = int(self.dut.voltage_out.value.signed_integer)

            assert actual == expected, \
                f"State={state}, status=0x00: expected {expected}, got {actual}"

    async def test_status_offset(self):
        """Test status encoding (state=2, status 0x00 vs 0x7F)."""
        state = 2

        # Test status=0x00 (no offset)
        self.dut.state_vector.value = state
        self.dut.status_vector.value = 0x00
        await ClockCycles(self.dut.clk, 1)

        expected_no_offset = TestValues.calculate_expected_digital(state, 0x00)
        actual_no_offset = int(self.dut.voltage_out.value.signed_integer)
        assert actual_no_offset == expected_no_offset

        # Test status=0x7F (max offset)
        self.dut.status_vector.value = 0x7F
        await ClockCycles(self.dut.clk, 1)

        expected_max_offset = TestValues.calculate_expected_digital(state, 0x7F)
        actual_max_offset = int(self.dut.voltage_out.value.signed_integer)
        assert actual_max_offset == expected_max_offset

        # Verify offset is positive (status adds to base)
        assert actual_max_offset > actual_no_offset

    async def test_fault_sign_flip(self):
        """Test fault flag (status[7]) flips sign."""
        state = 2

        # Normal (status[7]=0)
        self.dut.state_vector.value = state
        self.dut.status_vector.value = 0x00
        await ClockCycles(self.dut.clk, 1)

        normal_output = int(self.dut.voltage_out.value.signed_integer)
        assert normal_output > 0, "Normal output should be positive"

        # Fault (status[7]=1)
        self.dut.status_vector.value = 0x80
        await ClockCycles(self.dut.clk, 1)

        fault_output = int(self.dut.voltage_out.value.signed_integer)
        assert fault_output < 0, "Fault output should be negative"

        # Magnitude should be preserved
        assert abs(fault_output) == abs(normal_output), \
            f"Magnitude mismatch: normal={normal_output}, fault={fault_output}"

@cocotb.test()
async def test_forge_hierarchical_encoder_p1(dut):
    await setup_clock(dut)
    tester = ForgeHierarchicalEncoderTests(dut)
    await tester.run_all_tests()
```

---

## Task 2: Update BPD FSM Observer Tests

### Context

**Existing test:** `examples/basic-probe-driver/vhdl/cocotb_test/test_bpd_fsm_observer.py`

**Status:** This test used the old `fsm_observer.vhd` LUT-based pattern.

**Required changes:**
1. Update voltage decoder to use new hierarchical scheme
2. Add tests for status bit extraction
3. Verify fault flag behavior (negative voltage)

### Decoder Function Update

**Old decoder (LUT-based):**
```python
def decode_fsm_voltage(voltage_mv: float) -> int:
    """Map voltage to state via LUT."""
    # ... LUT lookup logic ...
```

**New decoder (hierarchical):**
```python
def decode_hierarchical_voltage(digital_value: int) -> dict:
    """
    Decode hierarchical voltage to state + status.

    Args:
        digital_value: Signed 16-bit digital value (from DUT)

    Returns:
        dict with 'state', 'status_lower', 'fault', 'digital_value'
    """
    # Extract fault flag (sign bit)
    fault = (digital_value < 0)
    digital_magnitude = abs(digital_value)

    # Decode state (200 digital units per state)
    state = digital_magnitude // 200
    remainder = digital_magnitude % 200

    # Decode status (0.78125 digital units per LSB)
    # Inverse: status_lower = remainder / 0.78125
    # Simplified: status_lower = (remainder * 128) / 100
    status_lower = (remainder * 128) // 100

    return {
        'state': state,
        'status_lower': status_lower,
        'fault': fault,
        'digital_value': digital_value
    }
```

### Test Updates

**Minimal changes needed:**
1. Replace `decode_fsm_voltage()` with `decode_hierarchical_voltage()`
2. Update assertions to check both state and status
3. Add fault flag tests

**Example test modification:**
```python
# OLD:
voltage_mv = analog_to_voltage(dut.OutputD.value)
state = decode_fsm_voltage(voltage_mv)
assert state == EXPECTED_STATE

# NEW:
digital_value = int(dut.OutputD.value.signed_integer)
decoded = decode_hierarchical_voltage(digital_value)
assert decoded['state'] == EXPECTED_STATE
assert decoded['status_lower'] <= 127  # 7-bit status
assert decoded['fault'] == EXPECTED_FAULT
```

---

## Task 3: Register Tests with run.py

### Update test_configs.py

**File:** `libs/forge-vhdl/tests/test_configs.py` (or equivalent registration)

**Add entry:**
```python
TEST_MODULES = {
    # ... existing tests ...

    "forge_hierarchical_encoder": {
        "constants": "forge_hierarchical_encoder_tests.forge_hierarchical_encoder_constants",
        "P1": "forge_hierarchical_encoder_tests.P1_forge_hierarchical_encoder_basic",
        "P2": "forge_hierarchical_encoder_tests.P2_forge_hierarchical_encoder_intermediate",
        "description": "Hierarchical voltage encoder (arithmetic, zero LUTs)"
    }
}
```

### Verify run.py Usage

```bash
# List all tests
uv run python tests/run.py --list

# Run P1 tests (default, LLM-optimized)
uv run python tests/run.py forge_hierarchical_encoder

# Run P2 tests with verbosity
TEST_LEVEL=P2_INTERMEDIATE COCOTB_VERBOSITY=NORMAL \
  uv run python tests/run.py forge_hierarchical_encoder
```

---

## Success Criteria

### P1 Tests
- [x] 3-5 essential tests implemented (4 tests)
- [x] Test reset behavior
- [x] Test state progression (0→1→2→3)
- [x] Test status offset encoding
- [x] Test fault sign flip
- [x] Output <20 lines when run (verified)
- [x] Runtime <5 seconds (verified)

### P2 Tests (Optional)
- [ ] 5-10 comprehensive tests
- [ ] Edge cases (state=31, state=63)
- [ ] Full status range (0x00-0xFF)
- [ ] Boundary conditions
- [ ] Output <50 lines when run

### BPD Test Updates
- [ ] Replace voltage decoder with hierarchical decoder
- [ ] Add status bit extraction tests
- [ ] Verify fault flag behavior
- [ ] Tests still pass with new encoding

### Integration
- [x] Tests registered in test_configs.py
- [x] `run.py` executes tests successfully
- [x] Tests compile without errors (1 timing issue to fix in Handoff 8)

---

## Constraints and Guidelines

### Critical Rules

1. **Test Digital Domain, Not Voltages!**
   - Encoder outputs `signed(15 downto 0)` digital values
   - Do NOT convert to voltages in tests
   - Platform-agnostic digital units

2. **Use .signed_integer for Signed Types**
   ```python
   # CORRECT:
   output = int(dut.voltage_out.value.signed_integer)

   # WRONG:
   output = int(dut.voltage_out.value)  # Loses sign!
   ```

3. **Keep P1 Tests Minimal**
   - <10 tests total
   - Small values (states 0-3, not 0-63)
   - No random testing in P1

4. **Follow forge-vhdl Patterns**
   - Inherit from `TestBase`
   - Use `conftest` utilities
   - No print statements (use `self.log()`)

### CocoTB Type Constraints

**CocoTB CANNOT access:**
- ❌ `real`, `boolean`, `time`, custom records

**CocoTB CAN access:**
- ✅ `signed`, `unsigned`, `std_logic_vector`, `std_logic`

**Our encoder uses `signed(15 downto 0)` → ✅ Compatible!**

---

## Reference Files

### forge-vhdl Documentation
- `libs/forge-vhdl/CLAUDE.md` - Progressive testing standard (authoritative)
- `libs/forge-vhdl/tests/test_base.py` - Base class implementation
- `libs/forge-vhdl/tests/conftest.py` - Setup utilities

### Existing Test Examples
- `libs/forge-vhdl/tests/forge_util_clk_divider_tests/` - Complete example
- `libs/forge-vhdl/tests/forge_lut_pkg_tests/` - Package test wrapper pattern

### Encoder Implementation
- `libs/forge-vhdl/vhdl/debugging/forge_hierarchical_encoder.vhd` - Component to test
- `Obsidian/Project/Review/HIERARCHICAL_ENCODER_DIGITAL_SCALING.md` - Design doc

### BPD Test to Update
- `examples/basic-probe-driver/vhdl/cocotb_test/test_bpd_fsm_observer.py` - Existing test

---

## Deliverables

**Files to create:**
1. `libs/forge-vhdl/tests/forge_hierarchical_encoder_tests/forge_hierarchical_encoder_constants.py`
2. `libs/forge-vhdl/tests/forge_hierarchical_encoder_tests/P1_forge_hierarchical_encoder_basic.py`
3. `libs/forge-vhdl/tests/forge_hierarchical_encoder_tests/P2_forge_hierarchical_encoder_intermediate.py` (optional)

**Files to modify:**
1. `libs/forge-vhdl/tests/test_configs.py` (or run.py registration)
2. `examples/basic-probe-driver/vhdl/cocotb_test/test_bpd_fsm_observer.py` (decoder update)

**Validation:**
- Tests run with `uv run python tests/run.py forge_hierarchical_encoder`
- P1 output <20 lines
- All tests pass (green output)

---

## Open Questions

### Question 1: P2 Test Scope
Should P2 tests include random testing or stick to deterministic edge cases?

**Options:**
- A: Deterministic only (states 0-31, status 0x00-0xFF grid)
- B: Add 10-20 random test cases
- C: Defer random testing to P3

**Recommendation:** Option A for now (P2 deterministic, P3 random if needed)

---

### Question 2: BPD Test Update Scope
Should we update ALL BPD tests or just the FSM observer test?

**Options:**
- A: Only update `test_bpd_fsm_observer.py`
- B: Update all tests that reference OutputD
- C: Add new test file for hierarchical encoding

**Recommendation:** Option A (minimal change, just update decoder function)

---

## Next Steps

**After Handoff 7 (test design):**
1. Proceed to **Handoff 8** - Run tests and validate
2. Fix any test failures
3. Iterate on P1 test selection if output >20 lines

**After Handoff 8 (test execution):**
1. Proceed to **Handoff 9** - Hardware validation with oscilloscope
2. Create Python decoder utility for real voltage data

---

**Created:** 2025-11-07
**Status:** Pending
**Priority:** P1 (Testing)
**Dependencies:** Handoff 6 complete
**Estimated Completion:** 2-3 hours active work

---

**END OF HANDOFF 7**

---

## REVISION NOTE (2025-11-07)

**Status:** This handoff has been superseded by a redesigned test architecture.

**Reason for Revision:**
- Created specialized CocoTB agent architecture (Designer + Runner agents)
- Designer agent re-did test architecture from scratch
- Found arithmetic error in original expected value calculation
  - **Original (wrong):** Status offset = 78 digital units
  - **Corrected:** Status offset = 99 digital units  
  - **Formula:** `(127 × 100) // 128 = 99` (integer division critical!)

**New Test Architecture:**
- **Location:** `Obsidian/Project/Test-Architecture/forge_hierarchical_encoder_test_design.md`
- **Git commit:** 207949dbe472b403fc9dd7ec388c254ba492683f
- **Designer agent:** `.claude/agents/cocotb-progressive-test-designer/`
- **Runner agent:** `.claude/agents/cocotb-progressive-test-runner/`

**Key Improvements:**
1. ✅ Correct expected value calculations (fixed integer division error)
2. ✅ Better test design (4 P1 tests vs original 5)
3. ✅ Complete helper function design (signal access patterns)
4. ✅ No wrapper needed (correctly identified CocoTB compatibility)
5. ✅ Implementation-ready pseudocode for Runner agent

**Next Steps:**
- Proceed to Handoff 8 with Runner agent executing new design
- Runner implements tests from: `Obsidian/Project/Test-Architecture/forge_hierarchical_encoder_test_design.md`

**Commit Reference:** 207949dbe472b403fc9dd7ec388c254ba492683f

---

**END OF REVISION NOTE**
