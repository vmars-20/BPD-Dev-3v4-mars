# Simplified Obsidian Workflow Guide

**Purpose:** A streamlined, practical guide for using Obsidian sessions without complexity

---

## The Problem with Current Workflow

The documented workflow has:
- 8 steps to create a session
- 10 steps to close a session
- Dual-commit strategies
- Compaction harvesting
- Handoff symlinks
- Multiple archive files

**This is too complex for daily use.**

---

## Simplified Approach

### Philosophy: Git is the Source of Truth

- **Git commits** = What happened
- **Obsidian notes** = Why and how (context, decisions, plans)
- **Don't duplicate** what git already tracks

### Core Principle: Minimal Viable Session

A session needs:
1. **session-plan.md** - What you're doing (created at start)
2. **session-summary.md** - What you did (created at end)

That's it. Everything else is optional.

---

## Simplified Workflow

### Starting a Session

**Step 1: Create directory**
```bash
mkdir -p Obsidian/Project/Sessions/2025-11-09-description
```

**Step 2: Create session-plan.md**
```markdown
# Session Plan - 2025-11-09-description

**Goal:** [What you're trying to accomplish]

## Objectives
- [ ] Objective 1
- [ ] Objective 2

## Notes
[Any context, blockers, etc.]
```

**Step 3: Commit it**
```bash
git add Obsidian/Project/Sessions/2025-11-09-description/
git commit -m "docs: Start session 2025-11-09-description"
```

**Done.** Start working.

### During Session

- **Do work normally** - Commit code as usual
- **Update session-plan.md** if goals change
- **Create handoffs** if you need to pause mid-task

### Ending a Session

**Step 1: Create session-summary.md**
```markdown
# Session Summary - 2025-11-09-description

**Goal:** [Original goal]
**Status:** ✅ Complete / 🚧 In Progress / ❌ Blocked

## What Was Done
- Accomplishment 1
- Accomplishment 2

## Key Decisions
- Decision 1: [What and why]

## Next Steps
- [ ] Next task 1
- [ ] Next task 2
```

**Step 2: Commit it**
```bash
git add Obsidian/Project/Sessions/2025-11-09-description/
git commit -m "docs: Close session 2025-11-09-description"
```

**Done.** Session closed.

---

## Optional Enhancements (Add Only If Needed)

### If You Want Commit History

Create `commits.md`:
```bash
git log --oneline --since="2025-11-09 00:00" > Obsidian/Project/Sessions/2025-11-09-description/commits.md
```

### If You Want Next Session Plan

Create `next-session-plan.md` (copy from session-summary.md "Next Steps" section)

### If You Have Active Handoffs

Link them in session-plan.md:
```markdown
## Active Handoffs
- [[Obsidian/Project/Handoffs/2025-11-09-handoff-1.md]]
```

---

## Worktree-Specific Notes

**If working in a worktree:**

- Commit session docs to worktree branch (not main)
- Session docs are worktree-specific
- No dual-commit needed (worktree is isolated)

**Example:**
```bash
# In worktree: /Users/vmars20/20251109/3v3Out-Dev
# On branch: 3v3Out-branch

git add Obsidian/Project/Sessions/2025-11-09-description/
git commit -m "docs: Session 2025-11-09-description"
# Commit stays on 3v3Out-branch, that's fine
```

---

## When to Use Handoffs

**Create a handoff when:**
- You're pausing mid-task
- You need to continue work in next session
- There's a blocker requiring human input

**Don't create handoffs for:**
- Completed work (git commits are enough)
- Simple tasks (just note in session-plan.md)
- One-session tasks (session-summary.md is enough)

**Handoff format:**
```markdown
# Handoff - 2025-11-09-description

**Context:** [What was done]
**Next Steps:** [What needs to happen next]
**Blockers:** [Any issues]

@claude please continue with [specific task]
```

---

## Common Patterns

### Pattern 1: Quick Task (1-2 hours)

**Start:**
- Create session-plan.md (5 min)
- Commit it

**End:**
- Create session-summary.md (5 min)
- Commit it

**Total overhead:** 10 minutes

### Pattern 2: Multi-Day Work

**Day 1:**
- Create session-plan.md
- Do work, commit code
- Create handoff if pausing mid-task

**Day 2:**
- Read handoff (or session-summary from Day 1)
- Continue work
- Update session-plan.md if goals change

**Final Day:**
- Create session-summary.md
- Close handoffs
- Commit everything

### Pattern 3: Blocked Work

**When blocked:**
- Create handoff documenting blocker
- Mark session-summary.md as "❌ Blocked"
- Note what needs to happen to unblock

**When unblocked:**
- Read handoff
- Continue work
- Close handoff when done

---

## What NOT to Do

### ❌ Don't Create Empty Files

If you didn't make decisions, don't create `decisions.md` with "No decisions made"

### ❌ Don't Duplicate Git History

Git already tracks commits. Only create `commits.md` if you want formatted summary.

### ❌ Don't Over-Engineer

If a simple note in session-plan.md works, don't create separate files.

### ❌ Don't Force Structure

If you don't need handoffs, don't create them. If you don't need next-session-plan.md, skip it.

---

## Comparison: Complex vs Simple

### Complex Workflow (Current)

**Start session:**
1. Ask for goal
2. Propose session ID
3. Ask about git branch
4. Create directory
5. Create session-plan.md from template
6. Search for active handoffs
7. Create symlinks
8. Load previous session context
9. Commit to session branch
10. Commit to main (dual-commit)

**Close session:**
1. Detect session
2. Verify session to close
3. Check token usage
4. Process compaction (if >80%)
5. Generate commits.md
6. Generate decisions.md
7. Generate next-session-plan.md
8. Generate session-summary.md
9. Review with user
10. Commit archive
11. Handle session branch merge
12. Clean up handoffs

**Total:** 22 steps

### Simple Workflow (Proposed)

**Start session:**
1. Create directory
2. Create session-plan.md
3. Commit

**Close session:**
1. Create session-summary.md
2. Commit

**Total:** 5 steps

---

## Migration Path

### For Existing Sessions

**Session 2025-11-09 (incomplete):**
1. Create session-summary.md marking as "not started"
2. Commit it
3. Done

**Future sessions:**
- Use simplified workflow
- Add optional files only if needed

### For Handoffs

**Existing handoffs:**
- Keep them
- Link in session-plan.md if relevant
- Close when work complete

**New handoffs:**
- Create only when pausing mid-task
- Keep format simple
- Close when done

---

## FAQ

**Q: What about compaction harvesting?**  
A: If token usage >80%, run `/compact` manually. Copy summary to session-summary.md if helpful. Don't automate it.

**Q: What about session branches?**  
A: Only create if you want isolated git history. Otherwise, work on current branch.

**Q: What about dual-commit to main?**  
A: Only needed if session branch will be deleted. In worktrees, commit to worktree branch only.

**Q: What about templates?**  
A: Use them if helpful, but don't feel obligated. Simple markdown is fine.

**Q: What about wikilinks?**  
A: Use them if you're actually using Obsidian UI. Otherwise, regular markdown links work.

---

## Success Criteria

**A workflow is "great" when:**
- ✅ Takes <5 minutes to start session
- ✅ Takes <5 minutes to close session
- ✅ Doesn't get in the way of actual work
- ✅ Provides value (context, decisions, plans)
- ✅ Feels natural, not burdensome

**If it doesn't meet these, simplify more.**

---

**Created:** 2025-11-09  
**Author:** @claude (workflow simplification)  
**Status:** Proposal - Review and adapt as needed
