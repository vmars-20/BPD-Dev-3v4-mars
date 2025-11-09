---
created: 2025-11-06
type: handoff
priority: P1
status: completed
depends_on:
git_commits:
  - fd0912d # feat: Add std_logic_reg and ±5V voltage serialization types
---

# Handoff 1: Fix forge-vhdl Serialization Types

**Date:** 2025-11-06 23:15
**Session:** Template Application - Phase 1
**Owner:** @claude
**Dependencies:** None
**Estimated Time:** 30 minutes

---

## Context: What Needs to Be Done

The BPD-RTL.yaml specification uses two datatypes that don't exist in the forge-vhdl serialization packages yet:

1. **`std_logic_reg`** - Currently using `boolean` as workaround (semantic mismatch)
2. **±5V voltage types** - Currently using `voltage_output_05v_s16` (±0.5V) which is WRONG!

These types need to be added to `libs/forge-vhdl/vhdl/packages/` before we can fix BPD-RTL.yaml.

**Critical Discovery:** Time types (`pulse_duration_ns_u16`, etc.) are NOT serialization types - they're forge-codegen metadata that maps to `unsigned` + conversion functions. No VHDL changes needed!

---

## What I Just Did (Previous Session)

✅ Read commit `001cb50014b2b9255b54e3769b467062a7b1e23f` from BPD-Debug repo
✅ Understood VHDL serialization package migration pattern
✅ Confirmed time types use conversion functions, not serialization types
✅ Identified exactly what's missing in forge-vhdl packages

---

## Next Steps

@claude please complete these tasks in order:

### Task 1.1: Add `std_logic_reg` Type

**File:** `libs/forge-vhdl/vhdl/packages/forge_serialization_types_pkg.vhd`

**What to add:**
```vhdl
-- std_logic_reg: Direct register bit type
-- No conversion functions needed, maps 1:1 to std_logic
-- Used for single-bit control register fields (NOT boolean logic!)
function std_logic_reg_from_raw(
    raw : std_logic
) return std_logic;

function std_logic_reg_to_raw(
    value : std_logic
) return std_logic;
```

**Implementation:**
```vhdl
-- Package body
function std_logic_reg_from_raw(raw : std_logic) return std_logic is
begin
    return raw;  -- Identity function
end function;

function std_logic_reg_to_raw(value : std_logic) return std_logic is
begin
    return value;  -- Identity function
end function;
```

**Rationale:**
- Semantic correctness: Register bits ≠ boolean logic
- No conversion overhead (optimizes away)
- Clear intent in generated code

### Task 1.2: Add ±5V Voltage Types

**File:** `libs/forge-vhdl/vhdl/packages/forge_serialization_voltage_pkg.vhd`

**What to add:** (mirror existing ±20V pattern)

```vhdl
-- Convert raw register bits to voltage_input_5v_bipolar_s16
-- Range: ±5.0V, Bits: 16, Type: signed
function voltage_input_5v_bipolar_s16_from_raw(
    raw : std_logic_vector(15 downto 0)
) return signed;

-- Convert voltage_input_5v_bipolar_s16 to raw register bits
function voltage_input_5v_bipolar_s16_to_raw(
    value : signed(15 downto 0)
) return std_logic_vector;

-- Convert raw register bits to voltage_output_5v_bipolar_s16
-- Range: ±5.0V, Bits: 16, Type: signed
function voltage_output_5v_bipolar_s16_from_raw(
    raw : std_logic_vector(15 downto 0)
) return signed;

-- Convert voltage_output_5v_bipolar_s16 to raw register bits
function voltage_output_5v_bipolar_s16_to_raw(
    value : signed(15 downto 0)
) return std_logic_vector;
```

**Implementation:** (same as ±20V types - identity conversion)
```vhdl
function voltage_input_5v_bipolar_s16_from_raw(
    raw : std_logic_vector(15 downto 0)
) return signed is
begin
    return signed(raw);
end function;

function voltage_input_5v_bipolar_s16_to_raw(
    value : signed(15 downto 0)
) return std_logic_vector is
begin
    return std_logic_vector(value);
end function;

-- (repeat for output variant)
```

**Why ±5V is critical:**
- Most common Moku DAC/ADC range (Go: ±5V, Lab/Pro: ±10V)
- BPD-RTL.yaml currently uses ±0.5V by mistake (wrong type name!)
- Should be standard type alongside ±20V, ±25V

### Task 1.3: Test Compilation

**Commands:**
```bash
cd libs/forge-vhdl
ghdl -a --std=08 vhdl/packages/forge_serialization_types_pkg.vhd
ghdl -a --std=08 vhdl/packages/forge_serialization_voltage_pkg.vhd
```

**Success criteria:**
- ✅ No compilation errors
- ✅ New functions accessible
- ✅ Ready for BPD-RTL.yaml update (Handoff 2)

---

## Files to Modify

1. `libs/forge-vhdl/vhdl/packages/forge_serialization_types_pkg.vhd`
   - Add `std_logic_reg_from_raw()` / `_to_raw()`

2. `libs/forge-vhdl/vhdl/packages/forge_serialization_voltage_pkg.vhd`
   - Add `voltage_input_5v_bipolar_s16` functions
   - Add `voltage_output_5v_bipolar_s16` functions

---

## Resources

**Reference Implementation:**
- See existing ±20V types in `forge_serialization_voltage_pkg.vhd:169-181`
- See existing `bool_to_sl()` in `forge_serialization_types_pkg.vhd:42-65`

**Migration Guide:**
- `VHDL_SERIALIZATION_MIGRATION.md` (from BPD-Debug commit)

**Documentation to Update:**
- `libs/forge-vhdl/llms.txt` - Add new types to catalog
- `CLAUDE.md` (root) - Update type system section

**Commands:**
```bash
# Test compilation
cd libs/forge-vhdl
ghdl -a --std=08 vhdl/packages/forge_serialization_types_pkg.vhd
ghdl -a --std=08 vhdl/packages/forge_serialization_voltage_pkg.vhd

# Update documentation
# (manual edit of llms.txt and CLAUDE.md)
```

---

## Success Criteria

- [x] `std_logic_reg_from_raw()` and `_to_raw()` added to forge_serialization_types_pkg.vhd
- [x] `voltage_input_5v_bipolar_s16` functions added to forge_serialization_voltage_pkg.vhd
- [x] `voltage_output_5v_bipolar_s16` functions added to forge_serialization_voltage_pkg.vhd
- [x] Both packages compile cleanly with GHDL
- [x] Documentation updated (llms.txt, CLAUDE.md updated with new types)
- [x] Ready to proceed to Handoff 2 (BPD-RTL.yaml update)

---

## Blockers

@human
- None expected - straightforward addition following existing patterns

---

## Handoff Chain

**This handoff:** 1 of 3
**Next handoff:** [[Obsidian/Project/Handoffs/2025-11-06/2025-11-06-handoff-2-update-bpd-rtl-yaml]]
**Previous:** None (starting point)

---

## Completion Summary

**Completed:** 2025-11-06 23:30
**Git Commit:** `fd0912d` - "feat: Add std_logic_reg and ±5V voltage serialization types"
**Files Modified:**
- `libs/forge-vhdl/vhdl/packages/forge_serialization_types_pkg.vhd`
- `libs/forge-vhdl/vhdl/packages/forge_serialization_voltage_pkg.vhd`
- `libs/forge-vhdl/CLAUDE.md`
- `libs/forge-vhdl/llms.txt`
- `CLAUDE.md` (root - documentation updates)

**Validation Results:**
```
✓ GHDL compilation successful for both packages
✓ std_logic_reg type added (identity conversion functions)
✓ voltage_input_5v_bipolar_s16 type added
✓ voltage_output_5v_bipolar_s16 type added
✓ Documentation updated in forge-vhdl and root
```

---

**Created:** 2025-11-06 23:15
**Status:** ✅ Completed
**Priority:** P1 (blocks Handoff 2)
**Dependencies:** None (starting point)
