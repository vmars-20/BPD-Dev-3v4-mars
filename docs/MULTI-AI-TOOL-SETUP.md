# Using Multiple AI Coding Assistants with Worktrees

**Question:** Can I use Cursor, Copilot, or other AI tools alongside Claude Code in different worktrees?

**Answer:** Yes! Worktrees are actually **perfect** for this. Here's how and what to watch out for.

---

## TL;DR: It Would Go Surprisingly Well

**Worktrees provide natural isolation:**
- ✅ Separate working directories (no file conflicts)
- ✅ Separate .venv environments (no dependency conflicts)
- ✅ Separate submodule checkouts (no version conflicts)
- ✅ Can work on different branches simultaneously

**Potential gotchas:**
- ⚠️  Shared git database (commits visible everywhere)
- ⚠️  Race conditions if committing simultaneously
- ⚠️  Different AI assistants might have different coding styles

**Verdict:** 7/10 - Would recommend with some guidelines

---

## What Actually Happens

### The Good (Natural Isolation)

**Each worktree is completely independent for:**

```
BPD-Dev-3v4-Local-Hardware-Testing/    ← Claude Code
├── Working files (isolated)
├── .venv/ (isolated)
├── libs/forge-vhdl/ (isolated submodule)
└── .git -> (shared)

BPD-Dev-3v4-Cursor-Experiment/          ← Cursor
├── Working files (isolated)
├── .venv/ (isolated)
├── libs/forge-vhdl/ (isolated submodule)
└── .git -> (shared)
```

**What this means:**
- ✅ Cursor can modify files in its worktree without affecting Claude's worktree
- ✅ Each can have different package versions in .venv
- ✅ Each can have different uncommitted changes
- ✅ You can switch between tools instantly (just switch directories)

### The Shared (Potential Conflicts)

**What's shared across all worktrees:**

```
.git/
├── commits (all tools see all commits)
├── branches (changes from any tool)
├── tags
├── remotes (origin, etc.)
└── config
```

**What this means:**
- ⚠️  If Cursor commits to `feature/cursor-test`, Claude Code sees that commit
- ⚠️  If you're on same branch in two worktrees, things get weird
- ⚠️  Both tools push/pull from same GitHub repo

---

## Recommended Setup Patterns

### Pattern 1: One Worktree Per Tool (Safest)

**Best for:** Experimentation, comparing tools, different feature work

```bash
# Worktree assignments
BPD-Dev-3v4-Local-Hardware-Testing  → Claude Code (feature/Local-Hardware-Testing)
BPD-Dev-3v4-Integration-testing     → Claude Code (feature/Integration-Development)
BPD-Dev-3v4-Cursor-Experiment       → Cursor     (feature/cursor-experiment)
BPD-Dev-3v4-Copilot-Testing         → Copilot    (feature/copilot-test)
```

**Setup:**
```bash
# Create new worktree for Cursor
ccmanager  # Press 'n' for new worktree
# Branch: feature/cursor-experiment
# Directory: BPD-Dev-3v4-Cursor-Experiment

cd /Users/vmars20/20251109/BPD-Dev-3v4-Cursor-Experiment
git submodule update --init --recursive
uv sync

# Open with Cursor instead of Claude
cursor .
```

**Benefits:**
- ✅ Zero risk of conflicts
- ✅ Can compare AI assistant outputs
- ✅ Each tool on its own branch
- ✅ Easy to delete when done

**Workflow:**
```
Claude: Working on hardware testing features
Cursor: Experimenting with UI refactoring
Copilot: Prototyping new algorithm
```

### Pattern 2: Same Branch, Different Worktrees (Careful!)

**Best for:** Quick experiments, reviewing AI suggestions before committing

**NOT RECOMMENDED but technically possible:**

```bash
# DON'T DO THIS unless you know what you're doing:
BPD-Dev-3v4-Claude    → branch: feature/shared-work
BPD-Dev-3v4-Cursor    → branch: feature/shared-work  # Same branch!
```

**Why this is risky:**
- ❌ If both commit to same branch → merge conflicts
- ❌ Confusing which tool made which commit
- ❌ Git doesn't prevent this (worktrees allow same branch)

**If you must do this:**
1. Only commit from one tool at a time
2. Other tool: `git pull` before making changes
3. Consider using `git stash` to move work between worktrees

### Pattern 3: Tool-Specific Branches (Recommended)

**Best for:** Long-term multi-tool usage

```bash
# Branch naming convention
feature/Local-Hardware-Testing-claude   → Claude Code
feature/Local-Hardware-Testing-cursor   → Cursor
feature/Local-Hardware-Testing-copilot  → Copilot

# Merge whichever works best into main feature branch
```

**Benefits:**
- ✅ Clear attribution (which AI made which changes)
- ✅ Can cherry-pick best ideas from each
- ✅ Zero risk of conflicts
- ✅ Easy to A/B test AI approaches

---

## Specific Tool Considerations

### Cursor

**What Cursor does:**
- Full VS Code fork with integrated AI chat
- Creates `.cursor/` directory for settings
- May create `.cursorrules` file for AI instructions
- Uses its own AI model (not Claude/GPT exclusively)

**Compatibility with your setup:**
- ✅ Will respect `.venv/` (works with uv)
- ✅ Can use your moku fork (sees pyproject.toml)
- ✅ Git operations work normally
- ⚠️  May suggest different code style than Claude

**Setup:**
```bash
cd /Users/vmars20/20251109/BPD-Dev-3v4-Cursor-Experiment
git submodule update --init --recursive
uv sync
cursor .  # Launch Cursor IDE
```

**Config files to ignore:**
```bash
# Add to .gitignore (if not already there)
.cursor/
.cursorrules
```

### GitHub Copilot

**What Copilot does:**
- VS Code/JetBrains extension
- Inline completions (less aggressive than Cursor/Claude)
- Doesn't make autonomous changes
- Minimal file system impact

**Compatibility with your setup:**
- ✅ Least invasive option
- ✅ Works in any editor (VS Code, Neovim, etc.)
- ✅ No special config files
- ✅ Just suggests completions, you commit manually

**Setup:**
```bash
cd /Users/vmars20/20251109/BPD-Dev-3v4-Copilot-Testing
git submodule update --init --recursive
uv sync
code .  # Launch VS Code with Copilot extension
```

**Recommendation:** Copilot is **safest** for mixed usage - it's just autocomplete!

### Claude Code (Current)

**What Claude Code does:**
- CLI-based agent
- ccmanager for session/worktree management
- Uses `.claude/` for config
- Can make autonomous commits

**Best used for:**
- ✅ Architectural changes
- ✅ Multi-file refactoring
- ✅ Documentation generation
- ✅ Complex debugging

---

## Potential Issues & Solutions

### Issue 1: Different Coding Styles

**Problem:** Each AI might format code differently

**Solution:**
```bash
# Enforce consistent style with tools
# Add to pyproject.toml (already have ruff/black)
[tool.ruff]
line-length = 100

[tool.black]
line-length = 100

# Run before committing from any tool
ruff check --fix .
black .
```

### Issue 2: Simultaneous Commits

**Problem:** Two tools commit at same time to different branches

**Solution:** This is actually fine! Git handles it:
```bash
# Claude commits to feature/claude-work
# Cursor commits to feature/cursor-work
# → No conflict, branches are independent
```

**Problem:** Two tools commit to SAME branch

**Solution:** Don't do this. Use different branches or worktrees.

### Issue 3: Submodule Confusion

**Problem:** Each worktree has separate submodule checkout

**Solution:** This is actually a **feature**! Each tool can work with different versions:
```bash
# Claude's worktree: libs/forge-vhdl at commit abc123
# Cursor's worktree: libs/forge-vhdl at commit def456
# → No conflict!
```

### Issue 4: Virtual Environment Confusion

**Problem:** Different AI tools might suggest different package versions

**Solution:** Each worktree has its own .venv:
```bash
# Claude's worktree
.venv/lib/python3.10/site-packages/moku  # Version from your fork

# Cursor's worktree (if it suggests different version)
.venv/lib/python3.10/site-packages/moku  # Could be different!

# → No conflict, isolated!
```

---

## Recommended Experiment

### Try This: Cursor in Separate Worktree

**Safe experiment to try:**

```bash
# 1. Create new worktree with ccmanager
ccmanager
# Press 'n'
# Branch: experiment/cursor-test
# Directory: BPD-Dev-3v4-Cursor-Test

# 2. Set up the worktree
cd /Users/vmars20/20251109/BPD-Dev-3v4-Cursor-Test
git submodule update --init --recursive
uv sync
uv run python scripts/diagnose_moku_env.py  # Verify setup

# 3. Launch Cursor
cursor .

# 4. Try some task with Cursor AI
# Example: Ask Cursor to "add type hints to diagnose_moku_env.py"

# 5. Compare with what Claude Code would do
# (Keep Claude's worktree untouched)

# 6. Commit Cursor's work
git add .
git commit -m "experiment: Cursor AI type hints"
git push origin experiment/cursor-test

# 7. Decide which AI's approach you prefer
# - Merge Cursor's branch if you like it
# - Or delete the worktree and use Claude's approach
ccmanager  # Press 'd' to delete Cursor worktree
```

**What you'll learn:**
- How Cursor's AI differs from Claude Code
- Whether worktree isolation works (spoiler: it will)
- Which tool you prefer for different tasks

---

## Best Practices for Multi-Tool Usage

### 1. One Branch Per Tool

```bash
# Clear ownership
feature/hardware-testing-claude
feature/hardware-testing-cursor
feature/hardware-testing-copilot

# Merge best ideas to main feature branch
feature/hardware-testing  # ← Curated best-of
```

### 2. Diagnostic Check Before Switching

```bash
# Before opening with different tool
cd /path/to/worktree
uv run python scripts/diagnose_moku_env.py

# Ensures environment is clean
```

### 3. Commit Before Switching Tools

```bash
# In Claude worktree
git add .
git commit -m "WIP: Claude's approach to X"

# Switch to Cursor worktree
cd ../BPD-Dev-3v4-Cursor-Test
# Start fresh
```

### 4. Use Tool-Specific Config Files

```bash
# .gitignore additions
.cursor/
.cursorrules
.copilot/
.vscode/settings.json  # If tool-specific
```

### 5. Document Which Tool Did What

```bash
# Commit messages
git commit -m "feat(cursor): Add type hints via Cursor AI"
git commit -m "feat(claude): Refactor with Claude Code"
git commit -m "feat(copilot): Manual edits with Copilot suggestions"
```

---

## What Would Actually Break

**The honest assessment:**

**Would NOT break:**
- ✅ File system (isolated per worktree)
- ✅ Python environments (isolated .venv)
- ✅ Submodules (isolated per worktree)
- ✅ Git (designed for this)
- ✅ Your moku fork setup (per-worktree)

**Might get messy:**
- ⚠️  Commit history (mixed authorship)
- ⚠️  Code style (different AI preferences)
- ⚠️  Git state if committing simultaneously
- ⚠️  Your mental model (which tool did what?)

**Would definitely break:**
- ❌ Using two tools in SAME worktree simultaneously
- ❌ Two tools committing to same branch at same time
- ❌ Not initializing submodules in new worktrees

---

## The Verdict

### Safety Score: 7/10

**Worktrees make this safer than you'd think!**

**Why it works:**
- Worktrees were designed for isolated parallel work
- Each tool gets its own sandbox
- Git handles the coordination
- Your setup (moku fork, diagnostic script) works per-worktree

**Why it might be messy:**
- Different AI styles
- Commit history confusion
- Need discipline about which tool uses which branch

### Recommended Approach

**Start conservative, expand if it works:**

```bash
# Phase 1: Experiment (1 worktree for Cursor)
Create one Cursor worktree on experiment branch
Try a small task
See if you like it

# Phase 2: Tool specialization (if Phase 1 works)
Claude Code: Architecture, refactoring, docs
Cursor: UI work, prototyping
Copilot: Day-to-day coding with autocomplete

# Phase 3: Tool-per-feature (if Phase 2 works)
Each major feature gets one primary AI tool
Other tools for second opinions
```

---

## Quick Decision Matrix

| Scenario | Recommended Setup | Risk Level |
|----------|------------------|------------|
| Just trying Cursor once | New worktree, experiment branch | 🟢 Low |
| Using Copilot alongside Claude | Same worktree OK (just autocomplete) | 🟢 Low |
| Cursor and Claude on different features | Separate worktrees, separate branches | 🟢 Low |
| Multiple tools on same branch | Separate worktrees, coordinate commits | 🟡 Medium |
| Multiple tools in same worktree | DON'T DO THIS | 🔴 High |
| Two tools committing simultaneously | Racing condition, merge conflicts | 🔴 High |

---

## Summary

**Your worktree setup is actually IDEAL for trying multiple AI tools:**

1. **Create dedicated worktree for Cursor:**
   ```bash
   ccmanager  # Create new worktree
   cd new-worktree
   git submodule update --init --recursive
   uv sync
   cursor .
   ```

2. **Keep them on separate branches:**
   - Claude: `feature/Local-Hardware-Testing`
   - Cursor: `experiment/cursor-test`

3. **Merge the best ideas later**

**It would go well, not badly!** Just follow the best practices above.

---

**Last Updated:** 2025-11-09
**Recommendation:** Try it! Worst case, delete the worktree.
