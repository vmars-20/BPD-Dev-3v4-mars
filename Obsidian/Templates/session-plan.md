---
session_id: <% tp.file.title %>
created: <% tp.date.now("YYYY-MM-DD HH:mm") %>
git_branch: <% await tp.system.prompt("Git branch (or 'main' if no session branch)") %>
---

# Session Plan - <% tp.file.title %>

## Session Scope
**Goal:** <% await tp.system.prompt("High-level session goal") %>

## Primary Objectives
- [ ]
- [ ]
- [ ]

## Expected Tasks
1.
2.
3.

## Active Handoffs
<!-- Auto-populated by /obsd_new_session or /obsd_continue_session -->

## Context to Load (Tier 1)
**Always load first:**
- [ ]
- [ ]

**Tier 2 (if needed):**
- [ ]

## Success Criteria
- [ ]
- [ ]

## Notes
<!-- Session-specific notes, blockers, decisions -->
