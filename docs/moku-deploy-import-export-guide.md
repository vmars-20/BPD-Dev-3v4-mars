# Moku Configuration Import/Export Guide

**Version:** 1.0.0
**Date:** 2025-11-09
**Tool:** `scripts/moku-deploy.py`

## Overview

The `moku-deploy.py` tool now supports **bidirectional** conversion between `.mokuconf` files (binary Moku desktop app format) and YAML (declarative MokuConfig format).

This enables:
- **Session handoffs**: Export current device state for later restoration
- **GUI → YAML workflow**: Create configs in desktop app, export to YAML
- **Backup/restore**: Archive device configurations
- **Multi-tool workflows**: Share configs between desktop app and CLI

---

## Command Reference

### 1. Export Device State to .mokuconf

**Export current running configuration from device:**

```bash
uv run python scripts/moku-deploy.py export-config \
  --device $MOKU_IP \
  --output my_config.mokuconf
```

**What gets exported:**
- Multi-instrument slot configuration (which instruments in which slots)
- Routing connections (signal path matrix)
- AFE settings (input/output ranges, coupling, impedance)
- DIO configuration (if applicable - Moku:Go/Delta only)
- Platform metadata

**Use cases:**
- Save current device state before making changes
- Create backup of working configuration
- Share configuration with team members
- Document production deployments

---

### 2. Import .mokuconf to Device

**Deploy a .mokuconf file to device:**

```bash
uv run python scripts/moku-deploy.py import-config \
  --device $MOKU_IP \
  --input my_config.mokuconf
```

**What happens:**
1. Validates .mokuconf file (checks platform compatibility)
2. Connects to device
3. Loads configuration using native moku API (`load_configuration()`)
4. Retrieves deployed state via introspection APIs
5. Displays deployed configuration summary

**Use cases:**
- Restore previously saved configuration
- Deploy GUI-created configs from CLI
- Quick deployment for testing

---

### 3. Convert .mokuconf to YAML

**Convert .mokuconf to declarative YAML (MokuConfig format):**

```bash
uv run python scripts/moku-deploy.py import-config \
  --device $MOKU_IP \
  --input desktop_app_config.mokuconf \
  --to-yaml deployment_config.yaml
```

**What happens:**
1. Loads .mokuconf to device temporarily
2. Retrieves deployed state via introspection APIs
3. Converts to `MokuConfig` YAML format
4. Saves to specified YAML file

**Key insight:** This creates a **declarative YAML** that can be:
- Version controlled (git-friendly)
- Edited by hand
- Used with `moku-deploy.py deploy` command
- Shared across teams

**Use cases:**
- Convert desktop app configs to version-controlled YAML
- Create baseline deployment configs from GUI
- Document production configurations in human-readable format

---

### 4. Dry-run Mode

**Inspect .mokuconf without deploying:**

```bash
uv run python scripts/moku-deploy.py import-config \
  --device 127.0.0.1 \
  --input my_config.mokuconf \
  --dry-run
```

**Output:**
- Platform type (Moku:Go/Lab/Pro/Delta)
- Layout (slots, inputs, outputs)
- No device connection required!

**Use case:** Quick inspection of .mokuconf files

---

## Workflow Examples

### Workflow 1: GUI → YAML → Git

**Goal:** Create config in desktop app, convert to YAML, commit to repo

```bash
# 1. Create configuration in Moku desktop app
#    (Configure instruments, routing, settings via GUI)

# 2. Export from device to .mokuconf
uv run python scripts/moku-deploy.py export-config \
  -d $MOKU_IP \
  -o gui_created_config.mokuconf

# 3. Convert to YAML
uv run python scripts/moku-deploy.py import-config \
  -d $MOKU_IP \
  -i gui_created_config.mokuconf \
  --to-yaml bpd-deployment.yaml

# 4. Commit YAML to git (human-readable, diff-friendly)
git add bpd-deployment.yaml
git commit -m "feat: Add BPD deployment config from GUI prototype"
```

---

### Workflow 2: Session Handoff (AI Assistant Collaboration)

**Goal:** Save state for next session/agent

```bash
# Session 1: Claude/Cursor creates deployment
uv run python scripts/moku-deploy.py deploy \
  -d $MOKU_IP \
  -c bpd-deploy.yaml

# Save state before ending session
uv run python scripts/moku-deploy.py export-config \
  -d $MOKU_IP \
  -o session1_final_state.mokuconf

# Session 2: Different agent/tool restores state
uv run python scripts/moku-deploy.py import-config \
  -d $MOKU_IP \
  -i session1_final_state.mokuconf

# Or convert to YAML for inspection
uv run python scripts/moku-deploy.py import-config \
  -d $MOKU_IP \
  -i session1_final_state.mokuconf \
  --to-yaml session1_state.yaml
```

---

### Workflow 3: Backup and Restore

**Goal:** Backup production config, test changes, restore if needed

```bash
# Backup current production state
uv run python scripts/moku-deploy.py export-config \
  -d $MOKU_IP \
  -o production_backup_$(date +%Y%m%d_%H%M%S).mokuconf

# Deploy experimental changes
uv run python scripts/moku-deploy.py deploy \
  -d $MOKU_IP \
  -c experimental_config.yaml

# If something goes wrong, restore backup
uv run python scripts/moku-deploy.py import-config \
  -d $MOKU_IP \
  -i production_backup_20251109_130047.mokuconf
```

---

## File Format Details

### .mokuconf Structure

.mokuconf files are **ZIP archives** containing:

```
MokuMultiInstrument_YYYYMMDD_HHMMSS.mokuconf (ZIP)
├── metadata.json                    # App version, OS info
├── compatibility.json                # Archive format version
├── MI_Config_compatibility.json     # Platform ID, layout
└── MI_Config                        # Configuration (JSON with base64 values)
```

**MI_Config_compatibility.json** example:
```json
{
  "platformID": 2,  // 1=Lab, 2=Go, 3=Pro, 4=Delta
  "configurationVersion": 0,
  "hardwareVersion": [4, 0, 0],
  "layout": {
    "slots": 2,
    "aIn": 2,
    "aOut": 2,
    "buses": 1,
    "dioPorts": 1
  }
}
```

**MI_Config** contains:
- Platform settings (platform_id)
- Instrument list (which instruments in which slots)
- Routing connections (signal matrix)
- AFE settings per channel (impedance, coupling, range)
- DIO direction settings (if applicable)

---

## Integration with Existing Commands

The new import/export commands **complement** the existing deployment workflow:

| Command | Purpose | Input | Output |
|---------|---------|-------|--------|
| `discover` | Find devices on network | Network scan | Device cache |
| `list` | Show cached devices | Device cache | Terminal display |
| `deploy` | Deploy YAML config | YAML file | Device state |
| **`export-config`** | **Export device state** | **Device** | **.mokuconf file** |
| **`import-config`** | **Import .mokuconf** | **.mokuconf file** | **Device state** |
| **`import-config --to-yaml`** | **Convert to YAML** | **.mokuconf file** | **YAML file** |

---

## State-Aware Deployment with Import/Export

The `deploy` command already has **state-aware deployment**. Combined with import/export, you get:

```bash
# 1. Export current state
uv run python scripts/moku-deploy.py export-config \
  -d $MOKU_IP \
  -o before_changes.mokuconf

# 2. Deploy new config (state-aware checks)
uv run python scripts/moku-deploy.py deploy \
  -d $MOKU_IP \
  -c new_config.yaml \
  -I  # Interactive mode: prompts on state mismatch

# 3. If deployment fails, restore previous state
uv run python scripts/moku-deploy.py import-config \
  -d $MOKU_IP \
  -i before_changes.mokuconf
```

---

## Using with @CLAUDE Annotated Moku Fork

The import/export commands leverage the **@CLAUDE annotations** in the LLM-annotated moku fork:

**APIs used:**
- `MultiInstrument.save_configuration()` - Export to .mokuconf
- `MultiInstrument.load_configuration()` - Import from .mokuconf
- `MultiInstrument.get_instruments()` - Retrieve deployed instruments
- `MultiInstrument.get_connections()` - Retrieve routing
- `MultiInstrument.get_frontend()` - Retrieve AFE settings (future)
- `MultiInstrument.get_output()` - Retrieve output settings (future)

**Repository:** `git@github.com:vmars-20/moku-3.0.4.1-llm-dev.git`
**Branch:** `main`

See [docs/Moku-Dev-module-handoff-notes.md](../Moku-Dev-module-handoff-notes.md) for complete API reference.

---

## Next Steps

### Future Enhancements

1. **Add control register introspection**
   - Use `CloudCompile.get_controls()` to retrieve CR0-CR15
   - Include in exported YAML under `control_registers`

2. **Add AFE settings to MokuConfig**
   - Extend `MokuConfig` model with optional AFE settings
   - Use `get_frontend()` / `get_output()` during export

3. **Offline .mokuconf inspection**
   - Parse MI_Config JSON directly (no device needed)
   - Display instruments, routing, settings
   - Useful for quick config review

4. **Diff command**
   - Compare two .mokuconf files
   - Compare .mokuconf vs device state
   - Useful for debugging state mismatches

---

## Troubleshooting

### Device already connected

```
✗ Connection failed: Device is already connected
```

**Solution:** Use `--force` (`-f`) flag:
```bash
uv run python scripts/moku-deploy.py export-config -d $MOKU_IP -o config.mokuconf --force
```

### Platform mismatch

If importing a Moku:Lab config to Moku:Go device, you'll get platform validation errors.

**Solution:** Only import .mokuconf files to matching platform types.

### .mokuconf file not found

```
[red]Input file not found: my_config.mokuconf[/red]
```

**Solution:** Check file path is correct. Use absolute paths or relative to current directory.

---

## Reference: Current Deployment Command

Your current BPD deployment command remains unchanged:

```bash
uv run python scripts/moku-deploy.py deploy \
  -d $MOKU_IP \
  -b ./test_bits.tar \
  -s 2 \
  -c ./bpd-deploy-CInputs-only.yaml
```

**New capability:** You can now **export the deployed state** after this command completes:

```bash
# After deployment
uv run python scripts/moku-deploy.py export-config \
  -d $MOKU_IP \
  -o bpd_deployed_state.mokuconf

# Or export and convert to YAML in one step
uv run python scripts/moku-deploy.py export-config \
  -d $MOKU_IP \
  -o bpd_deployed_state.mokuconf

uv run python scripts/moku-deploy.py import-config \
  -d $MOKU_IP \
  -i bpd_deployed_state.mokuconf \
  --to-yaml bpd_verified_config.yaml
```

This gives you a **verified YAML** that matches the actual deployed state!

---

**Last Updated:** 2025-11-09
**Author:** Claude + vmars20
**Status:** Ready for testing with hardware
