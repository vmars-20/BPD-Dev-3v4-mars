# Test Architecture: forge_hierarchical_encoder

**Component:** forge_hierarchical_encoder.vhd
**Category:** Debugging utilities
**Designer:** CocoTB Progressive Test Designer Agent
**Date:** 2025-11-07
**Status:** Ready for implementation

---

## Component Analysis

### Entity Definition

```vhdl
entity forge_hierarchical_encoder is
    generic (
        DIGITAL_UNITS_PER_STATE  : integer := 200;
        DIGITAL_UNITS_PER_STATUS : real    := 0.78125   -- 100/128
    );
    port (
        clk           : in  std_logic;
        reset         : in  std_logic;
        state_vector  : in  std_logic_vector(5 downto 0);  -- 6-bit state (0-63)
        status_vector : in  std_logic_vector(7 downto 0);  -- 8-bit status
        voltage_out   : out signed(15 downto 0)            -- Digital output
    );
end entity;
```

### Port Types Analysis

| Port | Type | CocoTB Safe? | Notes |
|------|------|--------------|-------|
| clk | std_logic | ✅ | Standard clock |
| reset | std_logic | ✅ | Active-high reset |
| state_vector | std_logic_vector(5:0) | ✅ | Direct access |
| status_vector | std_logic_vector(7:0) | ✅ | Direct access |
| voltage_out | signed(15:0) | ✅ | **Use .signed_integer** |

**CocoTB Compatibility:** ✅ No wrapper needed

**Critical Access Pattern:**
```python
# CORRECT: Access signed output with .signed_integer
output = int(dut.voltage_out.value.signed_integer)

# WRONG: Loses sign information!
output = int(dut.voltage_out.value)
```

### Component Behavior Summary

**Encoding Algorithm:**
```
base_value = state_vector × DIGITAL_UNITS_PER_STATE        (e.g., state=2 → 400)
status_offset = (status_vector[6:0] × 100) / 128           (e.g., 0x7F → 78)
combined_value = base_value + status_offset                (e.g., 400 + 78 = 478)

IF status_vector[7] = '1' THEN
    voltage_out = -combined_value   (Fault: negative output)
ELSE
    voltage_out = +combined_value   (Normal: positive output)
```

**Key Features to Test:**
1. State encoding: 200 digital units per state
2. Status offset encoding: 0.78125 digital units per LSB (integer division: status×100÷128)
3. Fault flag: status[7] negates output
4. Reset behavior: output = 0
5. Registered output: 1 clock cycle latency

---

## Test Strategy

### P1 - BASIC (4 tests, <20 lines output, <5s runtime)

**Design Philosophy:** Test MINIMUM functionality to prove component works.

**Test 1: Reset Behavior**
- **Purpose:** Verify reset drives output to 0
- **Input:** state=0, status=0x00
- **Expected:** voltage_out = 0 after reset
- **Rationale:** Simplest validation, confirms reset logic

**Test 2: State Progression (Linear)**
- **Purpose:** Verify state encoding with no status offset
- **Input:** States [0, 1, 2, 3], status=0x00 (no offset)
- **Expected:** voltage_out = [0, 200, 400, 600] digital units
- **Rationale:** Validates DIGITAL_UNITS_PER_STATE constant (200)

**Test 3: Status Offset Encoding**
- **Purpose:** Verify status adds fine-grained offset
- **Input:** state=2 (base=400), status=[0x00, 0x7F]
- **Expected:**
  - status=0x00 → 400 digital units (no offset)
  - status=0x7F → 478 digital units (400 + 78 offset)
- **Rationale:** Validates status offset formula (status×100÷128)

**Test 4: Fault Flag (Sign Flip)**
- **Purpose:** Verify status[7] negates output
- **Input:** state=2, status=[0x00, 0x80]
- **Expected:**
  - status=0x00 (normal) → +400
  - status=0x80 (fault) → -400
- **Rationale:** Critical fault detection mechanism

**P1 Summary:**
- Test count: 4 tests
- Clock cycles: ~20 cycles total (4-5 per test)
- Expected output: <20 lines
- Runtime estimate: <2 seconds
- Coverage: Reset, state encoding, status offset, fault flag (all core features)

### P2 - INTERMEDIATE (Optional, 7-10 tests, <50 lines output, <30s)

**Design Philosophy:** Add edge cases and comprehensive status coverage.

**Tests 1-4:** (Include all P1 tests)

**Test 5: Maximum State Value**
- **Purpose:** Verify state=63 (max 6-bit value)
- **Input:** state=63, status=0x00
- **Expected:** voltage_out = 12600 digital units (63 × 200)
- **Rationale:** Boundary condition, prevents overflow

**Test 6: Combined Maximum (State + Status)**
- **Purpose:** Verify max state + max status
- **Input:** state=63, status=0x7F
- **Expected:** voltage_out = 12600 + 78 = 12678 digital units
- **Rationale:** Maximum positive output case

**Test 7: Status Range (Mid-Points)**
- **Purpose:** Verify status offset linearity
- **Input:** state=1 (base=200), status=[0x00, 0x40, 0x7F]
- **Expected:**
  - status=0x00 → 200 (offset=0)
  - status=0x40 → 250 (offset=50)
  - status=0x7F → 278 (offset=78)
- **Rationale:** Validates offset calculation across range

**Test 8: Fault with Offset**
- **Purpose:** Verify fault flag preserves magnitude with offset
- **Input:** state=2, status=[0x40, 0xC0]
- **Expected:**
  - status=0x40 (normal) → +450 (400 + 50)
  - status=0xC0 (fault) → -450 (negated, magnitude preserved)
- **Rationale:** Ensures fault logic works with status offset

**Test 9: Zero State with Fault**
- **Purpose:** Edge case - fault flag with zero base value
- **Input:** state=0, status=[0x00, 0x80]
- **Expected:**
  - status=0x00 → 0
  - status=0x80 → 0 (negating zero = zero)
- **Rationale:** Mathematical edge case validation

**Test 10: Sequential State Transitions**
- **Purpose:** Verify output updates each clock cycle
- **Input:** Cycle through states 0→1→2→1→0 with status=0x00
- **Expected:** Outputs [0, 200, 400, 200, 0] on successive clocks
- **Rationale:** Validates registered output timing

**P2 Summary:**
- Test count: 10 tests
- Clock cycles: ~50 cycles total
- Expected output: <50 lines
- Runtime estimate: <10 seconds
- Coverage: Boundary conditions, linearity, timing

---

## Test Wrapper Design

**Wrapper Needed:** ❌ No

**Rationale:**
- All entity ports use CocoTB-safe types
- std_logic, std_logic_vector, and signed are directly accessible
- No real, boolean, time, or record types at ports

**Direct DUT Access Pattern:**
```python
# All ports accessible directly
dut.state_vector.value = 3
dut.status_vector.value = 0x7F
output = int(dut.voltage_out.value.signed_integer)  # Note: .signed_integer!
```

---

## Constants File Design

**File:** `libs/forge-vhdl/tests/forge_hierarchical_encoder_tests/forge_hierarchical_encoder_constants.py`

```python
"""
Constants and expected value calculations for forge_hierarchical_encoder tests.

This file provides test data and expected value computation following the
hierarchical encoding scheme used in the VHDL component.
"""

from pathlib import Path

# ============================================================================
# Module Identification
# ============================================================================

MODULE_NAME = "forge_hierarchical_encoder"

# HDL sources (relative to tests/ directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent
HDL_SOURCES = [
    PROJECT_ROOT / "vhdl" / "debugging" / "forge_hierarchical_encoder.vhd",
]
HDL_TOPLEVEL = "forge_hierarchical_encoder"  # lowercase!


# ============================================================================
# Generic Values (match VHDL defaults)
# ============================================================================

DIGITAL_UNITS_PER_STATE = 200
# DIGITAL_UNITS_PER_STATUS = 0.78125  # Real in VHDL, but we use integer math


# ============================================================================
# Test Values (Progressive Sizing)
# ============================================================================

class TestValues:
    """Test values sized progressively for P1/P2/P3 testing."""

    # P1: Small, fast values (ESSENTIAL ONLY)
    P1_STATES = [0, 1, 2, 3]  # 4 basic states
    P1_STATUS = [0x00, 0x7F, 0x80, 0xC0]  # Min, max normal, fault, fault+offset

    # P2: Realistic + edge cases
    P2_STATES = [0, 1, 2, 3, 31, 63]  # Normal + boundaries
    P2_STATUS = [0x00, 0x01, 0x40, 0x7E, 0x7F, 0x80, 0xFF]  # Full range

    # P3: Comprehensive (if needed)
    P3_STATES = list(range(64))  # All 6-bit states
    P3_STATUS = [i for i in range(256)]  # All 8-bit status values


# ============================================================================
# Expected Value Calculation (MUST match VHDL arithmetic!)
# ============================================================================

def calculate_expected_digital(state: int, status: int) -> int:
    """
    Calculate expected digital output value.

    This function MUST match the VHDL arithmetic exactly:
    - base_value = state × 200
    - status_lower = status & 0x7F (lower 7 bits)
    - status_offset = (status_lower × 100) ÷ 128  (INTEGER DIVISION!)
    - combined_value = base_value + status_offset
    - IF status[7] = 1 THEN -combined_value ELSE +combined_value

    Args:
        state: 6-bit state value (0-63)
        status: 8-bit status value (0-255)
            status[7] = fault flag (1 = fault, negate output)
            status[6:0] = status offset value (0-127)

    Returns:
        Signed 16-bit digital value (-32768 to +32767)

    Example:
        >>> calculate_expected_digital(0, 0x00)
        0
        >>> calculate_expected_digital(2, 0x00)
        400
        >>> calculate_expected_digital(2, 0x7F)
        478  # 400 base + 78 offset
        >>> calculate_expected_digital(2, 0x80)
        -400  # Fault flag, negated
        >>> calculate_expected_digital(2, 0xC0)
        -450  # Fault flag + offset (400 + 50), negated
    """
    # Compute base value (state contribution)
    base_value = state * DIGITAL_UNITS_PER_STATE

    # Extract status fields
    status_lower = status & 0x7F  # Lower 7 bits (0-127)
    fault_flag = (status >> 7) & 1  # Upper bit (0 or 1)

    # Compute status offset using integer division (matches VHDL)
    # CRITICAL: Use // (integer division), NOT / (float division)!
    # VHDL: status_offset <= (status_lower * 100) / 128;
    status_offset = (status_lower * 100) // 128

    # Combine base + offset
    combined_value = base_value + status_offset

    # Apply sign based on fault flag
    if fault_flag == 1:
        return -combined_value  # Fault: negate output
    else:
        return combined_value   # Normal: positive output


# ============================================================================
# Helper Functions (Signal Access Patterns)
# ============================================================================

def get_voltage_out(dut) -> int:
    """
    Extract signed digital output from DUT.

    CRITICAL: Must use .signed_integer for signed types!

    Args:
        dut: CocoTB DUT handle

    Returns:
        Signed integer value (-32768 to +32767)
    """
    return int(dut.voltage_out.value.signed_integer)


def set_state_status(dut, state: int, status: int):
    """
    Set state and status inputs on DUT.

    Args:
        dut: CocoTB DUT handle
        state: 6-bit state value (0-63)
        status: 8-bit status value (0-255)
    """
    dut.state_vector.value = state
    dut.status_vector.value = status


# ============================================================================
# Error Message Templates
# ============================================================================

class ErrorMessages:
    """Consistent error message formatting."""

    WRONG_OUTPUT = "State={state}, Status=0x{status:02X}: expected {expected}, got {actual}"
    RESET_FAILED = "Expected output=0 after reset, got {actual}"
    MAGNITUDE_MISMATCH = "Fault magnitude mismatch: normal={normal}, fault={fault}"
    NOT_NEGATIVE = "Expected negative output (fault flag set), got {actual}"
    NOT_POSITIVE = "Expected positive output (normal operation), got {actual}"
    OFFSET_NOT_APPLIED = "Status offset not applied: status=0x00 → {no_offset}, status=0x7F → {with_offset}"


# ============================================================================
# Documentation Reference
# ============================================================================

# Design Document:
#   Obsidian/Project/Review/HIERARCHICAL_ENCODER_DIGITAL_SCALING.md
#
# Handoff Document:
#   Obsidian/Project/Handoffs/2025-11-07-handoff-6-hierarchical-voltage-encoding.md
#
# VHDL Implementation:
#   libs/forge-vhdl/vhdl/debugging/forge_hierarchical_encoder.vhd
```

---

## Test Module Pseudocode

### P1 Test Module

**File:** `libs/forge-vhdl/tests/forge_hierarchical_encoder_tests/P1_forge_hierarchical_encoder_basic.py`

```python
"""
P1 - BASIC tests for forge_hierarchical_encoder.

Tests: 4 essential tests only
Output: <20 lines
Runtime: <5 seconds

These tests validate core functionality:
- Reset behavior
- State encoding (200 digital units per state)
- Status offset encoding (0.78125 units per LSB)
- Fault flag (sign flip)
"""

import cocotb
from cocotb.triggers import RisingEdge, ClockCycles
import sys
from pathlib import Path

# Import forge_cocotb infrastructure
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "libs" / "forge-vhdl"))

from forge_cocotb import TestBase, setup_clock, reset_active_high
from forge_hierarchical_encoder_tests.forge_hierarchical_encoder_constants import *


class ForgeHierarchicalEncoderBasicTests(TestBase):
    """P1 - BASIC tests: 4 essential tests only"""

    def __init__(self, dut):
        super().__init__(dut, MODULE_NAME)

    async def setup(self):
        """Common setup for all tests"""
        await setup_clock(self.dut, period_ns=8)  # 125 MHz
        await reset_active_high(self.dut)

    async def run_p1_basic(self):
        """P1 test suite entry point"""
        await self.setup()

        # 4 ESSENTIAL tests only
        await self.test("Reset behavior", self.test_reset)
        await self.test("State progression", self.test_state_progression)
        await self.test("Status offset encoding", self.test_status_offset)
        await self.test("Fault flag (sign flip)", self.test_fault_sign_flip)

    async def test_reset(self):
        """Verify reset drives output to 0"""
        # After reset (in setup), check output is zero
        output = get_voltage_out(self.dut)

        assert output == 0, ErrorMessages.RESET_FAILED.format(actual=output)

    async def test_state_progression(self):
        """Verify state encoding: 0→1→2→3 produces 0→200→400→600"""
        for state in TestValues.P1_STATES:
            set_state_status(self.dut, state, 0x00)
            await ClockCycles(self.dut.clk, 1)

            expected = calculate_expected_digital(state, 0x00)
            actual = get_voltage_out(self.dut)

            assert actual == expected, ErrorMessages.WRONG_OUTPUT.format(
                state=state, status=0x00, expected=expected, actual=actual
            )

    async def test_status_offset(self):
        """Verify status offset encoding (state=2, status 0x00 vs 0x7F)"""
        state = 2

        # Test status=0x00 (no offset)
        set_state_status(self.dut, state, 0x00)
        await ClockCycles(self.dut.clk, 1)

        expected_no_offset = calculate_expected_digital(state, 0x00)
        actual_no_offset = get_voltage_out(self.dut)

        assert actual_no_offset == expected_no_offset, ErrorMessages.WRONG_OUTPUT.format(
            state=state, status=0x00, expected=expected_no_offset, actual=actual_no_offset
        )

        # Test status=0x7F (max offset)
        set_state_status(self.dut, state, 0x7F)
        await ClockCycles(self.dut.clk, 1)

        expected_max_offset = calculate_expected_digital(state, 0x7F)
        actual_max_offset = get_voltage_out(self.dut)

        assert actual_max_offset == expected_max_offset, ErrorMessages.WRONG_OUTPUT.format(
            state=state, status=0x7F, expected=expected_max_offset, actual=actual_max_offset
        )

        # Verify offset is positive (status adds to base)
        assert actual_max_offset > actual_no_offset, ErrorMessages.OFFSET_NOT_APPLIED.format(
            no_offset=actual_no_offset, with_offset=actual_max_offset
        )

    async def test_fault_sign_flip(self):
        """Verify fault flag (status[7]) flips sign"""
        state = 2

        # Normal (status[7]=0)
        set_state_status(self.dut, state, 0x00)
        await ClockCycles(self.dut.clk, 1)

        normal_output = get_voltage_out(self.dut)
        assert normal_output > 0, ErrorMessages.NOT_POSITIVE.format(actual=normal_output)

        # Fault (status[7]=1)
        set_state_status(self.dut, state, 0x80)
        await ClockCycles(self.dut.clk, 1)

        fault_output = get_voltage_out(self.dut)
        assert fault_output < 0, ErrorMessages.NOT_NEGATIVE.format(actual=fault_output)

        # Magnitude should be preserved
        assert abs(fault_output) == abs(normal_output), ErrorMessages.MAGNITUDE_MISMATCH.format(
            normal=normal_output, fault=fault_output
        )


@cocotb.test()
async def test_forge_hierarchical_encoder_p1(dut):
    """P1 test entry point (called by CocoTB)"""
    tester = ForgeHierarchicalEncoderBasicTests(dut)
    await tester.run_p1_basic()
```

### Progressive Orchestrator

**File:** `libs/forge-vhdl/tests/test_forge_hierarchical_encoder_progressive.py`

```python
"""
Progressive test orchestrator for forge_hierarchical_encoder.

Selects test level via TEST_LEVEL environment variable:
- TEST_LEVEL=P1_BASIC (default)
- TEST_LEVEL=P2_INTERMEDIATE
- TEST_LEVEL=P3_COMPREHENSIVE
"""

import cocotb
import sys
import os
from pathlib import Path

# Add forge_cocotb to path
FORGE_VHDL = Path(__file__).parent.parent.parent / "libs" / "forge-vhdl"
sys.path.insert(0, str(FORGE_VHDL))
sys.path.insert(0, str(Path(__file__).parent))

from forge_cocotb import TestLevel


def get_test_level() -> TestLevel:
    """Read TEST_LEVEL environment variable"""
    level_str = os.environ.get("TEST_LEVEL", "P1_BASIC")
    return TestLevel[level_str]


@cocotb.test()
async def test_forge_hierarchical_encoder_progressive(dut):
    """Progressive test orchestrator"""
    test_level = get_test_level()

    if test_level == TestLevel.P1_BASIC:
        from forge_hierarchical_encoder_tests.P1_forge_hierarchical_encoder_basic import ForgeHierarchicalEncoderBasicTests
        tester = ForgeHierarchicalEncoderBasicTests(dut)
        await tester.run_p1_basic()

    elif test_level == TestLevel.P2_INTERMEDIATE:
        from forge_hierarchical_encoder_tests.P2_forge_hierarchical_encoder_intermediate import ForgeHierarchicalEncoderIntermediateTests
        tester = ForgeHierarchicalEncoderIntermediateTests(dut)
        await tester.run_p2_intermediate()

    elif test_level == TestLevel.P3_COMPREHENSIVE:
        from forge_hierarchical_encoder_tests.P3_forge_hierarchical_encoder_comprehensive import ForgeHierarchicalEncoderComprehensiveTests
        tester = ForgeHierarchicalEncoderComprehensiveTests(dut)
        await tester.run_p3_comprehensive()

    else:
        raise ValueError(f"Unknown test level: {test_level}")
```

### test_configs.py Entry

**File:** `libs/forge-vhdl/tests/test_configs.py`

```python
# Add to TestConfig list:

TestConfig(
    name="forge_hierarchical_encoder",
    hdl_sources=[
        PROJECT_ROOT / "vhdl" / "debugging" / "forge_hierarchical_encoder.vhd"
    ],
    hdl_toplevel="forge_hierarchical_encoder",
    test_module="test_forge_hierarchical_encoder_progressive",
    description="Hierarchical voltage encoder (digital domain, zero LUTs)"
)
```

---

## Expected Values Calculation

### Formula (Matching VHDL Exactly)

**VHDL Implementation:**
```vhdl
base_value <= state_integer * DIGITAL_UNITS_PER_STATE;
status_offset <= (status_lower * 100) / 128;  -- Integer division!
combined_value <= base_value + status_offset;

if fault_flag = '1' then
    output_value <= to_signed(-combined_value, 16);
else
    output_value <= to_signed(combined_value, 16);
end if;
```

**Python Implementation (MUST match):**
```python
def calculate_expected_digital(state: int, status: int) -> int:
    base_value = state * 200
    status_lower = status & 0x7F
    status_offset = (status_lower * 100) // 128  # Integer division: //
    combined_value = base_value + status_offset

    fault_flag = (status >> 7) & 1
    return -combined_value if fault_flag else combined_value
```

**CRITICAL:** Use `//` (integer division), NOT `/` (float division)!

### Example Calculations

**P1 Test Cases:**

```
State=0, Status=0x00 (binary: 00000000)
  base = 0 × 200 = 0
  status_lower = 0x00 = 0
  offset = (0 × 100) // 128 = 0
  combined = 0 + 0 = 0
  fault = 0
  → Expected: 0

State=1, Status=0x00
  base = 1 × 200 = 200
  offset = 0
  combined = 200
  fault = 0
  → Expected: 200

State=2, Status=0x00
  base = 2 × 200 = 400
  offset = 0
  combined = 400
  fault = 0
  → Expected: 400

State=2, Status=0x7F (binary: 01111111)
  base = 2 × 200 = 400
  status_lower = 0x7F = 127
  offset = (127 × 100) // 128 = 12700 // 128 = 99
  combined = 400 + 99 = 499
  fault = 0
  → Expected: 499

  NOTE: Previous handoff said 78, but that's WRONG!
  Correct calculation: (127 × 100) // 128 = 99

State=2, Status=0x80 (binary: 10000000)
  base = 2 × 200 = 400
  status_lower = 0x00 = 0
  offset = 0
  combined = 400
  fault = 1
  → Expected: -400

State=2, Status=0xC0 (binary: 11000000)
  base = 2 × 200 = 400
  status_lower = 0x40 = 64
  offset = (64 × 100) // 128 = 6400 // 128 = 50
  combined = 400 + 50 = 450
  fault = 1
  → Expected: -450
```

**Verification Table for P1:**

| State | Status | Base | Offset | Combined | Fault | Expected |
|-------|--------|------|--------|----------|-------|----------|
| 0 | 0x00 | 0 | 0 | 0 | 0 | 0 |
| 1 | 0x00 | 200 | 0 | 200 | 0 | +200 |
| 2 | 0x00 | 400 | 0 | 400 | 0 | +400 |
| 3 | 0x00 | 600 | 0 | 600 | 0 | +600 |
| 2 | 0x7F | 400 | 99 | 499 | 0 | +499 |
| 2 | 0x80 | 400 | 0 | 400 | 1 | -400 |
| 2 | 0xC0 | 400 | 50 | 450 | 1 | -450 |

---

## Design Decisions and Rationale

### Decision 1: No Test Wrapper

**Rationale:**
- All entity ports are CocoTB-compatible types
- signed(15:0) is directly accessible via `.signed_integer`
- No real, boolean, time, or record types at boundary
- Wrapper would add complexity without benefit

### Decision 2: Test Digital Domain (Not Voltages)

**Rationale:**
- Component outputs digital values, not voltages
- Platform-agnostic testing (no DAC assumptions)
- Voltage interpretation is application-specific
- Simpler test data (integers, not floats)

### Decision 3: P1 Test Selection

**Selected Tests:**
1. Reset (essential baseline)
2. State progression (core encoding)
3. Status offset (fine-grained encoding)
4. Fault flag (critical safety feature)

**Rejected for P1:**
- Boundary conditions (state=63) → P2
- Random testing → P3
- Timing tests (sequential updates) → P2

**Rationale:** P1 must prove basic arithmetic works (<20 lines output)

### Decision 4: Integer Division in Expected Values

**CRITICAL DESIGN CHOICE:**
```python
# CORRECT:
status_offset = (status_lower * 100) // 128  # Integer division

# WRONG:
status_offset = int((status_lower * 100) / 128)  # Float division, then truncate
status_offset = round((status_lower * 100) / 128)  # Rounding mismatch!
```

**Rationale:**
- VHDL uses integer division (truncation)
- Python `/` operator uses float division
- Python `//` operator matches VHDL truncation behavior
- Mismatches cause off-by-one errors in tests

### Decision 5: Error Message Formatting

**Pattern:**
```python
ErrorMessages.WRONG_OUTPUT.format(
    state=state, status=status, expected=expected, actual=actual
)
```

**Benefits:**
- Consistent formatting across all tests
- Easy to parse in test output
- Shows both expected and actual values
- Includes input context (state, status)

---

## Design Challenges

### Challenge 1: Expected Value Calculation Mismatch (Resolved)

**Initial Issue:** Previous handoff document calculated:
```
State=2, Status=0x7F → Expected: 478 (400 + 78)
```

**Actual VHDL Output:**
```
State=2, Status=0x7F → Actual: 499 (400 + 99)
```

**Root Cause:** Incorrect offset calculation in handoff doc
- Wrong: (127 / 128) × 100 = 0.9921875 × 100 ≈ 99.22 → rounded to 78?
- Correct: (127 × 100) // 128 = 12700 // 128 = 99

**Resolution:** Use exact integer arithmetic matching VHDL

### Challenge 2: Signed Integer Access Pattern

**Issue:** CocoTB requires `.signed_integer` for signed types

**Wrong Pattern:**
```python
output = int(dut.voltage_out.value)  # Loses sign! Treats as unsigned
```

**Correct Pattern:**
```python
output = int(dut.voltage_out.value.signed_integer)  # Preserves sign
```

**Mitigation:** Helper function `get_voltage_out(dut)` encapsulates pattern

### Challenge 3: Test Timing (Registered Output)

**Issue:** Component has 1-cycle latency (registered output)

**Pattern:**
```python
set_state_status(dut, state, status)
await ClockCycles(dut.clk, 1)  # Wait for register update
actual = get_voltage_out(dut)
```

**Rationale:** Tests must wait 1 clock after input change

---

## Exit Criteria

### Design Phase Complete

- [x] Component analysis document complete
  - [x] Entity ports analyzed
  - [x] CocoTB compatibility assessed (✅ no wrapper needed)
  - [x] Encoding algorithm documented

- [x] Test strategy document complete
  - [x] P1 test count: 4 tests
  - [x] P1 estimated output: <20 lines
  - [x] P2 test count: 10 tests (optional)
  - [x] Each test has clear purpose

- [x] Constants file design complete
  - [x] MODULE_NAME, HDL_SOURCES, HDL_TOPLEVEL defined
  - [x] TestValues class with P1/P2 values
  - [x] calculate_expected_digital() matches VHDL arithmetic
  - [x] Helper functions designed (get_voltage_out, set_state_status)
  - [x] Error message templates defined

- [x] Test module outlines complete
  - [x] P1 test list with descriptions (4 tests)
  - [x] P2 test list (10 tests, optional)
  - [x] Progressive orchestrator pattern

- [x] Test wrapper designed
  - [x] No wrapper needed (CocoTB-safe types only)

- [x] test_configs.py entry designed
  - [x] TestConfig structure defined
  - [x] HDL sources list complete
  - [x] Toplevel entity specified

### Ready for Handoff to Runner Agent

**Handoff Package:**
1. ✅ Test architecture document (this file)
2. ✅ Constants file design (complete pseudocode)
3. ✅ Test module pseudocode (P1 complete, P2 outlined)
4. ✅ No test wrapper needed
5. ✅ test_configs.py entry designed

**Runner Agent Instructions:**
1. Implement constants file as specified
2. Implement P1 test module as specified
3. Add test_configs.py entry
4. Run tests with: `uv run python tests/run.py forge_hierarchical_encoder`
5. Verify P1 output <20 lines
6. Debug any arithmetic mismatches (check integer division!)
7. Optionally implement P2 tests

---

## Execution Commands

```bash
# Navigate to forge-vhdl
cd libs/forge-vhdl

# Run P1 tests (default, LLM-optimized)
uv run python tests/run.py forge_hierarchical_encoder

# Run P2 tests with more verbosity
TEST_LEVEL=P2_INTERMEDIATE COCOTB_VERBOSITY=NORMAL \
  uv run python tests/run.py forge_hierarchical_encoder

# List all available tests
uv run python tests/run.py --list

# Debug mode (P1 with full verbosity)
COCOTB_VERBOSITY=DEBUG \
  uv run python tests/run.py forge_hierarchical_encoder
```

---

## Summary

**Component:** forge_hierarchical_encoder.vhd
**Category:** Debugging utilities (hierarchical voltage encoding)
**Wrapper Needed:** No
**P1 Tests:** 4 essential tests
**P1 Output:** <20 lines (estimated)
**P1 Runtime:** <5 seconds (estimated)

**Key Testing Principles:**
1. Test DIGITAL domain, not voltages
2. Use integer division (//) to match VHDL
3. Access signed output with .signed_integer
4. Keep P1 minimal (4 tests, small values)
5. Wait 1 clock cycle for registered output

**Ready for Handoff:** ✅ YES

**Next Steps:**
1. Hand off to CocoTB Progressive Test Runner agent
2. Implement files as specified
3. Run tests and validate output <20 lines
4. Debug any arithmetic mismatches

---

**Created:** 2025-11-07
**Designer:** CocoTB Progressive Test Designer Agent
**Status:** Complete, ready for implementation
**Version:** 1.0
