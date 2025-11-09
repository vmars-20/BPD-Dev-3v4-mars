---
session_id: 2025-11-07-bpd-debug-bus
created: 2025-11-07
git_branch: sessions/2025-11-07-bpd-debug-bus
---

# Session Plan - 2025-11-07-bpd-debug-bus

## Session Scope
**Goal:** Build complete BPD deployment + operation toolchain for hardware integration testing

## Primary Objectives
- [x] Create authoritative MokuConfig YAML specifications (Setup1: Dummy-DUT, Setup2: Real-DUT)
- [x] Validate YAML configs against Pydantic models (libs/moku-models validation script)
- [x] Document BPD two-tool architecture (Obsidian/Project/BPD-Two-Tool-Architecture.md)
- [ ] Polish moku-go.py deployment tool (move from /tmp, add YAML support)
- [ ] Build bpd-debug.py operational tool (FORGE control + debug bus monitoring)
- [ ] Create shared library (scripts/lib/bpd_controller.py, bpd_decoder.py)
- [ ] Test against live hardware (kick the tires)

## Expected Tasks
1. ✅ Draft MokuConfig YAML files for both deployment scenarios
2. ✅ Create validation script (YAML → Pydantic model verification)
3. ✅ Document two-tool architecture in Obsidian (authoritative reference)
4. ✅ Update CLAUDE.md to reference architecture document
5. ✅ Commit architecture docs + configs to git
6. Move moku-go.py from /tmp → scripts/moku-go.py
7. Add YAML loading support to moku-go.py (currently JSON-only)
8. Fix platform string resolution (moku_go → MOKU_GO_PLATFORM)
9. Add control register initialization from MokuConfig
10. Create bpd-debug.py scaffolding (CLI interface)
11. Implement BPDController class (FORGE state machine control)
12. Implement BPDDebugDecoder class (14-bit HVS decoder)
13. Implement DeploymentValidator class (verify hardware vs YAML)
14. Integration: bpd-debug.py calls moku-go.py for deployment
15. Test deployment workflow against live Moku:Go hardware
16. Test FORGE initialization sequence (CR0[31:29])
17. Test debug bus monitoring (read 14-bit HVS from oscilloscope)

## Active Handoffs
**Linked handoffs** (symlinked to ./handoffs/):
- [[2025-11-07-handoff-9-hardware-validation.md]] - Hardware validation workflows
- [[2025-11-07-handoff-8.5-integration-testing.md]] - Integration testing patterns

**Note:** Most handoffs are from previous VHDL development work. This session transitions to hardware deployment + Python control layer.

## Architecture Reference
**Authoritative Document:** [[Obsidian/Project/BPD-Two-Tool-Architecture.md]]

**Key principles:**
- **Two-tool architecture** - moku-go.py (deployment) + bpd-debug.py (operation)
- **Clear separation** - Hardware lifecycle vs application lifecycle
- **Composable tools** - Usable independently or together
- **MokuConfig YAML** - Documentation + automation + validation

## Context to Load (Tier 1)
**Always load first:**
- [ ] BPD-Two-Tool-Architecture.md - Architecture overview
- [ ] bpd-deployment-setup1-dummy-dut.yaml - Self-contained testing config
- [ ] bpd-deployment-setup2-real-dut.yaml - Live FI campaign config
- [ ] libs/moku-models/llms.txt - MokuConfig API reference
- [ ] examples/basic-probe-driver/BPD-RTL.yaml - Register specification

**Tier 2 (if needed):**
- [ ] libs/moku-models/CLAUDE.md - Platform integration patterns
- [ ] libs/forge-vhdl/CLAUDE.md - VHDL serialization packages
- [ ] Obsidian/Project/Review/CASCADING_PYPROJECT_STRATEGY.md - Two-tier testing

## Success Criteria
- [x] MokuConfig YAML files validate against Pydantic models
- [x] Architecture documented in authoritative Obsidian note
- [x] CLAUDE.md references BPD-Two-Tool-Architecture.md
- [ ] moku-go.py successfully deploys to live hardware
- [ ] bpd-debug.py connects to deployed system
- [ ] FORGE initialization sequence executes correctly (CR0[31:29])
- [ ] Debug bus readable and decodable (14-bit HVS)
- [ ] Can arm BPD FSM via Python control layer
- [ ] Can monitor FSM state in real-time via oscilloscope

## Dependencies
**Python packages** (add to root pyproject.toml):
```toml
[project.optional-dependencies]
deploy = [
    "moku>=2.0.0",       # 1st-party Liquid Instruments library
    "typer>=0.9.0",      # CLI framework
    "rich>=13.0.0",      # Pretty terminal output
    "zeroconf>=0.120.0", # Device discovery
    "loguru>=0.7.0",     # Logging
]
```

**Installation:**
```bash
uv sync --extra deploy
```

## Hardware Requirements
- Moku:Go device powered on and networked
- BPD bitstream available (or ready to build)
- DS1120A probe (or equivalent) for physical testing
- External PSU (24-450V DC) for probe power

## Notes
**Architecture Breakthrough:** Session started with deployment tool discussion, evolved into clean two-tool architecture pattern:
- moku-go.py = stateless deployment (generic, reusable)
- bpd-debug.py = stateful operation (BPD-specific)

**Key innovation:** bpd-debug.py can call moku-go.py internally (--deploy flag) for integrated workflow, but tools remain independently usable.

**Documentation strategy:** Created authoritative Obsidian note instead of embedding in CLAUDE.md → cleaner separation, easier for both humans and AI to reference.

**Validation infrastructure:** libs/moku-models/scripts/validate_moku_config.py enables pre-deployment verification of YAML configs. Follows cascading pyproject.toml strategy (Tier 1: component testing).

**Next session should focus on:** Live hardware testing, FORGE state machine validation, debug bus decoder verification.
