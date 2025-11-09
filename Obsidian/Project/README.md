@R# Project Workspace

**Purpose:** Obsidian-based workspace for agent-human collaboration within a git repository

This directory provides a lightweight system for Claude and humans to collaborate using Obsidian notes that live alongside code.

---

## Core Design Principles

### 1. Git-First History
- **Git commits are the source of truth** for what happened and when
- Obsidian notes are **active working memory**, not permanent archive
- Once work is committed to git, notes can be deleted/archived

### 2. Vault-at-Repo-Root
- Obsidian vault root = Git repository root (`../` from here)
- Enables wikilinks to any file: `[[CLAUDE.md]]`, `[[libs/forge-vhdl/llms.txt]]`
- No path conflicts between Obsidian navigation and code structure

### 3. Simple Attention Routing
- Use `@claude` to request Claude take action
- Use `@human` when human decision/input needed
- Searchable via grep: `grep -r "@claude" Obsidian/Project/`

---

## Directory Structure

```
Obsidian/Project/
├── README.md          (this file - START HERE)
├── Handoffs/          Session continuation notes (date-organized)
├── Sessions/          Daily session archives (YYYY-MM-DD/)
└── Test-Reports/      Test results and validation reports
```

**PDA Pattern (Progressive Disclosure of Architecture):**

For **Obsidian collaboration context**, use this entry point:
1. **Start:** `Obsidian/Project/README.md` (this file)
2. **Dive:** Specific subdirectory READMEs (Handoffs/, Sessions/)
3. **Details:** Individual handoff/session files

This parallels the monorepo-level pattern (`llms.txt → CLAUDE.md → source`) but for collaboration/session context instead of code/architecture context.

### Handoffs/
**Purpose:** Session handoff notes for continuation between Claude sessions

**Structure:** Date-based subdirectories (YYYY-MM-DD/)
- Example: `Handoffs/2025-11-07/2025-11-07-handoff-6-hierarchical-voltage-encoding.md`

**When to create:**
- Session ends mid-task (incomplete work)
- Complex multi-step work requiring multiple sessions
- Blocked on human input or external dependency
- Need to preserve context for future work

**Lifecycle:**
1. Created by Claude at end of session
2. Read by Claude/human at start of next session
3. Deleted/archived after work committed to git

**See:** [[Obsidian/Project/Handoffs/README|Handoffs README]]

### Sessions/
**Purpose:** Daily session archives capturing completed work, decisions, and next steps

**Structure:** Date-based directories with standardized files:
```
Sessions/YYYY-MM-DD/
├── session-summary.md       # Executive summary
├── commits.md               # All commits with context
├── decisions.md             # Architectural decisions
├── next-session-plan.md     # Tomorrow's roadmap
└── handoffs/                # Symbolic links to active handoffs
```

**Lifecycle:**
1. Created at end of each session (wrap-up)
2. Committed to git (permanent record)
3. Read at start of next session for context

**See:** [[Obsidian/Project/Sessions/README|Sessions README]]

---

## Conventions

### Date Format
**Always use:** `YYYY-MM-DD` (ISO 8601)
- Handoff filenames: `YYYY-MM-DD-HHMM-topic.md`
- Date fields in notes: `2025-11-06`

### Attention Routing
**Use @ mentions for delegation:**
- `@claude` - Claude should act on this
- `@human` - Human decision/input required

**Examples:**
```markdown
## Next Steps
@claude please implement the voltage type system using the pattern from [[libs/forge-vhdl/llms.txt]]

## Blockers
@human which approach do you prefer? See options below.
```

### Wikilinks
**Link to code files directly:**
- `[[CLAUDE.md]]` - Root architecture doc
- `[[libs/forge-vhdl/vhdl/packages/forge_common_pkg.vhd]]` - VHDL file
- `[[Obsidian/Templates/handoff.md]]` - Other Obsidian notes

**Absolute paths from vault root** (configured in `.obsidian/app.json`)

---

## Templates

See [[Obsidian/Templates/README|Templates README]] for available Templater templates.

**Available templates:**
- `handoff.md` - Session handoff note
- `prompt.md` - Reusable prompt
- `task.md` - Task tracking note

**Using templates:**
1. Create new note in appropriate directory
2. Insert template via Templater hotkey (or command palette)
3. Fill in placeholders
4. Use `@claude` or `@human` to route attention

---

## Session Management Slash Commands

### Three-Command Lifecycle

**Manage sessions efficiently with these slash commands:**

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/obsd_new_session` | Create new session with goals | Starting fresh work |
| `/obsd_continue_session` | Resume existing session | Continuing previous work |
| `/obsd_close_session` | Archive session + harvest `/compact` | Ending session |

**Quick Start:**
```
1. /obsd_new_session
   → Creates session-plan.md
   → Optional: Creates git branch (sessions/YYYY-MM-DD-description)
   → Links active handoffs

2. [Work happens, commits made]

3. /obsd_close_session
   → Checks token usage (recommend /compact if >80%)
   → Harvests compaction summary (if available)
   → Generates session archive (5-6 files)
   → Commits to git
   → Optional: Merges session branch
```

**Key Feature:** `/obsd_close_session` can harvest the context compaction summary from `/compact` command, turning it into structured session archive files automatically!

**See:** `.claude/commands/obsd_*` for detailed behavior

---

## Workflow Examples

### Example 1: New Session with Slash Command
```markdown
# User starts session
/obsd_new_session

# Claude asks: "What's the goal for this session?"
User: "BPD integration testing"

# Claude creates:
Obsidian/Project/Sessions/2025-11-07-bpd-integration/
├── session-plan.md          # Pre-filled with goal
└── handoffs/                # Links to active handoffs

# Claude reports:
"✅ Session 2025-11-07-bpd-integration created
 📂 Ready to start!"
```

### Example 2: Session Handoff (Manual)
```markdown
# End of Claude session
1. Create note: Obsidian/Project/Handoffs/2025-11-06-1500-fsm-debug.md
2. Document: What was done, what's next, blockers
3. Add: "@claude please continue debugging FSM observer"
4. Save note

# Start of next Claude session
1. Read: Obsidian/Project/Handoffs/2025-11-06-1500-fsm-debug.md
2. Load referenced files
3. Continue work
4. Once complete: Delete handoff (work now in git history)
```

### Example 2: Reusable Prompt
```markdown
# Discovered useful pattern
1. Create note: Obsidian/Project/Prompts/analyze-vhdl-register-mapping.md
2. Document: Purpose, prompt text, usage notes
3. Commit to git (permanent documentation)

# Later session
1. Reference: [[Obsidian/Project/Prompts/analyze-vhdl-register-mapping.md]]
2. Copy prompt text
3. Apply to current task
```

### Example 3: Human Decision Needed
```markdown
# Claude encounters decision point
1. Document options in note
2. Add: "@human which approach: A (fast) or B (clean)?"
3. Wait for human response

# Human reviews
1. Reads note
2. Adds decision: "@claude use approach B, cleaner long-term"
3. Claude continues in next response
```

---

## Integration with Git

### What Gets Committed
**DO commit:**
- ✅ Reusable prompts (`Prompts/`)
- ✅ Active handoffs (if work in progress)
- ✅ Important decision records

**DON'T commit (or clean up later):**
- ❌ Completed handoffs (after work committed)
- ❌ Temporary scratch notes
- ❌ Session-specific debugging notes

### Commit Strategy
```bash
# Commit reusable prompts immediately
git add Obsidian/Project/Prompts/<new-prompt>.md
git commit -m "docs: Add prompt for <task>"

# Commit handoffs if mid-work
git add Obsidian/Project/Handoffs/<handoff>.md
git commit -m "docs: Add handoff for <ongoing-task>"

# Clean up completed handoffs
rm Obsidian/Project/Handoffs/<completed-handoff>.md
git add -u
git commit -m "docs: Clean up completed handoffs"
```

---

## Relationship to .claude/

**`.claude/` directory:**
- Agent definitions (specialized AI agents)
- Shared knowledge docs (architecture, context management)
- Historical handoffs (examples from template development)

**`Obsidian/Project/` directory:**
- Active work notes (current session context)
- Reusable prompts (user-facing library)
- Ephemeral collaboration (deleted after completion)

**Key difference:**
- `.claude/` = Infrastructure for agents
- `Obsidian/Project/` = User workspace for collaboration

**See:** [[.claude/shared/CONTEXT_MANAGEMENT.md]] for how agents load context

---

## Quick Reference

### Finding Notes
```bash
# List all handoffs (chronological)
ls -lt Obsidian/Project/Handoffs/

# Find notes needing Claude's attention
grep -r "@claude" Obsidian/Project/

# Find notes needing human attention
grep -r "@human" Obsidian/Project/

# Search for topic
grep -r "voltage type" Obsidian/Project/
```

### Creating Notes
```bash
# Via Templater (in Obsidian)
1. Create new file in Obsidian/Project/Handoffs/
2. Name: 2025-11-06-1500-topic.md
3. Cmd+P → "Templater: Insert Template"
4. Choose: handoff.md

# Via command line
touch Obsidian/Project/Handoffs/2025-11-06-1500-topic.md
# Edit manually
```

---

## For Claude: How to Use This System

### Starting a Session

**Entry point:** Read this file first (Obsidian/Project/README.md)

**Then navigate to:**
- **Previous session:** `Sessions/YYYY-MM-DD/session-summary.md` (if continuing work)
- **Active handoffs:** `Handoffs/YYYY-MM-DD/` (if mid-task)
- **Next session plan:** `Sessions/YYYY-MM-DD/next-session-plan.md` (for today's priorities)

**Context loading (PDA pattern):**
1. Obsidian/Project/README.md (you are here)
2. Sessions/YYYY-MM-DD/session-summary.md (if continuing work)
3. Specific handoffs or session files as needed

### When you see a note with `@claude`:

1. **Read the note** - Understand context and request
2. **Load referenced resources** - Use wikilinks to find related files
3. **Perform requested action** - Execute the task
4. **Update the note** - Document what you did
5. **Route back if needed** - Use `@human` if you need input

### When creating a handoff at end of session:

1. **Use template** - Start from `Obsidian/Templates/handoff.md`
2. **Be specific** - Exact files, commands, next steps
3. **Use @claude** - Make it clear you need continuation
4. **Link to resources** - Use wikilinks to code files
5. **Save in Handoffs/YYYY-MM-DD/** - Follow date-based structure

### When wrapping up a session:

1. **Create session archive** - `Sessions/YYYY-MM-DD/`
2. **Use template** - Start from `Obsidian/Templates/session-summary.md`
3. **Fill in details** - Summary, commits, decisions, next steps
4. **Commit everything** - Session archive + any handoffs
5. **Clean state** - Ensure working tree clean

---

## Related Documentation

- [[Obsidian/Templates/README]] - Template system
- [[.claude/shared/CONTEXT_MANAGEMENT.md]] - How agents load context
- [[CLAUDE.md]] - Repository architecture (root)
- [[.claude/handoffs/README.md]] - Historical handoff examples

---

**Created:** 2025-11-06
**Last Updated:** 2025-11-06
**Maintained By:** Development Team