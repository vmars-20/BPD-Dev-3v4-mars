# Moku Instrument Forge - Monorepo Architecture Guide

**Version:** 2.0.0
**Purpose:** Composable monorepo for Moku platform + probe FPGA development
**Audience:** Human developers and AI agents

---

## Executive Summary

This monorepo implements the **FORGE 3-layer architecture** for building custom FPGA instruments on Moku platforms (Go/Lab/Pro/Delta) with integrated probe support.

**Key Innovation:** Safe initialization handshaking via **FORGE Control Scheme (CR0[31:29])** - a 3-bit calling convention between MCC CustomInstrument and your application logic.

**Reference Implementation:** Basic Probe Driver (BPD) in `examples/basic-probe-driver/` demonstrates production-grade FORGE architecture with hierarchical encoder for oscilloscope debugging (14-bit state+status encoding).

**BPD Deployment Architecture:** See [Obsidian/Project/BPD-Two-Tool-Architecture.md](Obsidian/Project/BPD-Two-Tool-Architecture.md) for complete two-tool deployment + operation architecture (moku-go.py + bpd-debug.py).

---

## Critical Architectural Pattern: FORGE Control Scheme

### The 3-Bit CR0[31:29] Calling Convention

**THIS IS FOUNDATIONAL KNOWLEDGE** - All Moku custom instruments MUST implement this pattern for safe initialization and MCC platform compliance.

```
CR0[31] = forge_ready   ← Set by loader after deployment complete
CR0[30] = user_enable   ← User control (GUI toggle)
CR0[29] = clk_enable    ← Clock gating control
```

Plus a fourth internal signal (not a register bit):
```
loader_done             ← BRAM loader FSM completion signal
```

### Combined Enable Logic

```vhdl
global_enable = forge_ready AND user_enable AND clk_enable AND loader_done
```

**All four conditions must be met** for the module to operate safely.

### Why This Pattern Exists

**Problem:** MCC CustomInstrument interface provides no native handshaking between FPGA deployment (BRAM loading) and application start. Without coordination:
- Application may start before configuration data loaded (undefined behavior)
- No safe user-controlled enable/disable
- No clock gating for power management
- Vendor changes to CustomInstrument break integrations

**Solution:** FORGE control scheme provides:
1. **Deployment handshaking** - `forge_ready` ensures configuration loaded
2. **User control** - `user_enable` for deliberate start/stop
3. **Clock gating** - `clk_enable` for power/debug control
4. **Safe defaults** - Power-on state (0x00000000) keeps module disabled

### Initialization Sequence

```
1. Power-on
   Control0 = 0x00000000
   → All control bits = '0'
   → global_enable = '0'
   → Module DISABLED (safe state)

2. MCC loader completes deployment
   Control0[31] ← 1  (forge_ready = 1)
   → Module still disabled (waiting for user)

3. User enables module via GUI
   Control0[30] ← 1  (user_enable = 1)
   → Module still disabled (clock not enabled)

4. User enables clock
   Control0[29] ← 1  (clk_enable = 1)
   → Module ENABLED ✓
   → global_enable = forge_ready AND user_enable AND clk_enable AND loader_done
                   = 1           AND 1            AND 1          AND 1
                   = 1 ✓
```

### Python Usage Example

```python
import moku

# Deployment complete (set by loader)
moku.set_control(0, 0x80000000)  # forge_ready = 1 (bit 31)

# User enables module
moku.set_control(0, 0xC0000000)  # forge_ready=1, user_enable=1 (bits 31,30)

# User enables clock
moku.set_control(0, 0xE0000000)  # All three bits set (bits 31,30,29)

# Module now operating!
# global_enable = 1
```

### Implementation Reference

**Authoritative VHDL Implementation:**
- Package: `libs/forge-vhdl/vhdl/packages/forge_common_pkg.vhd`
- Function: `combine_forge_ready(forge_ready, user_enable, clk_enable, loader_done) return std_logic`
- Constants: `FORGE_READY_BIT`, `USER_ENABLE_BIT`, `CLK_ENABLE_BIT`

**Production Example:**
- Shim layer: `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd` (Layer 2 of 3-layer architecture)
- Wrapper: `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_forge.vhd` (MCC interface)

**Complete Specification:**
- Full documentation: `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md` (comprehensive guide with diagrams)

---

## MCC CustomInstrument Interface

### Vendor Transition (2025-11-06)

**CRITICAL CHANGE:** Moku Control Computer (MCC) is transitioning to a new `CustomInstrument` entity interface. This affects ALL custom instrument development.

**Vendor Changes:**
- Reduced from 32 control registers → **16 control registers (CR0-CR15)**
- **16 status registers (SR0-SR15)** - Network readable (future release)
- Removed interlacing support (future feature, unstable)
- Removed platform-specific signals (Sync, ExtTrig - not universally supported)

**Network Capabilities:**
- **Control Registers (CR0-CR15):** Network settable via MCC API (Python/GUI) - **ACTIVE**
- **Status Registers (SR0-SR15):** Network readable via MCC API - **FUTURE** (not yet implemented)

### Foundational VHDL Entity Definitions

**IMPORTANT:** We maintain our own simplified, FORGE-compatible entity definitions isolated from vendor changes.

**Location:** `libs/platform/`

| File | Purpose | Status |
|------|---------|--------|
| [MCC_CustomInstrument.vhd](libs/platform/MCC_CustomInstrument.vhd) | **Authoritative** MCC interface entity | DO NOT MODIFY |
| [FORGE_App_Wrapper.vhd](libs/platform/FORGE_App_Wrapper.vhd) | **Template** for FORGE wrapper implementation | CUSTOMIZE |

**Key Architectural Principles:**

1. **MCC_CustomInstrument.vhd** - Vendor interface entity
   - Simplified from upstream (removed interlacing, Sync, ExtTrig)
   - 16 Control Registers (CR0[31:29] reserved for FORGE)
   - 16 Status Registers (future network readable)
   - Platform-agnostic (works on Go/Lab/Pro)

2. **FORGE_App_Wrapper.vhd** - Application wrapper template
   - Implements FORGE 3-layer architecture
   - Extracts FORGE control scheme (CR0[31:29])
   - **Abstracts Control Registers** → `app_reg_*` signals
   - Provides `ready_for_updates` handshaking
   - Main app is **completely Control Register agnostic!**

### The app_reg_* Abstraction

**CRITICAL DESIGN PRINCIPLE:** Main application thinks in terms of `app_reg_<name>` signals, **NOT** Control Registers!

**Example - What the Main App Sees:**
```vhdl
-- Main app port (Layer 3)
entity MyApp_forge_main is
    port (
        Clk               : in std_logic;
        Reset             : in std_logic;
        global_enable     : in std_logic;
        ready_for_updates : out std_logic;  -- Handshaking

        -- Application registers (typed, meaningful names)
        app_reg_enable          : in std_logic;
        app_reg_trigger_voltage : in signed(15 downto 0);  -- Voltage type
        app_reg_pulse_duration  : in unsigned(15 downto 0); -- Time type
        app_reg_threshold       : in signed(15 downto 0);   -- Voltage type

        -- Status outputs
        app_status_busy  : out std_logic;
        app_status_state : out std_logic_vector(5 downto 0)
    );
end entity;
```

**NO mention of:**
- Control0, Control1, CR0[5], etc.
- Network settable registers
- MCC CustomInstrument interface
- FORGE control scheme bits

**Shim Layer (Layer 2) Responsibilities:**
1. **Unpack** Control Registers → `app_reg_*` signals (with types from forge_serialization packages)
2. **Pack** `app_status_*` signals → Status Registers
3. **Synchronize** register updates with `ready_for_updates` handshaking
4. **Compute** `global_enable` from FORGE control scheme

**Benefits:**
- ✅ Main app is **portable** (no MCC knowledge)
- ✅ Main app is **testable** (pure typed signals)
- ✅ Vendor changes **isolated** to shim layer
- ✅ Type safety via forge_serialization packages
- ✅ Safe synchronization (no mid-cycle register changes)

### Register Update Handshaking

**Problem:** Control Registers are network settable and can change asynchronously. Main app FSM must be protected from mid-cycle register changes.

**Solution:** `ready_for_updates` signal from main app to shim.

**Pattern:**
```vhdl
-- In main app (Layer 3):
process(Clk, Reset)
begin
    if Reset = '1' then
        ready_for_updates <= '0';
        state <= IDLE;
    elsif rising_edge(Clk) then
        case state is
            when IDLE =>
                ready_for_updates <= '1';  -- Safe to latch new app_reg_* values
                if app_reg_enable = '1' then
                    ready_for_updates <= '0';  -- Lock registers during operation
                    state <= ARMED;
                end if;
            when ARMED =>
                ready_for_updates <= '0';  -- FSM busy, don't change registers!
                -- ... FSM logic ...
            -- ... other states ...
        end case;
    end if;
end process;
```

**Shim behavior:**
```vhdl
-- In shim (Layer 2):
process(Clk, Reset)
begin
    if Reset = '1' then
        app_reg_enable <= '0';
        -- ... initialize app_reg_* ...
    elsif rising_edge(Clk) then
        if ready_for_updates = '1' then
            -- Main app says it's safe to update
            app_reg_enable <= Control0(0);  -- Latch new value
            app_reg_trigger_voltage <= signed(Control1(15 downto 0));
            -- ... unpack other registers ...
        end if;
        -- else: Hold current values, main app is busy
    end if;
end process;
```

**Production Reference:**
- See: `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd` (main app with ready_for_updates)
- See: `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd` (shim with synchronization)

### BRAM Loader Integration (Layer 1)

**Status:** WIP - Design complete, integration pending

**Purpose:** Load configuration data (LUTs, coefficients, waveforms) into FPGA BRAM from external sources.

**Current State:**
- Reference implementation exists in external EZ-EMFI project (not included in template)
- Fundamentally works but needs adaptation for 16-register interface (was 32 registers)

**Integration Plan:**
1. Port BRAM loader from external reference to `libs/platform/forge_bram_loader.vhd`
2. Adapt register allocation for 16 Control Registers (MCC change)
3. Wire `loader_done` signal to FORGE wrapper
4. Update `forge_ready` flag when loader completes

**Register Allocation (Future):**
```
CR0[31:29] - FORGE control scheme (reserved)
CR0[28:0]  - Application registers
CR1-CR11   - Application registers
CR12-CR15  - BRAM loader protocol (tentative)
  CR12: BRAM address
  CR13: BRAM data
  CR14: BRAM control (write enable, bank select)
  CR15: BRAM status (loader_done, error flags)
```

**When integrated:**
```vhdl
-- In wrapper:
loader_done <= bram_loader_done_signal;  -- From Layer 1 BRAM loader

-- Current workaround:
loader_done <= '1';  -- Hardcoded until BRAM loader integrated
```

---

## FORGE 3-Layer Architecture

All custom instruments follow this pattern:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: MCC_TOP_forge_loader.vhd                          │
│          (Future: Static loader, shared across all apps)    │
│          - Manages BRAM loading                             │
│          - Sets forge_ready flag                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: <App>_forge_shim.vhd                              │
│          (Generated register mapping)                        │
│          - Receives FORGE control signals                    │
│          - Maps CR0-CR15 → friendly names                    │
│          - Computes global_enable                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: <App>_forge_main.vhd                              │
│          (Hand-written application logic)                    │
│          - Completely MCC-agnostic                           │
│          - Only knows friendly signal names                  │
│          - Contains FSM and application logic                │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Layer 1: MCC_TOP_forge_loader.vhd** (Future)
- Manages BRAM initialization from external sources
- Sets `forge_ready` flag when deployment complete
- Provides unified infrastructure for all Forge apps
- **Status:** Design complete, implementation pending

**Layer 2: <App>_forge_shim.vhd** (Present)
- Register mapping: CR0-CR15 → application signals
- FORGE control scheme enforcement (CR0[31:29])
- Computes `global_enable` from 4 conditions
- **Generation:** YAML → VHDL (via forge-codegen, future automation)
- **Current:** Hand-written per application
- **Template:** See `libs/platform/FORGE_App_Wrapper.vhd` for wrapper pattern
- **MCC Interface:** Uses `libs/platform/MCC_CustomInstrument.vhd` entity

**Layer 3: <App>_forge_main.vhd** (Present)
- Pure application logic (FSM, timers, outputs)
- Zero knowledge of Control Registers
- Zero knowledge of FORGE control scheme
- **Portability:** Can be reused across platforms
- **Example:** `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`

### Key Benefits

- ✅ **Safe initialization** - 4-condition enable prevents premature startup
- ✅ **MCC-agnostic application logic** - Layer 3 is portable
- ✅ **Vendor isolation** - CustomInstrument changes isolated to Layer 2
- ✅ **Code generation ready** - Shim layer structured for YAML automation
- ✅ **Deployment handshaking** - forge_ready ensures config loaded

---

## Repository Structure

### Core Platform (git submodules)

| Component | Purpose | Quick Ref |
|-----------|---------|-----------|
| [moku-models](libs/moku-models/) | **REQUIRED** - Moku platform specifications (Go/Lab/Pro/Delta) | [llms.txt](libs/moku-models/llms.txt) |
| [riscure-models](libs/riscure-models/) | Example probe specs (DS1120A EMFI) - Use as template | [llms.txt](libs/riscure-models/llms.txt) |

### VHDL Development Tools (git submodules)

| Component | Purpose | Quick Ref |
|-----------|---------|-----------|
| [forge-vhdl](libs/forge-vhdl/) | Reusable VHDL components + serialization packages | [llms.txt](libs/forge-vhdl/llms.txt) |
| [forge-codegen](tools/forge-codegen/) | YAML → VHDL code generator (23-type system) | [llms.txt](tools/forge-codegen/llms.txt) |

**Note:** forge-codegen is temporarily not used in current BPD workflow (manual VHDL development phase).

### Platform Templates (libs/platform/)

| File | Purpose | Status |
|------|---------|--------|
| [MCC_CustomInstrument.vhd](libs/platform/MCC_CustomInstrument.vhd) | **Authoritative** MCC interface entity (16 CR, 16 SR) | DO NOT MODIFY |
| [FORGE_App_Wrapper.vhd](libs/platform/FORGE_App_Wrapper.vhd) | **Template** for FORGE wrapper implementation | CUSTOMIZE PER APP |

**Key Points:**
- MCC_CustomInstrument.vhd is simplified vendor interface (isolated from upstream changes)
- FORGE_App_Wrapper.vhd demonstrates proper FORGE control scheme + app_reg_* abstraction
- These templates are referenced in MCC CustomInstrument Interface section above

### Reference Implementation: Basic Probe Driver (BPD)

| Component | Purpose | Documentation |
|-----------|---------|---------------|
| [basic-probe-driver](examples/basic-probe-driver/) | Production BPD reference implementation | [FORGE_ARCHITECTURE.md](examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md) |
| [BPD-RTL.yaml](examples/basic-probe-driver/BPD-RTL.yaml) | Authoritative register specification | (in examples/) |

**BPD demonstrates:**
- FORGE 3-layer architecture in production
- Hierarchical encoder for oscilloscope debugging (forge_hierarchical_encoder)
- CocoTB progressive testing (P1-P3 phases)
- Integration with Moku + Riscure models
- Proper use of forge_serialization_* packages

---

## Type System and BPD-RTL.yaml Refinements

### Current Type System Status

**Available in `libs/forge-vhdl/vhdl/packages/forge_serialization_*_pkg.vhd`:**

**Voltage Types (serialization):**
- ±0.5V (16-bit/8-bit, signed/unsigned)
- ±20V (16-bit/8-bit, signed/unsigned)
- ±25V (16-bit/8-bit, signed/unsigned)

**Time Types (serialization):**
- `ns_to_cycles()`, `us_to_cycles()`, `ms_to_cycles()`, `s_to_cycles()`
- Clock-frequency aware conversion functions

**Basic Types:**
- `bool_to_sl()`, `sl_to_bool()` (boolean ↔ std_logic conversion)

### Known Gaps and Refinements Needed

#### Issue #1: Missing `std_logic_reg` Datatype ✅ RESOLVED (2025-11-06)

**Previous State:** Using `boolean` as workaround for single-bit register fields
**Current State:** `std_logic_reg` type added to `forge_serialization_types_pkg.vhd`

**Affected fields in BPD-RTL.yaml:**
```yaml
# These 6 fields currently use 'boolean' but should use 'std_logic_reg'
- arm_enable (CR1[0])
- ext_trigger_in (CR1[1])
- auto_rearm_enable (CR1[2])
- fault_clear (CR1[3])
- monitor_enable (CR8[0])
- monitor_expect_negative (CR8[1])
```

**Problem:**
- `boolean` semantics are for logical operations, not hardware registers
- Generates `bool_to_sl()` / `sl_to_bool()` conversion overhead
- Conceptually wrong: these are **register bits**, not boolean logic

**Solution Implemented:**
- Added `std_logic_reg_from_raw()` and `std_logic_reg_to_raw()` to `forge_serialization_types_pkg.vhd`
- Identity functions (zero overhead)
- File: `libs/forge-vhdl/vhdl/packages/forge_serialization_types_pkg.vhd:48-57, 77-85`

**Next Steps:**
- Update BPD-RTL.yaml to use `std_logic_reg` instead of `boolean` for 6 fields (see Handoff 2)

**Impact:**
- ✅ Cleaner generated VHDL (no conversion overhead)
- ✅ Semantically correct (register bit ≠ boolean logic)
- ✅ Simpler shim layer generation

#### Issue #2: Missing ±5V Voltage Type ✅ RESOLVED (2025-11-06)

**Previous State:** BPD-RTL.yaml uses `voltage_output_05v_s16` which means **±0.5V**, not ±5V!
**Current State:** ±5V types added to `forge_serialization_voltage_pkg.vhd`

**Problem in BPD-RTL.yaml:**
```yaml
- name: trig_out_voltage
  datatype: voltage_output_05v_s16  # ±0.5V range
  min_value: -5000                  # ±5V in mV - WRONG!
  max_value: 5000
```

**Type name confusion:**
- `05v` = ±**0.5V** (not 5V!)
- BPD needs ±**5.0V** (Moku DAC/ADC range)

**Available voltage ranges in forge_serialization_voltage_pkg.vhd:**
- ±0.5V ✓ (too small for BPD)
- ±5V ✅ **ADDED!** (most common Moku DAC/ADC range)
- ±20V ✓ (works but overkill)
- ±25V ✓ (works but overkill)

**Solution Implemented:**
- Added `voltage_input_5v_bipolar_s16_from_raw()` / `_to_raw()`
- Added `voltage_output_5v_bipolar_s16_from_raw()` / `_to_raw()`
- Identity conversion functions (type cast only)
- File: `libs/forge-vhdl/vhdl/packages/forge_serialization_voltage_pkg.vhd:120-140, 303-329`

**Next Steps - Update BPD-RTL.yaml (Handoff 2):**
```yaml
- name: trig_out_voltage
  datatype: voltage_output_5v_bipolar_s16  # Correct!
  min_value: -5000
  max_value: 5000

- name: intensity_voltage
  datatype: voltage_output_5v_bipolar_s16  # Correct!
  min_value: -5000
  max_value: 5000

- name: probe_monitor_feedback
  datatype: voltage_input_5v_bipolar_s16  # Correct!
  min_value: -5000
  max_value: 5000

- name: monitor_threshold_voltage
  datatype: voltage_input_5v_bipolar_s16  # Correct!
  min_value: -5000
  max_value: 5000
```

**Impact:**
- ✅ **CRITICAL FIX** - Corrects BPD voltage type mismatch (was using ±0.5V!)
- ✅ ±5V is now standard type (most common Moku DAC/ADC range)
- ✅ Voltage type system gap closed

#### Issue #3: Voltage Type System Design Doc Not Implemented

**Design Document:** `WIP/voltage_types_reference.py` defines 3 voltage domains:
- `Voltage_3V3` → 0-3.3V (unipolar)
- `Voltage_5V0` → 0-5.0V (unipolar)
- `Voltage_5V_Bipolar` → ±5.0V (bipolar)

**Implementation Status:**
- `forge_serialization_voltage_pkg.vhd` has **different ranges** (±0.5V, ±20V, ±25V)
- Design doc voltage domains **not implemented** in VHDL packages

**Recommended Action:**
- Align `forge_serialization_voltage_pkg.vhd` with design doc
- Add missing ±5V types as priority
- Document relationship between design doc and implementation

---

## BPD-RTL.yaml: Authoritative Register Specification

**Status:** IN REVIEW (refinements needed, see above)

**File:** [BPD-RTL.yaml](BPD-RTL.yaml)

**Purpose:** Authoritative specification of Basic Probe Driver control registers and data types.

**Key Design Principles:**
1. **Ordering mirrors human workflow** - Configure arming → Tune outputs → Wire monitoring
2. **Millivolt units** - All voltages in mV for consistency with Moku platforms
3. **Minimal bit widths** - Time fields use narrowest width that preserves range
4. **Safety-first defaults** - Conservative values for thermal/electrical safety

**Register Allocation:**
```
CR0[31:29] - FORGE control scheme (reserved)
CR1        - Lifecycle control (arm, trigger, rearm, fault_clear)
CR2-CR5    - Output controls (trig voltage/duration, intensity voltage/duration)
CR6        - Trigger timeout
CR7        - Cooldown interval
CR8        - Monitor control
CR9        - Monitor threshold
CR10       - Monitor window start
CR11       - Monitor window duration
CR12-CR15  - Reserved (future expansion)
```

**Resolved Issues (2025-11-06):**
1. ✅ `std_logic_reg` datatype added to forge_serialization_types_pkg.vhd
2. ✅ ±5V voltage types added to forge_serialization_voltage_pkg.vhd

**Remaining Tasks (Handoff 2):**
1. Update BPD-RTL.yaml to use `std_logic_reg` instead of `boolean` for 6 control bits
2. Update BPD-RTL.yaml to use `voltage_*_5v_bipolar_s16` instead of `voltage_*_05v_s16`
3. Regenerate or manually update BPD shim layer to use new types

---

## Documentation Hierarchy

### Three-Tier Documentation Pattern

All submodules follow this token-efficient structure:

**Tier 1: llms.txt** (~500-1000 tokens)
- Quick component catalog
- Essential facts, API surface
- Common tasks and workflows
- Pointers to Tier 2

**Tier 2: CLAUDE.md** (~3-5k tokens)
- Complete design guide
- Integration patterns
- Development workflows
- Design rationale

**Tier 3: Source + Specialized Docs** (load as needed)
- VHDL implementations
- CocoTB tests
- Detailed guides (VHDL_CODING_STANDARDS.md, etc.)

### Navigation Pattern

**Quick question?** → Read llms.txt files
**Design/integration question?** → Read CLAUDE.md files
**Implementation/debugging?** → Read source code + specialized docs

---

## Common Workflows

### 1. Understanding FORGE Architecture

**Start here:**
1. Read this file (CLAUDE.md) - FORGE control scheme section
2. Read `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md` - Complete specification
3. Examine `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd` - Reference implementation

**Key insight:** CR0[31:29] is the calling convention between MCC and your app.

### 2. Developing New Custom Instrument

**Steps:**
1. Create YAML register specification (model: examples/basic-probe-driver/BPD-RTL.yaml)
2. Identify required datatypes from forge_serialization_* packages
3. Design Layer 3 (main) entity - application FSM/logic
4. Design Layer 2 (shim) - register mapping + FORGE control
5. Implement CustomWrapper - MCC interface + Layer 2 instantiation
6. Test with CocoTB progressive testing (P1 → P2 → P3)

**Critical:** Layer 2 MUST implement FORGE control scheme (CR0[31:29])

### 3. Adding New Probe Support

**Pattern:**
1. Keep `libs/moku-models/` (CORE - always required)
2. Keep or remove `libs/riscure-models/` (example reference)
3. Create `libs/<your-probe>-models/` (new probe specifications)
4. Model structure on riscure-models (Pydantic models, voltage safety)
5. Update monorepo pyproject.toml workspace members
6. Add 3-tier documentation (llms.txt → CLAUDE.md → source)

**Reference:** See TEMPLATE.md for complete customization guide

### 4. Type System Lookup

**Available types:**
- Check `libs/forge-vhdl/llms.txt` - Quick reference
- Check `libs/forge-vhdl/vhdl/packages/forge_serialization_*_pkg.vhd` - Implementation
- Check BPD-RTL.yaml - Usage examples

**Recent additions (2025-11-06):**
- ✅ `std_logic_reg` type added - Semantic correctness for register bits (not boolean logic)
- ✅ ±5V voltage types added - `voltage_input_5v_bipolar_s16`, `voltage_output_5v_bipolar_s16`

### 5. VHDL Component Usage

**Packages available:**
- `forge_common_pkg` - FORGE control scheme (combine_forge_ready)
- `forge_serialization_types_pkg` - Boolean conversions, register bit type (`std_logic_reg`)
- `forge_serialization_voltage_pkg` - Voltage register serialization (±0.5V, ±5V, ±20V, ±25V)
- `forge_serialization_time_pkg` - Time/cycle conversions
- `forge_voltage_3v3_pkg` - Direct 0-3.3V utilities
- `forge_voltage_5v0_pkg` - Direct 0-5.0V utilities
- `forge_voltage_5v_bipolar_pkg` - Direct ±5.0V utilities

**Import pattern:**
```vhdl
library WORK;
use WORK.forge_common_pkg.ALL;                   -- FORGE_READY control
use WORK.forge_serialization_types_pkg.ALL;      -- Core types
use WORK.forge_serialization_voltage_pkg.ALL;    -- Voltage serialization
use WORK.forge_serialization_time_pkg.ALL;       -- Time conversions
```

---

## Testing Strategy

### CocoTB Progressive Testing

BPD uses **progressive test levels** (P1 → P2 → P3 → P4) for token-efficient debugging:

**P1 - BASIC** (Default, LLM-optimized)
- 3-5 essential tests only
- <20 line output, <100 tokens
- Fast iteration for AI-assisted development

**P2 - INTERMEDIATE** (Standard validation)
- 10-15 tests with edge cases
- <50 line output
- Comprehensive feature coverage

**P3 - COMPREHENSIVE** (Full coverage)
- 20-30 tests with stress testing
- Boundary values, corner cases
- Production readiness validation

**Location:** `examples/basic-probe-driver/vhdl/cocotb_test/`

**Documentation:**
- `examples/basic-probe-driver/vhdl/cocotb_test/README.md` - Complete testing guide
- `libs/forge-vhdl/CLAUDE.md` - CocoTB progressive testing standard

---

## Key Design Principles

1. **FORGE Control Scheme** - CR0[31:29] calling convention is MANDATORY
2. **3-Layer Architecture** - Loader → Shim → Main (clean separation)
3. **MCC-Agnostic Application Logic** - Layer 3 knows nothing about Control Registers
4. **Safe Initialization** - 4-condition enable prevents premature startup
5. **Tiered Documentation** - llms.txt → CLAUDE.md → source (token efficiency)
6. **Type Safety** - Pydantic validation, voltage domain safety, serialization functions
7. **Context Efficiency** - Load minimally, expand as needed (200k token budget)
8. **Single Source of Truth** - Each submodule authoritative for its domain

---

## Development Status

**Current Phase:** BPD debugging and refinement

**Active Work:**
- BPD FSM implementation (has known bug - debugging deferred)
- Type system refinements (std_logic_reg, ±5V voltage types)
- Documentation updates (this file, llms.txt updates)

**Completed:**
- FORGE 3-layer architecture design
- BPD-RTL.yaml specification (pending refinements)
- VHDL serialization package migration to forge-vhdl
- CocoTB progressive testing infrastructure
- Hierarchical encoder for oscilloscope debugging (forge_hierarchical_encoder)

**Next Steps:**
1. Complete type system refinements (std_logic_reg, ±5V types)
2. Update BPD-RTL.yaml with correct types
3. Update root llms.txt with FORGE pattern summary
4. Update forge-codegen templates (VOLO → FORGE naming)
5. Return to BPD FSM debugging

---

## Related Documentation

### Monorepo Root
- **llms.txt** - Quick reference, navigation
- **TEMPLATE.md** - Monorepo customization guide (adding probes)
- **README.md** - Getting started, setup
- **VHDL_SERIALIZATION_MIGRATION.md** - Package migration notes

### Submodule Documentation
- **libs/forge-vhdl/CLAUDE.md** - VHDL components, CocoTB testing
- **libs/moku-models/CLAUDE.md** - Platform integration patterns
- **libs/riscure-models/CLAUDE.md** - Probe specifications
- **tools/forge-codegen/CLAUDE.md** - Code generation internals (dormant)

### BPD Reference Implementation
- **examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md** - Complete 3-layer architecture spec
- **examples/basic-probe-driver/vhdl/cocotb_test/README.md** - CocoTB testing guide
- **examples/basic-probe-driver/BPD-RTL.yaml** - Authoritative register specification
- **examples/basic-probe-driver/VHDL_SERIALIZATION_MIGRATION.md** - Package migration notes

### Architecture Deep Dives
- **.claude/shared/ARCHITECTURE_OVERVIEW.md** - v2.0 repository structure
- **.claude/shared/CONTEXT_MANAGEMENT.md** - Token optimization strategy
- **Obsidian/Project/BPD-Two-Tool-Architecture.md** - **✅ AUTHORITATIVE** BPD deployment + operation architecture
- **docs/migration/voltage_types_reference.py** - Voltage type system design doc (if exists)

---

## For AI Agents

### Context Loading Strategy

Follow tiered loading (see `.claude/shared/CONTEXT_MANAGEMENT.md`):

**Tier 1 (Always load first):**
- This file (CLAUDE.md) - Architecture overview
- Root llms.txt - Quick navigation
- Relevant submodule llms.txt files

**Tier 2 (Design/integration work):**
- Submodule CLAUDE.md files
- examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md (for FORGE pattern deep dive)
- Shared architecture docs (.claude/shared/)

**Tier 3 (Implementation/debugging):**
- Source code files
- Test files
- Specialized guides

### Obsidian Navigation Pattern

For **session context and collaboration workspace**, use parallel PDA pattern:

**Entry point:** `Obsidian/Project/README.md` (not llms.txt)
- Subdirectory READMEs: `Handoffs/README.md`, `Sessions/README.md`
- Specific files: Handoff/session documents

**Purpose:** Session handoffs, daily wrap-ups, and agent-human collaboration notes

**Key difference from code PDA:**
- Code/architecture: llms.txt → CLAUDE.md → source
- Session/collaboration: Obsidian/Project/README.md → subdirectory READMEs → notes

### Obsidian Session Management

**Three slash commands for session lifecycle:**

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/obsd_new_session` | Create new session with goals | Starting fresh work |
| `/obsd_continue_session` | Resume existing session | Continuing previous work |
| `/obsd_close_session` | Archive session + harvest `/compact` | Ending session |

**Key innovation:** `/obsd_close_session` can harvest context compaction summary from `/compact` command!

**Workflow:**
```
1. /obsd_new_session
   → Creates session-plan.md
   → Optional: Creates git branch (sessions/YYYY-MM-DD-description)
   → Links active handoffs

2. [Work happens, commits made]

3. If token usage >80%: User runs /compact

4. /obsd_close_session
   → Harvests compaction summary (if available)
   → Generates session archive (5-6 files)
   → Commits to git
   → Optional: Merges session branch
```

**Session archive structure:**
```
Obsidian/Project/Sessions/YYYY-MM-DD-description/
├── session-plan.md          # From open
├── compaction-summary.md    # Raw /compact output (if used)
├── session-summary.md       # Human-readable summary
├── commits.md               # Git log extraction
├── decisions.md             # Key technical decisions
├── next-session-plan.md     # Tomorrow's starting point
└── handoffs/                # Symlinks to active handoffs
```

**See:**
- `.claude/commands/obsd_new_session.md` - New session command
- `.claude/commands/obsd_continue_session.md` - Continue session command
- `.claude/commands/obsd_close_session.md` - Close session command
- `Obsidian/Project/Sessions/README.md` - Complete session management guide

### Critical Knowledge

**ALWAYS REMEMBER:**
1. **CR0[31:29] = FORGE control scheme** - This is NON-NEGOTIABLE for all Moku instruments
2. **3-layer architecture** - Loader → Shim → Main (isolation pattern)
3. **Type system gaps exist** - std_logic_reg missing, ±5V type missing (workarounds documented)
4. **BPD is reference implementation** - Look here for production patterns
5. **forge-codegen dormant** - Not currently used, manual VHDL development phase

### Delegation Strategy

**Use Task tool with Explore agent for:**
- Finding architectural patterns across codebase
- Understanding cross-file relationships
- Discovering undocumented conventions

**Use direct file reads for:**
- Specific implementation details
- Known file locations
- Quick lookups

---

**Last Updated:** 2025-11-06
**Maintained By:** Moku Instrument Forge Team
**Version:** 2.0.0
