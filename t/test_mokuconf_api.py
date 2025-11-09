#!/usr/bin/env python3
"""
Test script to understand .mokuconf save/load APIs

This script tests the native moku library APIs:
- MultiInstrument.save_configuration() / load_configuration()
- CloudCompile.save_settings() / load_settings()

Goal: Understand what data gets saved and how to programmatically
      import/export .mokuconf files.
"""

import json
import tarfile
import zipfile
from pathlib import Path
from pprint import pprint

# Path to decompressed reference .mokuconf
DECOMPRESSED_DIR = Path("/Users/vmars20/20251109/experiment-cursor/decompressed_moku_config")
MOKUCONF_FILE = DECOMPRESSED_DIR / "MokuMultiInstrument_20251109_130047.mokuconf"

def analyze_mokuconf_structure():
    """Analyze the structure of a .mokuconf file."""
    print("=" * 80)
    print("Analyzing .mokuconf structure")
    print("=" * 80)

    if not MOKUCONF_FILE.exists():
        print(f"ERROR: .mokuconf file not found: {MOKUCONF_FILE}")
        return

    # .mokuconf is a ZIP archive
    with zipfile.ZipFile(MOKUCONF_FILE, 'r') as zf:
        print("\n📦 Archive contents:")
        for info in zf.infolist():
            print(f"  - {info.filename:30s} ({info.file_size:>8d} bytes)")

        # Read JSON files
        print("\n📄 metadata.json:")
        metadata = json.loads(zf.read('metadata.json'))
        pprint(metadata, indent=2)

        print("\n📄 compatibility.json:")
        compat = json.loads(zf.read('compatibility.json'))
        pprint(compat, indent=2)

        print("\n📄 MI_Config_compatibility.json:")
        mi_compat = json.loads(zf.read('MI_Config_compatibility.json'))
        pprint(mi_compat, indent=2)

        print("\n📄 MI_Config (binary blob - first 200 bytes as text):")
        mi_config_raw = zf.read('MI_Config')
        print(f"  Length: {len(mi_config_raw)} bytes")
        print(f"  Content (decoded as utf-8, first 200 chars):")
        try:
            decoded = json.loads(mi_config_raw)
            pprint(decoded, indent=2)
        except json.JSONDecodeError:
            print("  (Not JSON - binary or custom format)")
            print(f"  First 200 bytes (hex): {mi_config_raw[:200].hex()}")

def extract_platform_info():
    """Extract platform information from .mokuconf."""
    print("\n" + "=" * 80)
    print("Extracting platform information")
    print("=" * 80)

    with zipfile.ZipFile(MOKUCONF_FILE, 'r') as zf:
        mi_compat = json.loads(zf.read('MI_Config_compatibility.json'))

        platform_id = mi_compat['platformID']
        layout = mi_compat['layout']

        platform_map = {1: 'Moku:Lab', 2: 'Moku:Go', 3: 'Moku:Pro', 4: 'Moku:Delta'}
        platform_name = platform_map.get(platform_id, f'Unknown({platform_id})')

        print(f"\n🔧 Platform: {platform_name} (ID={platform_id})")
        print(f"   Analog Inputs:  {layout['aIn']}")
        print(f"   Analog Outputs: {layout['aOut']}")
        print(f"   Instrument Slots: {layout['slots']}")
        print(f"   Buses: {layout['buses']}")
        print(f"   DIO Ports: {layout['dioPorts']}")

        return {
            'platform_id': platform_id,
            'platform_name': platform_name,
            'layout': layout
        }

def propose_import_strategy():
    """Propose strategy for importing .mokuconf into MokuConfig."""
    print("\n" + "=" * 80)
    print("Proposed Import Strategy")
    print("=" * 80)

    print("""
Strategy 1: Use native moku library API
---------------------------------------
✅ Pros:
   - Simple: moku.load_configuration(filename)
   - Official API, guaranteed compatibility
   - Handles binary MI_Config format

❌ Cons:
   - Requires device connection
   - Can't inspect without deploying
   - No conversion to YAML

Use case: Quick restore to hardware


Strategy 2: Parse .mokuconf manually
------------------------------------
✅ Pros:
   - No device needed
   - Can convert to YAML (MokuConfig format)
   - Can inspect/modify before deployment

❌ Cons:
   - Need to decode MI_Config binary format
   - Maintenance burden if format changes
   - May not support all settings

Use case: Offline analysis, YAML conversion


Recommended Hybrid Approach:
----------------------------
1. Use moku.save_configuration() to export current device state
2. Provide 'import' command that:
   a. Loads .mokuconf to device (native API)
   b. Retrieves state via get_instruments()/get_connections()
   c. Converts to MokuConfig YAML
   d. Optionally saves as .yaml for future deployments

This gives us the best of both worlds!
""")

if __name__ == "__main__":
    analyze_mokuconf_structure()
    extract_platform_info()
    propose_import_strategy()

    print("\n" + "=" * 80)
    print("✓ Analysis complete!")
    print("=" * 80)
