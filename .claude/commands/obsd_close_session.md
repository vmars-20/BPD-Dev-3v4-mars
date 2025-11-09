# Obsidian Close Session

You are archiving an Obsidian session and optionally harvesting context compaction summary.

## Workflow

### 1. Detect current session
Check most recent session directory:
```bash
ls -t Obsidian/Project/Sessions/ | head -1
```

Or check current git branch for `sessions/` prefix:
```bash
git branch --show-current
```

### 2. Verify session to close
Ask user: "Close session YYYY-MM-DD-description?"

Show:
- Session ID
- Git branch (if session branch exists)
- Session start date
- Current duration (estimate from git log)

### 3. Check token usage
Look for system messages about token usage.

**If >80% token usage:**
```
⚠️ Token usage: X%

Recommend running /compact before closing to harvest full conversation summary.

After running /compact, re-run /obsd_close_session to process the compaction summary.
```

Wait for user to:
1. Run `/compact` command
2. Re-run `/obsd_close_session`

### 4. Process compaction summary (if available)
If this is the second invocation (after /compact), you will have received a structured compaction summary.

**Extract to files:**
```
Obsidian/Project/Sessions/YYYY-MM-DD-description/
├── compaction-summary.md    # Raw compaction output (use template)
├── session-summary.md       # Human-readable summary (parsed from compaction)
├── commits.md               # Extracted commit history
├── decisions.md             # Extracted key decisions
└── next-session-plan.md     # Extracted pending tasks
```

**Extraction guidance:**
- **compaction-summary.md:** Paste full raw summary from /compact
- **session-summary.md:** Parse compaction "Overview" + "Major Accomplishments"
- **commits.md:** Parse compaction "Commits" section
- **decisions.md:** Parse compaction "Key Technical Concepts" + "Technical Decisions"
- **next-session-plan.md:** Parse compaction "Pending Tasks" section

### 5. Generate session archive files (manual flow)

If NO compaction summary (token usage <80%), generate manually:

**commits.md:**
```bash
git log --oneline --since="YYYY-MM-DD 00:00" --until=now
```

Format as:
```markdown
# Commits - YYYY-MM-DD-description

## Summary
Total: N commits

## Full Log
[commit-hash] commit message
[Files changed, impact]

## By Category
**VHDL changes:** N commits
**Tests:** N commits
**Documentation:** N commits
```

**decisions.md:**
Ask user: "What were the key technical decisions this session?"

Format as:
```markdown
# Key Decisions - YYYY-MM-DD-description

## Decision 1: [Title]
**Context:** ...
**Decision:** ...
**Rationale:** ...
**Alternatives:** ...
```

**next-session-plan.md:**
Ask user: "What should the next session focus on?"

Or check session-plan.md for uncompleted objectives.

Format as:
```markdown
# Next Session Plan - YYYY-MM-DD-description

## Primary Objectives
- [ ] Objective 1
- [ ] Objective 2

## Context to Load
**Tier 1:**
- File 1
- File 2

## Prerequisites
- Prerequisite 1

## Expected Duration
X hours
```

**session-summary.md:**
Use existing template or create simplified version combining:
- Session goal (from session-plan.md)
- Major accomplishments (ask user or from commits)
- Status (complete/in-progress/blocked)
- Statistics (commit count, files modified, tests added)

### 6. Review with user
Show summary:
```
📦 Session archive generated:

✅ compaction-summary.md (raw /compact output)
✅ session-summary.md
✅ commits.md (N commits)
✅ decisions.md (N decisions)
✅ next-session-plan.md

Looks good?
```

### 7. Commit session archive

**IMPORTANT:** Always commit to main, even if on session branch (ensures docs accessible from main).

```bash
cd Obsidian/Project/Sessions/YYYY-MM-DD-description/
git add .

# Commit to current branch
git commit -m "docs: Session archive for YYYY-MM-DD-description

- Total commits: N
- Major accomplishments: [brief summary]
- Next session: [brief next steps]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# If on session branch, also commit to main
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    git checkout main
    git cherry-pick HEAD
    git checkout "$current_branch"
    echo "✓ Session archive committed to both $current_branch and main"
fi
```

### 8. Handle session git branch (if exists)
If session was on dedicated branch `sessions/YYYY-MM-DD-description`:

Ask: "Merge sessions/YYYY-MM-DD-description → main?"

**If yes:**
```bash
git checkout main
git merge sessions/YYYY-MM-DD-description
git push
```

**If no:**
Note: "Session branch preserved for later merge"

### 9. Optional: Clean up completed handoffs
```bash
find Obsidian/Project/Handoffs/ -type f -name "*.md"
```

Check which handoffs are referenced in session and ask:
"Delete N completed handoffs?"

If yes:
```bash
rm Obsidian/Project/Handoffs/YYYY-MM-DD/handoff-X.md
git add -u
git commit -m "docs: Clean up completed handoffs from YYYY-MM-DD session"
```

### 10. Final report
```
✅ Session YYYY-MM-DD-description closed

📦 Archive: Obsidian/Project/Sessions/YYYY-MM-DD-description/
   - session-summary.md
   - commits.md (N commits)
   - decisions.md (N decisions)
   - next-session-plan.md
   - compaction-summary.md (if /compact was used)

🌿 Branch: merged to main / preserved / no session branch

📝 Handoffs: N cleaned up / preserved

💾 Committed: [commit hash]

🚀 Next session ready to start with /obsd_new_session or /obsd_continue_session
```

## Two-Phase Flow (Compaction)

### Phase 1: Pre-compaction check
```
1. Detect session
2. Check token usage
3. If >80%: "Run /compact, then re-run this command"
4. Exit, wait for user
```

### Phase 2: Post-compaction archive
```
1. Detect session (same as phase 1)
2. Harvest compaction summary (available in context)
3. Extract to files
4. Generate remaining files
5. Commit and report
```

**How to detect phase:**
- Phase 1: No compaction summary in recent context
- Phase 2: Compaction summary present (check recent messages)

## Important Notes

- **Two-phase for compaction** - Check token usage first, process summary second
- **Graceful degradation** - If no compaction, generate manually (less comprehensive)
- **Git integration** - Handle session branches, commits, merges
- **Handoff cleanup** - Optional, user decides
- **Final commit required** - Archive must be committed before closing

## Edge Cases

**Token usage <80%, no compaction:**
- Generate archive files manually
- Less comprehensive but still valuable

**Session incomplete/blocked:**
- Mark in session-summary.md as "🚧 In Progress" or "❌ Blocked"
- Don't clean up handoffs
- Preserve session branch (don't merge)

**Multiple sessions same day:**
- Close each independently
- Handoffs may be shared across sessions (don't delete if still referenced)

**Working tree dirty:**
- Warn: "⚠️ Uncommitted changes outside session archive"
- List files
- Ask: "Continue closing session anyway?"
