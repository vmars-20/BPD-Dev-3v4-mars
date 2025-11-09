--------------------------------------------------------------------------------
-- File: basic_probe_driver_custom_inst_main.vhd
-- Author: AI-assisted implementation (Claude Code)
-- Date: 2025-11-05
-- Version: 1.0 (P2 - YAML-aligned FSM implementation)
--
-- Description:
--   Five-state FSM for Basic Probe Driver following forge-vhdl standards.
--   Implements all 13 register fields from basic_probe_driver.yaml.
--
-- Platform: Moku:Go
-- Clock Frequency: 125 MHz (8 ns period)
--
-- FSM States (std_logic_vector encoding - Verilog compatible):
--   IDLE     (000000) - Waiting for arm signal
--   ARMED    (000001) - Waiting for trigger or timeout
--   FIRING   (000010) - Driving outputs (trigger + intensity pulses)
--   COOLDOWN (000011) - Thermal safety delay between pulses
--   FAULT    (111111) - Sticky fault state (requires fault_clear)
--
-- State Transitions:
--   IDLE → ARMED        : On rising edge of trigger event (external trigger_in)
--   ARMED → FIRING      : On trigger condition met
--   ARMED → FAULT       : On timeout (trigger_wait_timeout exceeded)
--   FIRING → COOLDOWN   : When both output pulses complete
--   COOLDOWN → IDLE     : When auto_rearm_enable = '0'
--   COOLDOWN → ARMED    : When auto_rearm_enable = '1'
--   FAULT → IDLE        : On fault_clear pulse
--   ANY → FAULT         : On safety violation
--
-- Timing Counters:
--   - ns counters: Direct cycle count @ 125 MHz (16-bit)
--   - μs counters: Prescaled by 125 (24-bit → 32-bit)
--   - s counters: Prescaled by 125M (16-bit → 32-bit)
--
-- Safety Features:
--   - Mandatory cooldown enforcement
--   - Timeout protection in ARMED state
--   - when others → FAULT for undefined states
--
-- References:
--   - basic_probe_driver.yaml (YAML spec)
--   - basic_probe_driver_custom_inst_shim.vhd (register interface)
--   - libs/forge-vhdl/docs/VHDL_CODING_STANDARDS.md (coding standards)
--   - libs/forge-vhdl/vhdl/debugging/fsm_observer.vhd (debug integration)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.forge_serialization_types_pkg.all;
use WORK.forge_serialization_voltage_pkg.all;
use WORK.forge_serialization_time_pkg.all;

entity BPD_forge_main is
    generic (
        CLK_FREQ_HZ : integer := 125000000  -- Moku:Go clock frequency
    );
    port (
        ------------------------------------------------------------------------
        -- Clock and Reset
        ------------------------------------------------------------------------
        Clk               : in  std_logic;
        Reset             : in  std_logic;  -- Active-high reset
        global_enable     : in  std_logic;  -- Combined FORGE ready signals
        ready_for_updates : out std_logic;  -- Handshake to shim

        ------------------------------------------------------------------------
        -- Application Signals (bpd_* prefix - meaningful domain names)
        ------------------------------------------------------------------------
        -- Arming and lifecycle
        bpd_arm_enable           : in std_logic;               -- Arm the FSM (IDLE → ARMED)
        bpd_ext_trigger_in       : in std_logic;               -- External trigger (ARMED → FIRING)
        bpd_trigger_wait_timeout : in unsigned(15 downto 0);  -- Max wait in ARMED (s)
        bpd_auto_rearm_enable    : in std_logic;               -- Re-arm after cooldown
        bpd_fault_clear          : in std_logic;               -- Clear fault state

        -- Output controls (trigger path)
        bpd_trig_out_voltage  : in signed(15 downto 0);    -- Trigger voltage (mV)
        bpd_trig_out_duration : in unsigned(15 downto 0);  -- Trigger pulse width (ns)

        -- Output controls (intensity path)
        bpd_intensity_voltage  : in signed(15 downto 0);    -- Intensity voltage (mV)
        bpd_intensity_duration : in unsigned(15 downto 0);  -- Intensity pulse width (ns)

        -- Timing controls
        bpd_cooldown_interval : in unsigned(23 downto 0);  -- Cooldown period (μs)

        -- Monitor/feedback
        bpd_probe_monitor_feedback    : in signed(15 downto 0);  -- ADC feedback (mV)
        bpd_monitor_enable            : in std_logic;             -- Enable comparator
        bpd_monitor_threshold_voltage : in signed(15 downto 0);  -- Threshold (mV)
        bpd_monitor_expect_negative   : in std_logic;             -- Polarity select
        bpd_monitor_window_start      : in unsigned(31 downto 0); -- Window delay (ns)
        bpd_monitor_window_duration   : in unsigned(31 downto 0); -- Window length (ns)

        ------------------------------------------------------------------------
        -- Physical I/O (DAC outputs)
        -- NEW: APP Layer 3 receives ONLY 3 outputs (OutputA/B/C)
        -- OutputD is RESERVED for FORGE infrastructure (driven by SHIM)
        ------------------------------------------------------------------------
        OutputA : out signed(15 downto 0);  -- Trigger output DAC
        OutputB : out signed(15 downto 0);  -- Intensity output DAC
        OutputC : out signed(15 downto 0);  -- Reserved
        -- OutputD removed (driven by SHIM hierarchical encoder)

        ------------------------------------------------------------------------
        -- Hierarchical Voltage Encoding (OutputD Debugging Channel)
        -- MANDATORY: APP exports state/status for SHIM encoder
        -- These signals are encoded into OutputD by the SHIM layer
        ------------------------------------------------------------------------
        app_state_vector  : out std_logic_vector(5 downto 0);  -- 6-bit FSM state (linear 0-31)
        app_status_vector : out std_logic_vector(7 downto 0)   -- 8-bit app status (bit 7 = fault)
    );
end entity BPD_forge_main;

architecture rtl of BPD_forge_main is

    ----------------------------------------------------------------------------
    -- FSM State Constants (6-bit encoding for fsm_observer compatibility)
    ----------------------------------------------------------------------------
    constant STATE_IDLE     : std_logic_vector(5 downto 0) := "000000";
    constant STATE_ARMED    : std_logic_vector(5 downto 0) := "000001";
    constant STATE_FIRING   : std_logic_vector(5 downto 0) := "000010";
    constant STATE_COOLDOWN : std_logic_vector(5 downto 0) := "000011";
    constant STATE_FAULT    : std_logic_vector(5 downto 0) := "111111";

    ----------------------------------------------------------------------------
    -- State Machine Signals
    ----------------------------------------------------------------------------
    signal state      : std_logic_vector(5 downto 0);
    signal next_state : std_logic_vector(5 downto 0);

    ----------------------------------------------------------------------------
    -- Time Conversion Signals (YAML units → clock cycles @ 125 MHz)
    ----------------------------------------------------------------------------
    signal trigger_wait_timeout_cycles   : unsigned(31 downto 0);  -- s → cycles
    signal trig_out_duration_cycles      : unsigned(31 downto 0);  -- ns → cycles
    signal intensity_duration_cycles     : unsigned(31 downto 0);  -- ns → cycles
    signal cooldown_interval_cycles      : unsigned(31 downto 0);  -- μs → cycles
    signal monitor_window_start_cycles   : unsigned(31 downto 0);  -- ns → cycles
    signal monitor_window_duration_cycles: unsigned(31 downto 0);  -- ns → cycles

    ----------------------------------------------------------------------------
    -- Timing Counters
    ----------------------------------------------------------------------------
    signal armed_timer       : unsigned(31 downto 0);  -- Timeout in ARMED state
    signal trig_out_timer    : unsigned(31 downto 0);  -- Trigger pulse counter
    signal intensity_timer   : unsigned(31 downto 0);  -- Intensity pulse counter
    signal cooldown_timer    : unsigned(31 downto 0);  -- Cooldown counter
    signal monitor_start_timer : unsigned(31 downto 0); -- Monitor window delay
    signal monitor_duration_timer : unsigned(31 downto 0); -- Monitor window length

    ----------------------------------------------------------------------------
    -- Control Flags
    ----------------------------------------------------------------------------
    signal trig_out_active   : std_logic;  -- Trigger output pulse active
    signal intensity_active  : std_logic;  -- Intensity output pulse active
    signal monitor_window_open : std_logic; -- Monitor window is active
    signal firing_complete   : std_logic;  -- Both pulses finished
    signal timeout_occurred  : std_logic;  -- Armed timeout exceeded
    signal cooldown_complete : std_logic;  -- Cooldown elapsed

    ----------------------------------------------------------------------------
    -- Monitor/Comparator Signals
    ----------------------------------------------------------------------------
    signal threshold_crossed : std_logic;  -- Comparator output
    signal monitor_triggered : std_logic;  -- Latch for threshold crossing

    ----------------------------------------------------------------------------
    -- Fault Detection
    ----------------------------------------------------------------------------
    signal fault_detected    : std_logic;  -- Safety violation flag
    signal fault_clear_prev  : std_logic;  -- Edge detection
    signal fault_clear_edge  : std_logic;  -- Rising edge of fault_clear

begin

    ------------------------------------------------------------------------
    -- Ready for Updates
    --
    -- Signal to shim when safe to update app_reg_* signals
    -- Only safe when FSM is in IDLE state (not actively running a sequence)
    ------------------------------------------------------------------------
    ready_for_updates <= '1' when state = STATE_IDLE else '0';

    ------------------------------------------------------------------------
    -- Time to Cycles Conversions
    --
    -- Convert YAML time units to clock cycles using platform-aware functions
    -- from forge_serialization_time_pkg
    ------------------------------------------------------------------------
    trigger_wait_timeout_cycles    <= resize(s_to_cycles(bpd_trigger_wait_timeout, CLK_FREQ_HZ), 32);
    trig_out_duration_cycles       <= resize(ns_to_cycles(bpd_trig_out_duration, CLK_FREQ_HZ), 32);
    intensity_duration_cycles      <= resize(ns_to_cycles(bpd_intensity_duration, CLK_FREQ_HZ), 32);
    cooldown_interval_cycles       <= resize(us_to_cycles(bpd_cooldown_interval, CLK_FREQ_HZ), 32);
    monitor_window_start_cycles    <= resize(ns_to_cycles(bpd_monitor_window_start, CLK_FREQ_HZ), 32);
    monitor_window_duration_cycles <= resize(ns_to_cycles(bpd_monitor_window_duration, CLK_FREQ_HZ), 32);

    ------------------------------------------------------------------------
    -- Edge Detector for bpd_fault_clear
    ------------------------------------------------------------------------
    FAULT_CLEAR_EDGE_PROC: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                fault_clear_prev <= '0';
            elsif global_enable = '1' then
                fault_clear_prev <= bpd_fault_clear;
            end if;
        end if;
    end process;

    fault_clear_edge <= bpd_fault_clear and not fault_clear_prev;

    ------------------------------------------------------------------------
    -- Monitor Comparator Logic
    --
    -- Compares bpd_probe_monitor_feedback against threshold with polarity control
    ------------------------------------------------------------------------
    MONITOR_COMPARATOR: process(bpd_probe_monitor_feedback, bpd_monitor_threshold_voltage,
                                 bpd_monitor_expect_negative)
    begin
        if bpd_monitor_expect_negative = '1' then
            -- Negative-going crossing detection (feedback < threshold)
            if bpd_probe_monitor_feedback < bpd_monitor_threshold_voltage then
                threshold_crossed <= '1';
            else
                threshold_crossed <= '0';
            end if;
        else
            -- Positive-going crossing detection (feedback > threshold)
            if bpd_probe_monitor_feedback > bpd_monitor_threshold_voltage then
                threshold_crossed <= '1';
            else
                threshold_crossed <= '0';
            end if;
        end if;
    end process;

    ------------------------------------------------------------------------
    -- State Register (Sequential)
    --
    -- Implements state transitions with active-high reset and clock enable
    ------------------------------------------------------------------------
    FSM_STATE_REG: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                state <= STATE_IDLE;
            elsif global_enable = '1' then
                state <= next_state;
            end if;
        end if;
    end process;

    ------------------------------------------------------------------------
    -- Next-State Logic (Combinational)
    --
    -- Implements FSM state transitions based on current state and inputs
    ------------------------------------------------------------------------
    FSM_NEXT_STATE: process(state, timeout_occurred, firing_complete,
                           cooldown_complete, bpd_auto_rearm_enable,
                           fault_clear_edge, fault_detected, bpd_arm_enable,
                           bpd_ext_trigger_in)
    begin
        -- Default: hold current state
        next_state <= state;

        case state is
            when STATE_IDLE =>
                -- Transition to ARMED when bpd_arm_enable asserted
                if bpd_arm_enable = '1' then
                    next_state <= STATE_ARMED;
                end if;

            when STATE_ARMED =>
                if timeout_occurred = '1' then
                    -- Timeout watchdog expired
                    next_state <= STATE_FAULT;
                elsif bpd_ext_trigger_in = '1' then
                    -- External trigger received
                    next_state <= STATE_FIRING;
                end if;

            when STATE_FIRING =>
                if firing_complete = '1' then
                    -- Both output pulses finished
                    next_state <= STATE_COOLDOWN;
                end if;

            when STATE_COOLDOWN =>
                if cooldown_complete = '1' then
                    if bpd_auto_rearm_enable = '1' then
                        -- Burst mode: re-arm automatically
                        next_state <= STATE_ARMED;
                    else
                        -- One-shot mode: return to idle
                        next_state <= STATE_IDLE;
                    end if;
                end if;

            when STATE_FAULT =>
                if fault_clear_edge = '1' then
                    -- Acknowledge fault and return to safe state
                    next_state <= STATE_IDLE;
                end if;

            when others =>
                -- Safety: any undefined state goes to FAULT
                next_state <= STATE_FAULT;

        end case;

        -- Override: any fault detection forces FAULT state
        if fault_detected = '1' then
            next_state <= STATE_FAULT;
        end if;
    end process;

    ------------------------------------------------------------------------
    -- Timing Counters (Sequential)
    --
    -- Implements all timing logic: timeouts, pulse durations, cooldown
    ------------------------------------------------------------------------
    TIMING_COUNTERS: process(Clk)
    begin
        if rising_edge(Clk) then
            if Reset = '1' then
                armed_timer <= (others => '0');
                trig_out_timer <= (others => '0');
                intensity_timer <= (others => '0');
                cooldown_timer <= (others => '0');
                monitor_start_timer <= (others => '0');
                monitor_duration_timer <= (others => '0');
                monitor_window_open <= '0';
                monitor_triggered <= '0';

            elsif global_enable = '1' then
                case state is
                    when STATE_IDLE =>
                        -- Reset all counters
                        armed_timer <= (others => '0');
                        trig_out_timer <= (others => '0');
                        intensity_timer <= (others => '0');
                        cooldown_timer <= (others => '0');
                        monitor_start_timer <= (others => '0');
                        monitor_duration_timer <= (others => '0');
                        monitor_window_open <= '0';
                        monitor_triggered <= '0';

                    when STATE_ARMED =>
                        -- Increment timeout counter
                        if armed_timer < trigger_wait_timeout_cycles then
                            armed_timer <= armed_timer + 1;
                        end if;

                    when STATE_FIRING =>
                        -- Trigger output pulse timing
                        if trig_out_timer < trig_out_duration_cycles then
                            trig_out_timer <= trig_out_timer + 1;
                        end if;

                        -- Intensity output pulse timing
                        if intensity_timer < intensity_duration_cycles then
                            intensity_timer <= intensity_timer + 1;
                        end if;

                        -- Monitor window timing
                        if bpd_monitor_enable = '1' then
                            if monitor_start_timer < monitor_window_start_cycles then
                                -- Delay before window opens
                                monitor_start_timer <= monitor_start_timer + 1;
                                monitor_window_open <= '0';
                            elsif monitor_duration_timer < monitor_window_duration_cycles then
                                -- Window is open
                                monitor_duration_timer <= monitor_duration_timer + 1;
                                monitor_window_open <= '1';

                                -- Latch threshold crossing during window
                                if threshold_crossed = '1' then
                                    monitor_triggered <= '1';
                                end if;
                            else
                                -- Window closed
                                monitor_window_open <= '0';
                            end if;
                        end if;

                    when STATE_COOLDOWN =>
                        -- Increment cooldown counter
                        if cooldown_timer < cooldown_interval_cycles then
                            cooldown_timer <= cooldown_timer + 1;
                        end if;

                    when STATE_FAULT =>
                        -- Hold all counters in fault state
                        null;

                    when others =>
                        -- Safety: reset counters
                        armed_timer <= (others => '0');
                        trig_out_timer <= (others => '0');
                        intensity_timer <= (others => '0');
                        cooldown_timer <= (others => '0');

                end case;
            end if;
        end if;
    end process;

    ------------------------------------------------------------------------
    -- Output Control (Concurrent)
    --
    -- Activate outputs based purely on state, matching reference FSM pattern
    -- Timers control state exit (firing_complete), not output activation
    -- This ensures outputs respond immediately when entering FIRING state
    ------------------------------------------------------------------------
    trig_out_active <= '1' when state = STATE_FIRING else '0';
    intensity_active <= '1' when state = STATE_FIRING else '0';

    ------------------------------------------------------------------------
    -- Status Flags (Combinational)
    --
    -- Derive control flags from counter values
    ------------------------------------------------------------------------
    timeout_occurred  <= '1' when (armed_timer >= trigger_wait_timeout_cycles) else '0';
    firing_complete   <= '1' when (trig_out_timer >= trig_out_duration_cycles
                                   and intensity_timer >= intensity_duration_cycles
                                   and state = STATE_FIRING) else '0';
    cooldown_complete <= '1' when (cooldown_timer >= cooldown_interval_cycles) else '0';

    ------------------------------------------------------------------------
    -- Fault Detection Logic
    --
    -- Detect safety violations (placeholder - extend as needed)
    ------------------------------------------------------------------------
    FAULT_DETECTION: process(state, armed_timer, trigger_wait_timeout_cycles)
    begin
        fault_detected <= '0';  -- Default: no fault

        -- Example: Detect timeout in ARMED state
        -- (This is already handled in FSM, but shown here for extensibility)
        if state = STATE_ARMED and armed_timer > trigger_wait_timeout_cycles then
            fault_detected <= '1';
        end if;

        -- Add additional fault conditions here:
        -- - Voltage out of range
        -- - Counter overflow
        -- - Invalid configuration
    end process;

    ------------------------------------------------------------------------
    -- Output Driver Logic
    --
    -- Drive DAC outputs with configured voltages when outputs are active
    ------------------------------------------------------------------------
    OutputA <= bpd_trig_out_voltage when trig_out_active = '1' else (others => '0');
    OutputB <= bpd_intensity_voltage when intensity_active = '1' else (others => '0');
    OutputC <= (others => '0');  -- Reserved for future use
    -- OutputD removed (driven by SHIM hierarchical encoder)

    ------------------------------------------------------------------------
    -- Hierarchical Voltage Encoding Exports
    --
    -- NEW: Export state/status vectors for SHIM layer encoder
    --
    -- APP Layer 3 is responsible for:
    --   1. Exporting current FSM state (6-bit, linear encoding 0-31)
    --   2. Exporting app-specific status (8-bit)
    --      - status[7] = fault flag (MANDATORY)
    --      - status[6:0] = app-specific (RECOMMENDED: copy state for redundancy)
    --
    -- SHIM Layer 2 will encode these into OutputD using hierarchical voltage
    -- encoding (200 digital units per state + fine-grained status offset)
    ------------------------------------------------------------------------

    -- Export FSM state directly (linear encoding 0-3 for normal, 63 for fault)
    app_state_vector <= state;

    -- Export app status vector (fault flag + state redundancy)
    -- status[7] = fault indicator (1 if in FAULT state)
    -- status[6:1] = copy of state[5:0] for redundancy
    -- status[0] = unused (future expansion)
    app_status_vector <= '1' & state(5 downto 0) & '0' when state = STATE_FAULT else
                         '0' & state(5 downto 0) & '0';

end architecture rtl;
