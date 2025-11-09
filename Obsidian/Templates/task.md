---
created: <% tp.date.now("YYYY-MM-DD") %>
type: task
status: open
---

# Task: <% tp.file.cursor(1) %>

## Description

<% tp.file.cursor(2) %>

---

## Action Items

### For Claude
- [ ] @claude <% tp.file.cursor(3) %>

### For Human
- [ ] @human <% tp.file.cursor(4) %>

---

## Context

**Why:**
<% tp.file.cursor(5) %>

**Success looks like:**
<% tp.file.cursor(6) %>

---

## Related Files

- [[<% tp.file.cursor(7) %>]]

---

## Notes

<% tp.file.cursor(8) %>

---

**Created:** <% tp.date.now("YYYY-MM-DD HH:mm") %>
**Status:** Open
**Priority:** <% tp.file.cursor(9) %>
