# FSM Observer Unification Strategy: Standardizing on forge_hierarchical_encoder

**Date:** 2025-11-07
**Decision:** Make `forge_hierarchical_encoder` the single, canonical approach for FSM observation
**Status:** Migration In Progress

---

## Executive Summary

We are unifying all FSM observation approaches in the monorepo to use `forge_hierarchical_encoder` as the single standard. This eliminates confusion, reduces maintenance burden, and establishes a consistent debugging methodology across all projects.

**Key Principle:** There should be ONE way to observe FSMs via oscilloscope - the hierarchical encoder approach.

---

## Architectural Decision

### The Problem

Currently, the monorepo has two competing FSM observation approaches:

1. **fsm_observer** (Legacy)
   - LUT-based voltage spreading (0V to 2.5V)
   - 64-entry lookup table
   - 6-bit state only, no status information
   - Large voltage steps (625mV per state)

2. **forge_hierarchical_encoder** (New Standard)
   - Pure arithmetic (zero LUTs)
   - 14-bit information (6-bit state + 8-bit status)
   - Compact encoding (30mV per state on ±5V platform)
   - Platform-agnostic digital units

Having two approaches causes:
- ❌ Confusion about which to use
- ❌ Duplicate test infrastructure
- ❌ Inconsistent documentation
- ❌ Different decoder implementations
- ❌ Wasted resources maintaining both

### The Solution

**forge_hierarchical_encoder becomes THE standard** for all FSM observation:

- ✅ Single implementation to maintain
- ✅ Consistent encoding across all projects
- ✅ Unified decoder utilities
- ✅ Clear documentation path
- ✅ Resource-efficient (zero LUTs)

---

## Migration Scope

### Files Requiring Changes

**VHDL Components (2 files):**
```
libs/forge-vhdl/vhdl/debugging/fsm_observer.vhd              → Refactor to wrapper
libs/forge-vhdl/vhdl/debugging/forge_hierarchical_encoder.vhd → Keep as-is (core)
```

**VHDL Usage (2 files):**
```
examples/basic-probe-driver/vhdl/external_Example/DS1140_polo_main.vhd
examples/basic-probe-driver/vhdl/CustomWrapper_bpd_forge.vhd
```

**Python Tests (9 files):**
```
examples/basic-probe-driver/vhdl/cocotb_test/test_fsm_observer.py
examples/basic-probe-driver/vhdl/cocotb_test/fsm_observer_tests/*.py (5 files)
examples/basic-probe-driver/vhdl/cocotb_test/test_configs.py
examples/basic-probe-driver/vhdl/proposed_cocotb_test/*.py (2 files)
```

**Documentation (5+ files):**
```
tools/forge-codegen/docs/debugging/fsm_observer_pattern.md
Obsidian/Project/Handoffs/2025-11-07-handoff-6-hierarchical-voltage-encoding.md
examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md
CLAUDE.md (root)
libs/forge-vhdl/CLAUDE.md
```

---

## Migration Strategy

### Phase 1: Wrapper Approach (Backward Compatible)

**Transform fsm_observer.vhd into a thin wrapper:**

```vhdl
-- libs/forge-vhdl/vhdl/debugging/fsm_observer.vhd (REFACTORED)
-- DEPRECATED: This is now a compatibility wrapper around forge_hierarchical_encoder
-- All new designs should use forge_hierarchical_encoder directly

entity fsm_observer is
    generic (
        NUM_STATES : integer := 5;
        -- Legacy generics ignored, kept for compatibility
        FAULT_STATE_THRESHOLD : integer := 5;
        V_MIN : real := 0.0;
        V_MAX : real := 2.5
    );
    port (
        clk : in std_logic;
        rst : in std_logic;
        state : in std_logic_vector(5 downto 0);
        voltage_out : out signed(15 downto 0)
    );
end entity;

architecture wrapper of fsm_observer is
    signal status_zero : std_logic_vector(7 downto 0) := (others => '0');
begin
    -- Instantiate the new standard encoder
    encoder : entity work.forge_hierarchical_encoder
        port map (
            clk => clk,
            reset => rst,
            state_vector => state,
            status_vector => status_zero,  -- No status for legacy compatibility
            voltage_out => voltage_out
        );

    -- Note: Output will be different than legacy fsm_observer!
    -- Legacy: 0V, 0.625V, 1.25V, 1.875V, 2.5V
    -- New: 0mV, 30mV, 61mV, 91mV, 122mV (on ±5V platform)

    assert false report
        "WARNING: fsm_observer is DEPRECATED. " &
        "Use forge_hierarchical_encoder directly for new designs. " &
        "Output scaling has changed - see migration guide."
        severity warning;
end architecture;
```

### Phase 2: Test Migration

**Update test expectations for new encoding:**

```python
# examples/basic-probe-driver/vhdl/cocotb_test/fsm_observer_tests/fsm_observer_constants.py

# OLD APPROACH (DEPRECATED)
# def calculate_expected_voltage(state_index):
#     """Legacy voltage spreading approach"""
#     v_step = (2.5 - 0.0) / (5 - 1)  # 0.625V per state
#     return 0.0 + (state_index * 0.625)

# NEW APPROACH (forge_hierarchical_encoder)
def calculate_expected_voltage(state_index, status=0x00):
    """
    Calculate expected voltage using hierarchical encoder approach.

    This now uses the forge_hierarchical_encoder algorithm:
    - 200 digital units per state
    - Platform converts to voltage (±5V = ±32768 digital)
    """
    # Digital domain calculation
    base_digital = state_index * 200
    status_lower = status & 0x7F
    status_offset = int(status_lower * 100 / 128)  # Integer division
    total_digital = base_digital + status_offset

    # Apply fault flag (sign flip)
    if status & 0x80:
        total_digital = -total_digital

    # Convert to voltage (platform-specific, ±5V assumed)
    voltage_mv = (total_digital / 32768.0) * 5000.0
    return voltage_mv / 1000.0  # Return in volts

# Backward compatibility wrapper
def calculate_legacy_voltage(state_index):
    """DEPRECATED: Use calculate_expected_voltage() instead"""
    import warnings
    warnings.warn(
        "calculate_legacy_voltage is deprecated. "
        "Use calculate_expected_voltage() for hierarchical encoding.",
        DeprecationWarning,
        stacklevel=2
    )
    return calculate_expected_voltage(state_index)
```

### Phase 3: Direct Usage Updates

**Update BPD CustomWrapper to use hierarchical encoder:**

```vhdl
-- examples/basic-probe-driver/vhdl/CustomWrapper_bpd_forge.vhd

-- OLD (remove):
-- observer : entity work.fsm_observer
--     generic map (NUM_STATES => 5)
--     port map (...)

-- NEW (add):
hierarchical_observer : entity work.forge_hierarchical_encoder
    port map (
        clk => Clk,
        reset => Reset,
        state_vector => fsm_state,
        status_vector => fsm_status,  -- Now we can encode status too!
        voltage_out => OutputD
    );
```

### Phase 4: Documentation Updates

**Update all references to point to hierarchical encoder:**

1. **Root CLAUDE.md** - Add migration notice
2. **libs/forge-vhdl/CLAUDE.md** - Mark fsm_observer deprecated
3. **Test README files** - Update expected voltage calculations
4. **Handoff documents** - Reference new encoding scheme

---

## Decoder Unification

### Single Decoder Function

```python
# tools/decoder/hierarchical_decoder.py

def decode_oscilloscope_voltage(voltage_mv, platform_range_mv=5000.0):
    """
    Universal decoder for forge_hierarchical_encoder output.

    This is THE standard decoder for all FSM observation.

    Args:
        voltage_mv: Measured voltage in millivolts
        platform_range_mv: Full-scale range (default ±5V)

    Returns:
        dict with 'state', 'status', 'fault', etc.
    """
    # Convert voltage to digital
    digital = int(voltage_mv * (32768 / platform_range_mv))

    # Detect fault (negative voltage)
    fault = digital < 0
    magnitude = abs(digital)

    # Decode state (200 units per state)
    state = magnitude // 200
    remainder = magnitude % 200

    # Decode status offset
    status_lower = int(remainder * 128 / 100)

    # Reconstruct full status
    status = 0x80 | status_lower if fault else status_lower

    return {
        'state': state,
        'status': status,
        'fault': fault,
        'voltage_mv': voltage_mv,
        'digital_value': digital
    }

# Legacy compatibility
def decode_fsm_observer_voltage(voltage):
    """DEPRECATED: Use decode_oscilloscope_voltage() instead"""
    import warnings
    warnings.warn("Use decode_oscilloscope_voltage()", DeprecationWarning)
    return decode_oscilloscope_voltage(voltage * 1000)  # Convert V to mV
```

---

## Benefits of Unification

### Technical Benefits
- **Zero LUT usage** - Pure arithmetic implementation
- **14-bit information density** - State + status in single channel
- **Platform agnostic** - Works on Go/Lab/Pro/Delta
- **Single bitstream** - No dev/prod variants needed
- **Consistent encoding** - Same algorithm everywhere

### Development Benefits
- **Single source of truth** - One encoder, one decoder
- **Clear documentation** - No confusion about approaches
- **Unified testing** - One set of test utilities
- **Reduced maintenance** - One implementation to maintain
- **Future-proof** - Easy to extend with more status bits

---

## Migration Timeline

| Phase | Task | Status | Target Date |
|-------|------|--------|-------------|
| 0 | Audit codebase | ✅ COMPLETE | 2025-11-07 |
| 1 | Document strategy | ✅ COMPLETE | 2025-11-07 |
| 2 | Refactor fsm_observer.vhd | 🔄 IN PROGRESS | 2025-11-07 |
| 3 | Update BPD integration | ⏳ PENDING | 2025-11-08 |
| 4 | Migrate tests | ⏳ PENDING | 2025-11-08 |
| 5 | Update documentation | ⏳ PENDING | 2025-11-08 |
| 6 | Validation testing | ⏳ PENDING | 2025-11-09 |
| 7 | Cleanup deprecated code | ⏳ PENDING | 2025-11-10 |

---

## Rollback Plan

If issues arise during migration:

1. **fsm_observer wrapper** preserves backward compatibility
2. **Git history** allows reverting individual changes
3. **Phased approach** allows partial rollback
4. **Tests** validate each migration step

---

## Success Criteria

Migration is complete when:

- [ ] All VHDL instantiations use forge_hierarchical_encoder (or wrapper)
- [ ] All tests expect hierarchical encoding values
- [ ] Documentation consistently references hierarchical encoder
- [ ] Single decoder function used everywhere
- [ ] No direct references to legacy voltage spreading
- [ ] Deprecation warnings added to all legacy code
- [ ] Integration tests pass with new encoding

---

## References

- **Hierarchical Encoder Design:** `Obsidian/Project/Review/HIERARCHICAL_ENCODER_DIGITAL_SCALING.md`
- **Original Handoff:** `Obsidian/Project/Handoffs/2025-11-07-handoff-6-hierarchical-voltage-encoding.md`
- **Test Results:** `Obsidian/Project/Test-Reports/2025-11-07-handoff-8-test-results.md`
- **Implementation:** `libs/forge-vhdl/vhdl/debugging/forge_hierarchical_encoder.vhd`

---

**Document Created:** 2025-11-07
**Author:** @claude
**Status:** Active Migration Strategy