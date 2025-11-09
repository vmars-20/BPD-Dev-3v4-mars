---
created: 2025-11-07
type: handoff
priority: P1
status: complete
completed: 2025-11-07
depends_on:
  - handoff-4-complete-forge-integration
---
Com
# Handoff 6: Hierarchical Voltage Encoding for OutputD

**Date:** 2025-11-07
**Session:** FORGE FSM Observer Architecture Refinement
**Owner:** @claude
**Dependencies:** Handoff 4 complete
**Estimated Time:** 3-4 hours

---

## Executive Summary

Replace the existing `fsm_observer.vhd` LUT-based voltage encoding with a **hierarchical arithmetic encoding scheme** that packs 14 bits of information (6-bit FSM state + 8-bit app status) into OutputD using human-readable voltage levels.

**Key Innovation:** Major state transitions appear as 200mV voltage steps (human-readable on oscilloscope), while 8-bit app-specific status appears as fine-grained "noise" (±100mV) around each base level. Fault conditions flip the sign (negative voltage).

**Impact:** Single oscilloscope channel captures full FSM state + application status with zero lookup tables, train-like-you-fight single bitstream, and backward compatibility with existing tooling.

---

## The Hierarchical Voltage Encoding Scheme

### Visual Representation (Oscilloscope View)

```
+2.5V ┤                                    ← STATE=5 (max normal state)
      │
+2.0V ┤         ╔═══╗                     ← STATE=4 + status noise
      │         ║   ║
+1.5V ┤    ╔════╝   ╚════╗                ← STATE=3 + status noise
      │    ║              ║
+1.0V ┤  ══╝              ╚══              ← STATE=2 + status noise
      │  ░░░░░░░░░░░░░░░░░░░              (░ = 8-bit status "noise" ±50mV)
+0.5V ┤══                                  ← STATE=1 + status noise
      │
 0.0V ┼══════════════════════════════════ ← STATE=0 (IDLE) + status noise
─────────────────────────────────────────
-0.5V ┤         ═══                       ← FAULT! (negative = fault)
      │
-2.0V ┤═══                                ← FAULT from STATE=4 (magnitude preserved)
```

### Encoding Formula

```
Base Voltage    = state_value * 200mV       (major 200mV steps)
Status Offset   = status[6:0] * 0.78125mV  (fine ±100mV noise)
Sign Flip       = status[7]                 (fault indicator)

OutputD_voltage = (Base + Offset) * sign
```

**Parameters:**
- **State resolution:** 6 bits (0-63, but 0-31 normal, 32-63 reserved)
- **Status resolution:** 7 bits payload + 1 bit fault flag (8 bits total)
- **Voltage range:** 0.0V - 2.5V nominal (±5V full-scale for faults)
- **State step size:** 200mV (human-readable major transitions)
- **Status noise range:** 0-100mV (±50mV typical, machine-decodable)

---

## Architecture Changes

### Layer Contracts (3-Layer FORGE Architecture)

#### **Layer 3: APP (Main Entity) - NEW Exports**

```vhdl
entity MyApp_forge_main is
    port (
        -- Standard FORGE signals (unchanged)
        Clk               : in  std_logic;
        Reset             : in  std_logic;
        global_enable     : in  std_logic;
        ready_for_updates : out std_logic;

        -- Application registers (unchanged)
        app_reg_* : in <type>;

        -- Physical I/O (CHANGED: 3 inputs, 3 outputs)
        InputA  : in  signed(15 downto 0);
        InputB  : in  signed(15 downto 0);
        InputC  : in  signed(15 downto 0);
        -- InputD removed (not used by app)

        OutputA : out signed(15 downto 0);  -- User-defined
        OutputB : out signed(15 downto 0);  -- User-defined
        OutputC : out signed(15 downto 0);  -- User-defined
        -- OutputD removed (reserved for FORGE infrastructure)

        -- **NEW:** FORGE-mandated status exports (14 bits)
        app_state_vector  : out std_logic_vector(5 downto 0);  -- FSM state (6 bits)
        app_status_vector : out std_logic_vector(7 downto 0)   -- App status (8 bits)
    );
end entity;
```

**APP Developer Contract:**

**MANDATORY:**
1. **Linear state encoding** (enforced):
   ```vhdl
   constant STATE_IDLE     : std_logic_vector(5 downto 0) := "000000";  -- 0
   constant STATE_ARMED    : std_logic_vector(5 downto 0) := "000001";  -- 1
   constant STATE_FIRING   : std_logic_vector(5 downto 0) := "000010";  -- 2
   constant STATE_COOLDOWN : std_logic_vector(5 downto 0) := "000011";  -- 3
   -- States 0-31: Normal operation
   -- States 32-63: Reserved for future use
   ```

2. **STATUS[7] = fault indicator** (enforced):
   ```vhdl
   app_status_vector(7) <= fault_detected or safety_violation or timeout;
   app_status_vector(6 downto 0) <= ... ;  -- App-specific (7 bits)
   ```

**RECOMMENDED Default Pattern:**
```vhdl
-- If no custom status needed, copy state into status for redundancy
app_status_vector <= fault_flag & app_state_vector(5 downto 0) & '0';
--                   ^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^   ^^^
--                   Bit 7        Bits 6:1 (state copy)            Bit 0 (unused)
```

**APP-Specific Status Examples:**
```vhdl
-- Example 1: Error code + counter
app_status_vector(7)   <= fault_detected;
app_status_vector(6:4) <= error_code;      -- 3-bit error code (8 types)
app_status_vector(3:0) <= counter(3:0);    -- 4-bit counter value

-- Example 2: Flags + progress
app_status_vector(7)   <= fault_detected;
app_status_vector(6)   <= timeout_active;
app_status_vector(5)   <= output_active;
app_status_vector(4:0) <= progress_pct(4:0);  -- 0-31 progress indicator
```

---

#### **Layer 2: SHIM (Register Mapping + Voltage Encoding)**

```vhdl
architecture rtl of MyApp_forge_shim is
    -- From APP (Layer 3)
    signal app_state_vector  : std_logic_vector(5 downto 0);
    signal app_status_vector : std_logic_vector(7 downto 0);

    -- Voltage encoding signals
    signal output_d_voltage : signed(15 downto 0);

begin
    -- Instantiate APP (Layer 3)
    APP_INST: entity WORK.MyApp_forge_main
        port map (
            -- ... standard signals ...

            -- Physical I/O (3 in, 3 out to APP)
            InputA  => InputA,
            InputB  => InputB,
            InputC  => InputC,
            OutputA => OutputA,
            OutputB => OutputB,
            OutputC => OutputC,

            -- State/Status exports (NEW)
            app_state_vector  => app_state_vector,
            app_status_vector => app_status_vector
        );

    -- **NEW:** Hierarchical voltage encoder (replaces fsm_observer)
    VOLTAGE_ENCODER: entity WORK.forge_hierarchical_encoder
        generic map (
            MV_PER_STATE  => 200.0,      -- 200mV per state step
            MV_PER_STATUS => 0.78125     -- ~100mV / 128 (7-bit status range)
        )
        port map (
            clk           => Clk,
            reset         => Reset,
            state_vector  => app_state_vector,   -- 6-bit state
            status_vector => app_status_vector,  -- 8-bit status
            voltage_out   => output_d_voltage    -- 16-bit signed output
        );

    -- Drive OutputD with encoded voltage
    OutputD <= output_d_voltage;

    -- **FUTURE:** Pack state+status into Status Register SR0
    -- Status0 <= x"0000" & app_state_vector & app_status_vector & "00";

end architecture;
```

---

#### **Layer 1: TOP (CustomWrapper Architecture)**

**No changes needed!** CustomWrapper passes through all 4 outputs:

```vhdl
architecture forge_app of AppName_CustomInstrument is
begin
    SHIM_INST: entity WORK.MyApp_forge_shim
        port map (
            -- ... FORGE control ...
            -- ... app registers ...

            InputA  => InputA,
            InputB  => InputB,
            InputC  => InputC,
            InputD  => InputD,   -- Unused by SHIM (future: BRAM loader)
            OutputA => OutputA,
            OutputB => OutputB,
            OutputC => OutputC,
            OutputD => OutputD   -- Hierarchical voltage from SHIM
        );
end architecture;
```

---

## New VHDL Component: forge_hierarchical_encoder

**Location:** `libs/forge-vhdl/vhdl/debugging/forge_hierarchical_encoder.vhd`

**Purpose:** Encode 14-bit state+status into voltage using arithmetic (no LUTs).

**Interface:**
```vhdl
entity forge_hierarchical_encoder is
    generic (
        MV_PER_STATE  : real := 200.0;      -- Voltage step per state (mV)
        MV_PER_STATUS : real := 0.78125     -- Voltage per status LSB (mV)
    );
    port (
        clk           : in  std_logic;
        reset         : in  std_logic;
        state_vector  : in  std_logic_vector(5 downto 0);   -- 6-bit state
        status_vector : in  std_logic_vector(7 downto 0);   -- 8-bit status
        voltage_out   : out signed(15 downto 0)              -- ±5V Moku scale
    );
end entity;
```

**Key Implementation Details:**
- Pure arithmetic (no lookup tables)
- Base voltage = state_integer * MV_PER_STATE
- Status offset = status_lower * MV_PER_STATUS
- Sign flip if status[7] = '1' (fault)
- Output scaled to Moku ±5V full-scale (32768 digital = 5V)

---

## File Modification Plan

### Phase 1: Core Infrastructure (libs/platform/)

**Priority: P0 (Foundation)**

1. **NEW:** `libs/forge-vhdl/vhdl/debugging/forge_hierarchical_encoder.vhd`
   - Create new voltage encoder component
   - Implement arithmetic encoding (state * 200mV + status * 0.78mV)
   - Sign flip logic for fault detection
   - Add comprehensive header comments

2. **UPDATE:** `libs/platform/FORGE_App_Wrapper.vhd`
   - Update Layer 3 (APP) template:
     - Change OutputA/B/C (3 outputs), remove OutputD from APP ports
     - Add `app_state_vector : out std_logic_vector(5:0)`
     - Add `app_status_vector : out std_logic_vector(7:0)`
   - Update Layer 2 (SHIM) template:
     - Instantiate `forge_hierarchical_encoder`
     - Wire `app_state_vector` and `app_status_vector` from APP
     - Drive OutputD with encoder output
   - Update architecture comments with new pattern

3. **UPDATE:** `libs/platform/MCC_CustomInstrument.vhd`
   - Add comments explaining OutputD reservation for FORGE infrastructure
   - Document that APP Layer 3 receives 3 inputs, 3 outputs

4. **DEPRECATE:** `libs/forge-vhdl/vhdl/debugging/fsm_observer.vhd`
   - Add deprecation notice in header
   - Point to `forge_hierarchical_encoder.vhd` as replacement
   - Mark as "Legacy - use hierarchical encoder for new designs"

---

### Phase 2: BPD Reference Implementation (examples/basic-probe-driver/vhdl/)

**Priority: P1 (Reference)**

5. **UPDATE:** `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`
   - Remove OutputD from port list (APP Layer 3)
   - Add `app_state_vector : out std_logic_vector(5 downto 0)`
   - Add `app_status_vector : out std_logic_vector(7 downto 0)`
   - Implement default pattern: `app_status_vector <= fault & state & "0"`
   - Update internal state constants to linear encoding (already done?)

6. **UPDATE:** `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd`
   - Add internal signals: `app_state_vector`, `app_status_vector`
   - Instantiate `forge_hierarchical_encoder`
   - Wire APP outputs to encoder inputs
   - Drive OutputD with encoder voltage output
   - Remove OutputD from APP instantiation port map

7. **UPDATE:** `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_forge.vhd`
   - No changes needed (already passes through OutputD)
   - Verify SHIM instantiation passes OutputD correctly

8. **REMOVE:** `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_with_observer.vhd`
   - Delete file (no longer needed - single bitstream pattern)
   - FSM observer now built into production wrapper

---

### Phase 3: Testing & Validation

**Priority: P2 (Validation)**

9. **NEW:** `libs/forge-vhdl/vhdl/debugging/test_forge_hierarchical_encoder.py`
   - CocoTB testbench for hierarchical encoder
   - Test cases:
     - Linear state progression (0→1→2→3, verify 0mV→200mV→400mV→600mV)
     - Status noise encoding (state=2, status=0x00 vs 0x7F, verify ~400mV vs ~500mV)
     - Fault detection (status[7]=1, verify negative voltage)
     - Sign flip magnitude preservation (state=3, fault → verify -600mV)

10. **UPDATE:** `examples/basic-probe-driver/vhdl/cocotb_test/test_bpd_fsm_observer.py`
    - Update voltage decoder to use new hierarchical scheme
    - Add tests for status bit extraction
    - Verify fault flag behavior (negative voltage)

11. **NEW:** `tools/oscilloscope_decoder.py`
    - Python utility to decode OutputD voltages
    - Input: voltage (float mV)
    - Output: dict with 'state', 'status_lower', 'fault', 'raw_state_mv', 'status_noise_mv'
    - Example usage in docstring

---

### Phase 4: Documentation Updates

**Priority: P2 (Communication)**

12. **UPDATE:** `CLAUDE.md`
    - Section: "FORGE 3-Layer Architecture"
      - Update Layer 3 responsibilities (3 outputs, state/status exports)
      - Document 14-bit state+status encoding standard
      - Add hierarchical voltage encoding explanation
    - Section: "MCC CustomInstrument Interface"
      - Document OutputD reservation for FORGE infrastructure
      - Explain APP Layer 3 reduced to 3 inputs/outputs
    - Add new section: "Hierarchical Voltage Encoding Standard"
      - Encoding formula
      - Decoder Python example
      - Oscilloscope visualization guide

13. **UPDATE:** `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md`
    - Update Layer 3 diagrams (remove OutputD from APP)
    - Add hierarchical voltage encoding section
    - Document state+status export pattern
    - Add oscilloscope debugging workflow with new encoding

14. **UPDATE:** `tools/forge-codegen/docs/debugging/fsm_observer_pattern.md`
    - Rename to `hierarchical_voltage_encoding.md`
    - Replace fsm_observer documentation with new scheme
    - Add Python decoder utility
    - Document fault detection pattern (negative voltage)

15. **UPDATE:** `libs/forge-vhdl/llms.txt`
    - Add `forge_hierarchical_encoder.vhd` to component list
    - Deprecate `fsm_observer.vhd` mention
    - Update debugging patterns section

16. **NEW:** `Obsidian/Project/Handoffs/hierarchical-voltage-encoding-cheatsheet.md`
    - Quick reference card for developers
    - State encoding rules (linear 0-31)
    - Status bit 7 = fault convention
    - Voltage decoding formulas
    - Python decoder one-liner

---

## Testing Strategy

### Unit Tests (CocoTB)

**Test 1: State Progression**
```python
# State 0 (IDLE), Status 0x00 → 0mV
# State 1 (ARMED), Status 0x00 → 200mV
# State 2 (FIRING), Status 0x00 → 400mV
# State 3 (COOLDOWN), Status 0x00 → 600mV
```

**Test 2: Status Noise**
```python
# State 2 (FIRING), Status 0x00 → 400mV + 0mV = 400mV
# State 2 (FIRING), Status 0x7F → 400mV + 100mV = 500mV
# Verify status creates ±100mV "noise" around base level
```

**Test 3: Fault Detection**
```python
# State 2, Status 0x12 (fault=0) → +414mV (positive)
# State 2, Status 0x92 (fault=1) → -414mV (negative, same magnitude)
```

**Test 4: Magnitude Preservation**
```python
# Transition: STATE=3 (normal) → FAULT
# Voltage should flip from +600mV to -600mV (magnitude shows last state)
```

---

## Benefits of This Scheme

### Compared to Old fsm_observer.vhd (LUT-based)

| Feature | Old (fsm_observer) | New (hierarchical) |
|---------|-------------------|-------------------|
| **State visibility** | ✅ Human-readable (0-2.5V steps) | ✅ Human-readable (200mV steps) |
| **Status visibility** | ❌ Not visible | ✅ ±100mV "noise" (7 bits) |
| **Fault detection** | ✅ Sign flip | ✅ Sign flip (status[7]) |
| **Information density** | 6 bits (state only) | 14 bits (state + status) |
| **Resource usage** | 64-entry LUT | Zero LUTs (pure arithmetic) |
| **Customization** | Generic parameters | Arithmetic constants |
| **Backward compat** | N/A | ✅ If status=0, behaves like old |

### Production Advantages

1. **✅ Train like you fight** - Single bitstream for dev and production
2. **✅ Zero resource overhead** - No LUTs, pure arithmetic
3. **✅ Human + machine readable** - 200mV steps (human) + status noise (machine)
4. **✅ Self-documenting** - Voltage on scope shows state progression
5. **✅ Fault diagnosis** - Negative voltage + magnitude shows failure state
6. **✅ Network + scope** - Same 14 bits available via Status Register (future)

---

## Migration Path for Existing Code

### For New Applications
- Follow template in updated `libs/platform/FORGE_App_Wrapper.vhd`
- APP exports 3 outputs + state_vector + status_vector
- SHIM instantiates `forge_hierarchical_encoder`
- Zero migration needed

### For Existing Applications (BPD)
1. Update APP entity (remove OutputD, add state/status exports)
2. Update SHIM (instantiate encoder, wire OutputD)
3. Update tests (new voltage decoder)
4. Remove test-only wrapper (single bitstream now)

**Estimated effort per application:** 1-2 hours

---

## Success Criteria

- [ ] `forge_hierarchical_encoder.vhd` component created and tested
- [ ] `libs/platform/FORGE_App_Wrapper.vhd` template updated
- [ ] BPD reference implementation migrated
- [ ] CocoTB tests pass with new voltage scheme
- [ ] Oscilloscope shows 200mV state steps + status noise
- [ ] Fault conditions produce negative voltage
- [ ] Python decoder utility works
- [ ] Documentation updated (CLAUDE.md, FORGE_ARCHITECTURE.md)
- [ ] `CustomWrapper_bpd_with_observer.vhd` removed (single bitstream)

---

## Open Questions / Decisions Needed

### Question 1: Generic Configuration
**Should `forge_hierarchical_encoder` generics be exposed at SHIM level?**

```vhdl
-- Option A: Hardcoded in encoder (simpler)
constant MV_PER_STATE : real := 200.0;

-- Option B: Configurable via SHIM generics (flexible)
entity MyApp_forge_shim is
    generic (
        STATE_VOLTAGE_STEP_MV : real := 200.0
    );
```

**Recommendation:** Option A (hardcoded) for consistency across all FORGE apps.

---

### Question 2: Status Register Integration
**When Status Registers (SR0-SR15) become network-readable, should we:**

```vhdl
-- Option A: Pack full 14 bits into SR0
Status0 <= x"0000" & app_state_vector & app_status_vector & "00";  -- 18 bits used

-- Option B: Separate registers
Status0 <= x"00000000" & "00" & app_state_vector;  -- State only
Status1 <= x"000000" & app_status_vector;          -- Status only

-- Option C: Don't use Status Registers (OutputD only)
-- (Keep Status Registers for future app-specific use)
```

**Recommendation:** Option C for now (Status Registers reserved for APP-specific data, not infrastructure).

---

### Question 3: InputD Usage
**What should SHIM do with InputD (unused by APP)?**

- Option A: Leave unused (current proposal)
- Option B: Pass to APP as optional (generic-controlled)
- Option C: Reserve for BRAM loader feedback (future)

**Recommendation:** Option A (unused) until BRAM loader implemented.

---

## References

### Implementation Files
- `libs/forge-vhdl/vhdl/debugging/forge_hierarchical_encoder.vhd` (NEW)
- `libs/platform/FORGE_App_Wrapper.vhd` (TEMPLATE)
- `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd` (REFERENCE)

### Documentation
- `CLAUDE.md` - Root architecture guide
- `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md` - Layer details
- `/tmp/mcc_min/oscilloscope_debugging_techniques.md` - Voltage scaling lessons

### Test Infrastructure
- `examples/basic-probe-driver/vhdl/cocotb_test/` - Progressive testing
- `libs/forge-vhdl/forge_cocotb/` - Test utilities

---

## Blockers

@human
- None expected
- All dependencies met (Handoff 4 complete)
- Clear specification and implementation path
- Backward compatible design

---

**Created:** 2025-11-07
**Status:** Pending
**Priority:** P1 (Architecture improvement)
**Dependencies:** Handoff 4 complete
**Estimated Completion:** 3-4 hours active work

---

## Completion Checklist

### Phase 1: Core Infrastructure ✅ COMPLETE
- [x] Create `forge_hierarchical_encoder.vhd`
- [x] Update `FORGE_App_Wrapper.vhd` template
- [x] Update `MCC_CustomInstrument.vhd` comments
- [x] Deprecate `fsm_observer.vhd`

### Phase 2: BPD Reference ✅ COMPLETE
- [x] Update `basic_probe_driver_custom_inst_main.vhd`
- [x] Update `BPD_forge_shim.vhd`
- [x] Verify `CustomWrapper_bpd_forge.vhd`
- [x] Remove `CustomWrapper_bpd_with_observer.vhd`

### Phase 3: Testing 🔜 NEXT (Handoff 7-8)
- [ ] Create encoder CocoTB tests (Handoff 7)
- [ ] Update BPD FSM observer tests (Handoff 7)
- [ ] Run CocoTB tests and validate (Handoff 8)
- [ ] Create oscilloscope decoder utility (Handoff 9)
- [ ] Validate on hardware (if available) (Handoff 9)

### Phase 4: Documentation 📝 DEFERRED
- [ ] Update `CLAUDE.md` architecture sections
- [ ] Update `FORGE_ARCHITECTURE.md`
- [ ] Update/rename `fsm_observer_pattern.md`
- [ ] Update `libs/forge-vhdl/llms.txt`
- [ ] Create quick reference cheatsheet

---

## Implementation Summary (Phase 1 & 2)

**Completed:** 2025-11-07
**Duration:** ~2 hours
**Files Created:** 2
**Files Modified:** 6
**Files Deleted:** 1

**Key Achievements:**
- ✅ Platform-agnostic digital encoding (two's complement)
- ✅ Zero LUT resources (pure arithmetic)
- ✅ 14-bit information density (6-bit state + 8-bit status)
- ✅ Single bitstream dev/prod pattern
- ✅ BPD reference implementation migrated

**Next Steps:** See Handoff 7 (CocoTB test design), Handoff 8 (test execution), Handoff 9 (hardware validation)

---

**END OF HANDOFF 6**
