# Obsidian Integration for Session Management

**Status:** Fully integrated - See `Obsidian/Project/README.md` for complete documentation

---

## What Is This?

This repo includes an Obsidian-based workspace for managing development sessions, handoffs, and collaboration between you and Claude.

**Key Features:**
- 📝 Session tracking with `/obsd_new_session`, `/obsd_continue_session`, `/obsd_close_session` slash commands
- 🔄 Context compaction harvesting (40-50x compression of Claude conversations)
- 🌿 Optional git branch per session for clean history
- 💾 Automatic session archiving (commits.md, decisions.md, next-session-plan.md)

---

## Quick Start

### Option 1: Use Slash Commands (Recommended)

```bash
# In Claude Code:
/obsd_new_session       # Start new session with goals
/obsd_continue_session  # Resume previous session
/obsd_close_session     # Archive session + harvest /compact summary
```

### Option 2: Manual Workflow

1. **Open Obsidian vault at repo root** (`/Users/johnycsh/20251109/BPD-Dev-3v4/`)
2. **Create session note** in `Obsidian/Project/Sessions/YYYY-MM-DD-description/`
3. **Use wikilinks** to reference code: `[[CLAUDE.md]]`, `[[libs/forge-vhdl/llms.txt]]`
4. **Use @mentions** for delegation:
   - `@claude` - Claude should act on this
   - `@human` - You need to make a decision

---

## Directory Structure

```
Obsidian/Project/
├── README.md          ← START HERE for complete documentation
├── Handoffs/          ← Mid-session continuation notes
├── Sessions/          ← Daily session archives (auto-generated)
└── Templates/         ← Templater templates for notes
```

---

## When to Use

**Use Obsidian sessions when:**
- Starting multi-day development work
- Want to preserve context between Claude sessions
- Need to document decisions and next steps
- Token usage >80% and need context compaction

**Skip Obsidian when:**
- Quick one-off tasks
- Just reading code or docs
- Simple bug fixes

---

## Complete Documentation

**For full details, workflows, and examples:**

👉 **See: `Obsidian/Project/README.md`** ← Complete guide

**Key related files:**
- `.claude/commands/obsd_new_session.md` - New session command
- `.claude/commands/obsd_continue_session.md` - Continue session command
- `.claude/commands/obsd_close_session.md` - Close session command
- `Obsidian/Project/Sessions/README.md` - Session management patterns

---

## Integration with Development

**Obsidian complements git, doesn't replace it:**

| Tool | Purpose | Source of Truth |
|------|---------|-----------------|
| **Git** | Code, commits, branches | What was built |
| **Obsidian** | Planning, decisions, context | Why and how |
| **Claude Code** | Implementation, testing | Execution |

**Workflow:**
1. Plan session in Obsidian (`/obsd_new_session`)
2. Implement in Claude Code (commits to git)
3. Archive session in Obsidian (`/obsd_close_session`)
4. Next session continues from session archive + git history

---

## Why Vault-at-Repo-Root?

**Design decision:** Obsidian vault root = Git repository root

**Benefits:**
- ✅ Wikilinks work naturally: `[[CLAUDE.md]]`, `[[libs/forge-vhdl/llms.txt]]`
- ✅ No path conflicts between Obsidian and git
- ✅ Code and docs unified in one navigation system
- ✅ Portable across machines (just clone repo + open in Obsidian)

---

## Not Using Obsidian?

**That's fine!** All core development workflows work without Obsidian:

- Read `CLAUDE.md` for architecture
- Read `llms.txt` files for quick reference
- Use git for history and context
- Session management is optional

Obsidian is a productivity enhancement, not a requirement.

---

**Created:** 2025-11-09
**See:** `Obsidian/Project/README.md` for complete documentation
