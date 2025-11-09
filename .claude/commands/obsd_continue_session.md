# Obsidian Continue Session

You are resuming an existing Obsidian session with full context load.

## Workflow

### 1. Detect existing sessions
```bash
ls -t Obsidian/Project/Sessions/
```

List most recent first. Show user:
```
Found sessions:
- 2025-11-07-bpd-integration (most recent)
- 2025-11-06-voltage-types
- 2025-11-05-forge-architecture
```

### 2. Ask which session to continue
Default to most recent. User can specify different session.

### 3. Check for session git branch
```bash
git branch --list "sessions/YYYY-MM-DD-description"
```

**If branch exists:**
Ask: "Found branch sessions/YYYY-MM-DD-description. Switch to it?"

If yes:
```bash
git checkout sessions/YYYY-MM-DD-description
```

**If branch doesn't exist:**
Note: "No session branch found, continuing on current branch: [current-branch]"

### 4. Skim recent commits for context
Get commits since session start date:
```bash
git log --oneline --since="YYYY-MM-DD 00:00" --until=now
```

Summarize:
```
📝 Commits since session start:
- Total: 8 commits
- VHDL changes: 5 commits
- Tests: 2 commits
- Documentation: 1 commit
```

Show last 5 commit messages for quick context.

### 5. Load session context files

**Read in this order:**
1. `session-plan.md` - Original session goals and objectives
2. Check `handoffs/` symlinks - List active handoffs
3. Find most recent handoff with `@claude` mention
4. Check previous session's `next-session-plan.md` (if exists)

**Extract key information:**
- Session goal
- Primary objectives (mark completed ✅ vs pending)
- Active handoffs
- Next steps from previous session

### 6. Check git status
```bash
git status
```

Report:
- Working tree clean? (yes/no)
- Modified files: N
- Untracked files: N

### 7. Report comprehensive context summary
```
✅ Session YYYY-MM-DD-description resumed

🌿 Branch: sessions/YYYY-MM-DD-description
📂 Directory: Obsidian/Project/Sessions/YYYY-MM-DD-description/

🎯 Goal: [from session-plan.md]

📝 Active handoffs: N
- handoff-X.md - [Brief description]
- handoff-Y.md - [Brief description]

💾 Recent commits: 8 since session start
- Last commit: [most recent commit message]
- [4 more recent commit summaries]

📋 Session objectives status:
✅ Objective 1 - Complete
🔄 Objective 2 - In progress
⏸️ Objective 3 - Pending

📌 Next steps (from previous session):
1. [Step 1]
2. [Step 2]

🔧 Git status: [clean / X files modified]

Ready to continue!
```

## Context Loading Strategy (PDA Pattern)

**Always load Tier 1 context:**
- Session plan
- Active handoffs with `@claude`
- Recent commit summaries (5-10 commits)
- Git status

**Load Tier 2 if needed (ask user first):**
- Specific handoff details
- Previous session summary (if multi-day)
- Related test results
- Architecture documents

**Do NOT automatically load:**
- All source files (only if user requests)
- Entire git log (just recent summary)
- All handoffs (only active ones with @claude)

## Important Notes

- **Heavy context load** - This command does the work so user doesn't have to
- **PDA pattern** - Start with summaries, drill down as needed
- **Git-aware** - Switch branches, check status, load commits
- **Handoff-aware** - Prioritize handoffs with `@claude` mentions
- **Token-efficient** - Summarize commits, don't dump full logs

## Edge Cases

**No active handoffs:**
- Report: "No active handoffs found"
- Focus on session plan and recent commits

**Multiple @claude mentions:**
- Load most recent handoff
- List others for user to choose

**Session branch merged:**
- Note: "Session branch was merged to main"
- Continue on current branch

**Working tree dirty:**
- Warn: "⚠️ Working tree has uncommitted changes"
- List modified files
- Ask if user wants to review before continuing
