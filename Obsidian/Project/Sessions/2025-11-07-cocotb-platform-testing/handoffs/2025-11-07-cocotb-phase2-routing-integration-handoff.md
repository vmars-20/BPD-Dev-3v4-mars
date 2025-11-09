# Phase 2 Routing Integration - Handoff Prompt

**Date:** 2025-11-07
**Session:** 2025-11-07-cocotb-platform-testing
**Branch:** `sessions/2025-11-07-cocotb-platform-testing`
**Status:** Active signal routing infrastructure complete, ready for integration testing

---

## Context

Phase 2 of the CocoTB Platform Testing Framework is **~70% complete**. The routing infrastructure is now fully functional and ready for end-to-end integration testing.

### ✅ Completed (Last Session)

1. **forge_counter_with_encoder.vhd** - Full FORGE 3-layer test DUT
   - Layer 1: MCC CustomInstrument interface with FORGE control
   - Layer 2: SHIM with hierarchical encoder (drives OutputD)
   - Layer 3: 6-bit auto-increment state counter (MAIN logic)
   - Compiled and verified with GHDL ✓

2. **test_platform_oscilloscope_capture.py** - 2/2 P1 tests passing
   - ✅ Test 1: Oscilloscope captures OutputD signal
   - ✅ Test 2: Hierarchical voltage decoding (state progression validated)
   - ⏸️ Test 3: Fault detection (TODO - 1-cycle overflow pulse timing issue)

3. **Active Signal Routing Infrastructure** - NEW! ✨
   - `simulation_backend._apply_routing_connection()`: Wires SlotNOutX → SlotMInY
   - `simulation_backend._parse_signal_name()`: Parses routing syntax ('Slot2OutD')
   - `oscilloscope.add_external_channel()`: Accepts routed signals from other slots
   - Pattern: `Slot2 DUT OutputD → signal_handle → Slot1 Oscilloscope InputA`

### 📍 Current State

**Files Modified (Last Commit: 2f7e409):**
- `libs/forge-vhdl/cocotb_test/platform/simulation_backend.py` - Routing infrastructure
- `libs/forge-vhdl/cocotb_test/platform/simulators/oscilloscope.py` - External channels
- `libs/forge-vhdl/cocotb_test/test_platform_oscilloscope_capture.py` - 2/2 tests
- `libs/forge-vhdl/cocotb_test/test_duts/forge_counter_with_encoder.vhd` - Test DUT

**Test Results:**
```bash
cd libs/forge-vhdl
uv run python cocotb_test/run.py platform_oscilloscope_capture
# Output: 2/2 tests PASS (1320ns runtime)
```

---

## Next Task: Integration Test with 2-Slot Routing

**Goal:** Validate Slot2OutD → Slot1InA signal routing with MokuConfig-driven setup.

### Task Breakdown

#### 1. Create Integration Test File
**File:** `libs/forge-vhdl/cocotb_test/test_platform_routing_integration.py`

**Test Strategy:**
```python
# Test 1: 2-slot setup with routing (P1)
# - Slot2: CloudCompile with forge_counter_with_encoder DUT
# - Slot1: Oscilloscope configured to capture 'InputA'
# - Routing: Slot2OutD → Slot1InA (BPD-Debug-Bus pattern)
# - Enable counter via CR0[31:29] FORGE control
# - Oscilloscope captures routed signal (not direct DUT access)
# - Decode hierarchical voltage from Slot1's InputA channel
# - Verify state progression: 0→1→2→...→15

# Test 2: Validate routing configuration (P1)
# - Check routing_matrix populated correctly
# - Verify external_channels in oscilloscope
# - Confirm signal_handle wiring (not value copying)
```

#### 2. Create MokuConfig YAML (Optional)
**File:** `libs/forge-vhdl/cocotb_test/configs/routing-test-2slot.yaml`

**Structure:**
```yaml
platform: moku_go
slots:
  1:
    instrument: oscilloscope
    settings:
      channels: ['InputA']  # Capture routed signal
      sample_rate: 125e6
  2:
    instrument: cloud_compile
    vhdl_source: test_duts/forge_counter_with_encoder.vhd
    control_registers:
      CR0: 0xE000000F  # FORGE enabled + max_state=15

routing:
  - source: Slot2OutD
    destination: Slot1InA
```

#### 3. Update test_configs.py
**Add entry:**
```python
"platform_routing_integration": TestConfig(
    name="platform_routing_integration",
    sources=[
        VHDL_PKG / "forge_common_pkg.vhd",
        VHDL_DEBUG / "forge_hierarchical_encoder.vhd",
        TESTS / "test_duts" / "forge_counter_with_encoder.vhd",
    ],
    toplevel="forge_counter_with_encoder",
    test_module="test_platform_routing_integration",
    category="platform",
),
```

---

## Implementation Notes

### Key Differences from Previous Tests

**test_platform_oscilloscope_capture.py:**
- Oscilloscope directly accesses DUT signals (`self.dut.OutputD`)
- Single-slot test (no routing)
- Channels: `['OutputD']`

**test_platform_routing_integration.py (NEW):**
- Oscilloscope accesses **routed** signal via `external_channels`
- 2-slot test with SimulationBackend coordinator
- Channels: `['InputA']` (destination of routing)
- Uses MokuConfig to define 2-slot setup + routing

### Routing Validation Checklist

```python
# In test setup:
backend = SimulationBackend(moku_config, dut)
await backend.setup()

# Verify routing applied:
assert 'Slot2OutD->Slot1InA' in backend.routing_matrix
oscilloscope = backend.get_instrument(1)
assert 'InputA' in oscilloscope.external_channels
assert oscilloscope.external_channels['InputA'] is dut.OutputD  # Signal handle wiring

# Capture from routed channel:
await backend.run(duration_ms=0.001)  # 1us capture
data = oscilloscope.get_data('InputA')  # Note: InputA, not OutputD!
```

---

## Expected Outcomes

### Success Criteria

1. ✅ Routing infrastructure wires Slot2.OutputD → Slot1.InputA
2. ✅ Oscilloscope captures samples from external channel (not DUT)
3. ✅ Hierarchical voltage decoding works on routed signal
4. ✅ State progression validated: 0→1→2→...→15
5. ✅ Test demonstrates BPD-Debug-Bus pattern

### Test Output (Expected)

```
T1: 2-slot routing (Slot2OutD → Slot1InA)
  Routing: Slot2OutD -> Slot1InA
  Wired: Slot2.OutputD → Slot1.InputA
  Captured 125 samples from InputA
  Decoded states: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0, 1, ...]
  ✓ PASS

T2: Routing configuration validation
  routing_matrix contains: Slot2OutD->Slot1InA
  external_channels contains: InputA
  Signal handle wired correctly
  ✓ PASS
```

---

## Known Issues to Address

### Issue #1: Fault Detection Test Timing
**File:** `test_platform_oscilloscope_capture.py:72`
**Status:** Skipped (TODO comment)

**Problem:**
- `overflow_flag` is pulsed for exactly 1 clock cycle (8ns)
- Oscilloscope samples at 125 MHz (8ns period)
- Timing alignment makes fault capture unreliable

**Potential Solutions:**
1. Increase oscilloscope sample rate (or use decimation = 0.5)
2. Modify DUT to hold overflow_flag for N cycles
3. Add trigger mode to oscilloscope (capture on negative edge)

**Priority:** P2 enhancement (not blocking for Phase 2 completion)

---

## Quick Start Commands

```bash
# Navigate to workspace
cd /Users/johnycsh/BPD-Dev

# Check branch
git status
# Expected: sessions/2025-11-07-cocotb-platform-testing

# Verify Phase 2 baseline
cd libs/forge-vhdl
uv run python cocotb_test/run.py platform_oscilloscope_capture
# Expected: 2/2 tests PASS

# Create integration test (YOUR TASK)
# 1. Create test_platform_routing_integration.py
# 2. Update test_configs.py
# 3. Run: uv run python cocotb_test/run.py platform_routing_integration
```

---

## References

### Key Files

**Platform Infrastructure:**
- `libs/forge-vhdl/cocotb_test/platform/simulation_backend.py` - Routing coordinator
- `libs/forge-vhdl/cocotb_test/platform/simulators/oscilloscope.py` - Signal capture

**Test DUT:**
- `libs/forge-vhdl/cocotb_test/test_duts/forge_counter_with_encoder.vhd` - Full FORGE 3-layer

**Existing Tests (Templates):**
- `test_platform_oscilloscope_capture.py` - Single-slot oscilloscope test
- `test_platform_counter_poc.py` - FORGE control sequence test
- `test_platform_bpd_deployment.py` - MokuConfig YAML parsing test

**Session Documentation:**
- `Obsidian/Project/Sessions/2025-11-07-cocotb-platform-testing/2025-11-07-cocotb-platform-test-PLAN.md`

### Handoff 6 Reference

**Hierarchical Voltage Encoding:**
- `Obsidian/Project/Handoffs/2025-11-07/2025-11-07-handoff-6-hierarchical-voltage-encoding.md`
- Encoding: `voltage = state × 200 + status × 0.78125`
- Fault: `status[7] = 1` → negative voltage

---

## Questions for Next Developer

1. **MokuConfig approach:** Should we create a YAML file or use Python dict for 2-slot config?
2. **Test scope:** P1 only (2 tests) or expand to P2 (5-7 tests with edge cases)?
3. **Fault detection:** Address timing issue now or defer to P2 enhancements?

---

**Ready to continue! The routing infrastructure is fully functional and waiting for integration validation.** 🚀

**Last Commit:** `2f7e409` (docs: Update session plan with Phase 2 routing progress)
**Next Step:** Create `test_platform_routing_integration.py` with 2-slot MokuConfig setup
