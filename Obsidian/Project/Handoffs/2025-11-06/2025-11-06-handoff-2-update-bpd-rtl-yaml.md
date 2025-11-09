---
created: 2025-11-06
type: handoff
priority: P1
status: completed
depends_on: handoff-1-fix-forge-vhdl-types
git_commits:
  - 1aecac2 # fix: Update BPD-RTL.yaml with correct semantic types
---

# Handoff 2: Update BPD-RTL.yaml with Correct Types

**Date:** 2025-11-06 23:15
**Session:** Template Application - Phase 2
**Owner:** @claude (with @human review)
**Dependencies:** Handoff 1 complete (new types in forge-vhdl)
**Estimated Time:** 20 minutes

---

## Context: What Needs to Be Done

BPD-RTL.yaml currently has **semantic type mismatches** that need fixing:

1. **6 fields using `boolean`** → Should be `std_logic_reg` (register bits, not logic)
2. **4 fields using `voltage_output_05v_s16`** → Should be `voltage_output_5v_bipolar_s16` (±5V, not ±0.5V!)

These are **critical bugs** - the 05v type means ±**0.5**V, not ±**5.0**V!

**Prerequisites:** Handoff 1 must be complete (types exist in forge-vhdl packages).

---

## What I Just Did (Previous Handoff)

From Handoff 1:
✅ Added `std_logic_reg` to forge_serialization_types_pkg.vhd
✅ Added ±5V voltage types to forge_serialization_voltage_pkg.vhd
✅ Verified compilation with GHDL
✅ Updated documentation

---

## Next Steps

@claude please make these surgical changes to BPD-RTL.yaml:

### Change 1: Fix Boolean → std_logic_reg (6 fields)

**Fields to change:**
```yaml
# Line ~26-31: Lifecycle control
- name: arm_enable
  datatype: boolean              # OLD
  datatype: std_logic_reg        # NEW

- name: ext_trigger_in
  datatype: boolean              # OLD
  datatype: std_logic_reg        # NEW

- name: auto_rearm_enable
  datatype: boolean              # OLD
  datatype: std_logic_reg        # NEW

- name: fault_clear
  datatype: boolean              # OLD
  datatype: std_logic_reg        # NEW

# Line ~140-153: Monitor control
- name: monitor_enable
  datatype: boolean              # OLD
  datatype: std_logic_reg        # NEW

- name: monitor_expect_negative
  datatype: boolean              # OLD
  datatype: std_logic_reg        # NEW
```

**Why:** These are register bits, not boolean logic. Semantic correctness matters!

### Change 2: Fix Voltage Types (4 fields)

**CRITICAL BUG FIX:**

```yaml
# Line ~72-80: Trigger output voltage
- name: trig_out_voltage
  datatype: voltage_output_05v_s16         # WRONG! This is ±0.5V
  datatype: voltage_output_5v_bipolar_s16  # CORRECT! This is ±5.0V
  min_value: -5000
  max_value: 5000

# Line ~94-102: Intensity output voltage
- name: intensity_voltage
  datatype: voltage_output_05v_s16         # WRONG! This is ±0.5V
  datatype: voltage_output_5v_bipolar_s16  # CORRECT! This is ±5.0V
  min_value: -5000
  max_value: 5000

# Line ~130-136: Probe monitor feedback
- name: probe_monitor_feedback
  datatype: voltage_input_20v_s16          # Too large, use ±5V
  datatype: voltage_input_5v_bipolar_s16   # CORRECT!
  min_value: -5000
  max_value: 5000

# Line ~156-164: Monitor threshold voltage
- name: monitor_threshold_voltage
  datatype: voltage_input_20v_s16          # Too large, use ±5V
  datatype: voltage_input_5v_bipolar_s16   # CORRECT!
  default_value: -200
  min_value: -5000
  max_value: 5000
```

**Why:**
- `05v` = ±0.5V (NOT ±5V!) - This is a naming convention issue in forge-codegen
- ±5V is the actual Moku:Go DAC/ADC range
- Using ±20V for ±5V signals is semantically wrong (wastes range)

### Change 3: Verify Time Types (NO CHANGES NEEDED)

**These are correct:**
```yaml
- name: trig_out_duration
  datatype: pulse_duration_ns_u16   # ✅ CORRECT

- name: trigger_wait_timeout
  datatype: pulse_duration_s_u16    # ✅ CORRECT

- name: cooldown_interval
  datatype: pulse_duration_us_u24   # ✅ CORRECT
```

**Why:** Time types are forge-codegen metadata, not VHDL serialization types. They map to `unsigned` + conversion functions.

---

## Files to Modify

1. **`examples/basic-probe-driver/BPD-RTL.yaml`**
   - Change 6 `boolean` → `std_logic_reg`
   - Change 2 `voltage_output_05v_s16` → `voltage_output_5v_bipolar_s16`
   - Change 2 `voltage_input_20v_s16` → `voltage_input_5v_bipolar_s16`

---

## Validation Steps

@claude after making changes:

1. **Verify YAML syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('examples/basic-probe-driver/BPD-RTL.yaml'))"
   ```

2. **Check type coverage:**
   ```bash
   grep "datatype:" examples/basic-probe-driver/BPD-RTL.yaml | sort | uniq -c
   ```

   Expected output should show:
   - `voltage_output_5v_bipolar_s16` (2 occurrences)
   - `voltage_input_5v_bipolar_s16` (2 occurrences)
   - `std_logic_reg` (6 occurrences)
   - `pulse_duration_*` (various time types)
   - NO `boolean`
   - NO `voltage_output_05v_s16`
   - NO `voltage_input_20v_s16`

3. **Document changes:**
   - Update YAML header comment with change notes
   - Note: "status: IN REVIEW" → "status: UPDATED 2025-11-06"

---

## Resources

**Reference:**
- Current BPD-RTL.yaml: `examples/basic-probe-driver/BPD-RTL.yaml`
- Type definitions: `libs/forge-vhdl/vhdl/packages/forge_serialization_*.vhd`

**Documentation:**
- Root `CLAUDE.md` - Type system section (update after this handoff)

**Commands:**
```bash
# Validate YAML
cd examples/basic-probe-driver
python -c "import yaml; yaml.safe_load(open('BPD-RTL.yaml'))"

# Check type usage
grep "datatype:" BPD-RTL.yaml | sort | uniq -c

# Compare before/after
git diff BPD-RTL.yaml
```

---

## Success Criteria

- [x] All 6 `boolean` fields changed to `std_logic_reg`
- [x] All 4 voltage fields use correct ±5V types
- [x] YAML validates successfully
- [x] No `voltage_output_05v_s16` remains (bug fixed!)
- [x] Git diff shows exactly 11 line changes (6 boolean + 4 voltage + 1 header)
- [x] Ready to proceed to Handoff 3 (template application)

---

## Blockers

@human please review voltage type changes before proceeding to Handoff 3:
- Confirm ±5V is correct range for Moku:Go (I believe it is)
- Approve changing from ±20V → ±5V for monitor inputs

---

## Handoff Chain

**This handoff:** 2 of 3
**Next handoff:** [[Obsidian/Project/Handoffs/2025-11-06/2025-11-06-handoff-3-apply-template-to-bpd]]
**Previous:** [[Obsidian/Project/Handoffs/2025-11-06/2025-11-06-handoff-1-fix-forge-vhdl-types]]

---

## Completion Summary

**Completed:** 2025-11-06 23:35
**Git Commit:** `1aecac2` - "fix: Update BPD-RTL.yaml with correct semantic types"
**Validation Results:**
```
✓ YAML syntax valid
✓ Datatype counts verified:
  - 6 × std_logic_reg
  - 2 × voltage_output_5v_bipolar_s16
  - 2 × voltage_input_5v_bipolar_s16
  - 5 × pulse_duration_* (various time types)
  - 0 × boolean (removed)
  - 0 × voltage_output_05v_s16 (removed)
  - 0 × voltage_input_20v_s16 (removed)
```

---

**Created:** 2025-11-06 23:15
**Status:** ✅ Completed
**Priority:** P1 (blocks Handoff 3)
**Dependencies:** Handoff 1 complete
