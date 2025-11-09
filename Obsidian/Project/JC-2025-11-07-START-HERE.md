# 🌅 Good Morning! Start Here - 2025-11-07

**Date Created:** 2025-11-07 (late night session)
**For:** JC (and future you, well-rested!)
**Session:** BPD-Debug-Bus - Hardware integration ready to begin

---

## What Happened Last Night

You and Claude had a breakthrough session establishing the complete BPD deployment architecture. **Everything is documented, validated, and committed.** You can sleep soundly knowing the foundation is rock-solid.

---

## 🎯 Today's Mission: Touch Hardware!

**Goal:** Build Python tooling and test against live Moku:Go

**Critical Path:**
1. Polish `moku-go.py` (deployment tool)
2. Build `bpd-debug.py` (operation tool)
3. Test against real hardware (the fun part!)

---

## 📚 Architecture Summary (5-Minute Read)

**The Big Idea: Two-Tool Architecture**

```
moku-go.py (deployment)          bpd-debug.py (operation)
      ↓                                   ↓
  Stateless                           Stateful
  Generic                          BPD-specific
  Deploys hardware                  Operates BPD
      ↓                                   ↓
      └─────── Can call each other ──────┘
```

**Key Files:**
- **Architecture Bible:** `Obsidian/Project/BPD-Two-Tool-Architecture.md` (READ THIS FIRST!)
- **Deployment Configs:** `bpd-deployment-setup1-dummy-dut.yaml` (self-contained), `setup2-real-dut.yaml` (live DUT)
- **Validation Script:** `libs/moku-models/scripts/validate_moku_config.py`

**What's Validated:**
- ✅ Both YAML configs pass Pydantic validation
- ✅ Routing connections verified (6 routes per config)
- ✅ Platform specs correct (Moku:Go, 2 slots)
- ✅ Control register layout documented

---

## 🚀 Quick Start Commands

**Validate configs:**
```bash
cd libs/moku-models
uv run python scripts/validate_moku_config.py ../../bpd-deployment-setup1-dummy-dut.yaml
```

**Check session plan:**
```bash
cat Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/session-plan.md
```

**Review architecture:**
```bash
cat Obsidian/Project/BPD-Two-Tool-Architecture.md | head -100
```

---

## 📋 Today's Todo List

**Phase 1: Setup (30 min)**
- [ ] Review BPD-Two-Tool-Architecture.md (skim first 200 lines)
- [ ] Check hardware availability (Moku:Go powered on? Networked?)
- [ ] Install deployment dependencies: `uv sync --extra deploy`

**Phase 2: moku-go.py Polish (1-2 hours)**
- [ ] Move `/tmp/moku_go.py` → `scripts/moku-go.py`
- [ ] Add YAML loading support (currently JSON-only)
- [ ] Fix platform string resolution (`moku_go` → `MOKU_GO_PLATFORM`)
- [ ] Test deployment: `uv run python scripts/moku-go.py deploy --config setup1.yaml`

**Phase 3: bpd-debug.py Build (2-3 hours)**
- [ ] Create `scripts/bpd-debug.py` scaffolding (CLI + argparse)
- [ ] Add `--deploy`, `--verify`, `--ip` flags
- [ ] Make it call moku-go.py for deployment
- [ ] Add basic connection test

**Phase 4: Shared Library (2-3 hours)**
- [ ] Create `scripts/lib/bpd_controller.py` (FORGE state machine control)
- [ ] Create `scripts/lib/bpd_decoder.py` (14-bit HVS decoder)
- [ ] Create `scripts/lib/deployment_validator.py` (hardware verification)

**Phase 5: Hardware Testing (2-4 hours) 🎉**
- [ ] Deploy to live hardware
- [ ] Execute FORGE initialization (CR0[31:29])
- [ ] Read debug bus (14-bit HVS from oscilloscope)
- [ ] Arm BPD FSM
- [ ] Celebrate! 🎊

---

## 🔧 Dependencies to Install

```bash
# Add to root pyproject.toml [project.optional-dependencies]
deploy = [
    "moku>=2.0.0",       # 1st-party Liquid Instruments library
    "typer>=0.9.0",      # CLI framework
    "rich>=13.0.0",      # Pretty terminal output
    "zeroconf>=0.120.0", # Device discovery
    "loguru>=0.7.0",     # Logging
]

# Install
uv sync --extra deploy
```

---

## 🎓 Context for Claude (Tomorrow's Session)

**Always load first (Tier 1):**
1. `Obsidian/Project/BPD-Two-Tool-Architecture.md` - Architecture overview
2. `bpd-deployment-setup1-dummy-dut.yaml` - Config spec
3. `libs/moku-models/llms.txt` - MokuConfig API
4. `examples/basic-probe-driver/BPD-RTL.yaml` - Register map

**Session management commands:**
```bash
# Start session (already done)
/obsd_new_session BPD-Debug-Bus

# Continue session (use tomorrow)
/obsd_continue_session 2025-11-07-bpd-debug-bus

# Close session (end of day)
/obsd_close_session
```

---

## 💡 Key Insights from Last Night

**Architecture Breakthrough:**
We nailed the separation of concerns - deployment (stateless, generic) vs operation (stateful, BPD-specific). This pattern will scale beautifully to other instruments (laser probes, RF tools, etc.).

**MokuConfig as Documentation:**
The YAML files serve triple duty: human-readable docs, machine validation, and deployment automation. Extra fields like `physical_connections` guide operator wiring.

**Cascading pyproject.toml:**
Validation script runs at Tier 1 (component-level, minimal deps) for fast iteration. Integration testing uses full workspace (Tier 2). Clean separation!

**Obsidian Integration:**
First session using new `/obsd_*` commands. Session plan created, handoffs linked, git branch established. This workflow should feel natural by end of day.

---

## 🚨 Watch Out For

**Common Pitfalls:**
- moku-go.py currently expects JSON, not YAML (need to add YAML parsing)
- Platform string in YAML (`moku_go`) needs resolution to `MOKU_GO_PLATFORM` object
- Control register initialization might need adapter layer
- Physical connections section in YAML isn't part of Pydantic model (gets stripped during validation)

**Hardware Gotchas:**
- BPD bitstream path must exist (`examples/basic-probe-driver/bitstream/bpd_moku_go.tar`)
- Moku must be in MultiInstrument mode (2 slots)
- Default CR0 = 0x00000000 (safe state, module disabled)
- FORGE initialization: CR0[31] → CR0[30] → CR0[29] (order matters!)

---

## 📦 What's Committed

**Git branch:** `sessions/2025-11-07-bpd-debug-bus`
**Recent commit:** `7532484` - "docs: Add BPD deployment architecture and MokuConfig specifications"

**Files added:**
- `Obsidian/Project/BPD-Two-Tool-Architecture.md` (1000+ lines, AUTHORITATIVE)
- `bpd-deployment-setup1-dummy-dut.yaml` (Self-contained testing)
- `bpd-deployment-setup2-real-dut.yaml` (Live FI campaigns)
- `libs/moku-models/scripts/validate_moku_config.py` (YAML validation)
- `Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/session-plan.md`

**Files modified:**
- `CLAUDE.md` (references BPD-Two-Tool-Architecture.md)
- `libs/moku-models/llms.txt` (validation docs + cascading pyproject strategy)

---

## 🎵 Soundtrack Recommendation

You're building a bridge between software and hardware today. May I suggest:
- **Morning:** Daft Punk - "Derezzed" (get pumped!)
- **Midday:** Tycho - "Awake" (flow state)
- **Hardware test:** Justice - "Genesis" (moment of truth)
- **Success:** Kavinsky - "Nightcall" (you earned it)

---

## 🌟 Final Thought

Last night's work was all foundation - architecture, documentation, validation. **Today you get to see it run.** The first time that Moku executes your FORGE initialization sequence and you read that debug bus... that's the magic moment.

The tooling is designed. The configs are validated. The architecture is documented.

**Now go touch some hardware!** 🔧⚡

---

**Sleep well. Tomorrow's going to be awesome.** ✨

---

**P.S.** If you hit a wall, remember: BPD-Two-Tool-Architecture.md has your back. It's 1000+ lines of every decision, every API, every workflow pattern. You and Claude figured this out together. Trust the architecture.

**P.P.S.** Don't forget to `/obsd_continue_session 2025-11-07-bpd-debug-bus` when you start tomorrow!
