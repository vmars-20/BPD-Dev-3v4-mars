# Moku Development Fork Integration Guide

**Version:** 1.0
**Last Updated:** 2025-11-09
**Status:** Production

---

## Overview

This project uses a **custom fork** of the Liquid Instruments `moku` library instead of the official PyPI package.

**Why?**
- 🤖 **LLM-annotated source code** - `@CLAUDE` comments guide AI assistants to important APIs
- 📚 **Enhanced documentation** - 3-tier docs (llms.txt → CLAUDE.md → source)
- 🔍 **Session introspection** - Comprehensive guides for querying running device state
- 🧪 **Development features** - Additional patterns for integration with moku-models

**Fork Location:** `git@github.com:vmars-20/moku-3.0.4.1-llm-dev.git`
**Base Version:** moku 4.0.3.1 (from PyPI)
**Compatibility:** 100% API-compatible drop-in replacement

---

## Quick Start (If Already Set Up)

If the fork is already configured in `pyproject.toml`, just run:

```bash
# From project root
git submodule update --init --recursive  # Initialize submodules (git worktrees!)
uv sync                                  # Install all dependencies including moku fork
```

**Verify installation:**
```bash
uv run python -c "from moku.instruments import MultiInstrument; print('✓ Moku fork working')"
```

If you get errors, skip to **Troubleshooting** section below.

---

## Initial Setup (From Scratch)

### Step 1: Prepare the Moku Fork Repository

The fork lives in `/tmp/moku-llm-annotated/` during development.

```bash
# Check if fork exists locally
ls -la /tmp/moku-llm-annotated/

# Should contain:
# - pyproject.toml (version 4.0.3.1)
# - CLAUDE.md (LLM guide)
# - llms.txt (quick reference)
# - README_LLM.md (fork explanation)
# - moku/ (annotated source code)
```

### Step 2: Push to GitHub (First Time Only)

```bash
cd /tmp/moku-llm-annotated

# Add remote (if not already added)
git remote add origin git@github.com:vmars-20/moku-3.0.4.1-llm-dev.git

# Push to GitHub
git push -u origin main
```

### Step 3: Update Project pyproject.toml

Edit the top-level `pyproject.toml`:

```toml
dependencies = [
    # ... other dependencies ...
    "moku @ git+ssh://git@github.com/vmars-20/moku-3.0.4.1-llm-dev.git@main",  # LLM-annotated fork
]
```

**Replace:**
```toml
"moku>=3.0.0",  # PyPI version (remove this)
```

### Step 4: Fix Nested Workspace Issue

**Problem:** `libs/forge-vhdl` is a git submodule that contains its own `[tool.uv.workspace]` section, which conflicts with the top-level workspace.

**Solution:** Comment out the nested workspace in `libs/forge-vhdl/pyproject.toml`:

```bash
# Edit libs/forge-vhdl/pyproject.toml
# Find [tool.uv.workspace] section and comment it out:
```

```toml
# ============================================================================
# UV WORKSPACE CONFIGURATION
# ============================================================================
# COMMENTED OUT: Nested workspaces not supported when used as submodule
# Uncomment if using forge-vhdl standalone
#
# [tool.uv.workspace]
# # Declare Python packages as workspace members
# # uv manages these as a unified dependency graph
# members = [
#     "python/forge_cocotb",
#     "python/forge_platform",
#     "python/forge_tools",
# ]
```

**Note:** This change should be committed to the forge-vhdl submodule if you control it.

### Step 5: Initialize Submodules (Git Worktree Users!)

**CRITICAL FOR GIT WORKTREES:** If you're working in a git worktree, submodules are NOT automatically initialized!

```bash
# From project root
git submodule update --init --recursive
```

**Verify:**
```bash
ls -la libs/forge-vhdl/pyproject.toml   # Should exist
ls -la libs/moku-models/pyproject.toml  # Should exist
ls -la libs/riscure-models/pyproject.toml  # Should exist
```

### Step 6: Sync Dependencies

```bash
uv sync
```

**Expected output:**
```
Using CPython 3.10.16
Creating virtual environment at: .venv
Resolved 47 packages in 1.03s
   Updating ssh://git@github.com/vmars-20/moku-3.0.4.1-llm-dev.git (main)
    Updated ssh://git@github.com/vmars-20/moku-3.0.4.1-llm-dev.git (4593a98...)
   Building moku @ git+ssh://...
      Built moku @ git+ssh://...
Installed 32 packages in 34ms
 + moku==4.0.3.1 (from git+ssh://git@github.com/vmars-20/moku-3.0.4.1-llm-dev.git@...)
```

### Step 7: Verify Installation

```bash
# Check moku is installed from GitHub
uv pip show moku
# Should show: Version: 4.0.3.1

# Test import
uv run python -c "from moku.instruments import MultiInstrument; print('✓ Success')"
```

---

## Troubleshooting

### Error: "Workspace member is missing a pyproject.toml"

**Symptom:**
```
error: Workspace member `/path/to/libs/forge-vhdl` is missing a `pyproject.toml`
```

**Cause:** Git submodules not initialized (common in git worktrees)

**Fix:**
```bash
git submodule update --init --recursive
```

**Verify:**
```bash
ls libs/forge-vhdl/pyproject.toml  # Should exist
```

---

### Error: "Nested workspaces are not supported"

**Symptom:**
```
error: Nested workspaces are not supported, but workspace member
(`/path/to/libs/forge-vhdl`) has a `uv.workspace` table
```

**Cause:** `libs/forge-vhdl/pyproject.toml` has its own `[tool.uv.workspace]` section

**Fix:**
```bash
# Edit libs/forge-vhdl/pyproject.toml
# Comment out the [tool.uv.workspace] section (see Step 4 above)
```

**Quick fix (bash one-liner):**
```bash
# Backup first!
cp libs/forge-vhdl/pyproject.toml libs/forge-vhdl/pyproject.toml.bak

# Comment out workspace section (adjust line numbers if needed)
sed -i.bak '34,43s/^/# /' libs/forge-vhdl/pyproject.toml
```

---

### Error: "Failed to clone repository" or SSH errors

**Symptom:**
```
error: Failed to clone repository:
  Permission denied (publickey)
```

**Cause:** SSH key not configured for GitHub

**Fix:**
```bash
# Test SSH access
ssh -T git@github.com
# Should output: "Hi username! You've successfully authenticated..."

# If failed, add SSH key to GitHub:
cat ~/.ssh/id_rsa.pub  # Copy this
# Add to: https://github.com/settings/keys
```

**Alternative (HTTPS):**
Change pyproject.toml to use HTTPS instead of SSH:
```toml
"moku @ git+https://github.com/vmars-20/moku-3.0.4.1-llm-dev.git@main",
```

---

### Error: Module 'moku' has no attribute '__version__'

**Symptom:**
```python
import moku
print(moku.__version__)  # AttributeError
```

**Cause:** The moku library doesn't expose `__version__` attribute (this is normal!)

**Fix:** Import what you need instead:
```python
from moku.instruments import MultiInstrument  # ✓ Correct
```

**Verify installation differently:**
```bash
uv pip show moku  # Shows version 4.0.3.1
```

---

### Error: "No module named 'moku'"

**Symptom:**
```python
from moku.instruments import MultiInstrument  # ModuleNotFoundError
```

**Cause:** Not running in uv environment

**Fix:**
```bash
# Always use uv run:
uv run python script.py

# Or activate venv:
source .venv/bin/activate
python script.py
```

---

## Git Worktree Workflow

**If you use git worktrees** (multiple branches checked out simultaneously), follow this pattern:

### Creating a New Worktree

```bash
# From main worktree
git worktree add ../BPD-Dev-New-Feature feature/new-feature

# CRITICAL: Initialize submodules in new worktree
cd ../BPD-Dev-New-Feature
git submodule update --init --recursive

# Sync dependencies
uv sync
```

### Checking Worktree Status

```bash
# List all worktrees
git worktree list

# Check if submodules are initialized
git submodule status
# Look for '-' prefix = not initialized
# Look for ' ' prefix = initialized correctly
```

**Example output:**
```
-f5cc2dc9... libs/forge-vhdl       # ✗ Not initialized
 f5cc2dc9... libs/forge-vhdl       # ✓ Initialized
```

---

## Maintenance

### Updating the Moku Fork

**When changes are made to `/tmp/moku-llm-annotated/`:**

```bash
# 1. Commit changes in fork
cd /tmp/moku-llm-annotated
git add .
git commit -m "Update: description of changes"
git push

# 2. Update project dependencies
cd /path/to/BPD-Dev-3v4-Local-Hardware-Testing
uv sync  # Pulls latest from GitHub
```

### Pinning to Specific Commit (Recommended for Stability)

Instead of tracking `@main`, pin to specific commit:

```toml
# pyproject.toml
"moku @ git+ssh://git@github.com/vmars-20/moku-3.0.4.1-llm-dev.git@4593a98",
```

**Benefits:**
- ✅ Reproducible builds
- ✅ No surprise changes
- ✅ Easier debugging

**Update process:**
```bash
# 1. Test new commit locally
cd /tmp/moku-llm-annotated
git log --oneline -5  # Find commit hash

# 2. Update pyproject.toml with new hash
# 3. Sync
uv sync
```

### Using Tags (Best Practice)

```bash
# In fork repository
cd /tmp/moku-llm-annotated
git tag -a v4.0.3.1-llm.1 -m "Initial LLM-annotated release"
git push --tags

# In project pyproject.toml
"moku @ git+ssh://git@github.com/vmars-20/moku-3.0.4.1-llm-dev.git@v4.0.3.1-llm.1",
```

---

## Reverting to Official PyPI Package

If needed, revert to official moku:

```toml
# pyproject.toml - Change from:
"moku @ git+ssh://git@github.com/vmars-20/moku-3.0.4.1-llm-dev.git@main",

# To:
"moku>=3.0.0",
```

```bash
uv sync  # Reinstalls from PyPI
```

---

## Documentation Access

The fork includes enhanced documentation:

**Location:** `/tmp/moku-llm-annotated/`

| File | Purpose | Token Budget |
|------|---------|--------------|
| `README_LLM.md` | Explains the fork concept | N/A |
| `llms.txt` | Quick reference for AI (~900 tokens) | 900 tokens |
| `CLAUDE.md` | Comprehensive API guide (~4000 tokens) | 4000 tokens |
| Source files | Annotated with `@CLAUDE` comments | Load as needed |

**Key features documented:**
- Session introspection APIs (`get_instruments()`, `get_connections()`, etc.)
- Graceful session handoffs (`persist_state=True`)
- Session key management (`Moku-Client-Key` header)
- Integration patterns with `moku-models`
- CloudCompile control register APIs

**For LLM-assisted development:**
```
"Read /tmp/moku-llm-annotated/llms.txt for quick orientation,
then read the Session Introspection section of CLAUDE.md"
```

---

## Integration with moku-models

The fork is designed to work with `moku-models` (also in this workspace):

**Deploy from MokuConfig:**
```python
from moku_models import MokuConfig
from moku.instruments import MultiInstrument, CloudCompile
import yaml

# Load config
config = MokuConfig.from_dict(yaml.safe_load(open('config.yaml')))

# Validate
config.validate_routing()

# Deploy using fork
moku = MultiInstrument(ip='192.168.1.100', platform_id=config.platform.slots)
for slot_num, slot_config in config.slots.items():
    moku.set_instrument(slot_num, CloudCompile, **slot_config.settings)
```

**Extract MokuConfig from running device:**
```python
from moku_models import MokuConfig, SlotConfig, MokuConnection, MOKU_LAB_PLATFORM

# Query device using fork's introspection APIs
moku = MultiInstrument(ip='192.168.1.100', platform_id=2)
instruments = moku.get_instruments()
connections = moku.get_connections()

# Create type-safe snapshot
config = MokuConfig(
    platform=MOKU_LAB_PLATFORM,
    slots={i+1: SlotConfig(instrument=inst) for i, inst in enumerate(instruments) if inst},
    routing=[MokuConnection(**c) for c in connections]
)
```

---

## Common Commands Reference

```bash
# Initial setup
git submodule update --init --recursive
uv sync

# Verify installation
uv pip show moku
uv run python -c "from moku.instruments import MultiInstrument; print('✓ OK')"

# Update fork from GitHub
uv sync

# Check worktrees
git worktree list

# Check submodules
git submodule status

# Activate venv (optional)
source .venv/bin/activate
```

---

## FAQ

### Q: Why not use the official PyPI package?

**A:** The official package lacks:
- LLM-optimized documentation for AI-assisted development
- Comprehensive session introspection guides
- Integration examples with type-safe models
- `@CLAUDE` source annotations for quick API discovery

### Q: Will this break when Liquid Instruments updates moku?

**A:** The fork is based on moku 4.0.3.1 and is pinned. To upgrade:
1. Update `/tmp/moku-llm-annotated/` from PyPI manually
2. Re-apply annotations
3. Test compatibility
4. Push updated fork

### Q: Can I use this fork on multiple machines?

**A:** Yes! The fork is on GitHub. On each machine:
```bash
git clone <project-repo>
git submodule update --init --recursive
uv sync  # Automatically fetches fork from GitHub
```

### Q: What if I need to use forge-vhdl standalone?

**A:** Uncomment the workspace section in `libs/forge-vhdl/pyproject.toml`:
```bash
cd libs/forge-vhdl
# Edit pyproject.toml, uncomment [tool.uv.workspace] section
uv sync  # Works standalone now
```

### Q: How do I know if I'm using the fork or PyPI version?

**A:**
```bash
uv pip show moku
# Look for: "Location: .../site-packages" (installed from GitHub)
# PyPI version would show different metadata
```

---

## Checklist for New Team Members

- [ ] Clone project repository
- [ ] Initialize submodules: `git submodule update --init --recursive`
- [ ] Verify submodules exist: `ls libs/*/pyproject.toml`
- [ ] Check SSH access to GitHub: `ssh -T git@github.com`
- [ ] Sync dependencies: `uv sync`
- [ ] Verify moku fork: `uv pip show moku` (should show 4.0.3.1)
- [ ] Test import: `uv run python -c "from moku.instruments import MultiInstrument; print('✓')"`
- [ ] Read fork docs: `/tmp/moku-llm-annotated/llms.txt`

---

## Troubleshooting Decision Tree

```
1. Can't sync dependencies?
   ├─ Missing pyproject.toml? → Run: git submodule update --init --recursive
   ├─ Nested workspace error? → Comment out [tool.uv.workspace] in libs/forge-vhdl/
   └─ SSH errors? → Check: ssh -T git@github.com

2. Import errors?
   ├─ ModuleNotFoundError? → Use: uv run python script.py
   └─ AttributeError on __version__? → Normal! Use: uv pip show moku

3. Working in git worktree?
   └─ New worktree created? → Always run: git submodule update --init --recursive
```

---

## Related Documentation

- **Project docs:** `docs/README.md`
- **Moku models:** `libs/moku-models/CLAUDE.md`
- **Fork repository:** `git@github.com:vmars-20/moku-3.0.4.1-llm-dev.git`
- **Upstream (official):** https://pypi.org/project/moku/

---

**Last Updated:** 2025-11-09
**Maintainer:** Moku Instrument Forge Team
**Version:** 1.0
**Status:** Production-ready
