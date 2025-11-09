# Hierarchical Voltage Encoder - Digital Scaling Design

**Date:** 2025-11-07
**Context:** Handoff 6 - Hierarchical Voltage Encoding for OutputD
**Purpose:** Document the separation of digital encoding (FPGA) vs analog scaling (platform)

---

## Executive Summary

The `forge_hierarchical_encoder` component produces **platform-agnostic digital values** using pure arithmetic. The actual voltage range is configured externally by the Moku platform's DAC settings, not hardcoded in VHDL.

**Key Principle:** Encoder generates digital codes in two's complement format. Platform hardware maps digital codes to voltages.

---

## Design Philosophy: Separation of Concerns

### What the Encoder Does (FPGA Domain)

**Responsibility:** Encode 14-bit state+status into 16-bit signed digital value

```vhdl
-- Encoder output:
voltage_out : out signed(15 downto 0)  -- Digital code, NOT voltage
```

**How it works:**
1. Base value = `state_integer * 200` (arbitrary digital units)
2. Status offset = `status_lower * 0.78125` (arbitrary digital units)
3. Sign flip if `status[7] = '1'` (fault indicator)
4. Output = `(base + offset) * sign` (two's complement)

**What it DOES NOT do:**
- ❌ Know about ±5V, ±10V ranges
- ❌ Hardcode voltage constants
- ❌ Platform-specific scaling

### What the Platform Does (Analog Domain)

**Responsibility:** Map digital codes to physical voltages

**Platform-specific configuration:**
- DAC/ADC range setting (±5V, ±10V, etc.)
- Calibration constants
- Full-scale digital value (typically ±32768 or ±32767)

**Example - Moku Go:**
```
Digital range: -32768 to +32767
Voltage range: -5V to +5V (configured in platform registers)
Scaling: 1 digital unit ≈ 0.15 mV (5000mV / 32768)
```

**Example - Moku Pro (hypothetical ±10V range):**
```
Digital range: -32768 to +32767 (same!)
Voltage range: -10V to +10V (configured differently)
Scaling: 1 digital unit ≈ 0.30 mV (10000mV / 32768)
```

---

## Two's Complement Convention

### Standard Signed Fixed-Point Representation

**Format:** `signed(15 downto 0)` (16-bit signed integer)

```
┌─────────┬──────────────────────────────────┐
│ Bit 15  │ Bits 14:0                        │
│ (Sign)  │ (Magnitude)                      │
└─────────┴──────────────────────────────────┘

Bit 15 = 0 → Positive value
Bit 15 = 1 → Negative value (two's complement)
```

**Range:**
- Minimum: -32768 (0x8000)
- Maximum: +32767 (0x7FFF)
- Zero: 0 (0x0000)

**Examples:**
```
Digital Value    Binary              Hex      Interpretation
─────────────    ──────              ───      ──────────────
+100             0000000001100100    0x0064   Positive
+32767           0111111111111111    0x7FFF   Max positive
0                0000000000000000    0x0000   Zero
-1               1111111111111111    0xFFFF   Negative
-100             1111111110011100    0xFF9C   Negative
-32768           1000000000000000    0x8000   Max negative
```

### Why Two's Complement?

1. **Standard hardware representation** - All VHDL signed types use it
2. **Arithmetic simplicity** - Addition/subtraction work naturally
3. **Sign detection** - MSB indicates sign (no separate flag)
4. **Universal** - Works across all platforms (Go/Lab/Pro/Delta)

---

## Hierarchical Encoding Arithmetic

### Formula (Digital Domain)

```
Base Digital Value  = state_value × 200        (0-6300 for states 0-31)
Status Offset       = status[6:0] × 0.78125    (0-99.6 for status 0-127)
Sign Multiplier     = status[7] ? -1 : +1      (fault detection)

Digital Output      = (Base + Offset) × Sign
```

### Parameters (Digital Units, Not Voltages!)

- **State step size:** 200 digital units per state
- **Status resolution:** 0.78125 digital units per LSB (100 / 128)
- **State range:** 0-31 (normal), 32-63 (reserved)
- **Status payload:** 7 bits (0-127)
- **Fault flag:** status[7]

### Example Calculations

**Example 1: State=0, Status=0x00 (IDLE, no fault)**
```
Base   = 0 × 200 = 0
Offset = 0 × 0.78125 = 0
Sign   = +1 (bit 7 = 0)
Output = (0 + 0) × +1 = 0 digital units
```

**Example 2: State=3, Status=0x40 (STATE_COOLDOWN, status=64)**
```
Base   = 3 × 200 = 600
Offset = 64 × 0.78125 = 50
Sign   = +1 (bit 7 = 0)
Output = (600 + 50) × +1 = 650 digital units
```

**Example 3: State=3, Status=0xC0 (FAULT from STATE_COOLDOWN)**
```
Base   = 3 × 200 = 600
Offset = 64 × 0.78125 = 50  (lower 7 bits = 0x40 = 64)
Sign   = -1 (bit 7 = 1)
Output = (600 + 50) × -1 = -650 digital units
```

### Maximum Digital Values

**Maximum positive (state=31, status=0x7F, no fault):**
```
Base   = 31 × 200 = 6200
Offset = 127 × 0.78125 ≈ 99.2
Output = 6200 + 99 = 6299 digital units
```

**Maximum negative (state=31, status=0xFF, fault):**
```
Base   = 31 × 200 = 6200
Offset = 127 × 0.78125 ≈ 99.2
Output = -(6200 + 99) = -6299 digital units
```

**Well within `signed(15 downto 0)` range:** ±6299 << ±32768 ✓

---

## Platform-Specific Voltage Mapping

### How Digital Values Become Voltages

The platform's DAC configuration determines the voltage scaling. The encoder **does not need to know this**.

**Typical Moku Platform DAC Configuration:**
```
Full-scale digital: ±32768 (or ±32767)
Full-scale voltage: ±5V (configurable)
```

**Voltage formula (performed by hardware, not VHDL):**
```
Voltage = Digital_Value × (Full_Scale_Voltage / Full_Scale_Digital)
        = Digital_Value × (5.0V / 32768)
        = Digital_Value × 0.1526 mV
```

### Example: State=3, Status=0x40 on Moku Go (±5V range)

**Digital output (from encoder):**
```
650 digital units
```

**Voltage output (from platform DAC):**
```
Voltage = 650 × (5000mV / 32768)
        = 650 × 0.1526 mV
        ≈ 99.2 mV
```

**Oscilloscope shows:** ~99 mV

**Interpretation:**
- Base state voltage: 3 × 200 × 0.1526 ≈ 91.5 mV (STATE_COOLDOWN)
- Status noise: 64 × 0.78125 × 0.1526 ≈ 7.6 mV

### Example: Same Digital Value on Hypothetical ±10V Platform

**Digital output (from encoder):**
```
650 digital units (SAME!)
```

**Voltage output (from platform DAC with ±10V range):**
```
Voltage = 650 × (10000mV / 32768)
        = 650 × 0.3052 mV
        ≈ 198.4 mV
```

**Oscilloscope shows:** ~198 mV (doubled voltage, same digital code!)

---

## Platform Agnosticism Benefits

### Why This Design is Superior

1. **✅ Single VHDL implementation** - Works on Go/Lab/Pro/Delta
2. **✅ No voltage constants** - Encoder doesn't hardcode ±5V
3. **✅ Platform configures range** - Software/registers set DAC range
4. **✅ Pure arithmetic** - No LUTs, no magic numbers
5. **✅ Future-proof** - New platforms with different ranges work immediately

### What Changes Per Platform

**In VHDL (encoder):** Nothing! Same code works everywhere.

**In platform configuration:**
- DAC range registers (±5V, ±10V, etc.)
- Full-scale calibration constants
- Software decoder scripts (know platform range)

**In documentation:**
- Platform-specific voltage examples
- Oscilloscope interpretation guides

---

## Integration Notes

### VHDL Encoder Interface

```vhdl
entity forge_hierarchical_encoder is
    generic (
        -- Digital scaling parameters (NOT voltages!)
        DIGITAL_UNITS_PER_STATE  : integer := 200;     -- Digital units per state
        DIGITAL_UNITS_PER_STATUS : real    := 0.78125  -- Digital units per status LSB
    );
    port (
        clk           : in  std_logic;
        reset         : in  std_logic;
        state_vector  : in  std_logic_vector(5 downto 0);   -- 6-bit state
        status_vector : in  std_logic_vector(7 downto 0);   -- 8-bit status
        voltage_out   : out signed(15 downto 0)              -- Digital code (two's complement)
    );
end entity;
```

**Note:** Generic parameters are in **digital units**, not millivolts!

### Python Decoder (Platform-Aware)

```python
def decode_hierarchical_voltage(voltage_mv: float, platform_range_mv: float = 5000.0) -> dict:
    """
    Decode OutputD voltage to state + status.

    Args:
        voltage_mv: Measured voltage in millivolts
        platform_range_mv: Platform full-scale range (default: ±5V = 5000mV)

    Returns:
        dict with 'state', 'status_lower', 'fault', 'digital_value'
    """
    # Convert voltage → digital value (platform-specific)
    full_scale_digital = 32768
    digital_value = int(voltage_mv * (full_scale_digital / platform_range_mv))

    # Extract fault flag (sign bit)
    fault = (digital_value < 0)
    digital_magnitude = abs(digital_value)

    # Decode state (200 digital units per state)
    state = digital_magnitude // 200
    remainder = digital_magnitude % 200

    # Decode status (0.78125 digital units per LSB)
    status_lower = int(remainder / 0.78125)

    return {
        'state': state,
        'status_lower': status_lower,
        'fault': fault,
        'digital_value': digital_value,
        'platform_range_mv': platform_range_mv
    }
```

### CocoTB Testbench (Platform-Agnostic)

```python
# Test encoder output in DIGITAL domain (no voltage conversion)
dut.state_vector.value = 3
dut.status_vector.value = 0x40
await ClockCycles(dut.clk, 1)

expected_digital = 3 * 200 + 64 * 0.78125  # 650 digital units
actual_digital = dut.voltage_out.value.signed_integer

assert actual_digital == 650, f"Expected 650, got {actual_digital}"
```

**Note:** Tests work in digital domain, independent of platform voltage range!

---

## Common Misconceptions

### ❌ Misconception 1: "Encoder outputs 200mV per state"

**Reality:** Encoder outputs **200 digital units per state**. The platform converts digital units to voltage.

### ❌ Misconception 2: "Need to change VHDL for different platforms"

**Reality:** Same VHDL works on all platforms. Platform DAC range is configured externally.

### ❌ Misconception 3: "Generic parameters should be in millivolts"

**Reality:** Generic parameters are **digital units** (platform-agnostic). Voltage interpretation happens in analog domain.

---

## Design Rationale

### Why Not Hardcode Voltage Constants?

**Rejected approach:**
```vhdl
-- BAD: Platform-specific constants in VHDL
constant MV_PER_STATE : real := 200.0;  -- Assumes ±5V platform!
constant FULL_SCALE_MV : real := 5000.0;
```

**Problems:**
1. ❌ Breaks on platforms with different DAC ranges
2. ❌ Requires recompilation for different platforms
3. ❌ Ties FPGA logic to analog configuration
4. ❌ Violates separation of concerns

**Correct approach:**
```vhdl
-- GOOD: Platform-agnostic digital units
constant DIGITAL_UNITS_PER_STATE : integer := 200;
```

**Benefits:**
1. ✅ Works on any platform
2. ✅ No recompilation needed
3. ✅ Clean digital/analog separation
4. ✅ Single source of truth (FPGA logic)

---

## References

### Related Documents
- **Handoff 6:** `Obsidian/Project/Handoffs/2025-11-07-handoff-6-hierarchical-voltage-encoding.md`
- **Implementation:** `libs/forge-vhdl/vhdl/debugging/forge_hierarchical_encoder.vhd` (to be created)
- **Alternative schemes:** `Obsidian/Project/Review/HIERARCHICAL_VOLTAGE_ENCODING_ALTERNATIVES.md`

### Platform Documentation
- **Moku Models:** `libs/moku-models/` - Platform specifications
- **CLAUDE.md:** Platform voltage ranges and ADC/DAC specs

### Test Infrastructure
- **CocoTB tests:** `libs/forge-vhdl/vhdl/debugging/test_forge_hierarchical_encoder.py`
- **Decoder utility:** `tools/oscilloscope_decoder.py`

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-07 | 1.0 | Initial design document |

---

**Last Updated:** 2025-11-07
**Maintained By:** Moku Instrument Forge Team
**Status:** Design Complete, Implementation Pending
