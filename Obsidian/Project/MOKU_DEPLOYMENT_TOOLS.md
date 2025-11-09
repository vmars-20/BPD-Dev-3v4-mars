# Moku Deployment Tools

**Simple, standalone scripts for reading and writing Moku device configurations.**

---

## Overview

Two minimal scripts that do exactly what they say:

- **`moku_read.py`** - Read device state, output validated MokuConfig (JSON)
- **`moku_write.py`** - Write config to device (no safety checks, overwrites everything)

**Total:** 290 lines (vs 1190 in original complex tool = 76% reduction)

---

## Quick Start

### Read Device State

```bash
# Read and display
python scripts/moku_read.py 192.168.13.147

# Read and save to file
python scripts/moku_read.py 192.168.13.147 > device-state.json
```

**Output:** Validated MokuConfig as JSON (Pydantic model)

### Write Config to Device

```bash
# Write from YAML file
python scripts/moku_write.py bpd-deployment-setup1-dummy-dut.yaml 192.168.13.147

# Write from JSON file
python scripts/moku_write.py device-state.json 192.168.13.147
```

**Behavior:** 
- Force disconnects all existing connections
- Overwrites device state completely
- No safety checks, no prompts, no compatibility checking
- Just writes and disconnects

---

## Usage Examples

### Example 1: Read Current State

```bash
# Read device state and save it
python scripts/moku_read.py 192.168.13.147 > current-state.json

# View the config
cat current-state.json | jq .
```

### Example 2: Deploy Configuration

```bash
# Deploy a YAML config file
python scripts/moku_write.py bpd-deployment-setup1-dummy-dut.yaml 192.168.13.147
```

### Example 3: Round-Trip (Read → Modify → Write)

```bash
# Read current state
python scripts/moku_read.py 192.168.13.147 > backup.json

# Modify backup.json (edit in your editor)

# Write modified config back
python scripts/moku_write.py backup.json 192.168.13.147
```

### Example 4: Pipeline Operations

```bash
# Read from device A, write to device B
python scripts/moku_read.py 192.168.1.100 | python scripts/moku_write.py - 192.168.1.101

# Validate config before writing
python scripts/moku_read.py 192.168.13.147 | jq . > validated.json
python scripts/moku_write.py validated.json 192.168.13.147
```

---

## Script Details

### `moku_read.py`

**Purpose:** Read current device state as validated MokuConfig

**Arguments:**
- `device-ip` - Device IP address

**Output:**
- JSON to stdout (validated Pydantic MokuConfig model)
- Can redirect to file: `> output.json`

**Features:**
- Auto-detects platform (tries Go, Lab, Pro, Delta)
- Reads instruments, routing, platform info
- Outputs validated Pydantic model
- Gracefully disconnects

**Example:**
```bash
python scripts/moku_read.py 192.168.13.147
```

**Output format:**
```json
{
  "platform": {
    "name": "Moku:Go",
    "ip_address": "192.168.13.147",
    ...
  },
  "slots": {
    "1": {
      "instrument": "Oscilloscope",
      ...
    },
    "2": {
      "instrument": "CloudCompile",
      ...
    }
  },
  "routing": [
    {"source": "Slot2OutC", "destination": "Slot1InA"},
    ...
  ],
  "metadata": {
    "exported_at": "2025-11-09T...",
    "source": "moku_read"
  }
}
```

---

### `moku_write.py`

**Purpose:** Write MokuConfig to device (overwrites everything)

**Arguments:**
- `config-file` - Path to YAML or JSON config file
- `device-ip` - Device IP address

**Behavior:**
- **Force disconnects** all existing connections
- **Overwrites** device state completely
- **No safety checks** - just writes
- **No prompts** - non-interactive
- **No compatibility checking** - assumes config is valid

**Supported config formats:**
- YAML (`.yaml`, `.yml`)
- JSON (`.json`)

**Platform string support:**
- `moku_go` → Moku:Go
- `moku_lab` → Moku:Lab
- `moku_pro` → Moku:Pro
- `moku_delta` → Moku:Delta

**Example:**
```bash
python scripts/moku_write.py bpd-deployment-setup1-dummy-dut.yaml 192.168.13.147
```

**Output:**
```
Loading config from bpd-deployment-setup1-dummy-dut.yaml...
Connecting to 192.168.13.147...
  ✓ Connected

Deploying instruments...
  Slot 1: Oscilloscope
    ✓ Deployed
  Slot 2: CloudCompile (bpd_moku_go.tar)
    ✓ Deployed

Configuring routing...
  ✓ 6 connections

✓ Deployment complete
  ✓ Disconnected
```

---

## Important Notes

### Safety

**⚠️ `moku_write.py` has NO safety checks:**
- Will overwrite device state without asking
- Will force disconnect all existing connections
- Will deploy even if device is in use
- No validation of current vs desired state
- No dry-run mode

**Always:**
- Read current state first (backup)
- Verify config file is correct
- Ensure device is available for deployment

### Platform Detection

Both scripts auto-detect platform by trying common platform IDs:
1. Moku:Go (platform_id=2)
2. Moku:Lab (platform_id=1)
3. Moku:Pro (platform_id=3)
4. Moku:Delta (platform_id=4)

If connection fails, script tries next platform automatically.

### Config Validation

Configs are validated as Pydantic MokuConfig models:
- Invalid configs will fail with clear error messages
- Routing is validated against platform port limits
- Slot numbers must be within platform limits

---

## Workflow Examples

### Workflow 1: Backup Before Deployment

```bash
# 1. Backup current state
python scripts/moku_read.py 192.168.13.147 > backup-$(date +%Y%m%d-%H%M%S).json

# 2. Deploy new config
python scripts/moku_write.py new-config.yaml 192.168.13.147

# 3. If something goes wrong, restore
python scripts/moku_write.py backup-20251109-143022.json 192.168.13.147
```

### Workflow 2: Clone Device Configuration

```bash
# Clone device A to device B
python scripts/moku_read.py 192.168.1.100 | python scripts/moku_write.py - 192.168.1.101
```

### Workflow 3: Validate Config Before Deployment

```bash
# Read current state
python scripts/moku_read.py 192.168.13.147 > current.json

# Edit config (add/modify slots, routing, etc.)
vim current.json

# Validate JSON syntax
python -m json.tool current.json > /dev/null && echo "Valid JSON"

# Deploy
python scripts/moku_write.py current.json 192.168.13.147
```

---

## Error Handling

### Connection Errors

If device is already connected:
```bash
# moku_read.py will try to connect without force
# If busy, will fail gracefully

# moku_write.py uses force_connect=True
# Will always disconnect existing connections
```

### Invalid Config

If config file is invalid:
```bash
# Both scripts validate as Pydantic MokuConfig
# Will show clear validation errors:
Error: 1 validation error for MokuConfig
platform
  Input should be a valid dictionary or instance of MokuGoPlatform
```

### Missing Dependencies

If moku library not installed:
```bash
Error: moku library not installed. Run: uv sync
```

---

## Comparison with Original Tool

**Original `moku-deploy.py`:**
- 1190 lines
- State comparison
- Interactive mode
- Force mode flags
- Device discovery
- Caching
- Export/import commands
- Rich formatting

**New scripts:**
- 290 lines total (76% reduction)
- No state comparison
- No interactive mode
- Always force (write) or never force (read)
- No discovery
- No caching
- Just read/write
- Simple output

**Philosophy:** Do one thing, do it well, no safety nets.

---

## Related Files

- **Scripts:** `scripts/moku_read.py`, `scripts/moku_write.py`
- **Models:** `libs/moku-models/moku_models/moku_config.py`
- **Config examples:** `bpd-deployment-setup1-dummy-dut.yaml`, `bpd-deployment-setup2-real-dut.yaml`

---

**Created:** 2025-11-09  
**Status:** Production-ready  
**License:** MIT
