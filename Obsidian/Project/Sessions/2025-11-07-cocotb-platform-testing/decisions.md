# Key Decisions - 2025-11-07-cocotb-platform-testing

**Date:** 2025-11-07
**Session:** CocoTB Platform Testing Framework (Phase 1+2)

---

## Decision 1: Signal Handle Wiring (Not Value Copying)

### Context
Routing matrix needs to simulate real Moku hardware behavior for signal routing between instrument slots. Initial design question: should routing store signal references or copy values?

### Decision
Store `SimHandleBase` references (signal handles) in external channels, **not** static integer values.

### Implementation
```python
# In simulation_backend.py (routing setup)
source_signal = getattr(source_simulator.dut, source_port)  # SimHandleBase
dst_simulator.add_external_channel(dst_port, source_signal)
                                                    ↑
                                    Pointer to signal handle
                                    NOT static value snapshot

# In oscilloscope.py (_get_signal)
def _get_signal(self, channel_name: str):
    # Check external channels first (routed signals)
    if channel_name in self._external_channels:
        return self._external_channels[channel_name]  # Returns SimHandleBase
    # Fall back to local DUT signals
    return getattr(self.dut, channel_name)
```

### Rationale
1. **Real Moku hardware behavior:** Inter-slot routing is just a 16-bit digital bus (wires, not snapshots)
2. **Dynamic signal access:** Signal handles enable reading latest value each oscilloscope sample
3. **Avoid stale data:** Value copying would freeze at routing setup time, missing all subsequent changes
4. **CocoTB native:** SimHandleBase is the proper CocoTB abstraction for VHDL signal access

### Alternatives Considered
**Option A: Static value copying**
```python
# Rejected approach:
value = int(source_signal.value)  # Snapshot at routing time
dst_simulator.add_external_channel(dst_port, value)
```
- ❌ Would not reflect dynamic signal changes
- ❌ Fundamentally wrong model of hardware behavior
- ❌ Would make all tests fail (oscilloscope would see frozen values)

**Option B: Re-read from source DUT each sample**
```python
# Rejected approach:
def _get_signal(self, channel_name):
    routing_info = self._get_routing_info(channel_name)
    source_dut = self._find_source_dut(routing_info)
    return getattr(source_dut, routing_info.source_port)
```
- ❌ Breaks encapsulation (oscilloscope needs to know about other simulators)
- ❌ More complex implementation
- ❌ Harder to debug (routing logic scattered)

### Impact
- ✅ **Routing tests pass:** 2-slot integration test validates dynamic signal capture
- ✅ **Hardware fidelity:** Simulation accurately models real Moku behavior
- ✅ **Clean architecture:** Routing setup is one-time, signal reading is transparent

### Validation
**Test:** `test_platform_routing_integration.py::test_routing_configuration`
- Verifies external channel is `SimHandleBase` instance (not integer)
- Confirms signal handle reference, not value copy

**Test:** `test_platform_routing_integration.py::test_routed_signal_capture`
- Captures 125 samples of counter incrementing through routed channel
- Validates multiple unique state values (proves dynamic reading)
- Decodes state progression 0→15 (hierarchical voltage decoding)

---

## Decision 2: Type-Agnostic 16-Bit Bus Design

### Context
Moku platforms route signals between slots using a 16-bit digital backplane. Question: should routing enforce voltage types or operate on raw bits?

### Decision
Routing matrix operates on **raw 16-bit signals with no type enforcement**. Type interpretation happens only at physical I/O boundaries (ADC/DAC), not inter-slot routing.

### Implementation
```vhdl
-- In MCC_CustomInstrument.vhd (vendor interface)
-- Convention: signed(15 downto 0) for all I/O
entity MCC_CustomInstrument is
    port (
        -- DAC outputs (convention: signed, could be std_logic_vector)
        OutputA : out signed(15 downto 0);
        OutputB : out signed(15 downto 0);
        OutputC : out signed(15 downto 0);
        OutputD : out signed(15 downto 0);

        -- ADC inputs (convention: signed, could be std_logic_vector)
        InputA : in signed(15 downto 0);
        InputB : in signed(15 downto 0);
        -- ...
    );
end entity;
```

```python
# In simulation_backend.py (routing)
# No type checking or conversion - just wire the signals
source_signal = getattr(source_simulator.dut, source_port)
dst_simulator.add_external_channel(dst_port, source_signal)
# CocoTB preserves VHDL type (signed/unsigned/std_logic_vector)
# But routing doesn't care - just passes bits through
```

### Rationale
1. **Hardware reality:** Real Moku inter-slot routing bypasses ADC/DAC (digital backplane, not analog)
2. **Type convention ≠ type enforcement:** VHDL uses `signed(15 downto 0)` by convention (bipolar ADC/DAC), but routing treats as raw bits
3. **Endpoint interpretation:** Type meaning is determined by ADC/DAC peripherals (physical I/O), not routing matrix
4. **Flexibility:** Could use `std_logic_vector` or `unsigned` and routing would still work

### Real Moku Platform Behavior
```
Slot 2 CustomInstrument
├─ OutputD: signed(15 downto 0) = 16'h0C80  (digital value)
    ↓
[16-bit digital backplane - just wires!]
    ↓ (no ADC/DAC conversion, no type checking)
Slot 1 CustomInstrument
├─ InputA: signed(15 downto 0) = 16'h0C80  (same digital value)
```

**Key insight:** ADC/DAC conversion only happens at physical I/O boundaries (IN1/IN2/OUT1/OUT2), not between slots.

### Alternatives Considered
**Option A: Type-checked routing with voltage conversion**
```python
# Rejected approach:
def route_signal(source, dest):
    if source.type != dest.type:
        raise TypeError("Type mismatch in routing")
    if source.voltage_range != dest.voltage_range:
        converted_value = convert_voltage(source, dest)
        return converted_value
```
- ❌ Too complex (no voltage domains in inter-slot routing)
- ❌ Doesn't match hardware (no conversion in digital backplane)
- ❌ Would break valid use cases (BPD hierarchical encoding uses raw digital values)

**Option B: Force all signals to std_logic_vector**
```vhdl
-- Rejected approach:
OutputD : out std_logic_vector(15 downto 0);  -- Type-neutral
InputA  : in  std_logic_vector(15 downto 0);
```
- ❌ Loses type information at endpoints (ADC/DAC need to know signed vs unsigned)
- ❌ Doesn't match MCC CustomInstrument convention (uses `signed` throughout)
- ❌ More type casting required in application logic

### Impact
- ✅ **BPD-Debug-Bus works:** Hierarchical encoding passes through routing unchanged
- ✅ **Hardware fidelity:** Simulation matches real Moku digital backplane behavior
- ✅ **Simple implementation:** No type conversion logic needed in routing
- ✅ **Flexible:** Supports any 16-bit VHDL type (signed/unsigned/std_logic_vector)

### Validation
**Test:** `test_platform_routing_integration.py::test_routed_signal_capture`
- Counter outputs `signed(15 downto 0)` with hierarchical encoding (0x0000, 0x00C8, 0x0190, ...)
- Oscilloscope captures via routed `InputA` (also `signed(15 downto 0)`)
- Decoding validates values match (no corruption, no type conversion)
- Proves type-agnostic routing preserves signal integrity

---

## Decision 3: BPD-Debug-Bus Pattern Validation

### Context
BPD design routes internal FSM state to oscilloscope slot for debugging (avoids needing JTAG or UART). Need to validate this pattern works before hardware deployment.

### Decision
Implement and validate full **Slot2OutD → Slot1InA routing path** with hierarchical voltage encoding/decoding in CocoTB platform tests.

### BPD-Debug-Bus Architecture
```
Slot 2: BPD CustomInstrument (CloudCompile)
├─ FSM State: 4-bit (0-15)
├─ Status Bits: 8-bit flags
├─ forge_hierarchical_encoder:
│   └─ Combines state × 200 + status_offset
│       → OutputD: signed(15 downto 0) digital value
│          ↓
│   [Routing Matrix: Slot2OutD → Slot1InA]
│          ↓
Slot 1: Oscilloscope
├─ InputA: captures routed signal
├─ Sample @ 125 MHz (8ns period)
├─ Read voltage (±5V analog equivalent)
└─ Decode: extract state and status
    └─ State = floor(voltage_millivolts / 200)
```

### Implementation
**Test:** `test_platform_routing_integration.py`

**Setup (MokuConfig YAML-driven):**
```yaml
slots:
  slot_2:
    instrument: CloudCompile
    bitstream: forge_counter_with_encoder.bit
    connections:
      OutputD: Slot1InA  # Routing declaration

  slot_1:
    instrument: Oscilloscope
    channels:
      - InputA  # Will capture routed signal
```

**Validation:**
1. Routing matrix populated correctly (Slot2OutD → Slot1InA)
2. Oscilloscope external channel wired to DUT.OutputD signal handle
3. Counter increments 0→15, encoder outputs hierarchical values
4. Oscilloscope captures 125 samples via routed InputA
5. Decoder extracts state progression (validates encoding/decoding match)

### Rationale
1. **De-risk hardware deployment:** Catch integration issues in simulation before hardware
2. **Validate hierarchical encoding:** Proves encoder/decoder are inverse operations
3. **Test routing fidelity:** Confirms routing doesn't corrupt signals
4. **Build confidence:** Successful simulation gives high confidence for hardware bring-up

### Alternatives Considered
**Option A: Skip simulation, test directly on hardware**
- ❌ High risk (hardware debugging is slow, no visibility)
- ❌ Wasted time if routing doesn't work (no easy debugging)
- ❌ Could damage hardware with bad configuration

**Option B: Test encoding/decoding separately (no routing)**
- ❌ Doesn't validate end-to-end integration
- ❌ Misses routing-specific bugs (signal corruption, timing)
- ❌ Less confidence for hardware deployment

### Impact
- ✅ **BPD-Debug-Bus validated:** 2-slot routing test passes with hierarchical encoding
- ✅ **High confidence for hardware:** Know it works in simulation before deploying
- ✅ **Early bug detection:** Fixed 3 platform bugs during integration testing
- ✅ **Reference implementation:** Test serves as example for future multi-slot designs

### Validation
**Test Results:**
```
test_routing_configuration           ✓ PASS
test_routed_signal_capture          ✓ PASS

Captured state progression: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
All unique states present ✓
Hierarchical decoding correct ✓
```

**Bugs Found and Fixed:**
1. CloudCompile signal assignment (CocoTB incompatibility)
2. Network CR async/await timing (Timer vs asyncio.sleep)
3. Simulator registry naming (capitalization)

**Outcome:** BPD-Debug-Bus pattern proven in simulation, ready for hardware testing.

---

## Decision 4: External Channel Priority in Oscilloscope

### Context
Oscilloscope simulator needs to capture both DUT-local signals (OutputA/B/C/D) and routed external signals (from other slots). Question: how to resolve channel name conflicts when routing overrides local signals?

### Decision
`_get_signal()` checks **external channels first**, then falls back to DUT signals. Routing can "override" default DUT signal access.

### Implementation
```python
# In oscilloscope.py
def _get_signal(self, channel_name: str):
    """Get signal handle for a channel name.

    Priority:
    1. External channels (routed from other slots) - FIRST
    2. DUT signals (local to this oscilloscope) - FALLBACK
    """
    # Check external channels first (routed signals)
    if channel_name in self._external_channels:
        return self._external_channels[channel_name]

    # Fall back to local DUT signals
    if not hasattr(self.dut, channel_name):
        raise AttributeError(f"Signal '{channel_name}' not found")

    return getattr(self.dut, channel_name)
```

### Rationale
1. **Hardware behavior:** Real Moku routing matrix takes precedence over local connections
2. **Explicit override:** If routing is configured, it should override default behavior
3. **Flexibility:** Allows same oscilloscope to work with local or routed signals
4. **Intuitive:** Routing is intentional, should have priority over implicit defaults

### Real Moku Platform Behavior
```
Scenario 1: No routing configured
├─ Oscilloscope.InputA → Local DUT input (e.g., physical IN1)

Scenario 2: Routing configured (Slot2OutD → Slot1InA)
├─ Oscilloscope.InputA → Routed signal from Slot 2 OutputD
└─ Local DUT input (physical IN1) is ignored/overridden
```

**Key insight:** Routing matrix is **higher priority** than default signal connections in real hardware.

### Alternatives Considered
**Option A: Separate methods for local vs external signals**
```python
# Rejected approach:
def get_local_signal(self, channel_name):
    return getattr(self.dut, channel_name)

def get_external_signal(self, channel_name):
    return self._external_channels[channel_name]

# User must know which to call - error-prone!
```
- ❌ Adds complexity (user must know signal source)
- ❌ Not how real hardware works (routing is transparent)
- ❌ More error-prone (wrong method call → wrong signal captured)

**Option B: External-only channels (reject local access)**
```python
# Rejected approach:
def _get_signal(self, channel_name):
    # ONLY allow external channels, reject local DUT signals
    if channel_name not in self._external_channels:
        raise ValueError("Only external channels allowed")
    return self._external_channels[channel_name]
```
- ❌ Too restrictive (oscilloscope can't capture local signals for debugging)
- ❌ Doesn't match real hardware (can capture both local and routed)
- ❌ Limits testing flexibility

**Option C: DUT signals first, external fallback**
```python
# Rejected approach (WRONG priority):
def _get_signal(self, channel_name):
    # Check DUT first (WRONG!)
    if hasattr(self.dut, channel_name):
        return getattr(self.dut, channel_name)
    # Fall back to external channels
    return self._external_channels[channel_name]
```
- ❌ Inverted priority (doesn't match hardware behavior)
- ❌ Routing would never override local signals
- ❌ Would break BPD-Debug-Bus test (captures local signal, not routed)

### Impact
- ✅ **Routing works correctly:** External channels override local signals as expected
- ✅ **Hardware fidelity:** Matches real Moku routing matrix behavior
- ✅ **Flexible debugging:** Can capture local signals when no routing configured
- ✅ **Intuitive API:** Single method for all signal access (transparent)

### Validation
**Test:** `test_platform_routing_integration.py::test_routing_configuration`
```python
# Verify external channel is registered
assert 'InputA' in osc._external_channels

# Verify signal handle is correct
external_signal = osc._external_channels['InputA']
assert external_signal is counter_dut.OutputD  # Points to Slot 2 DUT, not Slot 1
```

**Test:** `test_platform_routing_integration.py::test_routed_signal_capture`
```python
# Oscilloscope captures from InputA
# Because routing is configured (Slot2OutD → Slot1InA):
# → _get_signal('InputA') returns external channel (Slot2.OutputD)
# → NOT local DUT signal (Slot1.InputA from physical input)

samples = osc.capture('InputA', num_samples=125)
# Captures incrementing counter from Slot 2, not local input
```

**Outcome:** External channel priority matches real hardware, enables routing to override defaults.

---

## Summary

**4 Key Decisions:**
1. **Signal Handle Wiring** - Dynamic signal access via references (not value copying)
2. **Type-Agnostic Routing** - 16-bit bus with no type enforcement (matches hardware)
3. **BPD-Debug-Bus Validation** - Complete routing test with hierarchical encoding
4. **External Channel Priority** - Routing overrides local signals (hardware fidelity)

**Common Theme:** **Hardware fidelity** - every decision driven by matching real Moku platform behavior

**Impact:** Platform testing framework accurately simulates real hardware, giving high confidence for hardware deployment.

---

**Session:** 2025-11-07-cocotb-platform-testing
**Archived:** 2025-11-07
