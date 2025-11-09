# Prompts

**Purpose:** Library of reusable prompts for common development operations

---

## What Are Prompts?

Prompt notes are reusable templates for common tasks:
- Analysis patterns (e.g., "analyze VHDL register mapping")
- Refactoring workflows (e.g., "add new voltage type")
- Testing procedures (e.g., "validate CocoTB tests")
- Code review checklists (e.g., "review FPGA architecture")

**Key principle:** Prompts are **timeless** and **reusable** - commit to git as permanent documentation.

---

## Naming Convention

**Format:** `<verb>-<noun>-<qualifier>.md` (NO dates)

**Examples:**
- `analyze-vhdl-packages.md`
- `refactor-voltage-types.md`
- `validate-cocotb-tests.md`
- `review-register-mapping.md`

**Why this format:**
- `<verb>` - Action to perform
- `<noun>` - What to act on
- `<qualifier>` - Specificity if needed
- NO date - timeless reference

---

## When to Create

**DO create prompt when:**
- ✅ Found a useful analysis pattern
- ✅ Discovered repeatable workflow
- ✅ Common task done multiple times
- ✅ Want to standardize an operation

**DON'T create prompt for:**
- ❌ One-time specific tasks
- ❌ Project-specific details (use handoffs)
- ❌ Temporary workflows

---

## Template Usage

**Using Templater in Obsidian:**
1. Create new file: `analyze-topic.md`
2. Command palette: "Templater: Insert Template"
3. Choose: `prompt.md`
4. Fill in: Purpose, prompt text, usage notes
5. Commit to git

**See:** [[Obsidian/Templates/README|Templates README]]

---

## Lifecycle

```
1. Discover useful pattern
   ↓
2. Create prompt note
   ↓
3. Document: purpose, prompt text, usage
   ↓
4. Commit to git (permanent)
   ↓
5. Reuse in future sessions
   ↓
6. Update as pattern evolves
```

---

## What to Include

**Essential sections:**
- **Purpose** - What this prompt accomplishes
- **Prompt Text** - The actual prompt to copy/paste
- **Usage Notes** - When/how to use, variations
- **Related Files** - Wikilinks to relevant code

**Optional sections:**
- **Prerequisites** - Context needed before running
- **Expected Output** - What success looks like
- **Examples** - Previous uses of this prompt

**See template:** [[Obsidian/Templates/prompt.md]]

---

## Using Prompts

**Pattern:**
1. Find relevant prompt: `ls Obsidian/Project/Prompts/`
2. Read prompt note: Get context and prompt text
3. Copy prompt text
4. Adapt to current task (replace placeholders)
5. Execute with Claude

**Example:**
```markdown
# You want to analyze VHDL packages
1. Read: Obsidian/Project/Prompts/analyze-vhdl-packages.md
2. Copy prompt text
3. Replace: [[target-package.vhd]] with your actual file
4. Send to Claude: "@claude [prompt text]"
```

---

## Finding Prompts

```bash
# List all prompts
ls Obsidian/Project/Prompts/

# Search by action
ls Obsidian/Project/Prompts/analyze-*.md
ls Obsidian/Project/Prompts/refactor-*.md

# Search by content
grep -l "voltage" Obsidian/Project/Prompts/*.md
grep -l "VHDL" Obsidian/Project/Prompts/*.md
```

---

## Prompt Library (Index)

### Analysis Prompts
- (Empty - add your first analysis prompt!)

### Refactoring Prompts
- (Empty - add your first refactoring prompt!)

### Validation Prompts
- (Empty - add your first validation prompt!)

### Review Prompts
- (Empty - add your first review prompt!)

**Note:** Update this index as you add prompts, or use `ls` to discover.

---

## Example Prompt Structure

```markdown
# Analyze VHDL Register Mapping

## Purpose
Analyze a VHDL register mapping implementation for correctness and efficiency.

## Prompt
@claude please analyze the register mapping in [[target-file.vhd]]:

1. Check bit allocation correctness
2. Verify no overlaps or gaps
3. Calculate packing efficiency
4. Identify improvement opportunities

Reference the type system in [[libs/forge-vhdl/llms.txt]].

## Usage Notes
- Use when reviewing generated VHDL shims
- Compare against manifest.json for expected mapping
- Look for unused bits (efficiency <80%)

## Related Files
- [[libs/forge-vhdl/vhdl/packages/forge_serialization_types_pkg.vhd]]
- [[CLAUDE.md]] - Register mapping section
```

---

## Maintenance

**Updating prompts:**
1. Edit prompt file
2. Update "Last Updated" date
3. Commit changes
4. Use git log to see evolution

**Deprecating prompts:**
1. Add "DEPRECATED" to title
2. Explain why (what replaced it)
3. Keep file (historical reference)
4. Don't delete (git history value)

---

## Related Documentation

- [[Obsidian/Project/README]] - Full system overview
- [[Obsidian/Templates/prompt.md]] - Prompt template
- [[Obsidian/Project/Handoffs/README]] - Session handoffs (different purpose)

---

**Created:** 2025-11-06
**Last Updated:** 2025-11-06