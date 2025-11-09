---
session_id: 2025-11-07-network-connectivity
created: 2025-11-07
type: exploration-session
status: deferred
priority: P2
---

# Session Plan: Network Connectivity for Moku Hardware

## Session Scope

**Goal:** Implement and test network connectivity solution for accessing Moku hardware from remote environments

**Status:** DEFERRED - Initial exploration complete, implementation pending

## Background

During the BPD Debug Bus session, we discovered the need for network connectivity to access Moku hardware from Claude Code Web UI containers. Initial exploration has been completed and documented.

## Starting Point

**Exploration Complete:** `Obsidian/Project/network-tunneling-exploration.md`

Key findings:
- Container has Python but limited networking tools
- Moku uses HTTP on port 80
- Multiple viable solutions identified
- Questions need answering before implementation

## Objectives (When Resumed)

1. **Answer key questions:**
   - Static or dynamic public IP?
   - Port forwarding possible?
   - SSH server available?
   - VPS/relay server available?
   - Security requirements?

2. **Select approach based on answers:**
   - Option A: Direct port forwarding (simplest)
   - Option B: SSH reverse tunnel (most flexible)
   - Option C: Cloud relay service (most robust)

3. **Implement chosen solution:**
   - Set up network infrastructure
   - Test connectivity
   - Document configuration
   - Create helper scripts

4. **Validate with real hardware:**
   - Test moku-deploy.py over tunnel
   - Test bpd-debug.py over tunnel
   - Measure latency
   - Verify reliability

## Dependencies

**Tools Available:**
- `scripts/moku-deploy.py` - Deployment tool (complete)
- Network exploration document (complete)

**Tools Needed:**
- Selected tunneling solution
- Network configuration
- Security credentials

## Success Criteria

- [ ] Network solution selected based on requirements
- [ ] Tunnel/connectivity established
- [ ] Moku API accessible from remote environment
- [ ] Latency < 100ms for instrument control
- [ ] Solution documented and reproducible
- [ ] Security properly configured

## Files to Review When Resuming

1. `Obsidian/Project/network-tunneling-exploration.md` - Full exploration results
2. `scripts/moku-deploy.py` - Tool that needs connectivity
3. This session plan

## Notes

**Why Deferred:**
- Main BPD development can proceed locally
- Network connectivity is enhancement, not blocker
- Better to focus on core functionality first
- Can revisit when remote access becomes critical

**When to Resume:**
- After Phase 2/3 complete locally
- When remote collaboration needed
- When hardware permanently available
- When security requirements defined

## Quick Resume Command

When ready to resume this session:
```
/obsd_continue_session 2025-11-07-network-connectivity
```

---

**Session Type:** Exploration/Infrastructure
**Estimated Time:** 2-3 hours (when resumed)
**Priority:** P2 (enhancement, not critical path)