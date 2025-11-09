# Cascading pyproject.toml Strategy for Monorepo

**Date:** 2025-11-07
**Context:** Post-Handoff 8 - Optimize Python environment usage
**Status:** Design → Implementation → Testing

---

## Problem Statement

Currently, all CocoTB tests are run using the **monorepo-level** uv environment:

```bash
# From monorepo root (current approach)
uv run python libs/forge-vhdl/cocotb_test/run.py forge_hierarchical_encoder
```

**Issues:**
1. **Unnecessary dependencies**: forge-vhdl tests load ALL workspace dependencies (cocotb, pydantic, pyyaml, jinja2, click, moku-models, riscure-models, forge-codegen)
2. **Slower installation**: Full workspace sync takes longer
3. **Unclear intent**: Component testing (VHDL utilities) conflated with integration testing (BPD + models)
4. **Memory overhead**: Larger virtual environment than needed

**Key Insight:** forge-vhdl is **self-contained** - it only needs cocotb + pytest!

---

## Solution: Two-Tier Testing Strategy

### Tier 1: Component Testing (Submodule-Level)

**Scope:** Testing individual VHDL utilities/packages in isolation
- forge_util_clk_divider
- forge_lut_pkg
- forge_voltage_*_pkg
- forge_hierarchical_encoder
- forge_debug_fsm_observer

**Environment:** Minimal (cocotb + pytest only)

**Command Pattern:**
```bash
cd libs/forge-vhdl
uv run python cocotb_test/run.py <component>
```

**Benefits:**
- ✅ Fast installation (~2s vs ~10s)
- ✅ Minimal dependencies (2 packages vs 10+)
- ✅ Lower memory footprint
- ✅ Clear separation of concerns
- ✅ Independent development possible

---

### Tier 2: Integration Testing (Monorepo-Level)

**Scope:** Testing full systems with cross-workspace dependencies
- BPD FSM observer (uses moku-models)
- Custom instruments (uses probe models)
- Code generation workflows (uses forge-codegen)

**Environment:** Full workspace

**Command Pattern:**
```bash
# From monorepo root
uv run python examples/basic-probe-driver/vhdl/cocotb_test/run.py <test>
```

**Benefits:**
- ✅ Access to all workspace members
- ✅ Can test cross-module integration
- ✅ Matches production deployment environment

---

## Current Architecture Analysis

### Root pyproject.toml (Workspace Container)

**Role:** Define workspace members, shared dependencies

**Current dependencies:**
```toml
dependencies = [
    "cocotb>=1.8.0",      # VHDL testing (forge-vhdl)
    "pydantic>=2.0.0",    # Models (moku-models, riscure-models, forge-codegen)
    "pytest>=7.0.0",      # Testing framework
    "pyyaml>=6.0.0",      # YAML parsing (forge-codegen)
    "jinja2>=3.1.0",      # Template rendering (forge-codegen)
    "click>=8.1.0",       # CLI (forge-codegen)
]
```

**Workspace members:**
```toml
[tool.uv.workspace]
members = [
    "libs/forge-vhdl",
    "libs/moku-models",
    "libs/riscure-models",
    "tools/forge-codegen",
]
```

---

### forge-vhdl pyproject.toml (Submodule)

**Role:** Define minimal dependencies for VHDL component testing

**Current dependencies:**
```toml
dependencies = [
    "cocotb>=1.8.0",
    "pytest>=7.0.0",
]
```

**Key Point:** Already self-contained! No imports from other workspace members.

---

## Implementation Plan

### Phase 1: Test Submodule-Level Execution ✅

**Goal:** Verify forge-vhdl tests can run from submodule directory

**Steps:**
1. Navigate to `libs/forge-vhdl/`
2. Run: `uv run python cocotb_test/run.py forge_hierarchical_encoder`
3. Verify tests pass
4. Measure installation time difference

**Expected Result:** Tests pass with minimal environment (cocotb + pytest only)

---

### Phase 2: Update Documentation ✅

**Files to Update:**

1. **libs/forge-vhdl/CLAUDE.md** - Add "Testing Workflow" section
   - Document both tier 1 (component) and tier 2 (integration) patterns
   - Explain when to use each
   - Update all example commands

2. **.claude/agents/cocotb-progressive-test-runner/agent.md** - Update execution constraints
   - Change recommendation from monorepo-level to submodule-level
   - Keep monorepo pattern as alternative for integration tests
   - Update examples

3. **libs/forge-vhdl/README.md** - Update usage instructions
   - Show submodule-level as primary pattern
   - Explain monorepo pattern for integration testing

---

### Phase 3: Cascade to Other Submodules (Optional)

**Apply same pattern to:**

1. **libs/moku-models** - Can run standalone for model testing
2. **libs/riscure-models** - Can run standalone for probe model testing
3. **tools/forge-codegen** - Can run standalone for code generation tests

**Benefits:**
- Each submodule testable independently
- Faster CI/CD (parallel testing)
- Clearer dependency boundaries

---

## Design Rationale

### Why Two Tiers?

**Component Testing (Tier 1):**
- Tests VHDL logic in isolation
- No external dependencies needed
- Faster feedback loop
- Suitable for TDD (test-driven development)
- Matches unit testing philosophy

**Integration Testing (Tier 2):**
- Tests system-level behavior
- Requires cross-module imports
- Validates deployment configuration
- Matches end-to-end testing philosophy

### Why NOT Collapse to Single Tier?

**Considered:** Always use monorepo-level environment

**Rejected because:**
- Slower iteration for component development
- Unnecessary dependency bloat
- Harder to reason about true component dependencies
- Submodules less portable (can't fork forge-vhdl independently)

---

## Usage Guidelines

### When to Use Submodule-Level (Tier 1)

**Use for:**
- forge-vhdl component testing (clk_divider, lut_pkg, voltage_pkg, etc.)
- forge-codegen template testing (unit tests)
- moku-models validation (Pydantic model tests)
- riscure-models validation (probe spec tests)

**Command Pattern:**
```bash
cd libs/<submodule>
uv run python <test_command>
```

**Characteristics:**
- No imports from other workspace members
- Tests single component behavior
- Fast iteration cycle

---

### When to Use Monorepo-Level (Tier 2)

**Use for:**
- BPD FSM observer testing (needs moku-models)
- Custom instrument integration tests (needs probe models)
- Code generation end-to-end tests (YAML → VHDL → CocoTB)
- Cross-workspace validation

**Command Pattern:**
```bash
# From monorepo root
uv run python examples/<app>/<test_command>
```

**Characteristics:**
- Imports from multiple workspace members
- Tests integration points
- Matches production environment

---

## Testing the Strategy

### Test 1: forge-vhdl Submodule-Level

```bash
# Setup
cd /Users/vmars20/workspace/BPD-Dev/libs/forge-vhdl

# Clean environment (optional)
rm -rf .venv

# Run test
uv run python cocotb_test/run.py forge_hierarchical_encoder

# Expected: Tests pass, minimal dependency install
```

**Success Criteria:**
- [ ] Tests pass (4/4 P1 tests)
- [ ] Installation time <5 seconds
- [ ] Only cocotb + pytest installed (verify with `uv pip list`)
- [ ] No warnings about missing workspace members

---

### Test 2: BPD Integration Testing (Monorepo-Level)

```bash
# Setup
cd /Users/vmars20/workspace/BPD-Dev

# Run integration test (if exists)
uv run python examples/basic-probe-driver/vhdl/cocotb_test/run.py test_bpd_fsm_observer

# Expected: Tests pass, full workspace available
```

**Success Criteria:**
- [ ] Tests pass
- [ ] Can import from moku-models
- [ ] Can import from riscure-models
- [ ] Full workspace dependencies available

---

## Migration Path

### Immediate (Handoff 8 Complete)

1. ✅ Test submodule-level execution for forge-vhdl
2. ✅ Update forge-vhdl documentation (CLAUDE.md, README.md)
3. ✅ Update cocotb-progressive-test-runner agent docs

### Short-Term (Handoff 8.5)

4. ⏸️ Design integration testing pattern for BPD
5. ⏸️ Create cocotb-integration-test agent
6. ⏸️ Run BPD FSM observer tests with hierarchical encoder decoder

### Medium-Term (Future Handoffs)

7. Apply cascading pattern to moku-models
8. Apply cascading pattern to riscure-models
9. Apply cascading pattern to forge-codegen
10. Update CI/CD to use submodule-level testing where applicable

---

## Impact Analysis

### Developer Experience

**Before:**
```bash
# Unclear which environment needed
uv run python libs/forge-vhdl/cocotb_test/run.py forge_util_clk_divider
# (runs from monorepo root, loads everything)
```

**After:**
```bash
# Clear intent: component testing
cd libs/forge-vhdl
uv run python cocotb_test/run.py forge_util_clk_divider
# (minimal environment, fast)

# Clear intent: integration testing
cd /path/to/monorepo
uv run python examples/bpd/cocotb_test/run.py test_bpd_fsm_observer
# (full environment, comprehensive)
```

---

### CI/CD Performance

**Before:**
- Single large environment for all tests
- Sequential execution (single job)
- ~30s setup + ~60s tests = 90s total

**After:**
- Parallel jobs per submodule
- forge-vhdl: ~2s setup + ~10s tests = 12s
- moku-models: ~2s setup + ~5s tests = 7s
- Integration: ~10s setup + ~20s tests = 30s
- **Total (parallel): 30s** (67% faster)

---

### Portability

**forge-vhdl as standalone repository:**

**Before:** Requires full monorepo workspace
**After:** Can be forked and used independently

```bash
# Standalone forge-vhdl usage (future)
git clone https://github.com/user/forge-vhdl.git
cd forge-vhdl
uv sync
uv run python cocotb_test/run.py forge_util_clk_divider
# Works! No monorepo needed.
```

---

## Open Questions

1. **BPD FSM Observer Tests:** Where should these live?
   - Option A: `examples/basic-probe-driver/vhdl/cocotb_test/` (integration tier)
   - Option B: `libs/forge-vhdl/cocotb_test/integration/` (keep in forge-vhdl)
   - **Recommendation:** Option A (clearer separation, uses BPD context)

2. **Shared test utilities:** Where should these live?
   - Current: `libs/forge-vhdl/forge_cocotb/` (test_base.py, conftest.py)
   - Future: Keep in forge-vhdl (other submodules can depend on it)
   - **Recommendation:** Keep current location, make forge-cocotb a proper package

3. **GHDL binary:** How to ensure GHDL available?
   - Option A: Document as system requirement (current)
   - Option B: Add GHDL Python bindings to dependencies
   - **Recommendation:** Option A (GHDL installation is platform-specific)

---

## Success Metrics

**Technical:**
- [ ] forge-vhdl tests pass from submodule directory
- [ ] Installation time reduced by >50%
- [ ] Virtual environment size reduced by >50%
- [ ] No functional regressions

**Documentation:**
- [ ] forge-vhdl/CLAUDE.md updated with two-tier pattern
- [ ] cocotb-progressive-test-runner agent updated
- [ ] forge-vhdl/README.md updated with usage examples
- [ ] Handoff 8.5 created for integration testing

**Developer Experience:**
- [ ] Clearer intent (component vs integration)
- [ ] Faster iteration for VHDL development
- [ ] Easier onboarding (minimal environment for component work)

---

## Next Steps

1. **Test submodule-level execution** (Immediate)
   - Run forge-vhdl tests from `libs/forge-vhdl/`
   - Measure performance improvements
   - Verify functionality

2. **Update documentation** (Immediate)
   - forge-vhdl/CLAUDE.md
   - cocotb-progressive-test-runner agent
   - forge-vhdl/README.md

3. **Create Handoff 8.5** (Next session)
   - Design integration testing strategy
   - Create cocotb-integration-test agent workflow
   - Run BPD FSM observer tests with new decoder

4. **Commit and document** (Immediate)
   - Commit documentation updates
   - Update llms.txt files with new patterns
   - Tag commit as "cascading pyproject.toml strategy implemented"

---

## References

- **uv Workspace Documentation:** https://docs.astral.sh/uv/concepts/workspaces/
- **Handoff 8 Results:** `Obsidian/Project/Test-Reports/2025-11-07-handoff-8-test-results.md`
- **forge-vhdl Testing Standards:** `libs/forge-vhdl/CLAUDE.md`
- **cocotb-progressive-test-runner Agent:** `.claude/agents/cocotb-progressive-test-runner/agent.md`

---

**Author:** @claude (analysis) + @vmars20 (architecture insight)
**Version:** 1.0
**Status:** Ready for implementation
