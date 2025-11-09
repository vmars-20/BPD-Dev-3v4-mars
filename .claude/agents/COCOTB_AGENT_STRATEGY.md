# CocoTB Testing Agent Strategy

**Version:** 1.0 (2025-11-07)
**Purpose:** Specialized agent architecture for CocoTB testing in forge-vhdl
**Status:** ✅ Production-ready

---

## Overview

This document describes the **three-agent strategy** for CocoTB testing in the BPD-Dev monorepo:

1. **cocotb-progressive-test-designer** - Designs test architecture
2. **cocotb-progressive-test-runner** - Implements and executes tests
3. **cocotb-integration-test** - Full system integration testing

---

## Agent Comparison Matrix

| Aspect | Designer | Runner | Integration |
|--------|----------|--------|-------------|
| **Scope** | Unit tests (components) | Unit tests (components) | System tests (full app) |
| **Phase** | Design | Implementation | Validation |
| **Input** | VHDL component | Test design | Complete system |
| **Output** | Test architecture doc | Working tests | Integration report |
| **Executes Tests?** | ❌ No | ✅ Yes | ✅ Yes |
| **Designs Tests?** | ✅ Yes | ❌ No | ✅ Yes (integration level) |
| **GHDL Debugging?** | ❌ No | ✅ Yes | ✅ Yes |
| **Context** | forge-vhdl components | forge-vhdl components | BPD/full instruments |

---

## Workflow: Unit Testing a forge-vhdl Component

### Example: Testing forge_hierarchical_encoder

**Step 1: Designer Phase**

**User request:**
> "I need to test the forge_hierarchical_encoder component in libs/forge-vhdl/vhdl/packages/"

**Load agent:**
```
Use cocotb-progressive-test-designer
```

**Designer tasks:**
1. Read `libs/forge-vhdl/vhdl/packages/forge_hierarchical_encoder.vhd`
2. Analyze entity ports (check CocoTB compatibility)
3. Design P1 test strategy (2-4 essential tests)
4. Calculate expected values (match VHDL arithmetic)
5. Design constants file structure
6. Create test architecture document

**Designer output:**
```markdown
# Test Architecture: forge_hierarchical_encoder

## Component Analysis
- Entity: forge_hierarchical_encoder
- Category: packages
- Ports: clk, reset (active-high), state_vector[5:0], status_vector[7:0], voltage_out[signed 15:0]
- CocoTB compatibility: ✅ (all std_logic/signed/unsigned)

## Test Strategy

### P1 - BASIC (4 tests, <20 lines)
1. Reset behavior - Verify voltage_out=0 after reset
2. State progression - Test 3 states (0,1,2) → voltage mapping
3. Status offset - Verify status adds offset to base voltage
4. Fault detection - Verify bit 7 flips sign

### Expected Values
```python
def calculate_expected_digital(state: int, status: int) -> int:
    base_voltage = state * 200
    status_lower = status & 0x7F
    status_offset = (status_lower * 100) // 128  # Integer division!
    voltage = base_voltage + status_offset
    if status & 0x80:
        voltage = -voltage
    return voltage
```

### Constants File Design
- MODULE_NAME: "forge_hierarchical_encoder"
- P1_STATES: [0, 1, 2]
- P1_STATUS: [0x00, 0x80]
- Helper: get_voltage_out(dut) → signed integer access
```

**Handoff:** Designer gives test architecture to Runner

---

**Step 2: Runner Phase**

**Load agent:**
```
Use cocotb-progressive-test-runner
```

**Runner tasks:**
1. Receive test architecture from designer
2. Implement constants file (`forge_hierarchical_encoder_constants.py`)
3. Implement P1 test module (`P1_forge_hierarchical_encoder_basic.py`)
4. Implement progressive orchestrator (`test_forge_hierarchical_encoder_progressive.py`)
5. Add entry to `test_configs.py`
6. Execute tests: `uv run python cocotb_test/run.py forge_hierarchical_encoder`
7. Debug failures (signed access, integer division, reset polarity)
8. Iterate until all tests pass

**Runner output:**
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

**Success:** P1 tests complete, <20 lines, all green ✅

---

**Step 3: Optional P2/P3 (Runner continues)**

If needed, runner implements P2/P3 levels:
- P2: 5-10 tests, edge cases, realistic values
- P3: 10-25 tests, boundary conditions, comprehensive

---

## Workflow: Integration Testing BPD

### Example: Testing BPD FSM Observer

**User request:**
> "I need to test the BPD FSM observer integration with the hierarchical encoder decoder"

**Load agent:**
```
Use cocotb-integration-test
```

**Integration tester tasks:**
1. Read full BPD system (CustomWrapper → Shim → Main + decoder)
2. Design integration test strategy (Python → Registers → FSM → Hardware outputs)
3. Implement decoder validation tests
4. Execute: `make LEVEL=P1` in examples/basic-probe-driver/vhdl
5. Validate state/status extraction works end-to-end

**Key difference from unit testing:**
- **Unit tests:** Single component in isolation (forge_hierarchical_encoder)
- **Integration tests:** Full system with multiple components (BPD + encoder + decoder)

---

## When to Use Which Agent

### Use cocotb-progressive-test-designer when:
- ✅ Starting fresh test design for a forge-vhdl component
- ✅ Need test architecture for utilities/packages/debugging modules
- ✅ Have VHDL component, need test strategy
- ✅ Don't have test implementation yet

### Use cocotb-progressive-test-runner when:
- ✅ Have test design from designer agent
- ✅ Need to implement Python test code
- ✅ Need to execute tests and debug failures
- ✅ Fixing broken tests

### Use cocotb-integration-test when:
- ✅ Testing full instrument (BPD, CustomInstrument, etc.)
- ✅ Need end-to-end validation
- ✅ Testing register communication (Python → VHDL)
- ✅ Validating FSM integration

---

## Agent Handoff Pattern

### Pattern 1: Fresh Component Testing

```
User → Designer Agent
       ↓ (test architecture doc)
       Runner Agent
       ↓ (working tests)
       User (tests complete)
```

### Pattern 2: Fixing Broken Tests

```
User → Runner Agent (skip designer, go straight to implementation)
       ↓ (debug + fix)
       User (tests fixed)
```

### Pattern 3: Integration After Unit Tests

```
User → Designer Agent (unit test design)
       ↓
       Runner Agent (unit test implementation)
       ↓
       Integration Agent (system validation)
       ↓
       User (full validation complete)
```

---

## Context Loading Strategy

### Designer Agent Context (Tier 2)

**Always load:**
- `libs/forge-vhdl/CLAUDE.md` - Testing standards
- `libs/forge-vhdl/llms.txt` - Component catalog
- `libs/forge-vhdl/docs/COCOTB_TROUBLESHOOTING.md` - Type constraints

**Load as needed:**
- VHDL source file to test
- Reference test implementations (forge_util_clk_divider, forge_lut_pkg)

**Don't load:**
- Test execution infrastructure (runner concern)
- GHDL internals (runner concern)

### Runner Agent Context (Tier 2 + 3)

**Always load:**
- Test architecture from designer
- `libs/forge-vhdl/CLAUDE.md` - Testing standards
- `libs/forge-vhdl/docs/COCOTB_TROUBLESHOOTING.md` - Debugging guide

**Load as needed:**
- VHDL source (for debugging)
- Reference implementations (for patterns)
- forge_cocotb infrastructure (test_base.py, conftest.py)

**Don't load:**
- Test design documents (designer concern)

### Integration Agent Context (Tier 2 + 3)

**Always load:**
- `libs/forge-vhdl/CLAUDE.md` - Testing standards
- Full system VHDL (CustomWrapper, Shim, Main)
- BPD-RTL.yaml or equivalent specification

**Load as needed:**
- Integration test examples (BPD FSM observer)
- forge_cocotb infrastructure

---

## Agent Strengths & Limitations

### Designer Agent

**Strengths:**
- ✅ Excellent at analyzing VHDL entities
- ✅ Strong understanding of CocoTB type constraints
- ✅ Good at calculating expected values (matches VHDL arithmetic)
- ✅ Designs token-efficient test strategies

**Limitations:**
- ❌ Doesn't execute tests (no GHDL debugging)
- ❌ Can't validate if design works (needs runner)
- ❌ Pseudocode only (not full implementation)

### Runner Agent

**Strengths:**
- ✅ Excellent at Python/CocoTB implementation
- ✅ Strong GHDL debugging skills
- ✅ Good at fixing test failures (signal access, timing)
- ✅ Validates output quality (<20 lines)

**Limitations:**
- ❌ Doesn't redesign test architecture (follows designer)
- ❌ Can't make strategic test decisions (test count, strategy)
- ❌ Assumes design is correct

### Integration Agent

**Strengths:**
- ✅ Excellent at full system understanding
- ✅ Strong integration testing patterns
- ✅ Good at FSM/register validation
- ✅ Understands CustomInstrument wrappers

**Limitations:**
- ❌ Not focused on individual components
- ❌ Different scope from unit testing
- ❌ Assumes component tests already pass

---

## Agent Specialization Benefits

### Before Specialization (One Agent)

**Problems:**
- 🔴 Single agent overwhelmed with design + implementation + execution
- 🔴 Mixes test strategy with implementation details
- 🔴 Hard to delegate partial work
- 🔴 Context bloat (loads everything)

### After Specialization (Three Agents)

**Benefits:**
- ✅ Clear separation of concerns (design vs implementation vs integration)
- ✅ Easier delegation (user can stop after design phase)
- ✅ Reduced context per agent (more efficient)
- ✅ Parallel workflows possible (design next component while running previous)
- ✅ Better expertise per domain (focused knowledge)

---

## Summary

**Three-Agent Strategy:**

1. **cocotb-progressive-test-designer**
   - Scope: forge-vhdl component test architecture
   - Phase: Design
   - Output: Test strategy document

2. **cocotb-progressive-test-runner**
   - Scope: forge-vhdl component test implementation
   - Phase: Implementation + Execution
   - Output: Working tests (<20 lines P1)

3. **cocotb-integration-test**
   - Scope: Full system integration
   - Phase: Validation
   - Output: Integration test report

**Key Principle:** Separation of design (what to test) from implementation (how to test) from integration (system validation).

---

**Created:** 2025-11-07
**Maintainer:** Moku Instrument Forge Team
**Version:** 1.0
