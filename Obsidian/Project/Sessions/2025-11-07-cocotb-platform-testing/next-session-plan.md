# Next Session Plan - Hardware Validation Tools

**Session ID:** TBD (likely `2025-11-XX-bpd-hardware-validation`)
**Estimated Duration:** 4-6 hours
**Prerequisites:** Platform testing framework complete ✅

---

## Primary Objectives

### 1. Build Hardware Deployment and Debug Tools
- [ ] `scripts/moku-deploy.py` - Deploy bitstreams + configurations to real Moku hardware
- [ ] `scripts/moku-debug.py` - BPD operational tool with FORGE control and debug bus monitoring
- [ ] Supporting libraries:
  - [ ] `scripts/lib/bpd_controller.py` - FORGE control + register API
  - [ ] `scripts/lib/bpd_decoder.py` - 14-bit hierarchical voltage decoder

### 2. Validate BPD-Debug-Bus Design (Simulation + Hardware)
- [ ] Run platform routing integration test (simulation baseline)
- [ ] Deploy BPD to real Moku hardware
- [ ] Capture debug bus signals with oscilloscope (hardware validation)
- [ ] Compare simulation vs hardware results
- [ ] Identify and document any discrepancies

### 3. Iterate on Overall Design
- [ ] Fix any bugs discovered in hardware testing
- [ ] Refine FORGE initialization sequence if needed
- [ ] Validate hierarchical voltage encoding matches simulation
- [ ] Document hardware-specific quirks or timing issues

---

## Context to Load

### Tier 1 (Essential - Load First)
**Architecture:**
- `CLAUDE.md` - Monorepo architecture, FORGE control scheme
- `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md` - Complete FORGE spec
- `Obsidian/Project/BPD-Two-Tool-Architecture.md` - BPD deployment architecture

**Platform Testing (Reference):**
- `libs/forge-vhdl/cocotb_test/platform/README.md` - Platform testing guide
- `libs/forge-vhdl/cocotb_test/test_platform_routing_integration.py` - Baseline test

**Previous Session:**
- `Obsidian/Project/Sessions/2025-11-07-cocotb-platform-testing/session-summary.md` - What we just built
- `Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/PLAN.md` - Original tooling plan

### Tier 2 (Design/Integration)
**Deployment Specs:**
- `examples/basic-probe-driver/configs/bpd-deployment-setup1-dummy-dut.yaml` - Example config
- `examples/basic-probe-driver/configs/bpd-deployment-setup2-real-dut.yaml` - Production config

**Encoder/Decoder:**
- `libs/forge-vhdl/vhdl/components/forge_hierarchical_encoder.vhd` - Encoder implementation
- `Obsidian/Project/Handoffs/2025-11-06/handoff-6-hierarchical-encoder.md` - Encoding spec

**WIP Tools (if exists):**
- `wip/moku_go.py` - Foundation for moku-deploy.py (has discovery, caching, deployment)

### Tier 3 (Implementation - As Needed)
**VHDL Sources:**
- BPD main FSM (for understanding register interface)
- BPD shim layer (for register mapping)

**Test Infrastructure:**
- Platform test constants (for encoding parameters reference)

---

## Technical Approach

### Phase 1: Build moku-deploy.py (90 min)

**Goal:** Create stateless deployment tool with YAML support

**Starting Point:** `wip/moku_go.py` (if exists, otherwise from scratch)

**Key Features:**
1. **YAML Configuration Loading**
   - Parse MokuConfig YAML (device, slots, routing)
   - Support both JSON and YAML formats
   - Validate configuration structure

2. **Device Discovery**
   - Zeroconf/mDNS discovery (if available)
   - Manual IP address specification
   - Device caching (remember last-used devices)

3. **Deployment Operations**
   - Deploy bitstreams to slots
   - Configure routing matrix
   - Set initial Control Registers
   - Verify deployment success

**CLI Interface:**
```bash
# Discover devices
uv run python scripts/moku-deploy.py --discover

# Deploy configuration
uv run python scripts/moku-deploy.py --config bpd-deployment-setup2.yaml --ip 192.168.73.1

# Deploy with device name
uv run python scripts/moku-deploy.py --config bpd-deployment-setup2.yaml --device "Moku:Go-12345"
```

**Success Criteria:**
- Loads YAML configs correctly
- Can discover or connect to Moku devices
- Deploys bitstreams and routing
- Returns clear success/error messages

---

### Phase 2: Build moku-debug.py (90 min)

**Goal:** Create BPD-specific operational tool with FORGE control and debug monitoring

**Integration:** Can call moku-deploy.py or share deployment logic

**Key Features:**
1. **FORGE Control Sequence**
   - Initialize with 4-condition enable (CR0[31:29] + loader_done)
   - Arm/disarm BPD
   - Configure trigger voltage/duration
   - Configure intensity voltage/duration
   - Monitor status registers

2. **Debug Bus Monitoring**
   - Connect to oscilloscope slot (Slot 1)
   - Capture InputA (routed debug bus signal)
   - Decode hierarchical voltage encoding
   - Display FSM state and status flags in real-time

3. **Interactive Mode**
   - Live status display (curses/rich UI)
   - Manual control register updates
   - Oscilloscope trace visualization (optional)

**CLI Interface:**
```bash
# Deploy and enter debug mode
uv run python scripts/moku-debug.py --deploy bpd-deployment-setup2.yaml --ip 192.168.73.1

# Connect to already-deployed BPD
uv run python scripts/moku-debug.py --ip 192.168.73.1

# One-shot status read
uv run python scripts/moku-debug.py --ip 192.168.73.1 --status

# Capture debug bus (N samples)
uv run python scripts/moku-debug.py --ip 192.168.73.1 --capture 1000
```

**Success Criteria:**
- FORGE initialization works correctly
- Can arm/disarm BPD via Control Registers
- Captures debug bus signals from oscilloscope
- Decodes hierarchical encoding accurately
- Displays FSM state and status flags

---

### Phase 3: Simulation vs Hardware Validation (60-90 min)

**Goal:** Run same test in simulation and hardware, compare results

**Approach:**

1. **Baseline (Simulation):**
   ```bash
   cd libs/forge-vhdl
   uv run python cocotb_test/run.py platform_routing_integration
   # Capture: State progression 0→15, encoding values
   ```

2. **Deploy to Hardware:**
   ```bash
   uv run python scripts/moku-deploy.py \
     --config examples/basic-probe-driver/configs/bpd-deployment-setup2.yaml \
     --ip 192.168.73.1
   ```

3. **Capture Debug Bus (Hardware):**
   ```bash
   uv run python scripts/moku-debug.py \
     --ip 192.168.73.1 \
     --capture 125  # Same sample count as simulation
   ```

4. **Compare Results:**
   - State progression match? (0→15 in both)
   - Encoding values match? (hierarchical voltage levels)
   - Timing match? (125 samples @ 125 MHz = 1μs)
   - Any hardware-specific glitches or issues?

**Expected Outcomes:**

**Scenario A: Perfect Match ✅**
- Simulation and hardware results identical
- Validates platform simulator accuracy
- High confidence in simulation-based development

**Scenario B: Minor Differences 🟡**
- Timing slight off (clock frequency variation)
- Voltage levels slightly different (ADC/DAC noise)
- Document discrepancies, adjust simulator if needed

**Scenario C: Major Differences ❌**
- FSM behavior different (bug in VHDL or simulation)
- Encoding broken (bug in encoder or decoder)
- Debug and fix, re-test

**Deliverable:** Comparison report documenting simulation vs hardware validation

---

## Prerequisites

### Hardware Requirements
- [ ] Moku:Go device available
- [ ] Network connectivity to Moku device
- [ ] BPD bitstream compiled and ready

### Software Requirements
- [ ] Moku API installed (`pip install moku` or equivalent)
- [ ] Python 3.10+ environment
- [ ] YAML parser (`pyyaml`)

### Knowledge Requirements
- [ ] FORGE control scheme (CR0[31:29])
- [ ] Hierarchical voltage encoding (state × 200 + status)
- [ ] MokuConfig YAML structure
- [ ] BPD register mapping (from BPD-RTL.yaml)

---

## Expected Deliverables

### Code
1. **scripts/moku-deploy.py** (~200-300 lines)
   - YAML configuration loading
   - Device discovery and connection
   - Bitstream deployment
   - Routing configuration

2. **scripts/moku-debug.py** (~300-400 lines)
   - FORGE control interface
   - Debug bus capture and decoding
   - Status monitoring
   - Interactive mode (optional)

3. **scripts/lib/bpd_controller.py** (~150-200 lines)
   - FORGE initialization sequence
   - Register read/write API
   - High-level control methods

4. **scripts/lib/bpd_decoder.py** (~100-150 lines)
   - Hierarchical voltage decoder
   - State and status extraction
   - Voltage-to-digital conversion

### Documentation
1. **scripts/README.md**
   - Tool overview and architecture
   - Installation instructions
   - Usage examples
   - Troubleshooting guide

2. **Comparison Report** (Markdown or text file)
   - Simulation baseline results
   - Hardware test results
   - Discrepancy analysis
   - Recommendations for simulator refinements

### Session Archive
1. **Session summary** (accomplishments, issues, next steps)
2. **Commits log** (git history)
3. **Key decisions** (technical choices made)
4. **Next session plan** (follow-up work)

---

## Success Metrics

### Minimum Viable Product (4 hours)
- [ ] moku-deploy.py deploys BPD to hardware
- [ ] moku-debug.py can arm/disarm BPD
- [ ] Debug bus capture works (raw voltage values)
- [ ] Basic hierarchical decoding implemented

### Stretch Goals (6 hours)
- [ ] Interactive debug mode with live display
- [ ] Complete simulation vs hardware comparison
- [ ] Automated test suite (same tests in sim + hardware)
- [ ] Performance optimization

---

## Potential Risks and Mitigations

### Risk 1: Hardware Not Available
**Mitigation:** Focus on tool development with dry-run mode, defer hardware testing to next session

### Risk 2: Moku API Unfamiliar
**Mitigation:** Start with simple examples, use existing wip/moku_go.py as reference

### Risk 3: Debug Bus Not Working
**Mitigation:** Fall back to simulation-only validation, debug VHDL in next session

### Risk 4: Hierarchical Encoding Broken
**Mitigation:** Use raw voltage values first, add decoding later

---

## Context from Previous Session

**What We Just Built (2025-11-07-cocotb-platform-testing):**
- Complete platform testing framework (Phase 1+2)
- 2-slot routing integration test (Slot2OutD → Slot1InA)
- Oscilloscope simulator with hierarchical decoding
- BPD-Debug-Bus pattern validated in simulation

**Key Technical Decisions:**
- Signal handle wiring (not value copying) for routing
- Type-agnostic 16-bit bus design
- External channel priority in oscilloscope

**Test Results:**
- 5 test modules, 14+ P1 tests passing
- Routing integration complete (2/2 tests passing)
- Hierarchical encoding/decoding validated

**Files to Reference:**
- `test_platform_routing_integration.py` - Baseline test pattern
- `oscilloscope.py` - Capture and decode logic
- `simulation_backend.py` - Routing setup pattern

---

## Next Steps After This Session

**If Hardware Validation Succeeds:**
1. Return to BPD FSM debugging (known bug from earlier session)
2. Implement P2/P3 platform tests (trigger modes, multi-channel)
3. Cross-platform testing (Moku:Lab/Pro validation)

**If Hardware Validation Fails:**
1. Debug VHDL issues (FSM, encoder, FORGE control)
2. Refine simulator to better match hardware
3. Iterate on BPD design based on hardware findings

**Long-term:**
1. Type system refinements (std_logic_reg, ±5V types in BPD-RTL.yaml)
2. Phase 3 platform testing (advanced features)
3. Production BPD deployment and field testing

---

**Ready to Start:** Load context files from Tier 1, review previous session summary, begin Phase 1!

**Estimated Session Duration:** 4-6 hours
**Expected Outcome:** Working deployment and debug tools, initial hardware validation results
