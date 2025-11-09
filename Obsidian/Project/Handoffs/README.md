# Handoffs

**Purpose:** Session continuation notes for work that spans multiple Claude sessions

---

## Directory Structure (Date-Based)

**Current organization:**
```
Handoffs/
├── YYYY-MM-DD/              # Date-based subdirectories
│   ├── handoff-file-1.md
│   └── handoff-file-2.md
└── README.md                # This file
```

**Example:**
```
Handoffs/
├── 2025-11-06/              # 6 handoffs
├── 2025-11-07/              # 5 handoffs
├── 2025-11-08/              # 1 session start prompt
└── README.md
```

**Benefits:**
- Clean date-based grouping (matches Sessions/ structure)
- Easy to find handoffs from specific sessions
- Scalable for long-term projects
- Quick timeline identification

---

## What Are Handoffs?

Handoff notes capture context when:
- Session ends mid-task (work incomplete)
- Complex work requires multiple sessions
- Need to preserve decision context
- Blocked on human input or external dependency

**Key principle:** Handoffs are **ephemeral** - delete after work is committed to git. Git history is the permanent record.

---

## Naming Convention

**Format:** `YYYY-MM-DD/<YYYY-MM-DD-handoff-N-description>.md`

**Examples:**
- `2025-11-06/2025-11-06-handoff-1-fix-forge-vhdl-types.md`
- `2025-11-07/2025-11-07-handoff-6-hierarchical-voltage-encoding.md`
- `2025-11-08/2025-11-08-start-handoff-9-hardware-validation.md`

**Why this format:**
- `YYYY-MM-DD/` subdirectory - Groups by date
- `YYYY-MM-DD-handoff-N-` prefix - Maintains chronological sort within directory
- `<description>` - Quick topic identification
- `.md` - Markdown format

---

## When to Create

**DO create handoff when:**
- ✅ Session ending with incomplete work
- ✅ Multi-step task needing continuation
- ✅ Complex context that's hard to recreate
- ✅ Blocked on decision/input

**DON'T create handoff when:**
- ❌ Work completed and committed
- ❌ Simple task (can restart from scratch easily)
- ❌ Already documented in git commit message

---

## Template Usage

**Using Templater in Obsidian:**
1. Create new file: `2025-11-06-1500-topic.md`
2. Command palette: "Templater: Insert Template"
3. Choose: `handoff.md`
4. Fill in placeholders
5. Use `@claude` to indicate continuation needed

**See:** [[Obsidian/Templates/README|Templates README]]

---

## Lifecycle

```
1. Create handoff
   ↓
2. Commit to git (if mid-work)
   ↓
3. Next session reads handoff
   ↓
4. Work continues
   ↓
5. Work completed & committed to git
   ↓
6. Delete handoff (history now in git)
```

---

## What to Include

**Essential sections:**
- **What was done** - Completed work this session
- **What's next** - Specific next steps with `@claude`
- **Blockers** - Issues/decisions with `@human` if needed
- **Files modified** - Wikilinks to relevant files
- **Context** - Resources, commands, external references

**See template for full structure:** [[Obsidian/Templates/handoff.md]]

---

## Finding Handoffs

```bash
# List all date directories
ls -lt Obsidian/Project/Handoffs/

# List handoffs from specific date
ls -lt Obsidian/Project/Handoffs/2025-11-07/

# Find handoffs needing Claude action (recursive)
grep -r "@claude" Obsidian/Project/Handoffs/

# Find handoffs needing human input (recursive)
grep -r "@human" Obsidian/Project/Handoffs/

# Search by topic (recursive)
grep -r "voltage" Obsidian/Project/Handoffs/

# List all handoffs across all dates
find Obsidian/Project/Handoffs -name "*.md" -type f | grep -v README
```

---

## Cleanup Strategy

**When to delete:**
- Work committed to git (history preserved)
- Context no longer relevant
- Replaced by new handoff

**Command:**
```bash
# After committing work - delete individual handoff
rm Obsidian/Project/Handoffs/2025-11-07/2025-11-07-handoff-8-cocotb-test-execution.md
git add -u
git commit -m "docs: Clean up completed handoff"

# Or remove entire date directory if all handoffs complete
rm -rf Obsidian/Project/Handoffs/2025-11-06/
git add -u
git commit -m "docs: Archive 2025-11-06 handoffs (all complete)"
```

**Keep if:**
- Work still in progress
- Reference for similar future work
- Contains important decision context

---

## Related Documentation

- [[Obsidian/Project/README]] - Full system overview
- [[Obsidian/Templates/handoff.md]] - Handoff template
- [[.claude/handoffs/README.md]] - Historical examples (different system)

---

**Created:** 2025-11-06
**Last Updated:** 2025-11-06