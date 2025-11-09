---
session_id: 2025-11-07-bpd-debug-bus
phase: 2
created: 2025-11-07
type: phase-handoff
---

# Phase 2 Handoff: Build bpd-debug.py

## Current State Summary

**Session:** BPD Debug Bus Toolchain Development
**Progress:** Phase 1 Complete, Ready for Phase 2

### Completed Work

**✅ Phase 0: Foundation**
- Session plan and architecture documented
- YAML configs created and validated
- Git workspace prepared

**✅ Phase 1: moku-deploy.py**
- Successfully migrated from wip/moku_go.py
- YAML support implemented
- Dry-run mode added
- Tested with configuration files
- 429 lines of production code

**✅ Additional Accomplishments:**
- Network connectivity options explored (see separate session)
- Web UI Coordination Pattern documented
- Parallel workflow established

### Available Tools

```
scripts/
├── moku-deploy.py        ✅ Complete - Deployment tool with YAML support
├── validate_moku_config.py ✅ Complete - Config validation
└── lib/                   📁 Ready for BPD modules
```

---

## Phase 2 Objectives

### Primary Task
Build `scripts/bpd-debug.py` - BPD-specific operational tool

### Key Requirements

1. **Core Functionality:**
   - FORGE control scheme (CR0[31:29])
   - BPD register control (CR1-CR15)
   - Status monitoring
   - Debug bus decoding

2. **Architecture:**
   - Stateful connection (maintains Moku connection)
   - BPD-specific logic
   - Integration with moku-deploy.py

3. **Modules to Create:**
   ```
   scripts/
   ├── bpd-debug.py           # Main CLI tool
   └── lib/
       ├── bpd_controller.py  # FORGE control + registers
       ├── bpd_decoder.py     # 14-bit HVS decoder
       └── deployment_validator.py  # Config verification
   ```

---

## Implementation Guide

### Module 1: bpd_controller.py

```python
class BPDController:
    def __init__(self, ip: str, slot: int = 2):
        """Initialize connection to BPD on Moku."""

    # FORGE Control Scheme (CR0[31:29])
    def initialize_forge(self):
        """Execute complete FORGE initialization sequence."""
        # Set forge_ready (bit 31)
        # Set user_enable (bit 30)
        # Set clock_enable (bit 29)

    # Operational Control
    def arm_enable(self, enable: bool):
        """Enable/disable FSM arming."""

    def set_trigger_voltage(self, mv: int):
        """Set trigger output voltage in millivolts."""

    def set_trigger_duration(self, ns: int):
        """Set trigger pulse duration in nanoseconds."""
```

### Module 2: bpd_decoder.py

```python
@dataclass
class BPDState:
    fsm_state: str      # "IDLE", "ARMED", "FIRING", etc.
    status_bits: int    # Raw status value
    fault: bool         # Fault condition detected

class BPDDebugDecoder:
    def decode_voltage(self, voltage_mv: float) -> BPDState:
        """
        Decode hierarchical voltage from oscilloscope.
        Based on forge_hierarchical_encoder:
        - 200 digital units per state
        - ~30mV steps on ±5V platform
        """
```

### Module 3: bpd-debug.py CLI

```bash
# Basic operation (assume already deployed)
uv run python scripts/bpd-debug.py --ip 192.168.73.1

# Deploy and operate
uv run python scripts/bpd-debug.py \
  --ip 192.168.73.1 \
  --deploy bpd-deployment-setup1-dummy-dut.yaml

# Verify deployment
uv run python scripts/bpd-debug.py \
  --ip 192.168.73.1 \
  --verify bpd-deployment-setup1-dummy-dut.yaml
```

---

## Test Strategy

### Dry-Run Testing
Add `--dry-run` flag to test without hardware:
- Mock Moku connection
- Simulate register updates
- Test FORGE sequence logic
- Validate decoder math

### Integration Testing
Test with moku-deploy.py:
```bash
# Deploy with moku-deploy.py
uv run python scripts/moku-deploy.py deploy \
  --config bpd-deployment-setup1-dummy-dut.yaml \
  --device 192.168.73.1

# Then control with bpd-debug.py
uv run python scripts/bpd-debug.py --ip 192.168.73.1
```

---

## Reference Documentation

### FORGE Control Scheme
See: `CLAUDE.md` - Critical Architectural Pattern: FORGE Control Scheme

**Key Points:**
- CR0[31] = forge_ready (set by loader)
- CR0[30] = user_enable (user control)
- CR0[29] = clk_enable (clock gating)
- All must be '1' for operation

### BPD Register Map
See: `examples/basic-probe-driver/BPD-RTL.yaml`

**Key Registers:**
- CR1: Lifecycle control (arm, trigger, rearm, fault_clear)
- CR2-CR5: Output controls (voltages and durations)
- CR6-CR7: Timing controls
- CR8-CR11: Monitor controls

### Hierarchical Encoder
See: Handoff 8/8.5 documentation

**Voltage Encoding:**
- State 0 (IDLE): 0mV
- State 1 (ARMED): ~30mV
- State 2 (FIRING): ~61mV
- State 3 (COOLDOWN): ~91mV
- Fault: Negative voltage

---

## Success Criteria

- [ ] bpd-debug.py CLI works
- [ ] FORGE initialization sequence correct
- [ ] BPD registers controllable
- [ ] Debug decoder matches encoder spec
- [ ] Dry-run mode functional
- [ ] Integration with moku-deploy.py works

---

## Time Budget

**Estimated:** 90 minutes

**Breakdown:**
- 20 min: bpd_controller.py
- 15 min: bpd_decoder.py
- 30 min: bpd-debug.py main CLI
- 15 min: Integration testing
- 10 min: Documentation

---

## Options for Implementation

### Option A: Local Development
Continue in current or fresh CLI context

### Option B: Web UI Development
Create handoff for Web UI (can leverage fresh 200k context)

### Option C: Parallel Approach
- Web UI #1: Build core modules
- Web UI #2: Build tests
- Local: Integration and coordination

---

## Next Steps After Phase 2

**Phase 3: Documentation & Polish**
- Update CLAUDE.md
- Create comprehensive README
- Document usage workflows
- Final testing

**Future Enhancement:**
- Network connectivity (separate session created)
- Hardware validation
- Performance optimization

---

## Notes

The Web UI Coordination Pattern discovered during Phase 1 enables efficient parallel development. Network connectivity has been explored but deferred to a separate session to maintain focus on core BPD tooling.

**To Start Phase 2:**
1. Review this handoff
2. Choose implementation approach (local vs Web UI)
3. Begin with bpd_controller.py
4. Test incrementally with --dry-run