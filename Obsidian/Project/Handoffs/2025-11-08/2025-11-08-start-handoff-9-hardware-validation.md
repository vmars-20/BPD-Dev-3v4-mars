---
created: 2025-11-07
type: session-start-prompt
target-date: 2025-11-08
handoff: 9
priority: P1
---

# Session Start: Handoff 9 - Hardware Validation

**Date:** 2025-11-08
**Objective:** Validate hierarchical encoder output on Moku oscilloscope
**Prerequisites:** ✅ All complete (Handoffs 6, 7, 8, 8.5)

---

## Quick Context

We completed the full hierarchical encoder validation chain yesterday (2025-11-07):
- ✅ Design (Handoff 6)
- ✅ Implementation (forge_hierarchical_encoder.vhd)
- ✅ Component testing (Handoff 8) - 4/4 P1 tests passed
- ✅ Integration testing (Handoff 8.5) - 3/3 P1 tests passed
- ✅ FSM observer unification (unified decoder created)

**Today's Goal:** Validate on real Moku hardware with oscilloscope.

---

## Context Loading (Efficient)

### Tier 1 - Read These First (~5 min)

**Essential files (in order):**
1. `Obsidian/Project/Sessions/2025-11-07/session-summary.md` - Yesterday's work summary
2. `Obsidian/Project/Sessions/2025-11-07/next-session-plan.md` - Today's detailed plan
3. `Obsidian/Project/Handoffs/2025-11-07-handoff-9-hardware-validation.md` - Handoff spec

**Quick facts:**
- Hierarchical encoder: 200 digital units/state, status offset, fault sign flip
- Expected voltages: 0mV (IDLE), ~30mV (ARMED), ~61mV (FIRING), ~91mV (COOLDOWN)
- Fault detection: Negative voltage (e.g., -61mV)
- Decoder: `tools/decoder/hierarchical_decoder.py` (production-ready)

### Tier 2 - Load If Needed

- `CLAUDE.md` - FORGE architecture reference
- `libs/forge-vhdl/CLAUDE.md` - Hierarchical encoder design details
- Test reports from Handoffs 8 & 8.5

---

## Today's Tasks

**See full plan in:** `Obsidian/Project/Sessions/2025-11-07/next-session-plan.md`

### Phase 1: Preparation (15 min)
1. Check Moku platform availability
2. Review hardware setup requirements
3. Confirm oscilloscope access

### Phase 2: Deployment (30 min)
1. Upload BPD VHDL to Moku
2. Configure MCC CustomInstrument
3. Verify deployment successful
4. Configure oscilloscope (OutputD, ±5V range)

### Phase 3: Validation (60 min)
1. Run BPD through state transitions (IDLE→ARMED→FIRING→COOLDOWN)
2. Capture oscilloscope measurements
3. Validate voltage levels match simulation
4. Test decoder with real measurements
5. Capture screenshots/waveforms

### Phase 4: Documentation (30 min)
1. Create hardware validation test report
2. Document results vs expectations
3. Note any deviations
4. Mark Handoff 9 complete

### Phase 5: Wrap-Up (15 min)
1. Commit documentation
2. Update session summary (if continuing multi-day work)
3. Push to remote

**Total Estimated Time:** 2.5 hours

---

## Expected Results

### Oscilloscope Should Show

**State transitions (voltage stairstep):**
```
IDLE (0)       → 0 mV
ARMED (1)      → ~30 mV   (200 units * 5V / 32768)
FIRING (2)     → ~61 mV   (400 units * 5V / 32768)
COOLDOWN (3)   → ~91 mV   (600 units * 5V / 32768)
FAULT          → Negative voltage (sign flip)
```

**Decoder validation:**
```python
from hierarchical_decoder import decode_oscilloscope_voltage

# Oscilloscope reads ~61mV
result = decode_oscilloscope_voltage(61.0)
print(result['state'])  # Should be 2 (FIRING)
print(result['fault'])  # Should be False
```

---

## Success Criteria

**Hardware Validation:**
- [ ] BPD deploys successfully to Moku
- [ ] OutputD visible on oscilloscope
- [ ] Voltage levels match simulation (within ±10% tolerance)
- [ ] State transitions visible as clean voltage steps
- [ ] Fault detection works (negative voltage observed)

**Decoder Validation:**
- [ ] Python decoder correctly extracts state from oscilloscope measurements
- [ ] Status extraction works
- [ ] Fault flag detected correctly

**Documentation:**
- [ ] Hardware test report created (template: similar to Handoff 8.5)
- [ ] Oscilloscope screenshots captured
- [ ] Handoff 9 marked complete
- [ ] Committed and pushed

---

## Potential Issues & Solutions

### Issue: Platform Access
**Problem:** Moku not available
**Solution:** Use simulation mode OR defer hardware testing, document simulation validation

### Issue: Voltage Mismatch
**Problem:** Measured voltages ≠ simulation
**Diagnosis:** Check platform voltage range (±5V vs ±10V), DAC calibration
**Solution:** Adjust decoder `platform_range_mv` parameter

### Issue: Noisy Transitions
**Problem:** Voltage glitches during transitions
**Diagnosis:** Clock domain crossing, metastability
**Solution:** May need output register buffering

---

## Files to Create

**New:**
- `Obsidian/Project/Test-Reports/2025-11-08-handoff-9-hardware-validation-results.md`
- `Obsidian/Project/Test-Reports/oscilloscope-screenshots/` (directory for images)

**Update:**
- `Obsidian/Project/Handoffs/2025-11-07-handoff-9-hardware-validation.md` (mark complete)

---

## Session Prompt for Claude

```
I'm starting Handoff 9 - Hardware Validation for the hierarchical encoder.

Context:
- Yesterday (2025-11-07) completed component + integration testing
- All simulation tests passed (Handoffs 8 & 8.5)
- Ready for real hardware validation on Moku oscilloscope

Please:
1. Read Obsidian/Project/Sessions/2025-11-07/session-summary.md
2. Read Obsidian/Project/Sessions/2025-11-07/next-session-plan.md
3. Read Obsidian/Project/Handoffs/2025-11-07-handoff-9-hardware-validation.md

Then help me:
1. Check Moku platform availability
2. Deploy BPD to Moku (if platform available)
3. Configure oscilloscope for OutputD observation
4. Run state transitions and validate voltage levels
5. Test decoder with real measurements
6. Document results

Expected duration: 2-3 hours

Reference decoder: tools/decoder/hierarchical_decoder.py
Expected voltages: 0mV, ~30mV, ~61mV, ~91mV for states 0-3
```

---

## Architectural Context

**Why This Matters:**
- Completes full validation chain: Design → Component → Integration → Hardware ✅
- Proves hierarchical encoder works on real platform
- Validates decoder against actual oscilloscope measurements
- Production-ready confirmation for deployment

**After Handoff 9:**
- Hierarchical encoder fully validated
- Ready for production use
- Can proceed to BPD FSM debugging (Handoff 5 - deferred)
- Or: Additional probe development, P2/P3 testing

---

## Git Status Check

```bash
# Verify clean state
git status  # Should show: "working tree clean"

# Check we're on correct branch
git branch  # Should show: * BPD-Dev-main

# See yesterday's work
git log --oneline -5
```

**Expected:** 21 commits from 2025-11-07, last commit is session wrap-up

---

## Notes

**Hardware Dependency:** This handoff requires physical Moku platform access.

**Fallback Plan:** If hardware unavailable, document simulation validation as interim step and create hardware validation checklist for future.

**Time Box:** Maximum 3 hours. If validation fails, document blockers and create debugging handoff for follow-up.

---

**Ready to Start:** Yes ✅
**Prerequisites:** All complete ✅
**Estimated Duration:** 2-3 hours
**Priority:** P1 (Hardware validation)
