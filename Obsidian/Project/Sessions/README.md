# Session Archives

**Purpose:** Daily session wrap-ups capturing work accomplished, decisions made, and next steps planned.

---

## Structure

Each session gets a date-based directory:

```
Sessions/
└── YYYY-MM-DD/
    ├── session-summary.md       # High-level summary of the day's work
    ├── commits.md                # All commits with full messages and context
    ├── decisions.md              # Key architectural/design decisions
    ├── next-session-plan.md      # Tomorrow's starting point and priorities
    └── handoffs/                 # Symbolic links to active handoffs
        ├── handoff-X.md → ../../Handoffs/...
        └── ...
```

---

## Purpose

### session-summary.md
- **What:** Executive summary of the session
- **Contains:**
  - Main objective and status
  - Major milestones achieved
  - Architecture changes
  - Testing results
  - Blockers encountered
  - Session statistics

### commits.md
- **What:** Complete log of all commits from the day
- **Contains:**
  - Commits organized by topic/handoff
  - Full commit messages
  - Files changed
  - Impact summary

### decisions.md
- **What:** Key technical and architectural decisions
- **Contains:**
  - Decision context and rationale
  - Trade-offs considered
  - Alternatives evaluated
  - Validation results
  - Impact assessment

### next-session-plan.md
- **What:** Roadmap for tomorrow's session
- **Contains:**
  - Primary objectives
  - Context to load
  - Expected tasks
  - Success criteria
  - Potential issues and solutions
  - Time estimates

### handoffs/
- **What:** Symbolic links to active handoffs
- **Purpose:** Quick access to relevant handoff documents without navigation

---

## Session Management Slash Commands

**Recommended workflow - use these slash commands instead of manual creation:**

### `/obsd_new_session` - Start New Session
Creates session directory with plan, optional git branch, links handoffs.

**See:** `.claude/commands/obsd_new_session.md`

### `/obsd_continue_session` - Resume Session
Loads session context, checks git status, skims recent commits.

**See:** `.claude/commands/obsd_continue_session.md`

### `/obsd_close_session` - Archive Session
Generates archive files, optionally harvests `/compact` summary, commits.

**See:** `.claude/commands/obsd_close_session.md`

---

## Manual Usage (If Not Using Slash Commands)

### At Session End

1. **Create directory:**
   ```bash
   mkdir -p Obsidian/Project/Sessions/YYYY-MM-DD/handoffs
   ```

2. **Generate summaries:**
   - Review commits: `git log --oneline --since="YYYY-MM-DD 00:00"`
   - Fill in session-summary.md (use template)
   - Document commits in commits.md
   - Capture decisions in decisions.md
   - Plan next session in next-session-plan.md

3. **Link active handoffs:**
   ```bash
   cd Obsidian/Project/Sessions/YYYY-MM-DD/handoffs
   ln -s ../../../Handoffs/handoff-X.md handoff-X.md
   ```

4. **Commit everything:**
   ```bash
   git add Obsidian/Project/Sessions/YYYY-MM-DD/
   git commit -m "docs: Session wrap-up for YYYY-MM-DD"
   git push
   ```

### At Session Start

**Recommended:** Use `/obsd_continue_session` command (auto-loads all context)

**Manual alternative:**
1. **Read previous session summary:**
   ```bash
   cat Obsidian/Project/Sessions/YYYY-MM-DD/session-summary.md
   ```

2. **Load next-session-plan.md:**
   - Review objectives
   - Load recommended context (Tier 1 files)
   - Check prerequisites

3. **Check git status:**
   ```bash
   git status
   git log -1  # See last commit
   ```

4. **Start work** following the plan

---

## Template

**Location:** `Obsidian/Templates/session-summary.md`

**Usage (Obsidian):**
1. Create new note: `Obsidian/Project/Sessions/YYYY-MM-DD/session-summary.md`
2. Open command palette: `Cmd+P`
3. Search: "Templater: Insert Template"
4. Select: "session-summary"
5. Fill in placeholders

**Usage (Manual):**
```bash
cp Obsidian/Templates/session-summary.md \
   Obsidian/Project/Sessions/YYYY-MM-DD/session-summary.md
```

Then edit and replace:
- `{{date:YYYY-MM-DD}}` → Actual date
- `[Placeholders]` → Actual content

---

---

## Context Compaction Integration

**Key Innovation:** Sessions can harvest the `/compact` command output!

### How It Works

1. At session end, check token usage
2. If >80%, run user command: `/compact`
3. Claude receives structured summary internally
4. Run `/obsd_close_session` (second time)
5. Claude extracts summary → session archive files automatically

### Benefits of Compaction-Based Archiving

- ✅ **Complete capture** - Full conversation, not human memory
- ✅ **Structured extraction** - Chronological, technical, errors, decisions
- ✅ **Token-optimized** - 40-50x compression while preserving critical details
- ✅ **Consistent format** - Same structure every time

### Compaction Files

```
Sessions/YYYY-MM-DD/
├── compaction-summary.md    # Raw /compact output (reference)
├── session-summary.md       # Parsed human-readable summary
├── commits.md               # Extracted from compaction
├── decisions.md             # Extracted from compaction
└── next-session-plan.md     # Extracted from pending tasks
```

**See:** `.claude/commands/obsd_close_session.md` for implementation details

---

## Benefits

### For Humans
- ✅ Quick catch-up after breaks
- ✅ Context preservation across sessions
- ✅ Decision history for future reference
- ✅ Clear next steps

### For AI Agents
- ✅ Efficient context loading (read summary first)
- ✅ Token-efficient vs re-reading all commits
- ✅ Decision rationale available
- ✅ Clear delegation points (next-session-plan)

### For Project Management
- ✅ Daily progress tracking
- ✅ Velocity measurement (commits/day, handoffs/day)
- ✅ Blocker identification
- ✅ Milestone tracking

---

## Integration with Existing Obsidian Structure

### Handoffs
- **Location:** `Obsidian/Project/Handoffs/`
- **Relationship:** Sessions reference handoffs (via symlinks)
- **Lifecycle:** Handoffs are ephemeral (deleted after commit), sessions preserve history

### Test Reports
- **Location:** `Obsidian/Project/Test-Reports/`
- **Relationship:** Sessions link to test reports in summary
- **Lifecycle:** Test reports are permanent (committed)

### Architecture Documents
- **Location:** `Obsidian/Project/Architecture/`, `Obsidian/Project/Review/`
- **Relationship:** Decisions reference architecture docs
- **Lifecycle:** Architecture docs are permanent

---

## Session Archive Index

### 2025-11-07
**Objective:** Hierarchical encoder testing and BPD integration validation
**Status:** ✅ Complete
**Handoffs:** 6, 7, 8, 8.5
**Next:** Handoff 9 (hardware validation)

---

## Best Practices

### DO
- ✅ Create session summary at end of day
- ✅ Document all decisions with rationale
- ✅ Link to handoffs for context
- ✅ Plan next session before ending
- ✅ Commit session archive to git

### DON'T
- ❌ Delay session wrap-up (context loss)
- ❌ Skip decision rationale (future confusion)
- ❌ Forget to link active handoffs
- ❌ Leave next-session-plan empty
- ❌ Store binary files (use screenshots in separate dir)

---

## Maintenance

**Cleanup Policy:**
- Session archives are permanent (committed to git)
- Handoff symlinks may break if handoffs are moved/deleted (expected)
- Update README index when adding new sessions

**Backup:**
- All session archives committed to git
- No local-only content

---

**Created:** 2025-11-07
**Version:** 1.0
**Maintained By:** Project team
