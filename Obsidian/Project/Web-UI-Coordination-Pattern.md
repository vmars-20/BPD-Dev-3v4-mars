---
created: 2025-11-07
type: architectural-pattern
status: authoritative
---

# Web UI Coordination Pattern

## Executive Summary

A workflow pattern for leveraging Claude Code Web UI sessions in parallel to accomplish multiple tasks simultaneously, with local CLI coordination and bi-directional synchronization through GitHub.

**Key Innovation:** Using Obsidian session management + Web UI's independent branches to enable massive parallelization of development tasks.

---

## The Pattern

### 1. Local Coordination (CLI)
The local Claude CLI acts as the **orchestrator**:
- Creates session plans and handoffs
- Manages git branches and merges
- Tracks progress via TodoWrite
- Maintains session continuity

### 2. Web UI Workers (Parallel)
Multiple Web UI sessions act as **specialized workers**:
- Each gets its own `claude/[task-id]` branch
- Works independently from a common base commit
- Can run in parallel without conflicts
- Produces atomic, mergeable results

### 3. Bi-directional Sync
GitHub acts as the **synchronization hub**:
- Web UI pushes to `claude/*` branches
- Local CLI pulls and merges results
- PRs optional but recommended for review
- Clean history maintained on main

---

## Workflow Architecture

```
┌─────────────────────────────────────────────┐
│          LOCAL CLI (Orchestrator)           │
│                                              │
│  • Creates session plans                    │
│  • Generates handoff documents              │
│  • Manages git branches                     │
│  • Tracks todos                             │
│  • Merges completed work                    │
└────────────┬──────────────┬─────────────────┘
             │              │
             ▼              ▼
    ┌───────────────┐ ┌───────────────┐
    │   Web UI #1   │ │   Web UI #2   │
    │               │ │               │
    │ Phase 1 Task  │ │  Exploration  │
    │ claude/abc... │ │ claude/xyz... │
    └───────┬───────┘ └───────┬───────┘
            │                  │
            ▼                  ▼
    ┌──────────────────────────────────┐
    │         GitHub Repository        │
    │                                   │
    │  main ← claude/abc...            │
    │      ← claude/xyz...             │
    └───────────────────────────────────┘
```

---

## Implementation Guide

### Step 1: Create Handoff Point

In local CLI:
```bash
# Merge all current work to main
git checkout main
git merge sessions/[current-session]

# Create handoff commit
git commit --allow-empty -m "🎯 WEB UI HANDOFF: [Task description]"
git push origin main
```

### Step 2: Generate Quick-Start Card

Create a quick-start document with:
- Clear task description
- Files to read
- Expected deliverables
- Success criteria
- Time budget

Template:
```markdown
## Copy This to Claude Code Web UI:

I need to [TASK DESCRIPTION].

Starting point: commit [HASH] on main branch.

Please read:
1. [Document 1]
2. [Document 2]

Requirements:
- [Requirement 1]
- [Requirement 2]

Test with:
[Test commands]

Time budget: [X] minutes
```

### Step 3: Launch Web UI Workers

Open multiple Claude Code Web UI sessions:
- Each session gets the quick-start message
- They work independently
- No coordination needed between them

### Step 4: Merge Results

When Web UI completes:
```bash
# Fetch their branch
git fetch origin

# Option A: Create PR on GitHub
# Option B: Merge locally
git merge origin/claude/[task-id]

# Option C: Cherry-pick specific commits
git cherry-pick [commit-hash]
```

---

## Use Cases

### 1. Parallel Development
- **Phase 1:** Build tool A (Web UI #1)
- **Phase 2:** Build tool B (Web UI #2)
- **Phase 3:** Documentation (Web UI #3)

All run simultaneously!

### 2. Exploration + Implementation
- **Worker 1:** Explore solutions
- **Worker 2:** Implement known parts
- **Worker 3:** Write tests

### 3. Multi-Architecture Testing
- **Worker 1:** Test on Linux
- **Worker 2:** Test on macOS simulation
- **Worker 3:** Test with different Python versions

---

## Best Practices

### DO:
- ✅ Create clear handoff commits on main
- ✅ Write comprehensive quick-start cards
- ✅ Use descriptive task descriptions
- ✅ Set time budgets for each task
- ✅ Review changes before merging
- ✅ Keep tasks independent when possible

### DON'T:
- ❌ Have Web UI workers depend on each other
- ❌ Forget to push handoff to origin
- ❌ Skip the review step
- ❌ Overcomplicate the handoff messages

---

## Coordination Slash Command

Create `.claude/commands/coordinate_web_ui.md`:

```markdown
# Coordinate Web UI

You are helping coordinate parallel Web UI sessions.

## Workflow

1. Check current status:
   - What's on main?
   - What sessions are active?
   - What tasks are pending?

2. Create handoff points:
   - Merge to main
   - Create handoff commit
   - Generate quick-start cards

3. Track progress:
   - Monitor Web UI branches
   - Merge completed work
   - Update todos

4. Report status:
   - Completed tasks
   - Active workers
   - Next steps
```

Usage: `/coordinate_web_ui`

---

## Success Metrics

### Efficiency Gains
- **Sequential:** Task A (2hr) → Task B (2hr) → Task C (1hr) = 5 hours
- **Parallel:** Max(Task A, Task B, Task C) = 2 hours
- **Speedup:** 2.5x faster!

### Quality Benefits
- Each task gets fresh context (200k tokens)
- No context pollution between tasks
- Clean git history
- Reviewable changes

---

## Real-World Example

Today's session (2025-11-07-bpd-debug-bus):

1. **Local CLI:** Created session plan, handoffs, architecture docs
2. **Web UI #1:** Built moku-deploy.py (90 min)
3. **Web UI #2:** Explored network tunneling (45 min)
4. **Result:** Both tasks completed in parallel, merged successfully!

Time saved: ~45 minutes (ran concurrently instead of sequentially)

---

## Troubleshooting

### Web UI Can't Find Files
**Solution:** Ensure files are committed and pushed to main

### Merge Conflicts
**Solution:** Keep tasks independent, work on different files

### Lost Web UI Branch
**Solution:** Check GitHub branches page, all claude/* branches are preserved

### Accidentally Closed PR
**Solution:** Fetch branch and merge locally (as we did today!)

---

## Future Enhancements

1. **Automated Orchestration:** Script to generate handoffs automatically
2. **Status Dashboard:** Web UI to track all active workers
3. **Result Aggregation:** Automatic PR creation for completed tasks
4. **Performance Metrics:** Track time saved through parallelization

---

## Conclusion

The Web UI Coordination Pattern enables massive parallelization of development tasks by treating Web UI sessions as distributed workers coordinated by a local CLI orchestrator. This pattern is especially powerful for:

- Independent tasks that can run in parallel
- Exploration vs implementation separation
- Multi-platform or multi-configuration testing
- Documentation generation alongside development

**Key Insight:** Every Web UI session is a fresh 200k token context that can work independently. Use them like distributed compute nodes!

---

**Pattern Status:** AUTHORITATIVE
**First Used:** 2025-11-07 (BPD Debug Bus Session)
**Proven Results:** 2.5x speedup on parallel tasks