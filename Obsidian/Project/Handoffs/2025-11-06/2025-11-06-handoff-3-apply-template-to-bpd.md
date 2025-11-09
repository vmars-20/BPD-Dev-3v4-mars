---
created: 2025-11-06
type: handoff
priority: P1
status: pending
depends_on:
  - handoff-1-fix-forge-vhdl-types
  - handoff-2-update-bpd-rtl-yaml
---

# Handoff 3: Apply libs/platform/ Template Authoritatively to BPD

**Date:** 2025-11-06 23:15
**Session:** Template Application - Phase 3
**Owner:** @claude
**Dependencies:** Handoff 1 & 2 complete
**Estimated Time:** 60-90 minutes

---

## Context: What Needs to Be Done

Apply the `libs/platform/` FORGE template **authoritatively** to BPD, replacing the current halfway-migrated implementation.

**Critical Design Pattern:**
- **Shim layer** uses generic `app_reg_*` signals (template-level)
- **Main app** uses meaningful `bpd_*` signals (application-specific)
- **Connection** via direct port mapping in VHDL instantiation

```vhdl
-- In shim: Generic template signals
signal app_reg_trig_voltage : signed(15 downto 0);

-- In main: Meaningful BPD signals
entity BPD_forge_main is
    port (
        bpd_trig_out_voltage : in signed(15 downto 0);
        ...
    );
end entity;

-- Direct mapping in shim instantiation
MAIN: entity WORK.BPD_forge_main
    port map (
        bpd_trig_out_voltage => app_reg_trig_voltage,
        ...
    );
```

**Goal:** Shim stays generic (reusable template), main gets meaningful names.

---

## What I Just Did (Previous Handoffs)

From Handoff 1:
✅ Added `std_logic_reg` and ±5V types to forge-vhdl

From Handoff 2:
✅ Fixed BPD-RTL.yaml types (boolean → std_logic_reg, voltage fixes)
✅ Validated YAML syntax
✅ Confirmed 12 fields now use correct types

---

## Next Steps

@claude complete these tasks in order:

### Task 3.1: Update CustomWrapper (Top Level)

**File:** `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_forge.vhd`

**Current status:** Partially implements FORGE pattern
**Target:** Full compliance with `libs/platform/FORGE_App_Wrapper.vhd` template

**Changes needed:**

1. **Extract FORGE control scheme (CR0[31:29]):**
   ```vhdl
   signal forge_ready  : std_logic;  -- CR0[31]
   signal user_enable  : std_logic;  -- CR0[30]
   signal clk_enable   : std_logic;  -- CR0[29]
   signal loader_done  : std_logic;  -- Internal (hardcode '1' for now)

   forge_ready <= Control0(31);
   user_enable <= Control0(30);
   clk_enable  <= Control0(29);
   loader_done <= '1';  -- No BRAM loader yet
   ```

2. **Compute global_enable:**
   ```vhdl
   use WORK.forge_common_pkg.ALL;

   global_enable <= combine_forge_ready(
       forge_ready  => forge_ready,
       user_enable  => user_enable,
       clk_enable   => clk_enable,
       loader_done  => loader_done
   );
   ```

3. **Add clk_en port** (for future clock gating):
   ```vhdl
   entity basic_probe_driver_CustomInstrument is
       port (
           Clk    : in std_logic;
           Reset  : in std_logic;
           clk_en : in std_logic := '1';  -- NEW
           ...
       );
   end entity;
   ```

4. **Instantiate shim with generic signals:**
   - Pass `global_enable` to shim
   - Pass `ready_for_updates` from main → shim
   - Use `app_reg_*` signal naming at wrapper level

### Task 3.2: Update BPD Shim (Layer 2)

**File:** `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd`

**Current status:** Direct register mapping, no handshaking
**Target:** Template-compliant shim with `app_reg_*` signals

**Major changes:**

1. **Add `ready_for_updates` handshaking:**
   ```vhdl
   entity BPD_forge_shim is
       port (
           ...
           global_enable     : in  std_logic;
           ready_for_updates : in  std_logic;  -- NEW (from main)
           ...
       );
   end entity;
   ```

2. **Rename signals to template convention:**
   ```vhdl
   -- OLD (current BPD naming)
   signal arm_enable : std_logic;
   signal trig_out_voltage : signed(15 downto 0);

   -- NEW (template generic naming)
   signal app_reg_arm_enable : std_logic;
   signal app_reg_trig_out_voltage : signed(15 downto 0);
   ```

3. **Add synchronization logic:**
   ```vhdl
   process(Clk, Reset)
   begin
       if Reset = '1' then
           app_reg_arm_enable <= '0';
           -- ... initialize all app_reg_* ...
       elsif rising_edge(Clk) then
           if ready_for_updates = '1' then
               -- Main app says safe to update
               app_reg_arm_enable <= Control1(0);
               app_reg_trig_out_voltage <= signed(Control2(15 downto 0));
               -- ... unpack other registers ...
           end if;
           -- else: Hold current values, main is busy
       end if;
   end process;
   ```

4. **Update main instantiation with direct mapping:**
   ```vhdl
   MAIN: entity WORK.BPD_forge_main
       port map (
           Clk   => Clk,
           Reset => Reset,
           global_enable     => global_enable,
           ready_for_updates => ready_for_updates,  -- Output from main

           -- Direct mapping: bpd_* ← app_reg_*
           bpd_arm_enable           => app_reg_arm_enable,
           bpd_ext_trigger_in       => app_reg_ext_trigger_in,
           bpd_trig_out_voltage     => app_reg_trig_out_voltage,
           bpd_trig_out_duration    => app_reg_trig_out_duration,
           bpd_intensity_voltage    => app_reg_intensity_voltage,
           bpd_intensity_duration   => app_reg_intensity_duration,
           bpd_trigger_wait_timeout => app_reg_trigger_wait_timeout,
           bpd_cooldown_interval    => app_reg_cooldown_interval,
           bpd_auto_rearm_enable    => app_reg_auto_rearm_enable,
           bpd_fault_clear          => app_reg_fault_clear,

           -- Monitor signals
           bpd_monitor_enable            => app_reg_monitor_enable,
           bpd_monitor_expect_negative   => app_reg_monitor_expect_negative,
           bpd_monitor_threshold_voltage => app_reg_monitor_threshold_voltage,
           bpd_monitor_window_start      => app_reg_monitor_window_start,
           bpd_monitor_window_duration   => app_reg_monitor_window_duration,

           -- I/O
           bpd_probe_monitor_feedback => InputA,
           OutputA => OutputA,
           OutputB => OutputB,
           OutputC => OutputC,
           OutputD => OutputD
       );
   ```

### Task 3.3: Update BPD Main (Layer 3)

**File:** `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`

**Current status:** Uses mixed naming, no ready_for_updates
**Target:** Clean `bpd_*` signals, proper handshaking

**Changes needed:**

1. **Rename all ports to `bpd_*` convention:**
   ```vhdl
   entity BPD_forge_main is
       port (
           -- Clock & Control
           Clk               : in std_logic;
           Reset             : in std_logic;
           global_enable     : in std_logic;
           ready_for_updates : out std_logic;  -- NEW

           -- Lifecycle (bpd_* prefix)
           bpd_arm_enable           : in std_logic;
           bpd_ext_trigger_in       : in std_logic;
           bpd_trigger_wait_timeout : in unsigned(15 downto 0);
           bpd_auto_rearm_enable    : in std_logic;
           bpd_fault_clear          : in std_logic;

           -- Trigger output
           bpd_trig_out_voltage  : in signed(15 downto 0);
           bpd_trig_out_duration : in unsigned(15 downto 0);

           -- Intensity output
           bpd_intensity_voltage  : in signed(15 downto 0);
           bpd_intensity_duration : in unsigned(15 downto 0);

           -- Timing
           bpd_cooldown_interval : in unsigned(23 downto 0);

           -- Monitor
           bpd_probe_monitor_feedback    : in signed(15 downto 0);
           bpd_monitor_enable            : in std_logic;
           bpd_monitor_threshold_voltage : in signed(15 downto 0);
           bpd_monitor_expect_negative   : in std_logic;
           bpd_monitor_window_start      : in unsigned(31 downto 0);
           bpd_monitor_window_duration   : in unsigned(31 downto 0);

           -- Outputs
           OutputA : out signed(15 downto 0);
           OutputB : out signed(15 downto 0);
           OutputC : out signed(15 downto 0);
           OutputD : out signed(15 downto 0)
       );
   end entity BPD_forge_main;
   ```

2. **Add ready_for_updates logic:**
   ```vhdl
   process(Clk, Reset)
   begin
       if Reset = '1' then
           ready_for_updates <= '0';
           state <= IDLE;
       elsif rising_edge(Clk) then
           case state is
               when IDLE =>
                   ready_for_updates <= '1';  -- Safe to update
                   if bpd_arm_enable = '1' then
                       ready_for_updates <= '0';  -- Lock registers
                       state <= ARMED;
                   end if;

               when ARMED | FIRING | COOLDOWN =>
                   ready_for_updates <= '0';  -- FSM busy
                   -- ... state transitions ...

               when others =>
                   ready_for_updates <= '1';
                   state <= IDLE;
           end case;
       end if;
   end process;
   ```

3. **Update internal signal references:**
   - Everywhere that used `arm_enable` → now `bpd_arm_enable`
   - Everywhere that used `trig_out_voltage` → now `bpd_trig_out_voltage`
   - (Systematic rename of all input signals)

---

## Files to Modify

1. **`examples/basic-probe-driver/vhdl/CustomWrapper_bpd_forge.vhd`**
   - Add clk_en port
   - Extract CR0[31:29] FORGE control
   - Compute global_enable
   - Update shim instantiation

2. **`examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd`**
   - Rename signals to `app_reg_*`
   - Add `ready_for_updates` port
   - Add synchronization logic
   - Update main instantiation with direct mapping

3. **`examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`**
   - Rename all ports to `bpd_*`
   - Add `ready_for_updates` output
   - Implement handshaking logic
   - Update internal signal references

---

## Validation Steps

@claude after implementation:

1. **Check VHDL syntax:**
   ```bash
   cd examples/basic-probe-driver/vhdl
   ghdl -a --std=08 ../../../libs/forge-vhdl/vhdl/packages/*.vhd
   ghdl -a --std=08 src/basic_probe_driver_custom_inst_main.vhd
   ghdl -a --std=08 BPD_forge_shim.vhd
   ghdl -a --std=08 CustomWrapper_test_stub.vhd
   ghdl -a --std=08 CustomWrapper_bpd_forge.vhd
   ```

2. **Verify signal naming:**
   ```bash
   # Shim should have app_reg_*
   grep "signal app_reg_" BPD_forge_shim.vhd | wc -l  # Should be ~15

   # Main should have bpd_* ports
   grep "bpd_" src/basic_probe_driver_custom_inst_main.vhd | wc -l  # Should be ~15
   ```

3. **Check ready_for_updates:**
   ```bash
   # Shim declares as input from main
   grep "ready_for_updates.*in" BPD_forge_shim.vhd

   # Main declares as output
   grep "ready_for_updates.*out" src/basic_probe_driver_custom_inst_main.vhd
   ```

---

## Resources

**Template Reference:**
- `libs/platform/FORGE_App_Wrapper.vhd` - AUTHORITATIVE pattern
- `libs/platform/MCC_CustomInstrument.vhd` - Entity definition

**Current Implementation:**
- `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_forge.vhd`
- `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd`
- `examples/basic-probe-driver/vhdl/src/basic_probe_driver_custom_inst_main.vhd`

**Documentation:**
- `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md` - Update after changes

**Commands:**
```bash
cd examples/basic-probe-driver/vhdl

# Compile packages first
ghdl -a --std=08 ../../../libs/forge-vhdl/vhdl/packages/*.vhd

# Compile BPD in order
ghdl -a --std=08 src/basic_probe_driver_custom_inst_main.vhd  # Main first
ghdl -a --std=08 BPD_forge_shim.vhd                            # Shim second
ghdl -a --std=08 CustomWrapper_test_stub.vhd                   # Stub
ghdl -a --std=08 CustomWrapper_bpd_forge.vhd                   # Wrapper last

# Check for errors
echo $?  # Should be 0
```

---

## Success Criteria

- [ ] CustomWrapper extracts CR0[31:29] FORGE control
- [ ] CustomWrapper computes global_enable via combine_forge_ready()
- [ ] Shim uses `app_reg_*` signal naming (generic)
- [ ] Shim implements `ready_for_updates` synchronization
- [ ] Main uses `bpd_*` port naming (meaningful)
- [ ] Main implements `ready_for_updates` output logic
- [ ] Direct mapping in shim: `bpd_* => app_reg_*`
- [ ] All 3 files compile cleanly with GHDL
- [ ] Template pattern fully applied (no halfway migration artifacts)

---

## Blockers

@human
- None expected if Handoff 1 & 2 complete
- May need review of signal naming conventions

---

## Design Principle to Preserve

**Critical:** The shim layer must stay generic (template-level) while the main app gets meaningful names.

This allows:
- ✅ Shim reusable across applications
- ✅ Template updates propagate easily
- ✅ Main app has readable, domain-specific code
- ✅ Clear separation: platform (shim) vs. application (main)

---

## Handoff Chain

**This handoff:** 3 of 4
**Next handoff:** [[Obsidian/Project/Handoffs/2025-11-06/2025-11-06-handoff-4-complete-forge-integration]]
**Previous:** [[Obsidian/Project/Handoffs/2025-11-06/2025-11-06-handoff-2-update-bpd-rtl-yaml]]

---

## Git Commits

**Main commits:**
- `36e4276` - feat: Apply FORGE template pattern to BPD (Handoff 3)
- `49f3110` - feat: Create forge_cocotb reusable test infrastructure package
- `2c9abaa` - fix: Update test wrapper to use BPD_forge_main entity
- `df4d6b8` - docs: Add Handoff 4 - Complete FORGE integration

**Branch:** BPD-Dev-main
**Status:** Pushed to remote

---

**Created:** 2025-11-06 23:15
**Completed:** 2025-11-06 23:45
**Status:** Complete
**Priority:** P1 (final integration)
**Dependencies:** Handoff 1 & 2 complete
