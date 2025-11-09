#!/usr/bin/env python3
"""
moku_write: Write MokuConfig to device (no safety checks)

Usage:
    python scripts/moku_write.py <config.yaml> <device-ip>
"""

import json
import sys
from pathlib import Path

import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "libs" / "moku-models"))

from moku_models import MokuConfig
from moku_models import (
    MOKU_GO_PLATFORM,
    MOKU_LAB_PLATFORM,
    MOKU_PRO_PLATFORM,
    MOKU_DELTA_PLATFORM,
)

try:
    from moku.instruments import MultiInstrument, CloudCompile, Oscilloscope
except ImportError:
    print("Error: moku library not installed. Run: uv sync")
    sys.exit(1)


def load_config(config_path: Path) -> MokuConfig:
    """Load MokuConfig from file."""
    content = config_path.read_text()
    
    if config_path.suffix.lower() in ['.yaml', '.yml']:
        data = yaml.safe_load(content)
    else:
        data = json.loads(content)
    
    # Handle string platform identifiers
    if isinstance(data.get('platform'), str):
        platform_map = {
            'moku_go': MOKU_GO_PLATFORM,
            'moku_lab': MOKU_LAB_PLATFORM,
            'moku_pro': MOKU_PRO_PLATFORM,
            'moku_delta': MOKU_DELTA_PLATFORM,
        }
        platform_str = data['platform'].lower()
        if platform_str in platform_map:
            data['platform'] = platform_map[platform_str].model_dump()
        else:
            raise ValueError(f"Unknown platform: {platform_str}")
    
    return MokuConfig.model_validate(data)


def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/moku_write.py <config.yaml> <device-ip>")
        sys.exit(1)
    
    config_path = Path(sys.argv[1])
    device_ip = sys.argv[2]
    
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    
    # Load config
    print(f"Loading config from {config_path}...")
    config = load_config(config_path)
    
    # Determine platform_id
    platform_name = config.platform.name
    platform_id_map = {
        "Moku:Go": 2,
        "Moku:Lab": 1,
        "Moku:Pro": 3,
        "Moku:Delta": 4,
    }
    platform_id = platform_id_map.get(platform_name, 2)
    
    # Connect to device (force connect, no persist state)
    print(f"Connecting to {device_ip}...")
    moku = MultiInstrument(
        device_ip,
        platform_id=platform_id,
        force_connect=True,  # Force disconnect all
        persist_state=False  # Don't preserve state
    )
    print("  ✓ Connected")
    
    try:
        # Deploy instruments
        print("\nDeploying instruments...")
        for slot_num, slot_config in config.slots.items():
            if slot_config.instrument == 'CloudCompile':
                if not slot_config.bitstream:
                    print(f"  Slot {slot_num}: No bitstream, skipping")
                    continue
                
                # Resolve bitstream path (relative to project root or absolute)
                bitstream_path = Path(slot_config.bitstream)
                if not bitstream_path.is_absolute():
                    bitstream_path = PROJECT_ROOT / bitstream_path
                
                if not bitstream_path.exists():
                    print(f"  ✗ Error: Bitstream not found at {bitstream_path}")
                    raise FileNotFoundError(f"Bitstream package not found at {bitstream_path}")
                
                print(f"  Slot {slot_num}: CloudCompile ({bitstream_path.name})")
                cc = moku.set_instrument(slot_num, CloudCompile, bitstream=str(bitstream_path))
                
                # Apply control registers if specified
                if slot_config.control_registers:
                    for reg_num, reg_value in sorted(slot_config.control_registers.items()):
                        try:
                            cc.set_control(reg_num, reg_value)
                        except Exception as e:
                            print(f"    ⚠ Warning: CR{reg_num} = {e}")
            
            elif slot_config.instrument == 'Oscilloscope':
                print(f"  Slot {slot_num}: Oscilloscope")
                osc = moku.set_instrument(slot_num, Oscilloscope)
                if slot_config.settings:
                    try:
                        osc.set_frontend(1, **slot_config.settings)
                    except Exception as e:
                        print(f"    ⚠ Warning: Settings = {e}")
            
            else:
                print(f"  Slot {slot_num}: {slot_config.instrument} (not implemented, skipping)")
        
        # Configure routing
        if config.routing:
            print("\nConfiguring routing...")
            # Port names are automatically normalized by MokuConnection validator
            connections = [
                {'source': conn.source, 'destination': conn.destination}
                for conn in config.routing
            ]
            moku.set_connections(connections)
            print(f"  ✓ {len(connections)} connections")
        
        print("\n✓ Deployment complete")
    
    finally:
        # Disconnect
        try:
            moku.relinquish_ownership()
            print("  ✓ Disconnected")
        except Exception as e:
            print(f"  ⚠ Warning: {e}")


if __name__ == "__main__":
    main()
