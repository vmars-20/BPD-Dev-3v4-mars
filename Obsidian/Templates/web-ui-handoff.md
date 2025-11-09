---
created: <% tp.date.now("YYYY-MM-DD") %>
type: web-ui-handoff
priority: P1
status: pending
web_ui_branches: []
merged_branches: []
---

# Web UI Handoff: <% tp.file.cursor(1) %>

**Date:** <% tp.date.now("YYYY-MM-DD HH:mm") %>
**Session:** <% tp.file.cursor(2) %>
**Execution:** Web UI Worker
**Estimated Time:** <% tp.file.cursor(3) %>

---

## Task Description

<% tp.file.cursor(4) %>

---

## Quick-Start Message for Web UI

```
Copy this entire message to Claude Code Web UI:

<% tp.file.cursor(5) %>

Starting from commit: <% tp.file.cursor(6) %> on main branch

Please read:
1. <% tp.file.cursor(7) %>

Requirements:
- <% tp.file.cursor(8) %>

Test with:
<% tp.file.cursor(9) %>

Note: You'll be on branch claude/[auto-generated]. This is expected.
Time budget: <% tp.file.cursor(10) %>
```

---

## Expected Web UI Branch

**Pattern:** `claude/[task-description]-[unique-id]`
**Example:** `claude/migrate-tool-yaml-abc123def`

**To track after Web UI starts:**
```bash
git fetch origin
git branch -r | grep claude/
```

---

## Files Web UI Will Create/Modify

1. **`<% tp.file.cursor(11) %>`**
   - <% tp.file.cursor(12) %>

---

## Validation Commands

**For Web UI to test:**
```bash
<% tp.file.cursor(13) %>
```

---

## Merging Web UI Work

**After Web UI completes:**

### Option A: GitHub PR
1. Web UI provides PR link
2. Review changes on GitHub
3. Click "Squash and merge"
4. Pull locally: `git pull origin main`

### Option B: Local Merge
```bash
# Fetch Web UI branch
git fetch origin
git branch -r | grep claude/  # Find the branch

# Merge locally
git merge origin/claude/[branch-name] --no-ff -m "feat: [description]"
git push origin main

# Clean up
git push origin --delete claude/[branch-name]
```

### Option C: Cherry-pick
```bash
# Get specific commits
git cherry-pick [commit-hash]
```

---

## Success Criteria

- [ ] <% tp.file.cursor(14) %>
- [ ] Tests pass with dry-run
- [ ] Clear commit messages
- [ ] Branch ready for merge

---

## Tracking Web UI Branches

**Active Web UI Branch:** `[filled after launch]`
**Status:** `[pending | in-progress | complete | merged]`
**PR Link:** `[if created]`
**Merged Commit:** `[after merge]`

---

## Related Handoffs

**Parallel Tasks:** [[<% tp.file.cursor(15) %>]]
**Dependencies:** [[<% tp.file.cursor(16) %>]]
**Next Phase:** [[<% tp.file.cursor(17) %>]]

---

## Completion Log

**Web UI Started:** <time>
**Web UI Branch:** `claude/...`
**Completed:** <time>
**Merged:** <commit hash>
**Cleanup:** Branch deleted ✓

---

**Created:** <% tp.date.now("YYYY-MM-DD HH:mm") %>
**Status:** Pending Web UI Execution
**Coordination Pattern:** Web UI Worker (see Web-UI-Coordination-Pattern.md)