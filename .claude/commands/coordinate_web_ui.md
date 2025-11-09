# Coordinate Web UI Sessions

You are helping coordinate parallel Claude Code Web UI sessions for distributed task execution.

## Your Role

Act as the **orchestrator** for parallel Web UI workers. You manage handoffs, track progress, and merge results.

## Workflow

### 1. Assess Current State

```bash
# Check branch status
git branch -v
git status

# Check for active Web UI branches
git fetch origin
git branch -r | grep claude/

# Review pending tasks
# (Check todo list if using TodoWrite)
```

### 2. Prepare Handoffs

**For each task to delegate:**

a) Create handoff point:
```bash
# Ensure everything is on main
git checkout main
git merge sessions/[current] --no-ff

# Create clear handoff commit
git commit --allow-empty -m "🎯 WEB UI HANDOFF: [Task name]

[Detailed description of what needs to be done]
Files to read: [list files]
Expected output: [describe deliverables]"

git push origin main
```

b) Generate quick-start card:
```markdown
Create: Obsidian/Project/Sessions/[session]/[task]-quickstart.md

Contents:
- Copy-paste message for Web UI
- Clear requirements
- Test commands
- Success criteria
```

### 3. Launch Workers

For each parallel task:
1. User opens new Claude Code Web UI session
2. User pastes quick-start message
3. Worker begins independently

Track active workers:
```markdown
| Task | Branch | Status | Started |
|------|--------|--------|---------|
| Task 1 | claude/abc... | In Progress | 10:00 |
| Task 2 | claude/xyz... | In Progress | 10:05 |
```

### 4. Monitor Progress

```bash
# Check for completed work
git fetch origin
git branch -r | grep claude/

# For each completed branch:
git log origin/claude/[branch] --oneline -5
```

### 5. Merge Results

**Option A: Via GitHub PR**
- Direct user to create PR
- Review changes
- Merge on GitHub
- Pull locally

**Option B: Local Merge**
```bash
git fetch origin
git merge origin/claude/[branch] --no-ff
git push origin main
```

**Option C: Cherry-pick**
```bash
git cherry-pick [commit-hash]
```

### 6. Clean Up

```bash
# Update todos
# Archive completed quick-start cards
# Document results in session notes
```

## Key Commands

### Status Check
Show:
- Active Web UI branches
- Pending tasks
- Recent merges

### Create Handoff
1. Pick task from todo list
2. Create handoff commit
3. Generate quick-start card
4. Report ready for Web UI

### Merge Complete
1. Fetch Web UI branch
2. Review changes
3. Merge to main
4. Update todos

### Generate Report
Summary of:
- Tasks completed
- Time saved through parallelization
- Next recommended tasks

## Best Practices

1. **Keep tasks independent** - No dependencies between Web UI workers
2. **Clear communication** - Handoff messages must be self-contained
3. **Fresh contexts** - Each worker gets 200k tokens
4. **Atomic commits** - Each task produces mergeable result
5. **Review before merge** - Check Web UI's work

## Example Usage

```
User: /coordinate_web_ui