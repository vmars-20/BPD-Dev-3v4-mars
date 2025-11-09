# BPD Two-Tool Architecture

**Date:** 2025-11-07
**Status:** ✅ AUTHORITATIVE - Reference this for all BPD deployment/operation work
**Context:** Session: BPD-Debug-Bus integration testing
**Audience:** Human developers and AI agents

---

## Executive Summary

The BPD (Basic Probe Driver) system uses a **two-tool architecture** that cleanly separates hardware lifecycle (deployment) from application lifecycle (operation).

**Key Principle:** Deployment and operation are distinct phases with clear contracts between them.

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Deployment (moku-go.py)                                │
│ - Reads MokuConfig YAML                                         │
│ - Configures hardware to known state                            │
│ - Releases connection                                            │
│ - Exits (stateless)                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    Hardware Ready
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: Operation (bpd-debug.py)                               │
│ - Connects to deployed system                                   │
│ - Verifies configuration (optional)                             │
│ - Takes over session                                             │
│ - Operates BPD (FORGE control + monitoring)                     │
│ - Interactive/scripted control (stateful)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tool 1: `scripts/moku-go.py` - Deployment Tool

### Purpose
Get Moku hardware into known starting state from MokuConfig YAML specification.

### Characteristics
- **Stateless** - No persistent connection
- **Idempotent** - Can run multiple times safely
- **Generic** - Works with ANY MokuConfig (not BPD-specific)
- **Abstraction layer** - Wraps 1st-party `moku` library

### Input
MokuConfig YAML file (e.g., `bpd-deployment-setup1-dummy-dut.yaml`)

### Output
Deployed Moku system in known state, connection released

### Responsibilities
1. **Device discovery** - Find Moku on network (zeroconf)
2. **Device caching** - Store discovered devices (`~/.moku-deploy/device_cache.json`)
3. **Instrument deployment** - Deploy instruments to slots (CloudCompile, Oscilloscope, etc.)
4. **Routing configuration** - Configure MCC signal routing matrix
5. **Register initialization** - Set control registers to safe defaults
6. **Connection release** - Disconnect cleanly after deployment

### Usage Examples

```bash
# Discover devices on network
uv run python scripts/moku-go.py discover --timeout 5

# List cached devices
uv run python scripts/moku-go.py list

# Deploy from MokuConfig YAML
uv run python scripts/moku-go.py deploy \
  --device 192.168.73.1 \
  --config bpd-deployment-setup1-dummy-dut.yaml

# Deploy by device name (from cache)
uv run python scripts/moku-go.py deploy \
  --device MokuB106 \
  --config bpd-deployment-setup2-real-dut.yaml
```

### Key Design Decisions

**Why stateless?**
- Deployment is a one-time setup operation
- Holding connection blocks other tools
- Allows operator to verify deployment manually before operation

**Why generic (not BPD-specific)?**
- Same tool can deploy ANY custom instrument
- MokuConfig YAML abstracts instrument details
- Reusable across projects (laser probes, RF instruments, etc.)

**Why release connection?**
- Operator may want to inspect web UI
- bpd-debug.py needs exclusive connection
- Clean separation: deploy vs operate

---

## Tool 2: `scripts/bpd-debug.py` - Operation Tool

### Purpose
Operate deployed BPD instrument for fault injection campaigns and debugging.

### Characteristics
- **Stateful** - Maintains connection during operation
- **Interactive** - REPL or scripting interface
- **BPD-specific** - Understands FORGE control scheme + BPD registers
- **Verification-aware** - Can validate deployment before operation

### Input
- IP address of deployed Moku
- Optional: MokuConfig YAML for verification
- Optional: Deploy flag to call moku-go.py first

### Output
Interactive control session with real-time FSM monitoring

### Responsibilities
1. **Connection management** - Take over session from deployed system
2. **Deployment verification** - Validate hardware matches expected config
3. **Optional deployment** - Call moku-go.py if requested
4. **FORGE state machine control** - Execute safe initialization sequence
5. **Operational parameter control** - Manipulate CR1-CR15 registers
6. **Debug bus monitoring** - Read 14-bit HVS from oscilloscope
7. **Interactive control** - REPL or scripting interface for operation

### Usage Examples

```bash
# Assume hardware already deployed (fast iteration)
uv run python scripts/bpd-debug.py --ip 192.168.73.1

# Deploy fresh, then operate (integrated workflow)
uv run python scripts/bpd-debug.py \
  --ip 192.168.73.1 \
  --deploy bpd-deployment-setup1-dummy-dut.yaml

# Verify hardware matches spec, abort if mismatch
uv run python scripts/bpd-debug.py \
  --ip 192.168.73.1 \
  --verify bpd-deployment-setup1-dummy-dut.yaml
```

### Workflow Modes

**Mode 1: Assume Deployed (Fast Iteration)**
```
bpd-debug.py --ip 192.168.73.1
  ↓
Connect to Moku
  ↓
Assume correct deployment
  ↓
FORGE initialization (CR0[31:29])
  ↓
Interactive control session
```

**Mode 2: Deploy + Operate (Integrated)**
```
bpd-debug.py --ip 192.168.73.1 --deploy setup1.yaml
  ↓
Call: moku-go.py deploy --config setup1.yaml
  ↓
Wait for deployment completion
  ↓
Connect to Moku
  ↓
FORGE initialization (CR0[31:29])
  ↓
Interactive control session
```

**Mode 3: Verify + Operate (Defensive)**
```
bpd-debug.py --ip 192.168.73.1 --verify setup1.yaml
  ↓
Connect to Moku
  ↓
Verify deployment matches YAML spec
  ↓
If mismatch:
  - Show errors
  - Prompt: "Reconfigure device? [y/N]"
  - If yes: Call moku-go.py deploy
  - If no: Exit
  ↓
FORGE initialization (CR0[31:29])
  ↓
Interactive control session
```

### Key Design Decisions

**Why stateful?**
- Fault injection campaigns need persistent connection
- Real-time FSM monitoring requires continuous polling
- Interactive control implies session management

**Why BPD-specific?**
- Understands FORGE control scheme (CR0[31:29])
- Knows BPD register map (CR1-CR15)
- Decodes 14-bit debug bus (HVS)
- Not a generic tool - tailored for BPD operation

**Why call moku-go.py?**
- **Avoids code duplication** - Deployment logic in one place
- **Clear contract** - moku-go.py output = bpd-debug.py input
- **Composability** - Tools usable independently or together
- **Fail-fast** - Deployment errors caught before operation

---

## MokuConfig YAML Role

### Purpose
Authoritative specification of expected hardware configuration.

### Three Use Cases

**1. Deployment Input (moku-go.py)**
```bash
moku-go.py deploy --config bpd-deployment-setup1-dummy-dut.yaml
# Reads YAML, deploys hardware to match spec
```

**2. Verification Reference (bpd-debug.py)**
```bash
bpd-debug.py --ip 192.168.73.1 --verify bpd-deployment-setup1-dummy-dut.yaml
# Reads YAML, validates hardware matches spec
```

**3. Human Documentation**
Operator reads YAML to understand:
- Slot assignments
- Routing connections
- Control register initial values
- Physical BNC wiring requirements

### Key Design Decision: Documentation vs Automation

**MokuConfig YAML is BOTH:**
- ✅ **Machine-readable** - Pydantic validated, deployment automation
- ✅ **Human-readable** - Clear comments, physical connection docs

**Extra fields (not in Pydantic models):**
- `description` - Human-readable intent
- `physical_connections` - BNC wiring instructions

These are stripped during validation but preserved for human operators.

---

## File Structure

```
scripts/
├── moku-go.py                 # Deployment tool (stateless, generic)
├── bpd-debug.py               # Operation tool (stateful, BPD-specific)
├── validate_moku_config.py    # YAML validation (no hardware required)
└── lib/                       # Shared library code
    ├── bpd_controller.py      # BPDController class (FORGE + CR control)
    ├── bpd_decoder.py         # 14-bit HVS decoder (debug bus)
    └── deployment_validator.py # Config verification (hardware vs YAML)

bpd-deployment-setup1-dummy-dut.yaml   # Authoritative config (self-contained testing)
bpd-deployment-setup2-real-dut.yaml    # Authoritative config (live FI campaigns)
```

---

## Shared Library: `scripts/lib/`

### `bpd_controller.py` - BPD Operational Control

**Purpose:** High-level API for BPD operation (assumes deployment complete)

**Key Classes:**
- `BPDController` - Main control interface

**Responsibilities:**
- FORGE state machine control (CR0[31:29] sequence)
- Operational parameter control (CR1-CR15 manipulation)
- Register read/write wrappers
- Safe initialization patterns

**Example API:**
```python
class BPDController:
    def __init__(self, ip: str, slot: int = 2):
        """Connect to deployed BPD instrument."""

    # FORGE control scheme
    def set_forge_ready(self) -> None:
        """Set CR0[31] = 1 (deployment complete)."""

    def set_user_enable(self) -> None:
        """Set CR0[30] = 1 (user enables module)."""

    def set_clock_enable(self) -> None:
        """Set CR0[29] = 1 (clock gating enabled)."""

    def initialize_forge(self) -> None:
        """Execute complete FORGE initialization sequence."""
        self.set_forge_ready()
        self.set_user_enable()
        self.set_clock_enable()
        # Now: global_enable = 1, FSM operational

    # Operational parameters (CR1-CR15)
    def arm_enable(self, enable: bool) -> None:
        """Set CR1[0] - Arm the FSM."""

    def set_trigger_voltage(self, mv: int) -> None:
        """Set CR2 - Trigger output voltage (mV)."""

    def set_trigger_duration(self, ns: int) -> None:
        """Set CR3 - Trigger pulse duration (ns)."""

    def set_cooldown(self, us: int) -> None:
        """Set CR7 - Cooldown interval (µs)."""

    # Status monitoring
    def read_status(self) -> dict:
        """Read status registers (SR0-SR15)."""

    def read_debug_bus(self) -> 'BPDState':
        """Read 14-bit debug bus from oscilloscope."""
```

---

### `bpd_decoder.py` - Debug Bus Decoder

**Purpose:** Decode 14-bit HVS voltage to human-readable FSM state

**Key Classes:**
- `BPDDebugDecoder` - HVS decoder
- `BPDState` - Decoded state dataclass

**Responsibilities:**
- 14-bit HVS voltage decoding
- FSM state extraction (IDLE, ARMED, TRIGGERED, etc.)
- Status bit extraction
- Human-readable formatting

**Example API:**
```python
class BPDState:
    fsm_state: str       # "IDLE", "ARMED", "TRIGGERED", etc.
    status_bits: int     # Raw status value
    raw_value: int       # Raw 14-bit value
    voltage: float       # Measured voltage (V)

class BPDDebugDecoder:
    def decode_voltage(self, voltage: float) -> BPDState:
        """Decode HVS voltage to FSM state."""
        # Hierarchical voltage scheme decoding
        # See: forge_hierarchical_encoder.vhd for encoding scheme
```

---

### `deployment_validator.py` - Configuration Verification

**Purpose:** Verify deployed hardware matches MokuConfig YAML spec

**Key Classes:**
- `DeploymentValidator` - Hardware verification

**Responsibilities:**
- Slot verification (correct instruments deployed)
- Routing verification (connections match spec)
- Bitstream verification (correct bitstream loaded)
- Error reporting

**Example API:**
```python
class DeploymentValidator:
    def __init__(self, config_path: str):
        """Load MokuConfig YAML spec."""
        self.config = MokuConfig.from_yaml(config_path)

    def verify_deployment(self, ip: str) -> list[str]:
        """
        Verify deployed hardware matches spec.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Connect to deployed system
        moku = MultiInstrument(ip, platform_id=2)

        # Verify slots
        for slot_num, expected in self.config.slots.items():
            actual = moku.get_instrument(slot_num)
            if actual.type != expected.instrument:
                errors.append(f"Slot {slot_num}: Expected {expected.instrument}, got {actual.type}")

        # Verify routing (if possible)
        # Note: MCC doesn't expose routing matrix for reading - future enhancement

        # Verify bitstream (if possible)
        # Note: Limited bitstream introspection - future enhancement

        return errors
```

---

## Workflow Patterns

### Pattern 1: Fresh Deployment

**Use Case:** Starting new session, ensure clean state

```bash
# Step 1: Deploy hardware
uv run python scripts/moku-go.py deploy \
  --device 192.168.73.1 \
  --config bpd-deployment-setup1-dummy-dut.yaml

# Step 2: Operate BPD
uv run python scripts/bpd-debug.py --ip 192.168.73.1
```

---

### Pattern 2: Integrated Workflow

**Use Case:** One-command deployment + operation

```bash
# Single command (calls moku-go.py internally)
uv run python scripts/bpd-debug.py \
  --ip 192.168.73.1 \
  --deploy bpd-deployment-setup1-dummy-dut.yaml
```

---

### Pattern 3: Fast Iteration

**Use Case:** Hardware already deployed, rapid testing

```bash
# Assume hardware ready (skip deployment)
uv run python scripts/bpd-debug.py --ip 192.168.73.1

# Operator manually adjusts parameters, tests again
uv run python scripts/bpd-debug.py --ip 192.168.73.1

# Repeat...
```

---

### Pattern 4: Defensive Verification

**Use Case:** Unsure if hardware matches expected config

```bash
# Verify before operating (abort if mismatch)
uv run python scripts/bpd-debug.py \
  --ip 192.168.73.1 \
  --verify bpd-deployment-setup1-dummy-dut.yaml
```

---

## Design Rationale

### Why Two Tools (Not One)?

**Considered:** Single tool handling both deployment and operation

**Rejected because:**
1. **Violates single responsibility principle** - Deployment ≠ Operation
2. **Harder to test in isolation** - Can't test deployment without operation
3. **Less composable** - Can't use moku-go.py for other instruments
4. **Unclear boundaries** - When does deployment end and operation begin?

**Benefits of two-tool approach:**
- ✅ Clear separation of concerns
- ✅ Tools testable independently
- ✅ moku-go.py reusable for other instruments
- ✅ Explicit contract: deployment output = operation input
- ✅ Flexible workflows (deploy-only, operate-only, integrated)

---

### Why moku-go.py is Generic (Not BPD-Specific)?

**Key insight:** MokuConfig YAML already contains instrument-specific details.

**Example:**
```yaml
# BPD deployment
slots:
  2:
    instrument: CloudCompile
    bitstream: examples/basic-probe-driver/bitstream/bpd_moku_go.tar
    control_registers: { ... }

# Laser probe deployment (future)
slots:
  2:
    instrument: CloudCompile
    bitstream: examples/laser-probe/bitstream/laser_probe_moku_go.tar
    control_registers: { ... }
```

**Same tool, different configs!**

moku-go.py reads YAML, deploys accordingly. No BPD-specific logic needed.

---

### Why bpd-debug.py Can Call moku-go.py?

**Key insight:** Deployment is a prerequisite for operation.

**Without this pattern:**
```bash
# User must remember correct order
moku-go.py deploy --config setup1.yaml
bpd-debug.py --ip 192.168.73.1
```

**With this pattern:**
```bash
# Single command, correct order guaranteed
bpd-debug.py --ip 192.168.73.1 --deploy setup1.yaml
```

**Benefits:**
- ✅ User convenience (one command)
- ✅ Correct ordering guaranteed (deploy before operate)
- ✅ No code duplication (reuses moku-go.py)
- ✅ Tools still independently usable

---

## Future Extensions

### Additional Operational Tools

**Pattern:** New tools can reuse moku-go.py for deployment

```bash
# Automated FI campaign runner
scripts/bpd-campaign.py \
  --ip 192.168.73.1 \
  --deploy setup2-real-dut.yaml \
  --campaign experiments/glitch-campaign-1.yaml

# Automated testing
scripts/bpd-test.py \
  --ip 192.168.73.1 \
  --deploy setup1-dummy-dut.yaml \
  --run-tests
```

---

### Remote Deployment

**Use Case:** Deploy to Moku on different subnet

```bash
# Discover devices via SSH tunnel
moku-go.py discover --ssh user@remote-host

# Deploy via tunnel
moku-go.py deploy \
  --device 192.168.1.100 \
  --config bpd-deployment.yaml \
  --ssh user@remote-host
```

---

### Multi-Device Orchestration

**Use Case:** Coordinate multiple Mokus

```bash
# Deploy to array of devices
moku-go.py deploy \
  --devices moku-array.yaml \
  --config bpd-deployment.yaml

# Coordinate multi-Moku FI campaign
bpd-campaign.py \
  --devices moku-array.yaml \
  --campaign distributed-glitch.yaml
```

---

## Reference Links

**MokuConfig Specifications:**
- `bpd-deployment-setup1-dummy-dut.yaml` - Self-contained testing
- `bpd-deployment-setup2-real-dut.yaml` - Live FI campaigns

**Validation:**
- `scripts/validate_moku_config.py` - YAML validation (no hardware)
- `libs/moku-models/scripts/validate_moku_config.py` - Submodule validation

**FORGE Architecture:**
- `CLAUDE.md` - Complete FORGE specification
- `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md` - Deep dive
- `libs/forge-vhdl/vhdl/packages/forge_common_pkg.vhd` - VHDL implementation

**BPD Register Specification:**
- `examples/basic-probe-driver/BPD-RTL.yaml` - Authoritative register map

**Deployment Strategy:**
- `Obsidian/Project/Review/CASCADING_PYPROJECT_STRATEGY.md` - Two-tier testing

---

## Version History

**v1.0 (2025-11-07)** - Initial architecture
- Two-tool pattern established
- moku-go.py deployment (generic, stateless)
- bpd-debug.py operation (BPD-specific, stateful)
- MokuConfig YAML as documentation + automation
- Shared library structure defined

---

**Last Updated:** 2025-11-07
**Maintained By:** BPD Development Team
**Status:** ✅ AUTHORITATIVE - Reference for all BPD work
