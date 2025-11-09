# Obsidian Update Session (Mid-Session Commit)

**Purpose:** Commit session progress to main during active session work (not just at close).

**When to use:**
- After completing a significant milestone
- Before switching branches temporarily
- To ensure session docs are always accessible from main
- When creating/updating handoffs mid-session

---

## Workflow

### 1. Detect current session
```bash
git branch --show-current
# If on sessions/YYYY-MM-DD-description, extract session ID
```

Or ask user: "Which session to update?" if unclear.

### 2. Check for uncommitted changes in session directory
```bash
git status Obsidian/Project/Sessions/YYYY-MM-DD-description/
```

### 3. Stage and commit session updates

**If on session branch:**
```bash
# Stage session docs
git add Obsidian/Project/Sessions/YYYY-MM-DD-description/

# Commit to session branch
git commit -m "docs: Update session YYYY-MM-DD-description progress

[Brief description of what was added/updated]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Cherry-pick to main (critical step!)
current_branch=$(git branch --show-current)
git checkout main
git cherry-pick "$current_branch"
git checkout "$current_branch"
```

**If already on main:**
```bash
# Just commit normally
git add Obsidian/Project/Sessions/YYYY-MM-DD-description/
git commit -m "docs: Update session YYYY-MM-DD-description progress

[Brief description]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 4. Confirm and report
```
✅ Session progress committed

📂 Session: YYYY-MM-DD-description
🌿 Committed to: main + sessions/YYYY-MM-DD-description
💾 Commit: [hash]

Updated files:
- [list files that changed]

Session work continues...
```

---

## When to Use This Command

### Use Cases
1. **After major milestone:** Completed Phase 1, moving to Phase 2
2. **New handoff created:** Added handoff document mid-session
3. **Before context switch:** Need to switch branches, want docs preserved
4. **Periodic backup:** Long session, commit progress every ~2 hours
5. **Before `/compact`:** Ensure docs committed before clearing context

### Don't Use When
- Only code changes (not session docs) - use regular git workflow
- Session just started - wait until meaningful progress
- About to close session - use `/obsd_close_session` instead

---

## Important Notes

- **Always commit to main:** This is the core principle - session docs must be on main
- **Cherry-pick is preferred:** Cleaner than merge for single-commit updates
- **Don't skip this:** Without it, docs are stranded on session branch
- **Session branch is working area:** Main is the source of truth for docs
