---
created: 2025-11-07 10:52
for: Quick resume after break
---

 ● Where should the platform testing framework live within the repository?
   → forge-vhdl extension
 ● What testing priority should we focus on for Phase 1 MVP?
   → BPD FSM validation
 ● Should we create a specialized 'platform-testing' agent or reuse existing infrastructure?
   → I think we should include a phase in the PLAN to review the best approach (however your context window right now is
   probably perfect prepared for this, so now might be good)

   Also, althouh these are not __strictly__ necessary for the platform-testing, the following YML files describe,
   authoritatively, the Moku_Config setup that we will ultimately be aiming for

   see @bpd-deployment-setup1-dummy-dut.yaml and @bpd-deployment-setup2-real-dut.yaml
 ● Which advanced features should be included in the phased plan?
   → Multi-channel capture, Routing simulation, Trigger modes, The 'routing simulation' will be sufficient if it gracefully
   handles the 2-slot setup showin in @bpd-deployment-setup1-dummy-dut.yaml

   One last thing: The platform simulator should include __explicit__ primitives for setting the MCC CR's **over the network**
  
   this primitive will introduce real world amounts of delay (on the order of 200ms) and is used to draw a clear and well
   defined boundary between the 'outside world' (that is will ultimately be driven by a python script inputting values over the
   networked CRs)

   does that all make sense
   
# 🚀 QUICK START - Phase 2: bpd-debug.py

## Copy & Paste to New Context:

```
I need to continue Phase 2 of the BPD Debug Bus session.

Current status:
- Phase 1 COMPLETE: scripts/moku-deploy.py works with YAML
- Phase 2 READY: Build bpd-debug.py

Please read:
1. Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/phase2-handoff.md
2. Obsidian/Project/Sessions/2025-11-07-bpd-debug-bus/PLAN.md (for context)

Task: Build scripts/bpd-debug.py with:
- BPDController class (FORGE control + registers)
- BPDDebugDecoder class (14-bit HVS decoder)
- CLI interface with --dry-run support

Key files needed:
- scripts/lib/bpd_controller.py - FORGE CR0[31:29] control
- scripts/lib/bpd_decoder.py - Hierarchical voltage decoder
- scripts/bpd-debug.py - Main CLI

Test configs available:
- bpd-deployment-setup1-dummy-dut.yaml
- bpd-deployment-setup2-real-dut.yaml

Time budget: 90 minutes
```

## What You've Already Built:

✅ **scripts/moku-deploy.py** - Works! Test it:
```bash
uv run python scripts/moku-deploy.py --help
```

## What's Next:

Build the BPD control tool that uses the deployment tool.

## Branch Decision:

The session branch `sessions/2025-11-07-bpd-debug-bus` still exists locally but all work through Phase 1 has been merged to main.

**Option A: Continue on main** (Recommended)
- Everything is already merged
- Simpler workflow
- No branch management needed

**Option B: Return to session branch**
```bash
git checkout sessions/2025-11-07-bpd-debug-bus
git merge main  # Bring in all the merged work
```

## All Safe & Committed:

- ✅ Everything merged to main
- ✅ Claude branches cleaned up
- ✅ No uncommitted work
- ✅ Ready to continue!

---

**Current branch:** main (all session work merged here)
**Session branch:** sessions/2025-11-07-bpd-debug-bus (still exists but behind main)
**Last commit:** 7cae8d0
**Status:** Ready for Phase 2!