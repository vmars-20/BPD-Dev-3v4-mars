# Templates

**Purpose:** Templater templates for creating consistent Obsidian notes

---

## Available Templates

### 1. `handoff.md`
**Purpose:** Session handoff notes for multi-session work

**Use when:**
- Session ends mid-task
- Need to preserve complex context
- Blocked on decision/input

**Creates:**
- Context section (what was done)
- Next steps with `@claude` routing
- Blockers with `@human` routing
- Files/resources/success criteria

**Output location:** `Obsidian/Project/Handoffs/`

---

### 2. `prompt.md`
**Purpose:** Reusable prompt library entries

**Use when:**
- Found useful analysis pattern
- Want to standardize workflow
- Creating repeatable operation

**Creates:**
- Purpose statement
- Prompt text (copy/paste ready)
- Usage notes and examples
- Related files

**Output location:** `Obsidian/Project/Prompts/`

---

### 3. `task.md`
**Purpose:** Task tracking with agent/human delegation

**Use when:**
- Planning multi-step work
- Coordinating agent and human actions
- Tracking discrete tasks

**Creates:**
- Task description
- Action items (`@claude` and `@human`)
- Context and success criteria
- Related files

**Output location:** Anywhere in `Obsidian/Project/`

---

### 4. `session-plan.md`
**Purpose:** Session planning with goals and objectives

**Use when:**
- Starting new session via `/obsd_new_session`
- Continuing session via `/obsd_continue_session`
- Manually planning ad-hoc sessions

**Creates:**
- Session ID and git branch metadata
- Primary objectives (checklist)
- Expected tasks
- Active handoffs list
- Success criteria

**Output location:** `Obsidian/Project/Sessions/YYYY-MM-DD-description/`

**Note:** Usually auto-created by slash commands, not manual

---

### 5. `session-summary.md`
**Purpose:** End-of-session wrap-up with accomplishments

**Use when:**
- Closing session via `/obsd_close_session`
- Manually documenting session results

**Creates:**
- Session overview and status
- Major accomplishments
- Commit summary (see commits.md)
- Key decisions (see decisions.md)
- Statistics and next steps

**Output location:** `Obsidian/Project/Sessions/YYYY-MM-DD-description/`

**Note:** Part of complete session archive (5-6 files total)

---

### 6. `compaction-summary.md`
**Purpose:** Preserve raw context compaction output

**Use when:**
- `/obsd_close_session` after running `/compact` command
- Token usage >80% and compaction was used

**Creates:**
- Raw compaction summary output
- Extraction notes for other files
- Usage documentation

**Output location:** `Obsidian/Project/Sessions/YYYY-MM-DD-description/`

**Note:** Only created when `/compact` is used (high token usage)

---

## Using Templates

### In Obsidian (Recommended)

1. **Create new note** in appropriate directory
   - Handoffs: `Obsidian/Project/Handoffs/2025-11-06-1500-topic.md`
   - Prompts: `Obsidian/Project/Prompts/analyze-topic.md`
   - Tasks: `Obsidian/Project/task-topic.md`

2. **Insert template**
   - Command Palette: `Cmd/Ctrl+P`
   - Type: `Templater: Insert Template`
   - Choose template

3. **Fill placeholders**
   - Press `Tab` to jump between cursor positions
   - Fill in each `<% tp.file.cursor(N) %>` placeholder

4. **Save** - Template variables will populate

---

## Template Syntax

These templates use **Templater plugin** syntax:

### Date/Time
- `<% tp.date.now("YYYY-MM-DD") %>` - Current date (ISO 8601)
- `<% tp.date.now("YYYY-MM-DD HH:mm") %>` - Date and time

### Cursors
- `<% tp.file.cursor(1) %>` - Jump to position 1
- Press `Tab` to move to next cursor position

### Frontmatter
```yaml
---
created: <% tp.date.now("YYYY-MM-DD") %>
type: handoff
---
```

**Note:** No JavaScript used - simple Templater syntax only

---

## Configuring Templater

**Check plugin settings:**
1. Settings → Templater
2. Template folder location: `Obsidian/Templates`
3. Trigger Templater on new file creation: Enabled (optional)
4. Enable folder templates: Enabled (optional)

**Folder templates (optional):**
- Set `Obsidian/Project/Handoffs/` → `handoff.md`
- Set `Obsidian/Project/Prompts/` → `prompt.md`

---

## Frontmatter Fields

All templates use consistent frontmatter:

### Common Fields
- `created` - Creation date (YYYY-MM-DD)
- `type` - Note type (handoff/prompt/task)

### Type-Specific
- **Handoff:** `status` (active/complete)
- **Task:** `status` (open/in-progress/complete), `priority` (high/medium/low)

**Used for:**
- Dataview queries (if plugin installed)
- Filtering/searching
- Metadata tracking

---

### 7. `web-ui-handoff.md`
**Purpose:** Handoff tasks to Claude Code Web UI workers

**Use when:**
- Delegating task to Web UI for parallel execution
- Need fresh 200k token context
- Task is independent and self-contained

**Creates:**
- Quick-start message for Web UI
- Branch tracking fields
- Merge instructions
- Success criteria

**Key features:**
- Tracks `claude/[task]-[id]` branches
- Provides merge strategies (PR, local, cherry-pick)
- Documents branch lifecycle

**Output location:** `Obsidian/Project/Sessions/[session]/` or `Obsidian/Project/Handoffs/`

---

### 8. `web-ui-tracker.md`
**Purpose:** Track multiple parallel Web UI workers and their branches

**Use when:**
- Running multiple Web UI sessions in parallel
- Need to monitor branch status
- Coordinating merges from multiple workers

**Creates:**
- Active worker table
- Branch monitoring commands
- Completion log
- Cleanup tracking
- Parallelization statistics

**Output location:** `Obsidian/Project/Sessions/[session]/`

---

## Customization

### Adding New Templates
1. Create `.md` file in `Obsidian/Templates/`
2. Use Templater syntax: `<% tp.date.now() %>`, `<% tp.file.cursor(N) %>`
3. Add frontmatter with `created` and `type`
4. Document in this README

### Modifying Templates
1. Edit template file directly
2. Changes apply to new notes only (existing notes unchanged)
3. Update this README if structure changes

---

## Session Management Slash Commands

**For session templates (4, 5, 6 above), use these slash commands:**

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/obsd_new_session` | Create new session with plan | Starting fresh work |
| `/obsd_continue_session` | Resume existing session | Continuing previous work |
| `/obsd_close_session` | Archive session with summary | Ending session |

**Workflow:**
1. `/obsd_new_session` → Creates session-plan.md
2. [Work happens, commits made]
3. `/obsd_close_session` → Creates session archive (5-6 files)

**See:** `.claude/commands/obsd_*` for detailed slash command behavior

---

## Related Documentation

- [Templater Plugin Docs](https://silentvoid13.github.io/Templater/)
- [[Obsidian/Project/README]] - Project workspace overview
- [[Obsidian/Project/Handoffs/README]] - Handoff conventions
- [[Obsidian/Project/Sessions/README]] - Session management guide
- [`.claude/commands/obsd_new_session.md`](../../.claude/commands/obsd_new_session.md) - New session command
- [`.claude/commands/obsd_continue_session.md`](../../.claude/commands/obsd_continue_session.md) - Continue session command
- [`.claude/commands/obsd_close_session.md`](../../.claude/commands/obsd_close_session.md) - Close session command

---

**Created:** 2025-11-06
**Last Updated:** 2025-11-07