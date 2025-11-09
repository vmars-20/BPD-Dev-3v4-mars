# BPD-Dev-3v4 - Basic Probe Driver Development

> **Status:** 🚧 **Active WIP** - Current development repo for BPD v3.4 with FORGE architecture

**What:** Production development of Basic Probe Driver (BPD) custom instrument for Moku platforms using FORGE 3-layer architecture pattern.

---

## 📐 Reference System Architecture

**Complete BPD wiring and signal routing diagram:**

![BPD Reference Wiring Diagram](static/BPD-Reference-Drawing.png)

*Complete system architecture showing Moku device slots, internal MCC routing, physical BNC connections, and integration with Riscure DS1100 probe and DUT.*

The diagram illustrates:
- **Moku device UI**: Two virtual instruments (Oscilloscope in Slot 1, BPD-Debug-BUS/CloudCompile in Slot 2) with internal MCC routing
- **Physical wiring**: External connections between Moku physical ports (PHY_IN1, PHY_IN2, PHY_OUT1, PHY_OUT2) and the Riscure DS1100 probe
- **Signal flow**: DUT trigger → Moku → Probe control signals → Fault injection

**Key signal paths:**
- **PHY_IN1**: External DUT trigger (0-5V TTL) → Slot2.InputA (BPD trigger)
- **PHY_IN2**: Probe coil current monitor (-1.4V to 0V, AC coupled) → Slot2.InputB
- **PHY_OUT1**: Probe digital_glitch trigger (0-3.3V TTL) ← Slot2.OutputA
- **PHY_OUT2**: Probe pulse_amplitude control (0-3.3V analog) ← Slot2.OutputB
- **Slot2.OutputC**: BPD-Debug-Bus (14-bit HVS encoded FSM state) → Slot1.InputA (Oscilloscope monitoring)

---

## 🚀 Quick Start: Reading & Writing Device Configurations

### Reading Device State

```bash
# Read current device state (polite, non-invasive)
# Default: writes to ./curr_model.json
python scripts/moku_read.py $MOKU_IP

# Read with detailed settings (frontend, control registers, DIO)
python scripts/moku_read.py $MOKU_IP --level 2

# Custom output file
python scripts/moku_read.py $MOKU_IP -o my_config.json

# Write to stdout (for piping)
python scripts/moku_read.py $MOKU_IP --output -
```

**Progressive escalation levels:**
- **Level 1** (default): Basic info (instruments, routing) - non-invasive
- **Level 2**: Detailed settings (frontend, output, control registers, DIO)
- **Level 3**: Maximum invasiveness (force connect if needed)

### Writing Device Configuration

```bash
# Write configuration to device (force connect, overwrites state)
python scripts/moku_write.py my_config.yaml $MOKU_IP
python scripts/moku_write.py curr_model.json $MOKU_IP
```

**Supported formats:**
- YAML (`.yaml`, `.yml`)
- JSON (`.json`)

### Complete Workflow

```bash
# Read → Inspect → Modify → Write
python scripts/moku_read.py $MOKU_IP -o current.json
# ... edit current.json ...
python scripts/moku_write.py current.json $MOKU_IP
```

**Script Features:**
- `moku_read.py`: Progressive escalation, always offers to get more details
- `moku_write.py`: Direct deployment (no safety checks, force connect)
- Both use validated `MokuConfig` Pydantic models
- Outputs are always validatable and ready for deployment

---

**Version:** 3.4-WIP  
**Last Updated:** 2025-11-09
