--------------------------------------------------------------------------------
-- File: BPD_forge_shim.vhd
-- Generated: 2025-11-05
-- Generator: Manual (will be automated via forge-codegen in future)
--
-- Description:
--   Register mapping shim for Basic Probe Driver (BPD) ForgeApp.
--   Maps raw Control Registers (CR20-CR30) to friendly signal names
--   and instantiates the application main entity.
--
-- Layer 2 of 3-Layer Forge Architecture:
--   Layer 1: MCC_TOP_forge_loader.vhd (static, shared)
--   Layer 2: BPD_forge_shim.vhd (THIS FILE - register mapping)
--   Layer 3: BPD_forge_main.vhd (hand-written app logic)
--
-- Register Mapping:
--   CR1[3:0]   : Lifecycle control (arm_enable, ext_trigger_in, auto_rearm, fault_clear)
--   CR2[15:0]  : Trigger output voltage (mV)
--   CR3[15:0]  : Trigger pulse duration (ns)
--   CR4[15:0]  : Intensity output voltage (mV)
--   CR5[15:0]  : Intensity pulse duration (ns)
--   CR6[15:0]  : Trigger wait timeout (s)
--   CR7[23:0]  : Cooldown interval (μs)
--   CR8[1:0]   : Monitor control (enable, expect_negative)
--   CR9[15:0]  : Monitor threshold voltage (mV)
--   CR10[31:0] : Monitor window start delay (ns)
--   CR11[31:0] : Monitor window duration (ns)
--
-- References:
--   - forge_common_pkg.vhd (FORGE_READY control scheme)
--   - external_Example/DS1140_polo_shim.vhd (pattern reference)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library WORK;
use WORK.forge_common_pkg.all;

entity BPD_forge_shim is
    port (
        ------------------------------------------------------------------------
        -- Clock and Reset
        ------------------------------------------------------------------------
        Clk         : in  std_logic;
        Reset       : in  std_logic;  -- Active-high reset

        ------------------------------------------------------------------------
        -- FORGE Control Signals (from MCC_TOP_forge_loader or CustomWrapper)
        ------------------------------------------------------------------------
        forge_ready  : in  std_logic;  -- CR0[31] - Set by loader
        user_enable  : in  std_logic;  -- CR0[30] - User control
        clk_enable   : in  std_logic;  -- CR0[29] - Clock gating
        loader_done  : in  std_logic;  -- BRAM loader FSM done signal

        ------------------------------------------------------------------------
        -- Application Registers (from MCC_TOP_forge_loader)
        -- Raw Control Registers CR1-CR11 (MCC provides CR0-CR15)
        ------------------------------------------------------------------------
        app_reg_1 : in  std_logic_vector(31 downto 0);
        app_reg_2 : in  std_logic_vector(31 downto 0);
        app_reg_3 : in  std_logic_vector(31 downto 0);
        app_reg_4 : in  std_logic_vector(31 downto 0);
        app_reg_5 : in  std_logic_vector(31 downto 0);
        app_reg_6 : in  std_logic_vector(31 downto 0);
        app_reg_7 : in  std_logic_vector(31 downto 0);
        app_reg_8 : in  std_logic_vector(31 downto 0);
        app_reg_9 : in  std_logic_vector(31 downto 0);
        app_reg_10 : in  std_logic_vector(31 downto 0);
        app_reg_11 : in  std_logic_vector(31 downto 0);

        ------------------------------------------------------------------------
        -- BRAM Interface (from forge_bram_loader FSM)
        ------------------------------------------------------------------------
        bram_addr   : in  std_logic_vector(11 downto 0);  -- 4KB address space
        bram_data   : in  std_logic_vector(31 downto 0);  -- 32-bit data
        bram_we     : in  std_logic;                      -- Write enable

        ------------------------------------------------------------------------
        -- MCC I/O (from CustomWrapper)
        -- Native MCC types: signed(15 downto 0) for all ADC/DAC channels
        ------------------------------------------------------------------------
        InputA      : in  signed(15 downto 0);
        InputB      : in  signed(15 downto 0);
        OutputA     : out signed(15 downto 0);
        OutputB     : out signed(15 downto 0);
        OutputC     : out signed(15 downto 0);
        OutputD     : out signed(15 downto 0)
    );
end entity BPD_forge_shim;

architecture rtl of BPD_forge_shim is

    ----------------------------------------------------------------------------
    -- Template-Level Application Register Signals (Generic Naming)
    -- These use app_reg_* prefix for template reusability
    ----------------------------------------------------------------------------

    -- Lifecycle control
    signal app_reg_arm_enable           : std_logic;  -- Arm FSM (IDLE→ARMED transition)
    signal app_reg_ext_trigger_in       : std_logic;  -- External trigger input
    signal app_reg_auto_rearm_enable    : std_logic;  -- Re-arm after cooldown
    signal app_reg_fault_clear          : std_logic;  -- Clear fault state

    -- Trigger output control
    signal app_reg_trig_out_voltage     : signed(15 downto 0);    -- Voltage (mV)
    signal app_reg_trig_out_duration    : unsigned(15 downto 0);  -- Duration (ns)

    -- Intensity output control
    signal app_reg_intensity_voltage    : signed(15 downto 0);    -- Voltage (mV)
    signal app_reg_intensity_duration   : unsigned(15 downto 0);  -- Duration (ns)

    -- Timing control
    signal app_reg_trigger_wait_timeout : unsigned(15 downto 0);  -- Timeout (s)
    signal app_reg_cooldown_interval    : unsigned(23 downto 0);  -- Cooldown (μs)

    -- Monitor/feedback
    signal app_reg_monitor_enable            : std_logic;              -- Enable comparator
    signal app_reg_monitor_expect_negative   : std_logic;              -- Polarity select
    signal app_reg_monitor_threshold_voltage : signed(15 downto 0);    -- Threshold (mV)
    signal app_reg_monitor_window_start      : unsigned(31 downto 0);  -- Window delay (ns)
    signal app_reg_monitor_window_duration   : unsigned(31 downto 0);  -- Window length (ns)

    ----------------------------------------------------------------------------
    -- Global Enable Signal
    -- Combines all FORGE_READY control bits for safe operation
    ----------------------------------------------------------------------------
    signal global_enable : std_logic;

    ----------------------------------------------------------------------------
    -- Handshaking Signal
    -- From main app indicating safe window to update app_reg_* signals
    ----------------------------------------------------------------------------
    signal ready_for_updates : std_logic;

    ----------------------------------------------------------------------------
    -- Hierarchical Voltage Encoding Signals
    -- NEW: State/status vectors from APP for OutputD encoding
    ----------------------------------------------------------------------------
    signal app_state_vector  : std_logic_vector(5 downto 0);  -- FSM state from APP
    signal app_status_vector : std_logic_vector(7 downto 0);  -- App status from APP

begin

    ----------------------------------------------------------------------------
    -- Global Enable Computation
    --
    -- All 4 conditions must be met for app to operate:
    --   1. forge_ready  = 1  (loader has deployed bitstream)
    --   2. user_enable  = 1  (user has enabled module)
    --   3. clk_enable   = 1  (clock gating enabled)
    --   4. loader_done  = 1  (BRAM loading complete)
    ----------------------------------------------------------------------------
    global_enable <= combine_forge_ready(forge_ready, user_enable, clk_enable, loader_done);

    ----------------------------------------------------------------------------
    -- Register Synchronization: Control Registers → app_reg_* signals
    --
    -- Synchronizes register updates with ready_for_updates handshake
    -- Only latches new values when main app indicates it's safe
    ----------------------------------------------------------------------------
    REGISTER_SYNC: process(Clk, Reset)
    begin
        if Reset = '1' then
            -- Initialize all app_reg_* signals to safe defaults
            app_reg_arm_enable           <= '0';
            app_reg_ext_trigger_in       <= '0';
            app_reg_auto_rearm_enable    <= '0';
            app_reg_fault_clear          <= '0';
            app_reg_trig_out_voltage     <= (others => '0');
            app_reg_trig_out_duration    <= to_unsigned(100, 16);   -- Safe default 100ns
            app_reg_intensity_voltage    <= (others => '0');
            app_reg_intensity_duration   <= to_unsigned(200, 16);   -- Safe default 200ns
            app_reg_trigger_wait_timeout <= to_unsigned(2, 16);     -- Safe default 2s
            app_reg_cooldown_interval    <= to_unsigned(10, 24);    -- Safe default 10μs
            app_reg_monitor_enable            <= '1';               -- Enabled by default
            app_reg_monitor_expect_negative   <= '1';               -- Negative polarity
            app_reg_monitor_threshold_voltage <= to_signed(-200, 16); -- -200mV default
            app_reg_monitor_window_start      <= (others => '0');
            app_reg_monitor_window_duration   <= to_unsigned(5000, 32); -- 5μs default

        elsif rising_edge(Clk) then
            if ready_for_updates = '1' then
                -- Main app says safe to update - latch new register values

                -- CR1: Lifecycle control bits
                app_reg_arm_enable        <= app_reg_1(0);
                app_reg_ext_trigger_in    <= app_reg_1(1);
                app_reg_auto_rearm_enable <= app_reg_1(2);
                app_reg_fault_clear       <= app_reg_1(3);

                -- CR2: Trigger output voltage
                app_reg_trig_out_voltage  <= signed(app_reg_2(15 downto 0));

                -- CR3: Trigger pulse duration
                app_reg_trig_out_duration <= unsigned(app_reg_3(15 downto 0));

                -- CR4: Intensity output voltage
                app_reg_intensity_voltage <= signed(app_reg_4(15 downto 0));

                -- CR5: Intensity pulse duration
                app_reg_intensity_duration <= unsigned(app_reg_5(15 downto 0));

                -- CR6: Trigger wait timeout
                app_reg_trigger_wait_timeout <= unsigned(app_reg_6(15 downto 0));

                -- CR7: Cooldown interval
                app_reg_cooldown_interval <= unsigned(app_reg_7(23 downto 0));

                -- CR8: Monitor control bits
                app_reg_monitor_enable          <= app_reg_8(0);
                app_reg_monitor_expect_negative <= app_reg_8(1);

                -- CR9: Monitor threshold voltage
                app_reg_monitor_threshold_voltage <= signed(app_reg_9(15 downto 0));

                -- CR10: Monitor window start delay
                app_reg_monitor_window_start <= unsigned(app_reg_10);

                -- CR11: Monitor window duration
                app_reg_monitor_window_duration <= unsigned(app_reg_11);
            end if;
            -- else: Hold current values, main app is busy
        end if;
    end process;

    ----------------------------------------------------------------------------
    -- Instantiate Application Main Entity
    --
    -- Direct mapping: bpd_* ← app_reg_* (meaningful names ← generic names)
    -- Main app is MCC-agnostic, uses domain-specific bpd_* naming
    ----------------------------------------------------------------------------
    BPD_MAIN_INST: entity WORK.BPD_forge_main
        generic map (
            CLK_FREQ_HZ => 125000000  -- Moku:Go clock frequency
        )
        port map (
            -- Clock and Control
            Clk               => Clk,
            Reset             => Reset,
            global_enable     => global_enable,
            ready_for_updates => ready_for_updates,  -- Output from main

            -- Direct mapping: bpd_* ← app_reg_*
            bpd_arm_enable           => app_reg_arm_enable,
            bpd_ext_trigger_in       => app_reg_ext_trigger_in,
            bpd_trigger_wait_timeout => app_reg_trigger_wait_timeout,
            bpd_auto_rearm_enable    => app_reg_auto_rearm_enable,
            bpd_fault_clear          => app_reg_fault_clear,

            bpd_trig_out_voltage     => app_reg_trig_out_voltage,
            bpd_trig_out_duration    => app_reg_trig_out_duration,

            bpd_intensity_voltage    => app_reg_intensity_voltage,
            bpd_intensity_duration   => app_reg_intensity_duration,

            bpd_cooldown_interval    => app_reg_cooldown_interval,

            bpd_probe_monitor_feedback    => InputA,
            bpd_monitor_enable            => app_reg_monitor_enable,
            bpd_monitor_threshold_voltage => app_reg_monitor_threshold_voltage,
            bpd_monitor_expect_negative   => app_reg_monitor_expect_negative,
            bpd_monitor_window_start      => app_reg_monitor_window_start,
            bpd_monitor_window_duration   => app_reg_monitor_window_duration,

            -- Physical I/O (3 outputs for APP, OutputD driven by SHIM)
            OutputA => OutputA,
            OutputB => OutputB,
            OutputC => OutputC,
            -- OutputD removed (driven by hierarchical encoder below)

            -- Hierarchical Voltage Encoding (state/status exports)
            app_state_vector  => app_state_vector,   -- 6-bit FSM state
            app_status_vector => app_status_vector   -- 8-bit app status
        );

    ----------------------------------------------------------------------------
    -- Hierarchical Voltage Encoder for OutputD
    --
    -- NEW: Replaces fsm_observer pattern
    -- Encodes app_state_vector (6-bit) + app_status_vector (8-bit) into OutputD
    -- using arithmetic encoding (200 digital units per state + fine offset)
    ----------------------------------------------------------------------------
    HIERARCHICAL_ENCODER: entity WORK.forge_hierarchical_encoder
        generic map (
            DIGITAL_UNITS_PER_STATE  => 200,      -- 200 digital units per state step
            DIGITAL_UNITS_PER_STATUS => 0.78125   -- ~100 digital units / 128 (status range)
        )
        port map (
            clk           => Clk,
            reset         => Reset,
            state_vector  => app_state_vector,   -- From APP (6-bit)
            status_vector => app_status_vector,  -- From APP (8-bit)
            voltage_out   => OutputD             -- To MCC DAC (16-bit signed)
        );

end architecture rtl;
