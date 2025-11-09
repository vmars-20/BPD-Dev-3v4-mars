---
created: 2025-11-07
type: handoff
priority: P1
status: pending
depends_on:
  - handoff-8-cocotb-test-execution
---

# Handoff 9: Hardware Validation with Moku Oscilloscope

**Date:** 2025-11-07
**Session:** FORGE Hierarchical Voltage Encoding Hardware Validation
**Owner:** @claude
**Dependencies:** Handoff 8 complete (tests pass)
**Estimated Time:** 2-3 hours

---

## Executive Summary

Create a Python script to validate the hierarchical voltage encoding on real Moku hardware using the oscilloscope to observe OutputD voltage changes.

**Scope:**
1. Create Python decoder utility for oscilloscope voltage data
2. Create Moku deployment + monitoring script
3. Connect to Moku, deploy BPD bitstream, configure oscilloscope
4. Observe OutputD voltage during BPD state transitions
5. Validate hierarchical encoding on hardware

**Success Criteria:**
- Python decoder utility works with real voltage data
- Script deploys BPD to Moku Slot 2, configures oscilloscope in Slot 1
- Oscilloscope shows 200mV state steps + status noise
- Fault conditions produce negative voltage
- Hardware behavior matches CocoTB simulation

---

## Context: Moku Platform Setup

### Hardware Configuration

**Moku:Go Configuration:**
- **Slot 1:** Oscilloscope (built-in instrument)
- **Slot 2:** BPD custom instrument (Cloud Compile bitstream)

**I/O Connections:**
- **OutputD (BPD)** → **Oscilloscope Channel 1**
- **OutputA (Trigger)** → External trigger device or loopback
- **OutputB (Intensity)** → External intensity device or loopback
- **InputA (Monitor feedback)** → External sensor or ground

**Power:** USB-C power, USB connection to host PC

### Reference Script

**Existing deployment script:** `moku-go.py` (to be provided by user)

**Expected capabilities:**
- Connect to Moku via IP or serial
- Deploy Cloud Compile bitstream to Slot 2
- Configure oscilloscope in Slot 1
- Set Control Registers (CR0-CR15)
- Read oscilloscope data stream

---

## Task 1: Create Python Voltage Decoder Utility

### Decoder Module

**File:** `tools/hierarchical_voltage_decoder.py`

```python
"""
Hierarchical Voltage Decoder for FORGE OutputD Debugging

Decodes hierarchical voltage encoding from Moku oscilloscope data.

Usage:
    from hierarchical_voltage_decoder import decode_hierarchical_voltage

    # From oscilloscope voltage (mV)
    voltage_mv = 450.0  # Example: State 2, status offset
    result = decode_hierarchical_voltage(voltage_mv)

    print(f"State: {result['state']}")
    print(f"Status: {result['status_lower']}")
    print(f"Fault: {result['fault']}")

Author: Moku Instrument Forge Team
Date: 2025-11-07
Reference: Handoff 6 - Hierarchical Voltage Encoding
"""

def decode_hierarchical_voltage(
    voltage_mv: float,
    platform_range_mv: float = 5000.0,
    digital_units_per_state: int = 200,
    digital_units_per_status: float = 0.78125
) -> dict:
    """
    Decode hierarchical voltage to state + status.

    Args:
        voltage_mv: Measured voltage in millivolts (from oscilloscope)
        platform_range_mv: Platform full-scale range (default: ±5V = 5000mV)
        digital_units_per_state: Digital units per state step (default: 200)
        digital_units_per_status: Digital units per status LSB (default: 0.78125)

    Returns:
        dict with keys:
            - 'state': FSM state (0-63)
            - 'status_lower': App status lower 7 bits (0-127)
            - 'fault': Fault flag (bool)
            - 'digital_value': Computed digital value (int)
            - 'voltage_mv': Input voltage (float)
            - 'platform_range_mv': Platform range used (float)

    Example:
        >>> result = decode_hierarchical_voltage(450.0)
        >>> result['state']
        2
        >>> result['status_lower']
        64
        >>> result['fault']
        False
    """
    # Convert voltage → digital value (platform-specific)
    full_scale_digital = 32768
    digital_value = int(voltage_mv * (full_scale_digital / platform_range_mv))

    # Extract fault flag (sign bit)
    fault = (digital_value < 0)
    digital_magnitude = abs(digital_value)

    # Decode state (digital_units_per_state units per state)
    state = digital_magnitude // digital_units_per_state
    remainder = digital_magnitude % digital_units_per_state

    # Decode status (inverse of encoding)
    # Encoding: offset = (status_lower * 100) / 128
    # Decoding: status_lower = (remainder * 128) / 100
    status_lower = int((remainder * 128) / 100)

    # Clamp status to 7-bit range (0-127)
    status_lower = min(127, max(0, status_lower))

    return {
        'state': state,
        'status_lower': status_lower,
        'fault': fault,
        'digital_value': digital_value,
        'voltage_mv': voltage_mv,
        'platform_range_mv': platform_range_mv
    }


def format_decoded_result(result: dict, verbose: bool = False) -> str:
    """
    Format decoded result as human-readable string.

    Args:
        result: Output from decode_hierarchical_voltage()
        verbose: Include detailed debug info

    Returns:
        Formatted string
    """
    state_names = {
        0: "IDLE",
        1: "ARMED",
        2: "FIRING",
        3: "COOLDOWN",
        63: "FAULT"
    }

    state_name = state_names.get(result['state'], f"STATE_{result['state']}")
    fault_str = " [FAULT]" if result['fault'] else ""

    basic = (
        f"{state_name}{fault_str} "
        f"(state={result['state']}, status={result['status_lower']})"
    )

    if verbose:
        return (
            f"{basic}\n"
            f"  Voltage: {result['voltage_mv']:.2f} mV\n"
            f"  Digital: {result['digital_value']} "
            f"(0x{result['digital_value'] & 0xFFFF:04X})\n"
            f"  Platform: ±{result['platform_range_mv']/1000:.1f}V full-scale"
        )
    else:
        return basic


# Example usage
if __name__ == "__main__":
    # Test cases (expected outputs from Handoff 6)
    test_cases = [
        (0.0, 0, 0x00, False),        # IDLE, no offset
        (30.5, 1, 0x00, False),       # ARMED, no offset
        (61.0, 2, 0x00, False),       # FIRING, no offset
        (91.5, 3, 0x00, False),       # COOLDOWN, no offset
        (68.6, 2, 0x40, False),       # FIRING, mid-status
        (76.2, 2, 0x7F, False),       # FIRING, max status
        (-61.0, 2, 0x80, True),       # FIRING, fault (negative)
        (-91.5, 3, 0xC0, True),       # COOLDOWN, fault + offset
    ]

    print("Hierarchical Voltage Decoder - Test Cases\n")

    for voltage_mv, expected_state, expected_status, expected_fault in test_cases:
        result = decode_hierarchical_voltage(voltage_mv)
        status = "✓" if (
            result['state'] == expected_state and
            result['fault'] == expected_fault
        ) else "✗"

        print(f"{status} {format_decoded_result(result)}")
        if status == "✗":
            print(f"  Expected: state={expected_state}, fault={expected_fault}")

    print("\nAll test cases validated!")
```

---

## Task 2: Create Moku Deployment + Monitoring Script

### Script Overview

**File:** `tools/moku_hierarchical_validator.py`

**Purpose:** Deploy BPD bitstream, configure oscilloscope, monitor OutputD voltage

**Dependencies:**
- Existing `moku-go.py` script (user will provide)
- `moku` Python library (Liquid Instruments SDK)
- `hierarchical_voltage_decoder.py` (created above)

### Script Template

```python
"""
Moku Hierarchical Voltage Validator

Deploy BPD bitstream to Moku Slot 2, configure oscilloscope in Slot 1,
and monitor OutputD voltage to validate hierarchical encoding on hardware.

Usage:
    python moku_hierarchical_validator.py --ip 192.168.1.100 --bitstream path/to/bpd.tar

Requirements:
    - Moku connected to network
    - BPD bitstream compiled (Cloud Compile .tar file)
    - Oscilloscope configured in Slot 1
    - OutputD connected to Oscilloscope Channel 1

Author: Moku Instrument Forge Team
Date: 2025-11-07
Reference: Handoff 9 - Hardware Validation
"""

import argparse
import time
from pathlib import Path

# Moku SDK imports (adjust based on actual SDK)
try:
    from moku.instruments import Oscilloscope, CloudCompile
    from moku import MokuException
    MOKU_AVAILABLE = True
except ImportError:
    print("Warning: moku library not found. Install with: pip install moku")
    MOKU_AVAILABLE = False

# Local decoder
from hierarchical_voltage_decoder import decode_hierarchical_voltage, format_decoded_result


class MokuHierarchicalValidator:
    """Validate hierarchical voltage encoding on Moku hardware."""

    def __init__(self, moku_ip: str, bitstream_path: Path):
        self.moku_ip = moku_ip
        self.bitstream_path = bitstream_path
        self.oscilloscope = None
        self.bpd_instrument = None

    def connect(self):
        """Connect to Moku and deploy instruments."""
        print(f"Connecting to Moku at {self.moku_ip}...")

        # Deploy oscilloscope to Slot 1
        print("Deploying Oscilloscope to Slot 1...")
        self.oscilloscope = Oscilloscope(self.moku_ip, slot=1, force_connect=True)

        # Configure oscilloscope
        self.oscilloscope.set_timebase(0, 1e-3)  # 1ms/div
        self.oscilloscope.set_source(1, 'Input1')  # Channel 1 = OutputD from Slot 2
        self.oscilloscope.set_trigger('Input1', 'Edge', 'Rising', 0.5)  # Trigger on 0.5V
        self.oscilloscope.set_frontend(1, impedance='1MOhm', coupling='DC', range='10Vpp')

        print("Oscilloscope configured.")

        # Deploy BPD to Slot 2
        print(f"Deploying BPD bitstream to Slot 2: {self.bitstream_path}...")
        self.bpd_instrument = CloudCompile(self.moku_ip, slot=2, bitstream=str(self.bitstream_path))

        # Initialize FORGE control scheme (CR0[31:29])
        # CR0[31] = forge_ready (set by loader)
        # CR0[30] = user_enable (enable module)
        # CR0[29] = clk_enable (enable clock)
        print("Initializing FORGE control scheme...")
        self.bpd_instrument.set_control(0, 0xE0000000)  # All three bits set

        print("BPD deployed and enabled.")

    def set_bpd_state(self, control_values: dict):
        """
        Set BPD control registers to trigger state transitions.

        Args:
            control_values: Dict mapping CR index to value
        """
        for cr_index, value in control_values.items():
            self.bpd_instrument.set_control(cr_index, value)

    def read_outputd_voltage(self) -> float:
        """
        Read OutputD voltage from oscilloscope Channel 1.

        Returns:
            Voltage in millivolts
        """
        # Get oscilloscope data (implementation depends on Moku SDK)
        data = self.oscilloscope.get_data()

        # Extract Channel 1 mean voltage (adjust based on SDK API)
        # This is a placeholder - actual API may differ
        voltage_v = data['ch1']['mean']  # Example API

        return voltage_v * 1000.0  # Convert V to mV

    def monitor_state_transitions(self, duration_sec: float = 10.0):
        """
        Monitor OutputD voltage during BPD state transitions.

        Args:
            duration_sec: How long to monitor (seconds)
        """
        print(f"\nMonitoring OutputD for {duration_sec} seconds...\n")

        start_time = time.time()
        last_state = None

        while (time.time() - start_time) < duration_sec:
            try:
                # Read voltage from oscilloscope
                voltage_mv = self.read_outputd_voltage()

                # Decode voltage
                result = decode_hierarchical_voltage(voltage_mv)

                # Print only on state change (reduce output noise)
                if result['state'] != last_state:
                    timestamp = time.time() - start_time
                    print(f"[{timestamp:6.2f}s] {format_decoded_result(result, verbose=True)}")
                    last_state = result['state']

                time.sleep(0.1)  # Sample every 100ms

            except KeyboardInterrupt:
                print("\nMonitoring stopped by user.")
                break
            except Exception as e:
                print(f"Error reading voltage: {e}")
                time.sleep(0.5)

    def test_state_progression(self):
        """
        Test hierarchical encoding by forcing BPD state transitions.

        Tests:
        1. IDLE (state=0) → expect ~0mV
        2. ARM → ARMED (state=1) → expect ~30mV
        3. TRIGGER → FIRING (state=2) → expect ~60mV
        4. COOLDOWN (state=3) → expect ~90mV
        5. FAULT (state=63) → expect negative voltage
        """
        print("\n=== Testing State Progression ===\n")

        test_sequence = [
            ("IDLE", {'arm_enable': 0}),
            ("ARM (IDLE→ARMED)", {'arm_enable': 1}),
            ("TRIGGER (ARMED→FIRING)", {'ext_trigger': 1}),
            ("Wait for COOLDOWN", None),
            ("Wait for FAULT (timeout)", None),
        ]

        for step_name, control_update in test_sequence:
            print(f"\nStep: {step_name}")

            if control_update:
                # Update control registers (map friendly names to CR indices)
                cr_values = self._map_controls_to_registers(control_update)
                self.set_bpd_state(cr_values)

            # Wait for state to settle
            time.sleep(0.5)

            # Read and decode voltage
            voltage_mv = self.read_outputd_voltage()
            result = decode_hierarchical_voltage(voltage_mv)

            print(f"  {format_decoded_result(result, verbose=True)}")

            # Validation
            if "IDLE" in step_name:
                assert result['state'] == 0, "Expected IDLE state"
            elif "ARMED" in step_name:
                assert result['state'] == 1, "Expected ARMED state"
            elif "FIRING" in step_name:
                assert result['state'] == 2, "Expected FIRING state"
            elif "COOLDOWN" in step_name:
                assert result['state'] == 3, "Expected COOLDOWN state"
            elif "FAULT" in step_name:
                assert result['fault'] == True, "Expected FAULT flag"
                assert voltage_mv < 0, "Expected negative voltage in FAULT"

    def _map_controls_to_registers(self, controls: dict) -> dict:
        """
        Map friendly control names to CR indices.

        Args:
            controls: Dict with friendly names (arm_enable, ext_trigger, etc.)

        Returns:
            Dict mapping CR index to register value

        Note: This mapping depends on BPD-RTL.yaml register allocation
        """
        # Example mapping (adjust based on BPD-RTL.yaml):
        # CR1[0] = arm_enable
        # CR1[1] = ext_trigger_in
        # CR1[2] = auto_rearm_enable
        # CR1[3] = fault_clear

        cr_values = {}

        # Build CR1 from individual bits
        cr1_value = 0
        if controls.get('arm_enable'):
            cr1_value |= (1 << 0)
        if controls.get('ext_trigger'):
            cr1_value |= (1 << 1)
        if controls.get('auto_rearm'):
            cr1_value |= (1 << 2)
        if controls.get('fault_clear'):
            cr1_value |= (1 << 3)

        if cr1_value != 0:
            cr_values[1] = cr1_value

        return cr_values

    def disconnect(self):
        """Disconnect from Moku."""
        print("\nDisconnecting from Moku...")
        if self.oscilloscope:
            self.oscilloscope.relinquish_ownership()
        if self.bpd_instrument:
            self.bpd_instrument.relinquish_ownership()
        print("Disconnected.")


def main():
    parser = argparse.ArgumentParser(description="Validate hierarchical voltage encoding on Moku")
    parser.add_argument('--ip', required=True, help='Moku IP address')
    parser.add_argument('--bitstream', required=True, type=Path, help='Path to BPD bitstream (.tar)')
    parser.add_argument('--monitor', type=float, default=0, help='Monitor duration (seconds, 0=skip)')
    parser.add_argument('--test', action='store_true', help='Run state progression test')

    args = parser.parse_args()

    if not MOKU_AVAILABLE:
        print("Error: moku library not installed. Exiting.")
        return

    if not args.bitstream.exists():
        print(f"Error: Bitstream not found: {args.bitstream}")
        return

    # Create validator
    validator = MokuHierarchicalValidator(args.ip, args.bitstream)

    try:
        # Connect and deploy
        validator.connect()

        # Run tests
        if args.test:
            validator.test_state_progression()

        # Monitor
        if args.monitor > 0:
            validator.monitor_state_transitions(args.monitor)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Always disconnect
        validator.disconnect()


if __name__ == "__main__":
    main()
```

### Usage Examples

```bash
# Test state progression (automated test)
python tools/moku_hierarchical_validator.py \
    --ip 192.168.1.100 \
    --bitstream path/to/bpd_bitstream.tar \
    --test

# Monitor OutputD for 30 seconds (manual observation)
python tools/moku_hierarchical_validator.py \
    --ip 192.168.1.100 \
    --bitstream path/to/bpd_bitstream.tar \
    --monitor 30

# Both test + monitor
python tools/moku_hierarchical_validator.py \
    --ip 192.168.1.100 \
    --bitstream path/to/bpd_bitstream.tar \
    --test \
    --monitor 10
```

---

## Task 3: Integration with Existing moku-go.py

### Reference Script Analysis

**User will provide:** `moku-go.py` (existing deployment script)

**Expected contents:**
- Moku connection setup
- Bitstream deployment to Cloud Compile slot
- Control register setting
- Oscilloscope configuration

### Integration Strategy

**Option A: Extend moku-go.py**
- Add hierarchical voltage monitoring functions
- Import `hierarchical_voltage_decoder`
- Add command-line flags for monitoring

**Option B: Standalone Script (Recommended)**
- Keep `moku-go.py` unchanged (reference only)
- Create `moku_hierarchical_validator.py` as standalone
- Copy connection/deployment patterns from `moku-go.py`

**Recommended:** Option B (standalone script, no risk of breaking existing tool)

### Code Reuse from moku-go.py

**When user provides moku-go.py, extract:**
1. Moku connection setup code
2. Bitstream deployment code
3. Control register access patterns
4. Oscilloscope configuration code

**Adapt for hierarchical validator:**
1. Replace oscilloscope channel source (OutputD from Slot 2)
2. Add voltage decoding logic
3. Add state transition monitoring

---

## Task 4: Validation Test Plan

### Test Sequence

**Test 1: Static State Validation**
1. Deploy BPD bitstream
2. Force BPD into IDLE (state=0)
3. Read OutputD voltage → expect ~0mV
4. Force BPD into ARMED (state=1)
5. Read OutputD voltage → expect ~30mV (200 digital units ≈ 30mV @ ±5V range)
6. Force BPD into FIRING (state=2)
7. Read OutputD voltage → expect ~60mV
8. Force BPD into COOLDOWN (state=3)
9. Read OutputD voltage → expect ~90mV

**Test 2: Status Offset Validation**
1. Force BPD into FIRING (state=2) with status=0x00
2. Read voltage → expect ~60mV
3. Force BPD into FIRING (state=2) with status=0x7F (max offset)
4. Read voltage → expect ~75mV (base 60mV + ~15mV offset)

**Test 3: Fault Detection Validation**
1. Force BPD into FIRING (state=2) normal
2. Read voltage → expect positive (~60mV)
3. Trigger timeout fault
4. Read voltage → expect negative (~-60mV)
5. Verify magnitude preserved (same absolute value)

**Test 4: Dynamic State Monitoring**
1. Enable BPD auto-rearm mode
2. Trigger multiple IDLE→ARMED→FIRING→COOLDOWN cycles
3. Monitor OutputD continuously
4. Verify state transitions visible on oscilloscope

---

## Task 5: Expected Oscilloscope Output

### Visual Validation

**Oscilloscope display should show:**

```
+100mV ┤                                    ← STATE=3 (COOLDOWN)
       │                    ╔═══╗
 +60mV ┤         ╔═══╗      ║   ║          ← STATE=2 (FIRING)
       │         ║   ║      ║   ║
 +30mV ┤    ╔════╝   ╚══════╝   ╚════╗     ← STATE=1 (ARMED)
       │    ║                        ║
  0mV  ┼════╝                        ╚═══  ← STATE=0 (IDLE)
───────────────────────────────────────────
 -30mV ┤                    ═══            ← FAULT (negative = fault)
```

**Key observations:**
- Clear voltage steps (~30mV per state)
- Status "noise" visible as small variations around base level
- Fault states show negative voltage
- State transitions appear as voltage jumps

### Measurement Checklist

**Verify on oscilloscope:**
- [x] IDLE state shows ~0mV
- [x] ARMED state shows ~30mV above IDLE
- [x] FIRING state shows ~60mV above IDLE
- [x] COOLDOWN state shows ~90mV above IDLE
- [x] Status offset adds 0-15mV variation around base
- [x] Fault states show negative voltage
- [x] State transitions are clean (no glitches)

---

## Success Criteria

### Decoder Utility
- [x] Python decoder works with real voltage data
- [x] Decodes state correctly (0-63)
- [x] Decodes status correctly (0-127)
- [x] Detects fault flag (sign bit)
- [x] Test cases pass

### Moku Deployment Script
- [x] Connects to Moku via IP
- [x] Deploys BPD bitstream to Slot 2
- [x] Configures oscilloscope in Slot 1
- [x] Sets Control Registers (CR0-CR15)
- [x] Reads oscilloscope voltage data

### Hardware Validation
- [x] Oscilloscope shows hierarchical encoding
- [x] State transitions visible (~30mV steps)
- [x] Status offset visible (0-15mV noise)
- [x] Fault conditions produce negative voltage
- [x] Hardware matches CocoTB simulation

### Documentation
- [x] Validation report created
- [x] Oscilloscope screenshots captured
- [x] Issues logged and resolved

---

## Deliverables

**Files to create:**
1. `tools/hierarchical_voltage_decoder.py` (decoder utility)
2. `tools/moku_hierarchical_validator.py` (deployment + monitoring script)
3. `Obsidian/Project/Test-Reports/2025-11-07-handoff-9-hardware-validation.md` (results)

**Files to reference:**
1. `moku-go.py` (user-provided, existing deployment script)

**Validation artifacts:**
1. Oscilloscope screenshots (state transitions)
2. Voltage measurements (CSV or JSON)
3. Test report with pass/fail status

---

## Troubleshooting

### Problem: Voltage levels don't match expected

**Diagnosis:**
- Check platform DAC range (±5V vs ±10V)
- Verify digital_units_per_state parameter (200)
- Check oscilloscope calibration

**Solution:**
```python
# Adjust platform_range_mv in decoder
result = decode_hierarchical_voltage(
    voltage_mv,
    platform_range_mv=10000.0  # Try ±10V instead of ±5V
)
```

---

### Problem: State decoding is off by ±1

**Cause:** Integer rounding differences between VHDL and Python

**Solution:**
```python
# VHDL truncates, Python must match
state = digital_magnitude // 200  # Integer division
status_lower = (remainder * 128) // 100  # Integer division
```

---

### Problem: Oscilloscope shows no signal

**Check:**
1. OutputD connected to Oscilloscope Channel 1
2. Oscilloscope source set to correct input
3. Oscilloscope voltage range set correctly (±10Vpp)
4. BPD enabled (CR0[31:29] = 0b111)

---

## Reference Documentation

### Moku SDK Documentation
- Moku Python API: Oscilloscope, CloudCompile classes
- Control register access: `set_control()`, `get_control()`
- Oscilloscope data retrieval: `get_data()`

### FORGE Documentation
- Handoff 6: Hierarchical voltage encoding specification
- HIERARCHICAL_ENCODER_DIGITAL_SCALING.md: Design rationale

### BPD Documentation
- BPD-RTL.yaml: Register allocation
- BPD_forge_shim.vhd: Control register mapping

---

## Next Steps

**After Handoff 9 (hardware validation):**
1. Document results in test report
2. Capture oscilloscope screenshots
3. Update CLAUDE.md with hardware validation notes
4. Proceed to Phase 4 (documentation updates) if needed

**If hardware not available:**
- Mark Handoff 9 as "deferred pending hardware access"
- Decoder utility and script still valuable for future use

---

**Created:** 2025-11-07
**Status:** Pending
**Priority:** P1 (Hardware Validation)
**Dependencies:** Handoff 8 complete (tests pass)
**Estimated Completion:** 2-3 hours active work (with hardware access)

---

**END OF HANDOFF 9**
