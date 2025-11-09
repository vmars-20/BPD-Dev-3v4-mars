# moku-deploy.py Simplification Analysis

**Current State:** 1190 lines, 12 functions, 5 commands

---

## Current Features

### Commands
1. `discover` - Zeroconf device discovery
2. `list` - List cached devices
3. `deploy` - Main deployment (with state checking)
4. `export-config` - Export current device state
5. `import-config` - Import config from device

### Deploy Features
- State-aware deployment (retrieves current state)
- State comparison (desired vs current)
- Interactive mode (-I) - prompts on mismatch
- Force mode (-F) - overrides without prompting
- Debug mode (-D) - verbose logging
- Dry-run mode
- Device caching
- Bitstream-only deployment (creates minimal config)
- Full config deployment (YAML/JSON)
- Platform detection and mapping
- Rich console formatting

### Complexity Sources
1. **State comparison logic** (~200 lines) - `compare_states()`, `display_state_diff()`
2. **State retrieval** (~100 lines) - `retrieve_current_state()`
3. **Device caching** (~50 lines) - `load_cache()`, `save_cache()`, cache management
4. **Platform mappings** (~30 lines) - Multiple platform ID/name mappings
5. **Rich formatting** - Tables, colors, console output
6. **Error handling** - Extensive try/except blocks
7. **Config parsing** - YAML/JSON, string platform resolution
8. **Export/import** - Additional commands

---

## Core Functionality (What's Essential?)

**Minimum viable deployment:**
1. Connect to device (IP or cached name)
2. Load config (YAML/JSON)
3. Deploy config to device
4. Disconnect

**That's it.** Everything else is nice-to-have.

---

## Simplification Strategy

### Option A: Radical Simplification (Recommended)
**Target:** ~200-300 lines

**Keep:**
- `deploy` command only
- Basic config loading (YAML/JSON)
- Simple device connection
- Basic error handling

**Remove:**
- State comparison (just deploy, don't check)
- Interactive mode (-I)
- Force mode (-F) - just always deploy
- Device discovery (use IP directly)
- Device caching
- Export/import commands
- Rich formatting (use simple print)
- Platform detection (assume config has platform)
- Dry-run mode
- Debug mode (use Python logging if needed)

**Result:** Simple, focused tool that just deploys.

### Option B: Moderate Simplification
**Target:** ~500-600 lines

**Keep:**
- `deploy` command
- `discover` command (useful for finding devices)
- Basic state checking (warn, don't fail)
- Simple caching (just IP/name mapping)

**Remove:**
- Interactive mode
- Force mode (just warn and deploy)
- Export/import
- Rich formatting
- Complex state diff display

**Result:** Still useful but much simpler.

### Option C: Keep Features, Simplify Implementation
**Target:** ~800 lines

**Keep all features but:**
- Simplify state comparison logic
- Reduce code duplication
- Simplify error handling
- Use simpler formatting

**Result:** Same features, cleaner code.

---

## Recommendation: Option A (Radical)

**Why?**
- Deployment should be simple: "Here's config, deploy it"
- State checking adds complexity without much value
- Device discovery can be done manually or with separate tool
- Caching is nice but not essential
- Most users just want: `deploy --device IP --config file.yaml`

**New API:**
```bash
# Simple deployment
python scripts/moku-deploy.py deploy --device 192.168.1.100 --config deployment.yaml

# That's it. No flags, no modes, just deploy.
```

**What gets removed:**
- ~400 lines of state comparison
- ~200 lines of device discovery/caching
- ~150 lines of export/import
- ~100 lines of interactive/force modes
- ~100 lines of rich formatting
- ~50 lines of platform mapping complexity

**Estimated reduction:** 1190 → ~250 lines (79% reduction)

---

## Implementation Plan

1. **Create simplified version** (`moku-deploy-simple.py`)
2. **Core deploy function:**
   - Load config (YAML/JSON)
   - Connect to device
   - Deploy config
   - Disconnect
3. **Test with existing configs**
4. **Compare functionality**
5. **Replace original if successful**

---

**Next Step:** Implement Option A (radical simplification)
