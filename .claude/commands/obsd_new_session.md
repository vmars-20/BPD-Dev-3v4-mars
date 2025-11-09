# Obsidian New Session

You are creating a new Obsidian session with defined scope and optional git branch.

## Workflow

### 1. Ask for session scope/goal
```
"What's the goal for this session?"
```

Examples:
- "BPD integration testing"
- "Voltage type system refactor"
- "Hardware validation with oscilloscope"

### 2. Propose session ID
Format: `YYYY-MM-DD-description` (slugified goal)

Example: `2025-11-07-bpd-integration`

Ask user to confirm or modify.

### 3. Git branch strategy
Ask: "Create a session git branch or work on current branch?"

**If new branch:**
- Ask: "Branch from 'main' or current branch '[current-branch]'?"
- Create branch: `git checkout -b sessions/YYYY-MM-DD-description`

**If current branch:**
- Note current branch in session metadata
- Proceed without branching

### 4. Create session directory
```bash
mkdir -p Obsidian/Project/Sessions/YYYY-MM-DD-description/handoffs
```

### 5. Create session-plan.md
Use template: `Obsidian/Templates/session-plan.md`

Pre-fill with:
- Session ID (from step 2)
- Goal (from step 1)
- Git branch (from step 3)
- Created timestamp

Ask user for:
- Primary objectives (3-5 items)
- Expected tasks (5-10 items)
- Success criteria (3-5 items)

### 6. Search for active handoffs
```bash
grep -r "@claude" Obsidian/Project/Handoffs/
```

If found, ask: "Found N handoffs with @claude. Link them to this session?"

If yes, create symlinks:
```bash
cd Obsidian/Project/Sessions/YYYY-MM-DD-description/handoffs/
ln -s ../../../Handoffs/YYYY-MM-DD/handoff-X.md handoff-X.md
```

### 7. Load previous session context (if continuing work)
Check if previous session exists with `next-session-plan.md`:
```bash
ls -t Obsidian/Project/Sessions/*/next-session-plan.md | head -1
```

If found, read and incorporate into current session plan.

### 8. Commit session docs to main (CRITICAL!)

**IMPORTANT:** Always commit session docs to main, even if working on a session branch.
This ensures docs are accessible regardless of branch state.

```bash
# If on session branch, stash or commit any work-in-progress
git add Obsidian/Project/Sessions/YYYY-MM-DD-description/

# Commit to current branch first
git commit -m "docs: Create session YYYY-MM-DD-description

Session goal: [brief goal]
Branch: sessions/YYYY-MM-DD-description (or current)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# If on session branch, also commit to main
if [ "$(git branch --show-current)" != "main" ]; then
    current_branch=$(git branch --show-current)
    git checkout main
    git cherry-pick HEAD  # Or merge if preferred
    git checkout "$current_branch"
fi
```

### 9. Report session creation
```
✅ Session YYYY-MM-DD-description created

📂 Directory: Obsidian/Project/Sessions/YYYY-MM-DD-description/
🌿 Branch: sessions/YYYY-MM-DD-description (or current branch name)
📝 Committed to: main + session branch ✓
🎯 Goal: [user's goal]
📝 Active handoffs: N linked

📋 Session Plan:
[Summary of objectives and tasks]

Ready to start!
```

## Important Notes

- **Session ID format:** Always `YYYY-MM-DD-description` (date + slugified goal)
- **Git branch naming:** `sessions/YYYY-MM-DD-description` (if creating branch)
- **Handoff symlinks:** Use relative paths `../../../Handoffs/...`
- **ALWAYS commit to main:** Session docs must be accessible from main branch
- **Dual-commit strategy:** Commit to session branch, then cherry-pick/merge to main

## Files Created

```
Obsidian/Project/Sessions/YYYY-MM-DD-description/
├── session-plan.md          # Pre-filled from template
└── handoffs/                # Symlinks to active handoffs (if any)
    └── handoff-X.md → ../../../Handoffs/YYYY-MM-DD/handoff-X.md
```

## Edge Cases

**Multiple sessions same day:**
- Use suffixes: `2025-11-07-morning-bpd`, `2025-11-07-afternoon-voltage`
- Or: `2025-11-07-bpd-1`, `2025-11-07-bpd-2`

**No active handoffs:**
- Create empty `handoffs/` directory
- Note in session plan: "No active handoffs"

**Continuing multi-day work:**
- Load previous `next-session-plan.md`
- Link same handoffs as previous session
- Update session plan with continuation context
