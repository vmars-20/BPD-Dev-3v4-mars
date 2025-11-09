---
date: 2025-11-07
type: next-session-plan
target-date: 2025-11-08
priority: P1
estimated-duration: 2-3 hours
---

# Next Session Plan: 2025-11-08

**Primary Objective:** Handoff 9 - Hardware Validation with Moku Oscilloscope

**Prerequisites:** ✅ All complete
- Handoff 6: Hierarchical encoder design ✓
- Handoff 7: CocoTB test design ✓
- Handoff 8: Component testing (P1 tests passed) ✓
- Handoff 8.5: Integration testing (BPD validated) ✓
- Unified decoder: Production-ready ✓

---

## Session Starting Point

### Context to Load (Tier 1 - Quick Reference)

**Essential files to read first:**
1. `llms.txt` (root) - Repository structure
2. `Obsidian/Project/Sessions/2025-11-07/session-summary.md` (this session)
3. `Obsidian/Project/Handoffs/2025-11-07-handoff-9-hardware-validation.md` - Next handoff spec

**Quick catch-up:**
- Hierarchical encoder implemented and validated in simulation
- BPD integration confirmed through CocoTB tests
- Ready for real hardware oscilloscope observation

### Git Status
- Working tree: Clean ✓
- Branch: `BPD-Dev-main`
- Remote: Up to date with origin

---

## Primary Task: Handoff 9 - Hardware Validation

### Objective
Validate hierarchical encoder output on actual Moku oscilloscope, confirm voltage levels and state transitions visible in hardware.

### Handoff Document
**Location:** `Obsidian/Project/Handoffs/2025-11-07-handoff-9-hardware-validation.md`

**Key sections:**
- Hardware setup requirements
- Oscilloscope configuration
- Expected voltage levels
- Validation procedure
- Success criteria

### Prerequisites (All Complete ✅)
1. ✅ forge_hierarchical_encoder.vhd implemented
2. ✅ BPD_forge_shim integrates encoder
3. ✅ CustomWrapper exports OutputD
4. ✅ Decoder validated in simulation
5. ✅ Component tests passed (Handoff 8)
6. ✅ Integration tests passed (Handoff 8.5)

---

## Expected Tasks

### Task 1: Review Hardware Setup
**Files to check:**
- Moku platform connection status
- BPD deployment configuration
- Oscilloscope channel mapping

**Action:**
- Verify Moku:Go/Lab/Pro platform available
- Confirm oscilloscope access
- Check deployment readiness

### Task 2: Deploy BPD to Moku Platform
**Files involved:**
- VHDL sources from `examples/basic-probe-driver/vhdl/`
- MCC synthesis outputs from previous tests
- Deployment manifest

**Action:**
- Upload VHDL to Moku platform
- Configure MCC CustomInstrument
- Verify deployment successful

### Task 3: Configure Oscilloscope
**Expected configuration:**
- Channel: OutputD (debug channel)
- Voltage range: ±5V
- Time base: Appropriate for FSM transitions
- Trigger: On state transitions (if possible)

**Reference values (from simulation):**
```
STATE_IDLE (0)     → 0 mV
STATE_ARMED (1)    → ~30 mV
STATE_FIRING (2)   → ~61 mV
STATE_COOLDOWN (3) → ~91 mV
FAULT              → Negative voltage (sign flip)
```

### Task 4: Run FSM Through States
**Action:**
- Trigger BPD state transitions via Control Registers
- Observe OutputD on oscilloscope
- Capture screenshots/waveforms
- Validate voltage levels match simulation

**Expected behavior:**
- Voltage stairstep: 0mV → 30mV → 61mV → 91mV
- Fault: Negative voltage (e.g., -61mV during FIRING fault)
- Transitions clean (no glitches)

### Task 5: Validate Decoder
**Action:**
- Capture oscilloscope measurements (mV)
- Use `tools/decoder/hierarchical_decoder.py` to decode
- Verify decoded state matches actual FSM state
- Confirm status extraction works

**Python usage:**
```python
from hierarchical_decoder import decode_oscilloscope_voltage

# Oscilloscope reads ~61mV
result = decode_oscilloscope_voltage(61.0)
print(result['state'])  # Should be 2 (FIRING)
print(result['fault'])  # Should be False
```

### Task 6: Document Results
**Create:**
- Hardware validation test report
- Oscilloscope screenshots
- Voltage measurement table
- Comparison: simulation vs hardware

**Template:** Similar to Handoff 8.5 test report

---

## Success Criteria

### Hardware Validation ✅
- [ ] BPD deploys successfully to Moku platform
- [ ] OutputD visible on oscilloscope
- [ ] Voltage levels match simulation (within tolerance)
- [ ] State transitions visible as voltage steps
- [ ] Fault detection works (negative voltage)

### Decoder Validation ✅
- [ ] Python decoder correctly extracts state from oscilloscope measurements
- [ ] Status extraction works
- [ ] Fault flag detected correctly

### Documentation ✅
- [ ] Hardware test report created
- [ ] Screenshots captured
- [ ] Handoff 9 marked complete
- [ ] Committed and pushed

---

## Potential Issues

### Issue 1: Platform Access
**Problem:** Moku platform not available
**Workaround:** Use Moku simulation mode (if available)
**Alternative:** Defer hardware testing, document simulation validation

### Issue 2: Voltage Level Mismatch
**Problem:** Measured voltages don't match simulation
**Diagnosis:**
- Check platform voltage range (±5V vs ±10V)
- Verify DAC calibration
- Check for voltage scaling in MCC

**Solution:** Adjust decoder `platform_range_mv` parameter

### Issue 3: Noisy Transitions
**Problem:** Voltage transitions show glitches
**Diagnosis:**
- Check clock domain crossing (if any)
- Verify registered outputs (should be clean)
- Check for metastability

**Solution:** May need output register buffering

---

## Context Management

### Tier 1 (Load First)
- Session summary (this file's parent: session-summary.md)
- Handoff 9 specification
- Root llms.txt

### Tier 2 (Load If Needed)
- `CLAUDE.md` - FORGE architecture reference
- `libs/forge-vhdl/CLAUDE.md` - Hierarchical encoder design
- `tools/decoder/hierarchical_decoder.py` - Decoder implementation

### Tier 3 (Load For Debugging)
- BPD VHDL source files
- Test reports from Handoff 8/8.5
- CustomWrapper implementation

**Token Budget:** Start fresh (~25k tokens used for Tier 1+2)

---

## Recommended Session Flow

### Phase 1: Preparation (15 min)
1. Read session summary from 2025-11-07
2. Load Handoff 9 specification
3. Review hardware setup requirements
4. Check Moku platform availability

### Phase 2: Deployment (30 min)
1. Upload VHDL to Moku platform
2. Configure MCC CustomInstrument
3. Verify deployment
4. Configure oscilloscope

### Phase 3: Validation (60 min)
1. Run BPD through state transitions
2. Capture oscilloscope measurements
3. Validate voltage levels vs simulation
4. Test decoder with real measurements
5. Capture screenshots/data

### Phase 4: Documentation (30 min)
1. Create hardware validation test report
2. Document results vs expectations
3. Note any deviations or issues
4. Mark Handoff 9 complete

### Phase 5: Wrap-Up (15 min)
1. Commit documentation
2. Update session summary
3. Push to remote
4. Identify next steps (if any)

**Total Estimated Time:** 2.5 hours

---

## Architectural Stopping Points

**After Handoff 9:**
- Hardware validation complete
- Full validation chain: Design → Component Test → Integration Test → Hardware ✓
- Hierarchical encoder production-ready for deployment

**Possible Next Steps:**
1. BPD FSM debugging (Handoff 5 - deferred earlier)
2. Additional probe development
3. Performance optimization
4. Extended CocoTB tests (P2/P3 levels)

---

## Questions to Resolve

**Before starting:**
1. Is Moku platform accessible?
2. Which platform (Go/Lab/Pro)?
3. Is oscilloscope configured and ready?
4. Do we have deployment permissions?

**During session:**
1. Are voltage levels within expected tolerance?
2. Do we need to adjust decoder parameters?
3. Should we capture extended waveforms for documentation?

---

## Files to Create/Update

**New files:**
- `Obsidian/Project/Test-Reports/2025-11-08-handoff-9-hardware-validation-results.md`
- `Obsidian/Project/Test-Reports/oscilloscope-screenshots/` (directory)

**Update files:**
- `Obsidian/Project/Handoffs/2025-11-07-handoff-9-hardware-validation.md` (mark complete)
- `CLAUDE.md` (if any architecture notes from hardware testing)

**Commit:**
- Hardware validation results
- Oscilloscope data
- Handoff 9 completion

---

## Session Health Checklist

**Before ending session:**
- [ ] All work committed and pushed
- [ ] Documentation complete
- [ ] Handoff status updated
- [ ] Next session plan created (if continuing)
- [ ] Working tree clean

**Token management:**
- Load Tier 1 docs first
- Only load source code if debugging needed
- Use Tier 2 docs for reference
- Keep <100k tokens in context

---

## Fallback Plan

**If hardware unavailable:**
1. Document simulation validation as interim step
2. Create hardware validation checklist for future
3. Move to alternate work (BPD FSM debugging, P2/P3 tests)
4. Update Handoff 9 with "blocked - hardware access" status

**If validation fails:**
1. Debug systematically (voltage scaling, DAC config, etc.)
2. Document failures and hypotheses
3. Create debugging handoff for follow-up
4. Don't force completion - document blockers clearly

---

## Key Contacts / Resources

**Documentation:**
- Handoff 9 spec: `Obsidian/Project/Handoffs/2025-11-07-handoff-9-hardware-validation.md`
- Previous test results: `Obsidian/Project/Test-Reports/2025-11-07-handoff-8*`
- Decoder: `tools/decoder/hierarchical_decoder.py`

**VHDL Sources:**
- Encoder: `libs/forge-vhdl/vhdl/debugging/forge_hierarchical_encoder.vhd`
- BPD Shim: `examples/basic-probe-driver/vhdl/BPD_forge_shim.vhd`
- CustomWrapper: `examples/basic-probe-driver/vhdl/CustomWrapper_bpd_forge.vhd`

**Reference Values:**
- Simulation test results: Handoff 8 test report
- Integration test results: Handoff 8.5 test report
- Voltage calculations: Handoff 6 design doc

---

**Session Goal:** Complete hardware validation, close out hierarchical encoder validation chain

**Success Metric:** Oscilloscope shows expected voltage levels matching simulation

**Time Box:** 2-3 hours maximum

**Ready to Start:** Yes ✅ (all prerequisites complete)
