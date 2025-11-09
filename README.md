# BPD-Dev-3v4 - Basic Probe Driver Development

> **Status:** 🚧 **Active WIP** - Current development repo for BPD v3.4 with FORGE architecture

**What:** Production development of Basic Probe Driver (BPD) custom instrument for Moku platforms using FORGE 3-layer architecture pattern.

**Why this repo exists:** Unified development environment with intentionally broken-out git submodules for clean dependency management and independent versioning of shared components.

---

## 🎯 What's Actually Here

This is your **working BPD development repo** with all the pieces properly connected:

```
BPD-Dev-3v4/
├── examples/basic-probe-driver/     ← BPD production code (THIS IS THE MAIN EVENT)
│   ├── vhdl/                         ← FORGE 3-layer implementation
│   │   ├── CustomWrapper_bpd_forge.vhd
│   │   ├── BPD_forge_shim.vhd       ← Register mapping layer
│   │   ├── BPD_forge_main.vhd       ← FSM (has known bug, being debugged)
│   │   └── tests/                    ← CocoTB progressive testing (P1-P3)
│   └── BPD-RTL.yaml                  ← Register specification
│
├── libs/                             ← Git submodules (independently versioned)
│   ├── forge-vhdl/                   ← VHDL components + serialization packages
│   ├── moku-models/                  ← Platform specs (Go/Lab/Pro/Delta)
│   ├── riscure-models/               ← Probe specs (EMFI example)
│   └── platform/                     ← FORGE templates (NOT a submodule)
│       ├── MCC_CustomInstrument.vhd  ← Vendor interface (16 CR, 16 SR)
│       └── FORGE_App_Wrapper.vhd     ← Wrapper template
│
├── tools/forge-codegen/              ← YAML→VHDL generator (dormant, manual VHDL phase)
├── docs/                             ← Reference documentation
├── .claude/                          ← AI agent definitions + slash commands
└── Obsidian/Project/                 ← Optional session management workspace
```

---

## 🔑 Key Concepts (for 2am debugging)

### FORGE = Safety Pattern for Moku Custom Instruments

**Problem:** Network-settable registers + 125MHz FPGA = chaos when registers change mid-cycle

**Solution:** 3-layer architecture with safe initialization handshaking

```vhdl
-- CR0[31:29] = FORGE control scheme (THIS IS CRITICAL)
forge_ready <= Control0(31);  -- Network: "registers loaded"
user_enable <= Control0(30);  -- User: "enable instrument"
clk_enable  <= Control0(29);  -- Clock: "clocking enabled"

global_enable <= forge_ready AND user_enable AND clk_enable AND loader_done;
```

**All 4 conditions must be true** before your instrument runs. No glitches, no race conditions.

### 3 Layers = Clean Separation

```
Layer 1: BRAM Loader (future)     ← Pre-loads config data
          ↓
Layer 2: Shim                     ← CR0-CR15 → app_reg_* signals
          ↓                          (sync with ready_for_updates)
Layer 3: Main                     ← Pure FSM logic, zero CR knowledge
```

**Key insight:** Main app thinks in `app_reg_trigger_voltage`, NOT `Control2[15:0]`. Shim layer handles all the MCC interface ugliness.

---

## 🚀 Getting Started

### First Time Setup

```bash
# Clone with submodules (IMPORTANT: --recurse-submodules!)
git clone --recurse-submodules https://github.com/YOUR-USERNAME/BPD-Dev-3v4.git
cd BPD-Dev-3v4

# Setup Python environment
uv sync

# Verify everything loaded
python -c "from moku_models import MOKU_GO_PLATFORM; print('✅ Ready!')"
```

### If You Forgot `--recurse-submodules` (we've all been there)

```bash
# Initialize all submodules
git submodule update --init --recursive

# Verify they're actually there
ls libs/forge-vhdl/vhdl/packages/  # Should show forge_*.vhd files
```

### Running BPD Tests

```bash
cd examples/basic-probe-driver/vhdl/tests/

# P1 - Fast iteration (LLM-optimized, <20 lines per test)
uv run python run.py

# P2 - Comprehensive (all features)
TEST_LEVEL=P2_INTERMEDIATE uv run python run.py

# P3 - Full coverage (stress testing)
TEST_LEVEL=P3_COMPREHENSIVE uv run python run.py
```

---

## 📚 Documentation (Progressive Depth)

### When You Need Quick Answers

**Start here:** `llms.txt` files (500-1000 tokens, essential facts)

```bash
cat llms.txt                           # This repo overview
cat libs/forge-vhdl/llms.txt           # VHDL components
cat libs/moku-models/llms.txt          # Platform specs
cat tools/forge-codegen/llms.txt       # Code generator (dormant)
```

### When You Need Design Details

**Next level:** `CLAUDE.md` files (3-5k tokens, complete architecture)

```bash
cat CLAUDE.md                          # Full repo architecture
cat libs/forge-vhdl/CLAUDE.md          # VHDL design patterns
cat libs/moku-models/CLAUDE.md         # Platform integration
```

### When You Need Implementation Specifics

**Deep dive:** Source code + specialized docs

```bash
# BPD complete architecture spec
cat examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md

# Testing guide
cat examples/basic-probe-driver/vhdl/tests/README.md

# MCC interface details
cat libs/platform/MCC_CustomInstrument.vhd
```

---

## 🧩 Git Submodules Explained (the confusing bits)

### What Are Submodules?

**Think of them as:** Git repos pinned to specific commits inside your parent repo.

**Why use them here:**
- `libs/forge-vhdl` - Shared VHDL components (reused across instruments)
- `libs/moku-models` - Platform specs (independent versioning)
- `libs/riscure-models` - Probe specs (optional, example reference)
- `tools/forge-codegen` - Code generator (dormant, may reactivate)

**Key insight:** Each submodule is **independently versioned**. Update one without touching others.

### Common Submodule Operations

```bash
# Pull latest changes in all submodules
git submodule update --remote

# Make changes inside a submodule
cd libs/forge-vhdl
git checkout -b my-feature
# ... make changes ...
git add . && git commit -m "feat: add new component"
git push origin my-feature

# Update parent repo to point to new submodule commit
cd ../..  # Back to BPD-Dev-3v4 root
git add libs/forge-vhdl
git commit -m "chore: update forge-vhdl submodule"
```

### Submodule Troubleshooting

**Problem:** `libs/forge-vhdl/` is empty or has wrong commit

```bash
# Re-initialize submodules
git submodule update --init --recursive
```

**Problem:** Made changes inside submodule but parent repo doesn't see them

```bash
# Submodule changes must be committed INSIDE the submodule first
cd libs/forge-vhdl
git status  # Should be clean
cd ../..
git add libs/forge-vhdl  # Now update parent pointer
```

---

## 🔬 Current Development Status

### What's Working

- ✅ FORGE 3-layer architecture fully specified
- ✅ BPD-RTL.yaml register specification complete
- ✅ VHDL serialization packages (voltage, time, types)
- ✅ CocoTB progressive testing infrastructure (P1-P3)
- ✅ Hierarchical encoder for oscilloscope debugging (14-bit state+status)
- ✅ MCC CustomInstrument interface (16 CR, 16 SR)

### What's In Progress

- 🚧 **BPD FSM debugging** (known bug, actively working on it)
- 🚧 Type system refinements (std_logic_reg, ±5V voltage types added, YAML needs update)
- 🚧 BRAM loader integration (Layer 1 - design complete, implementation pending)

### What's Next

1. Complete BPD FSM debugging
2. Update BPD-RTL.yaml with correct types (std_logic_reg, voltage_*_5v_bipolar_s16)
3. Regenerate or manually update shim layer
4. Full integration testing on Moku hardware
5. Production validation

---

## 🎓 Learning Path (for new contributors or future-you)

### 1. Understand the Problem

Read: `docs/GITHUB_TEMPLATE_SETUP.md` - Why FORGE exists, what it solves

### 2. See It In Action

Study: `examples/basic-probe-driver/` - Complete reference implementation
- Start: `examples/basic-probe-driver/README.md`
- Deep dive: `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md`

### 3. Understand the Pieces

Explore submodules:
- `libs/forge-vhdl/` - Reusable VHDL components
- `libs/moku-models/` - Platform specifications
- `libs/platform/` - FORGE templates (MCC interface)

### 4. Build Your Own

Copy BPD structure, replace logic:
- Keep: FORGE patterns (CR0[31:29], app_reg_* abstraction, ready_for_updates)
- Replace: BPD-specific FSM with your instrument logic

---

## 🗂️ Optional: Obsidian Session Management

**TL;DR:** Obsidian workspace for managing dev sessions with Claude, including context compaction and automatic archiving.

**Slash commands:**
```bash
/obsd_new_session       # Start fresh session
/obsd_continue_session  # Resume previous session
/obsd_close_session     # Archive + harvest /compact summary
```

**Full details:** See `docs/OBSIDIAN_INTEGRATION.md` or `Obsidian/Project/README.md`

**Not using Obsidian?** That's fine! All core workflows work without it.

---

## 🛠️ Common Development Tasks

### Running BPD on Moku Hardware

```bash
# Deploy + operate BPD
# See: Obsidian/Project/BPD-Two-Tool-Architecture.md for complete workflow

# Tool 1: moku-go.py (deployment + control)
python scripts/moku-go.py --deploy   # Deploy to Moku:Go

# Tool 2: bpd-debug.py (monitoring + debugging)
python scripts/bpd-debug.py --monitor  # Watch oscilloscope state encoding
```

### Updating Submodule to Latest

```bash
# Update specific submodule
cd libs/forge-vhdl
git pull origin main
cd ../..
git add libs/forge-vhdl
git commit -m "chore: update forge-vhdl to latest"
```

### Adding New VHDL Component to forge-vhdl

```bash
# Work inside submodule
cd libs/forge-vhdl
git checkout -b feat/my-new-component

# Add component
# ... create vhdl/components/my_component.vhd ...

# Test it
cd tests/
uv run python run.py

# Commit in submodule
git add vhdl/components/my_component.vhd
git commit -m "feat: add my_component"
git push origin feat/my-new-component

# Update parent repo
cd ../..
git add libs/forge-vhdl
git commit -m "feat: integrate new forge-vhdl component"
```

---

## 📞 Getting Help

### Documentation Hierarchy

1. **Quick question?** → Read relevant `llms.txt`
2. **Design question?** → Read relevant `CLAUDE.md`
3. **Implementation question?** → Read source code + specialized docs
4. **Still stuck?** → Check `Obsidian/Project/Handoffs/` for recent context

### Key Architecture Files

- `CLAUDE.md` - Complete monorepo architecture (THIS FILE = gold standard)
- `examples/basic-probe-driver/vhdl/FORGE_ARCHITECTURE.md` - FORGE pattern spec
- `libs/platform/MCC_CustomInstrument.vhd` - Vendor interface entity
- `Obsidian/Project/BPD-Two-Tool-Architecture.md` - Deployment architecture

### AI Assistance

```bash
# Claude Code slash commands
/customize-monorepo      # Adapt this template for new instruments
/obsd_new_session        # Start managed development session
```

---

## 📋 Checklists (for context switching)

### Starting Development Session

- [ ] `git status` - Clean working tree?
- [ ] `git submodule status` - All submodules at expected commits?
- [ ] `uv sync` - Python environment up to date?
- [ ] Read `Obsidian/Project/Sessions/YYYY-MM-DD/next-session-plan.md` (if exists)

### Before Committing

- [ ] Tests pass? (`cd examples/basic-probe-driver/vhdl/tests/ && uv run python run.py`)
- [ ] VHDL compiles? (GHDL or vendor tools)
- [ ] Submodule changes committed first? (if working in submodule)
- [ ] Commit message follows convention? (`feat:`, `fix:`, `docs:`, `chore:`)

### Before Pushing

- [ ] Working tree clean? (`git status`)
- [ ] Submodule pointers updated? (`git submodule status`)
- [ ] Documentation updated? (if adding features)
- [ ] Tests still pass? (paranoid final check)

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 🎉 Quick Mental Model

**Think of this repo as:**

```
BPD-Dev-3v4
├── YOUR WORK HERE        ← examples/basic-probe-driver/
├── Shared libraries      ← libs/* (git submodules)
├── Code generator        ← tools/forge-codegen/ (dormant)
├── Documentation         ← docs/, CLAUDE.md, llms.txt
└── Optional session mgmt ← Obsidian/Project/
```

**When in doubt:**
1. Check `git submodule status` (are submodules loaded?)
2. Read `CLAUDE.md` (what's the architecture?)
3. Study BPD reference (how does it work?)
4. Run tests (does it still work?)

**Most common mistake:** Forgetting `--recurse-submodules` when cloning. If `libs/forge-vhdl/` is empty, run `git submodule update --init --recursive`.

---

**Version:** 3.4-WIP
**Last Updated:** 2025-11-09
**Primary Developer:** johnycsh
**Status:** Active development, BPD FSM debugging phase

**Remember:** When you're sleep-deprived and can't remember how submodules work, just read this file. That's why it exists. ☕
