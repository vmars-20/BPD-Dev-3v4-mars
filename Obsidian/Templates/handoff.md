---
created: <% tp.date.now("YYYY-MM-DD") %>
type: handoff
priority: P1
status: pending
depends_on:
git_commits: []
---

# Handoff: <% tp.file.cursor(1) %>

**Date:** <% tp.date.now("YYYY-MM-DD HH:mm") %>
**Session:** <% tp.file.cursor(2) %>
**Owner:** @claude (with @human review)
**Dependencies:** <% tp.file.cursor(3) %>
**Estimated Time:** <% tp.file.cursor(4) %>

---

## Context: What Needs to Be Done

<% tp.file.cursor(5) %>

---

## What I Just Did (Previous Handoff)

<% tp.file.cursor(6) %>

---

## Next Steps

@claude please:

<% tp.file.cursor(7) %>

---

## Files to Modify

1. **`<% tp.file.cursor(8) %>`**
   - <% tp.file.cursor(9) %>

---

## Validation Steps

@claude after making changes:

1. **<% tp.file.cursor(10) %>**
   ```bash
   <% tp.file.cursor(11) %>
   ```

---

## Resources

**Reference:**
- <% tp.file.cursor(12) %>

**Documentation:**
- <% tp.file.cursor(13) %>

**Commands:**
```bash
<% tp.file.cursor(14) %>
```

---

## Success Criteria

- [ ] <% tp.file.cursor(15) %>

---

## Blockers

@human <% tp.file.cursor(16) %>

---

## Handoff Chain

**This handoff:** <% tp.file.cursor(17) %> of <% tp.file.cursor(18) %>
**Next handoff:** [[<% tp.file.cursor(19) %>]]
**Previous:** [[<% tp.file.cursor(20) %>]]

---

## Completion Summary

**Completed:** <completion date and time>
**Git Commit:** `<commit hash>` - "<commit message>"
**Validation Results:**
```
<validation output>
```

---

**Created:** <% tp.date.now("YYYY-MM-DD HH:mm") %>
**Status:** Pending
**Priority:** P1 (blocks next handoff)
**Dependencies:** <dependencies from front matter>
