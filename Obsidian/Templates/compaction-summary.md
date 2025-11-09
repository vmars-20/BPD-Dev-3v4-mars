---
session_id: <% tp.file.title %>
compaction_time: <% tp.date.now("YYYY-MM-DD HH:mm") %>
---

# Context Compaction Summary - <% tp.file.title %>

## Purpose
This file captures the raw output from Claude's `/compact` command, which generates a structured summary of the entire conversation when context usage is high (>80%).

## Raw Summary Output

<!-- Paste the full compaction summary that Claude receives after you run /compact -->

```
[Paste compaction summary here]
```

## Extraction Notes

**This summary was used to generate:**
- `commits.md` - Extracted commit history and file changes
- `decisions.md` - Extracted key technical decisions and rationale
- `next-session-plan.md` - Extracted pending tasks and next steps
- `session-summary.md` - Human-readable executive summary

**Benefits of compaction-based session archiving:**
- ✅ Complete conversation capture (not human memory)
- ✅ Structured extraction (chronological, technical, errors)
- ✅ Token-optimized (preserves critical details)
- ✅ Consistent format across sessions

## Usage
1. At session end, check token usage
2. If >80%, run `/compact` command
3. Claude receives structured summary
4. Run `/obsd_close_session` to harvest summary
5. This file preserves raw compaction output
