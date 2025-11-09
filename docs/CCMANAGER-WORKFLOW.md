# ccmanager Workflow Guide

**Tool:** ccmanager v2.9.2
**Purpose:** TUI for managing Claude Code sessions across git worktrees
**Your Setup:** 3 worktrees managed by ccmanager

---

## Overview

**ccmanager** is a Terminal User Interface (TUI) that:
- 📁 Creates and manages git worktrees
- 🤖 Launches Claude Code sessions for each worktree
- 🔄 Copies session data between worktrees
- ⌨️  Provides keyboard shortcuts for quick navigation

**Your Current Worktrees:**
```
BPD-Dev-3v4-mars                     (main branch)
BPD-Dev-3v4-Integration-testing      (feature/Integration-Development)
BPD-Dev-3v4-Local-Hardware-Testing   (feature/Local-Hardware-Testing) ← YOU ARE HERE
```

---

## Quick Start

### Launch ccmanager

```bash
ccmanager
```

This opens a TUI where you can:
- View all worktrees
- Create new worktrees
- Launch Claude sessions
- Switch between worktrees
- Delete worktrees

### Keyboard Shortcuts

**Navigation:**
- `↑/↓` - Navigate worktree list
- `Enter` - Launch Claude Code in selected worktree
- `Escape` - Cancel/go back
- `Ctrl+E` - Return to menu (from within)

**Actions:**
- `n` - Create new worktree
- `d` - Delete worktree
- `r` - Refresh list
- `q` - Quit ccmanager

---

## Common Workflows

### 1. Creating a New Feature Branch Worktree

**Using ccmanager TUI:**

1. Launch ccmanager:
   ```bash
   ccmanager
   ```

2. Press `n` (new worktree)

3. Enter:
   - Branch name: `feature/your-feature-name`
   - Worktree directory name (defaults based on branch)

4. ccmanager creates:
   - New git worktree
   - New directory
   - Checks out branch

5. Select the new worktree and press `Enter` to launch Claude

**Behind the scenes:**
```bash
# ccmanager runs something like:
git worktree add ../BPD-Dev-3v4-Your-Feature feature/your-feature-name
cd ../BPD-Dev-3v4-Your-Feature
claude  # Launch Claude Code session
```

### 2. Switching Between Worktrees

**Option A: Using ccmanager (Recommended)**
```bash
ccmanager
# Navigate to desired worktree
# Press Enter to launch Claude session
```

**Option B: Manual (if already in terminal)**
```bash
cd /Users/vmars20/20251109/BPD-Dev-3v4-Integration-testing
claude  # Launch Claude Code
```

### 3. Pushing Your Work to GitHub

**From within Claude Code session:**

Your work is committed to git normally. To push:

```bash
# Check what branch you're on
git branch

# Push to GitHub
git push origin <branch-name>

# For your current worktree:
git push origin feature/Local-Hardware-Testing
```

**Important:** ccmanager manages worktrees locally, but git operations (push/pull) work normally!

### 4. Deleting a Worktree

**Using ccmanager (Safest):**

1. Launch ccmanager
2. Navigate to worktree to delete
3. Press `d` (delete)
4. Confirm deletion

**Manual (if you know what you're doing):**
```bash
# From main worktree
cd /Users/vmars20/20251109/BPD-Dev-3v4-mars

# Remove worktree
git worktree remove ../BPD-Dev-3v4-Old-Feature

# Optional: Delete branch too
git branch -d feature/old-feature
```

---

## Critical: Submodules in Worktrees

**⚠️ IMPORTANT:** When ccmanager creates a new worktree, **submodules are NOT automatically initialized!**

**After creating new worktree, always run:**

```bash
cd /path/to/new/worktree
git submodule update --init --recursive
uv sync
```

**Why:** This project uses git submodules:
- `libs/forge-vhdl`
- `libs/moku-models`
- `libs/riscure-models`

Each worktree needs its own copy of submodules.

**Quick check if submodules are initialized:**
```bash
ls libs/forge-vhdl/pyproject.toml  # Should exist
```

**Diagnostic tool:**
```bash
uv run python scripts/diagnose_moku_env.py
# Will warn if submodules not initialized
```

---

## Session Data Copying

**Feature:** `copySessionData: true` (enabled in your config)

**What it does:**
- When creating new worktree, ccmanager can copy Claude session history
- Useful for continuing work across branches

**Config location:** `~/.config/ccmanager/config.json`

---

## Understanding Your Setup

### Worktree Structure

```
/Users/vmars20/20251109/
├── BPD-Dev-3v4-mars/              ← Main worktree (shared .git)
│   └── .git/                       ← Real git database
│
├── BPD-Dev-3v4-Integration-testing/
│   ├── .git                        ← Symlink to main .git
│   ├── libs/                       ← Own copy of submodules
│   ├── .venv/                      ← Own virtual environment
│   └── ... project files ...
│
└── BPD-Dev-3v4-Local-Hardware-Testing/  ← YOU ARE HERE
    ├── .git                        ← Symlink to main .git
    ├── libs/                       ← Own copy of submodules
    ├── .venv/                      ← Own virtual environment
    └── ... project files ...
```

**Key points:**
- All worktrees share the same git database (commits, branches, tags)
- Each worktree has separate working files
- Submodules are separate per worktree
- Virtual environments (.venv) are separate per worktree

### Git Operations

**What's shared:**
- ✅ Commits (visible in all worktrees)
- ✅ Branches (can push/pull from any worktree)
- ✅ Tags
- ✅ Remotes (origin, etc.)

**What's separate:**
- ❌ Working files (your code edits)
- ❌ Submodule checkouts (must init per worktree)
- ❌ .venv directories
- ❌ Build artifacts

---

## Pushing to GitHub

**Your current worktree has new commits.**

To make them available on GitHub:

```bash
# From your current worktree
git push origin feature/Local-Hardware-Testing
```

**This pushes:**
- ✅ Your branch to GitHub
- ✅ All commits on that branch
- ✅ Makes it available for:
  - Pull requests
  - Other team members
  - Other machines
  - Code review

**This does NOT push:**
- ❌ The worktree directory structure (local only)
- ❌ ccmanager configuration (local only)

**When others clone:**
```bash
git clone <repo-url>
git checkout feature/Local-Hardware-Testing  # Gets your commits
```

They'll have a normal working directory (not a worktree unless they create one).

---

## Best Practices

### 1. One Branch Per Worktree

**Good:**
```
BPD-Dev-3v4-mars                → main
BPD-Dev-3v4-Local-Hardware      → feature/Local-Hardware-Testing
BPD-Dev-3v4-Integration         → feature/Integration-Development
```

**Avoid:** Switching branches within a worktree (defeats the purpose!)

### 2. Initialize Submodules Immediately

**After creating new worktree:**
```bash
git submodule update --init --recursive
uv sync
```

### 3. Push Regularly

**Don't let work pile up locally:**
```bash
git push origin <branch-name>  # Backup + collaboration
```

### 4. Clean Up Finished Worktrees

**After merging PR:**
```bash
# Use ccmanager to delete worktree
ccmanager
# Press 'd' on finished worktree
```

### 5. Keep Main Worktree Clean

**Use main worktree for:**
- Quick reference
- Creating new worktrees
- Reviewing merged changes

**Don't use main worktree for:**
- Active development (use feature worktrees)

---

## Troubleshooting

### Issue: "Cannot launch Claude in this worktree"

**Cause:** Worktree may be in detached HEAD state or missing dependencies

**Fix:**
```bash
cd /path/to/worktree
git status  # Check branch status
git checkout <branch-name>  # If detached
uv sync  # Install dependencies
```

### Issue: "Submodules empty in new worktree"

**Cause:** Submodules not initialized (ccmanager doesn't do this automatically)

**Fix:**
```bash
git submodule update --init --recursive
```

**Verify:**
```bash
uv run python scripts/diagnose_moku_env.py
```

### Issue: "Can't push - permission denied"

**Cause:** SSH key not configured for GitHub

**Fix:**
```bash
ssh -T git@github.com  # Test connection
# If fails, add SSH key to GitHub: https://github.com/settings/keys
```

### Issue: "Changes in wrong worktree"

**Cause:** Made changes in wrong worktree

**Fix:**
```bash
# Stash changes
git stash

# Switch to correct worktree (via ccmanager or cd)
cd /path/to/correct/worktree

# Apply stashed changes
git stash pop
```

---

## Advanced: ccmanager Configuration

**Config file:** `~/.config/ccmanager/config.json`

**Current settings:**
```json
{
  "worktree": {
    "autoDirectory": false,      // Manually specify directory names
    "copySessionData": true      // Copy Claude session history
  },
  "command": {
    "command": "claude"           // Launch Claude Code
  }
}
```

**Customization options:**
- `autoDirectory: true` - Auto-generate worktree directory names
- `copySessionData: false` - Start fresh Claude sessions
- Custom launch command (e.g., with flags)

---

## Workflow Comparison

### ccmanager Workflow (Recommended)
```bash
# 1. Launch TUI
ccmanager

# 2. Create new worktree (press 'n')
#    → Enter branch name
#    → Enter directory name
#    → Automatically created

# 3. Initialize submodules
git submodule update --init --recursive
uv sync

# 4. Work in Claude Code session
#    → Make changes
#    → Commit regularly

# 5. Push to GitHub
git push origin <branch>

# 6. Delete worktree when done (press 'd' in ccmanager)
```

### Manual Workflow (Not Recommended)
```bash
# More steps, more error-prone
git worktree add ../path feature/branch
cd ../path
git submodule update --init --recursive
uv sync
claude
# ... work ...
git worktree remove ../path
```

**Verdict:** Use ccmanager! It's designed for this.

---

## Quick Reference

### Common ccmanager Commands

| Action | Command |
|--------|---------|
| Launch TUI | `ccmanager` |
| Create worktree | Press `n` in TUI |
| Launch Claude | Press `Enter` on worktree |
| Delete worktree | Press `d` on worktree |
| Refresh list | Press `r` |
| Quit | Press `q` |

### After Creating New Worktree

```bash
cd /path/to/new/worktree
git submodule update --init --recursive  # CRITICAL!
uv sync                                  # Install dependencies
uv run python scripts/diagnose_moku_env.py  # Verify setup
```

### Pushing Your Work

```bash
git status  # Check what branch you're on
git push origin <branch-name>  # Push to GitHub
```

---

## Next Steps for Your Current Work

**You just committed moku fork integration work.**

**Recommended actions:**

1. **Push to GitHub (preserve work):**
   ```bash
   git push origin feature/Local-Hardware-Testing
   ```

2. **Continue working:**
   - ccmanager already launched Claude session in this worktree
   - Make more changes as needed
   - Commit regularly

3. **When ready, create PR:**
   - Go to GitHub repository
   - Open pull request: `feature/Local-Hardware-Testing` → `main`
   - Request review

4. **After PR merged:**
   - Use ccmanager to delete this worktree (press 'd')
   - Your work is now in main branch

---

## Related Documentation

- **Git worktrees:** `docs/MOKU-DEV-MODULE.md` - Submodule handling
- **Environment setup:** `scripts/diagnose_moku_env.py`
- **ccmanager repo:** https://github.com/anthropics/ccmanager (probably)

---

**Last Updated:** 2025-11-09
**ccmanager Version:** 2.9.2
**Your Worktrees:** 3 active
