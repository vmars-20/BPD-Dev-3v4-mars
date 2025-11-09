# Obsidian Session Quick Start - Simplified Workflow

**This is the simple way. 5 steps total.**

---

## Starting a Session (3 steps)

```bash
# 1. Create directory
mkdir -p Obsidian/Project/Sessions/2025-11-09-your-goal

# 2. Create session-plan.md (copy template below)
# 3. Commit it
git add Obsidian/Project/Sessions/2025-11-09-your-goal/
git commit -m "docs: Start session 2025-11-09-your-goal"
```

**session-plan.md template:**
```markdown
# Session Plan - 2025-11-09-your-goal

**Goal:** [What you're trying to accomplish]

## Objectives
- [ ] Objective 1
- [ ] Objective 2

## Notes
[Any context, blockers, etc.]
```

**Done!** Now just work normally and commit code as usual.

---

## Ending a Session (2 steps)

```bash
# 1. Create session-summary.md (copy template below)
# 2. Commit it
git add Obsidian/Project/Sessions/2025-11-09-your-goal/
git commit -m "docs: Close session 2025-11-09-your-goal"
```

**session-summary.md template:**
```markdown
# Session Summary - 2025-11-09-your-goal

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

**Done!** Session closed.

---

## That's It!

- **Start:** 3 steps (create dir, create plan, commit)
- **End:** 2 steps (create summary, commit)
- **Total:** 5 steps

No slash commands needed. No complex workflows. Just simple markdown files.

---

## Optional: Handoffs (Only If Needed)

**Create a handoff when pausing mid-task:**

```markdown
# Handoff - 2025-11-09-description

**Context:** [What was done]
**Next Steps:** [What needs to happen next]
**Blockers:** [Any issues]

@claude please continue with [specific task]
```

Save to: `Obsidian/Project/Handoffs/2025-11-09-handoff-1.md`

---

## Worktree Notes

**If in a worktree (like you are now):**
- Commit to worktree branch (3v3Out-branch)
- No need to commit to main
- Session docs stay with worktree

---

**See:** `Obsidian/Project/Review/SIMPLIFIED_WORKFLOW_GUIDE.md` for full details
