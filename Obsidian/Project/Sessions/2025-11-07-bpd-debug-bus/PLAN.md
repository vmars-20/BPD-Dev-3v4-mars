---
session_id: 2025-11-07-bpd-debug-bus
created: 2025-11-07
type: implementation-plan
time_budget: 3-4 hours
approach: incremental
---

# Session Implementation Plan: BPD Debug Bus Toolchain

## Executive Summary

Build Python deployment and operation tools for BPD hardware testing using an incremental approach with quick validation cycles. Refining existing `wip/moku_go.py` and renaming to `moku-deploy.py` to avoid product name collision with Moku:Go.

**Key Deliverables:**
1. `scripts/moku-deploy.py` - Stateless deployment tool (generic)
2. `scripts/bpd-debug.py` - Stateful operation tool (BPD-specific)
3. Supporting libraries for BPD control and debug bus decoding

---

## Phase 0: Foundation (15 min) ✅

**Status:** IN PROGRESS

**Objective:** Clean workspace and establish baseline for development

**Deliverables (Contract):**
- ✅ Commit staged changes (BPD-Debug-Bus-Diagram.png move)
- ✅ Review wip/moku_go.py current state - DONE (file exists, has core functionality)
- 🔄 Create PLAN.md in session directory - IN PROGRESS
- ⏸️ Clean git workspace

**Key Findings from Review:**
- `wip/moku_go.py` exists with discovery, caching, and deployment features
- Currently uses JSON config files (needs YAML support)
- Has proper device resolution by name or IP
- Includes zeroconf discovery functionality

---

## Phase 1: Build moku-deploy.py (90 min)

**Status:** PENDING

**Objective:** Create refined deployment tool with YAML support

**Deliverables (Contract):**
1. Migrate `wip/moku_go.py` → `scripts/moku-deploy.py`
2. Add YAML loading support (currently JSON-only)
3. Fix platform string resolution (moku_go → MOKU_GO_PLATFORM)
4. Update imports to use correct paths
5. Device cache functionality (already present, needs testing)

**Implementation Tasks:**
```python
# Key changes needed:
1. Rename and move file to scripts/
2. Update app name from "moku-go" to "moku-deploy"
3. Add YAML support:
   - Load MokuConfig from YAML files
   - Support both JSON and YAML formats
4. Fix import paths for new location
5. Test with existing YAML configs:
   - bpd-deployment-setup1-dummy-dut.yaml
   - bpd-deployment-setup2-real-dut.yaml
```

**Quick Test (15 min):**
- Dry-run validation against both YAML configs
- Verify YAML loading works correctly
- Test device discovery (if network available)
- Verify cache persistence

**Success Criteria:**
- Tool runs without errors
- YAML configs load and validate
- Device cache works
- Ready for integration with bpd-debug.py

---

## Phase 2: Build bpd-debug.py Core (90 min)

**Status:** PENDING

**Objective:** Create BPD-specific operational tool

**Deliverables (Contract):**
1. `scripts/bpd-debug.py` - Main CLI tool
2. `scripts/lib/bpd_controller.py` - FORGE control + register API
3. `scripts/lib/bpd_decoder.py` - 14-bit HVS decoder
4. Integration with moku-deploy.py (--deploy flag)

### Module 1: bpd_controller.py
```python
class BPDController:
    # FORGE control scheme (CR0[31:29])
    def initialize_forge(self)  # Complete 4-condition enable

    # Operational control
    def arm_enable(self, enable: bool)
    def set_trigger_voltage(self, mv: int)
    def set_trigger_duration(self, ns: int)

    # Status monitoring
    def read_status(self) -> dict
```

### Module 2: bpd_decoder.py
```python
class BPDDebugDecoder:
    def decode_voltage(self, voltage: float) -> BPDState
    # Based on forge_hierarchical_encoder.vhd
    # 200 digital units per state
    # ~30mV steps on ±5V platform
```

### Module 3: bpd-debug.py
```python
# CLI interface:
uv run python scripts/bpd-debug.py --ip 192.168.73.1
uv run python scripts/bpd-debug.py --deploy config.yaml --ip 192.168.73.1
uv run python scripts/bpd-debug.py --verify config.yaml --ip 192.168.73.1
```

**Quick Test (15 min):**
- Unit tests for decoder (test vectors from Handoff 6)
- Dry-run mode validation
- Verify FORGE initialization sequence logic
- Test integration with moku-deploy.py

**Success Criteria:**
- FORGE control logic correct (CR0[31:29])
- Decoder matches hierarchical encoder spec
- CLI works in dry-run mode
- Integration with deployment tool functional

---

## Phase 3: Documentation & Commit (30 min)

**Status:** PENDING

**Objective:** Complete documentation and commit all work

**Deliverables (Contract):**
1. Update CLAUDE.md with tool usage instructions
2. Create `scripts/README.md` with tool documentation
3. Commit all tools with clear messages
4. Update session status

**Documentation Tasks:**
1. **CLAUDE.md Updates:**
   - Add "Common Workflows" section for new tools
   - Document moku-deploy.py usage
   - Document bpd-debug.py usage
   - Update "Development Status"

2. **scripts/README.md:**
   - Tool overview and architecture
   - Installation instructions
   - Usage examples
   - Troubleshooting guide

3. **Git Commits:**
   ```bash
   # Suggested commit structure:
   - "feat: Add moku-deploy.py deployment tool with YAML support"
   - "feat: Add bpd-debug.py operational tool with FORGE control"
   - "feat: Add BPD control and decoder libraries"
   - "docs: Add tool documentation and usage guides"
   ```

**Success Criteria:**
- Clear documentation for next session
- All code committed with descriptive messages
- Tools ready for hardware testing
- Session objectives achieved

---

## Timeline

| Phase | Duration | Start | End | Status |
|-------|----------|-------|-----|--------|
| Phase 0 | 15 min | 0:00 | 0:15 | IN PROGRESS |
| Phase 1 | 90 min | 0:15 | 1:45 | PENDING |
| Test 1 | 15 min | 1:45 | 2:00 | PENDING |
| Phase 2 | 90 min | 2:00 | 3:30 | PENDING |
| Test 2 | 15 min | 3:30 | 3:45 | PENDING |
| Phase 3 | 30 min | 3:45 | 4:15 | PENDING |

**Total:** ~4 hours 15 minutes

---

## Risk Mitigation

1. **Time Overrun:**
   - Focus on core functionality only
   - Defer advanced features to next session
   - Document TODOs for incomplete features

2. **Integration Issues:**
   - Use dry-run mode for testing
   - Mock hardware connections
   - Focus on logic correctness

3. **YAML Loading Problems:**
   - Support both JSON and YAML
   - Validate against existing configs
   - Clear error messages

---

## Success Metrics

### Minimum Viable Product (3 hours):
- [ ] moku-deploy.py works with YAML files
- [ ] bpd-debug.py has basic FORGE control
- [ ] Decoder implementation complete
- [ ] Dry-run testing successful

### Stretch Goals (if time permits):
- [ ] Full integration testing
- [ ] Advanced error handling
- [ ] Interactive REPL mode
- [ ] Performance optimization

---

## Next Session Planning

**If Hardware Available:**
- Test deployment on live Moku:Go
- Validate FORGE initialization sequence
- Monitor debug bus with oscilloscope
- Complete Handoff 9 (hardware validation)

**If Hardware Not Available:**
- Enhance error handling and validation
- Add more comprehensive tests
- Implement P2/P3 test levels
- Work on BPD FSM debugging

---

## Notes

- Using existing `wip/moku_go.py` as foundation saves significant time
- Renaming to `moku-deploy.py` avoids confusion with Moku:Go product
- Incremental approach allows for quick validation cycles
- Dry-run mode ensures tools work without hardware

**Session Goal:** Deliver working tools ready for hardware testing

**Success Indicator:** Both tools functional in dry-run mode with YAML support