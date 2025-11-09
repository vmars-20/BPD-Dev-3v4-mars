# Phase 2 Continuation Prompt - CocoTB Platform Testing

**Copy this prompt into a new Claude Code window to start Phase 2:**

---

## Context

I'm continuing work on the CocoTB Platform Testing Framework. **Phase 1 is 100% complete** and tagged as `platform-testing-phase1-complete` (commit `6868946`).

**Branch:** `sessions/2025-11-07-cocotb-platform-testing`
**Session Plan:** `@Obsidian/Project/Sessions/2025-11-07-cocotb-platform-testing/2025-11-07-cocotb-platform-test-PLAN.md`

## Phase 1 Achievements (Quick Reference)

✅ **Platform Infrastructure:**
- Network CR API with 200ms delays (`network_cr.py`)
- Simulation backend coordinator (`simulation_backend.py`)
- Oscilloscope simulator (`oscilloscope.py`)

✅ **Validation Tests:**
- FORGE control scheme tests (2 test cases)
- Counter PoC with 3-layer architecture (3/3 P1 tests passing)
- BPD deployment YAML integration (5/5 P1 tests passing)

✅ **Documentation:**
- Quick-start guide: `libs/forge-vhdl/cocotb_test/platform/README.md` (440 lines)
- Session plan with complete progress tracking

## Phase 2: BPD Deployment Validation (Start Here!)

**Goals:**
1. **Expand deployment tests** (P2/P3 levels)
   - Edge cases for YAML parsing
   - Multi-configuration testing
   - Error handling validation

2. **Simulate oscilloscope captures**
   - Wire up actual signal flow
   - Test BPD-Debug-Bus routing (Slot2OutD → Slot1InA)
   - Validate hierarchical voltage encoding

3. **Test routing matrix with signals**
   - Validate 2-slot routing (setup1: dummy-DUT, setup2: real-DUT)
   - Simulate signal propagation through routing
   - Test routing matrix reconfiguration

4. **Validate network CR updates with BPD registers**
   - Test CR0-CR15 updates with deployment configs
   - Validate control register persistence
   - Test concurrent CR updates across slots

## Quick Start Commands

```bash
# Check current branch and status
git status
git log --oneline -5

# View Phase 1 completion
git show platform-testing-phase1-complete --no-patch

# Review session plan
cat Obsidian/Project/Sessions/2025-11-07-cocotb-platform-testing/2025-11-07-cocotb-platform-test-PLAN.md

# Review quick-start docs
cat libs/forge-vhdl/cocotb_test/platform/README.md

# Run existing tests to validate baseline
cd libs/forge-vhdl
uv run python cocotb_test/run.py platform_bpd_deployment  # 5/5 P1 tests
uv run python cocotb_test/run.py platform_counter_poc      # 3/3 P1 tests
```

## Key Files to Review

1. **Session Plan:** `Obsidian/Project/Sessions/2025-11-07-cocotb-platform-testing/2025-11-07-cocotb-platform-test-PLAN.md`
2. **Platform README:** `libs/forge-vhdl/cocotb_test/platform/README.md`
3. **Deployment Test (P1):** `libs/forge-vhdl/cocotb_test/test_platform_bpd_deployment.py`
4. **Deployment YAMLs:**
   - `bpd-deployment-setup1-dummy-dut.yaml` (synthetic trigger)
   - `bpd-deployment-setup2-real-dut.yaml` (external trigger)

## Technical Context

**FORGE Control Scheme (CR0[31:29]):**
- `CR0[31]` = forge_ready (loader complete)
- `CR0[30]` = user_enable (user control)
- `CR0[29]` = clk_enable (clock gating)
- `global_enable = forge_ready AND user_enable AND clk_enable AND loader_done`

**BPD-Debug-Bus Routing:**
- Source: Slot2OutD (BPD custom instrument)
- Destination: Slot1InA (Oscilloscope)
- Encoding: 14-bit hierarchical voltage encoding (forge_hierarchical_encoder)

**Network CR Delays:**
- Realistic 200ms async delays for CR updates
- Simulates real MCC network behavior

## Recommended Approach for Phase 2

### Step 1: Expand P1 Tests → P2/P3
Start with `test_platform_bpd_deployment.py`:
- Add P2 tests (10-15 tests, edge cases)
- Add P3 tests (20-30 tests, comprehensive)
- Test error conditions (invalid YAML, bad routing)

### Step 2: Oscilloscope Signal Capture
Create `test_platform_oscilloscope_capture.py`:
- Test multi-channel capture setup
- Validate BPD-Debug-Bus signal routing
- Test sample rate configuration

### Step 3: Routing Matrix Validation
Expand routing tests:
- Test signal propagation Slot2OutD → Slot1InA
- Validate routing matrix updates
- Test slot-to-physical-port routing (Slot2OutA → OUT1)

### Step 4: Network CR Integration
Test full deployment workflow:
- Load YAML → Apply CRs → Validate DUT state
- Test concurrent CR updates (multi-slot)
- Validate CR persistence after routing changes

## Success Metrics for Phase 2

- [ ] P2/P3 deployment tests passing (15+ tests)
- [ ] Oscilloscope captures BPD-Debug-Bus signals
- [ ] Routing matrix functional with signal flow
- [ ] Network CR updates validated with both deployment YAMLs

## Questions for Me

1. Should I start with P2/P3 test expansion, or oscilloscope signal capture?
2. Do you want to test with real VHDL DUT (forge_counter), or behavioral models only?
3. Priority: breadth (more test cases) or depth (signal simulation)?

## Current Working Directory

Expected: `/Users/johnycsh/BPD-Dev`

**Let's continue where we left off! Ready to tackle Phase 2?** 🚀

---

**Pro tip:** After reviewing the session plan and README, start by running the existing P1 tests to validate your baseline, then choose your first Phase 2 objective.
