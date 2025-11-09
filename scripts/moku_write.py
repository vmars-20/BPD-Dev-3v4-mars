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
                
                # Configure frontend (input channels)
                if slot_config.settings:
                    # Filter out sample_rate (not a valid set_frontend parameter)
                    # Sample rate is platform-dependent and set automatically
                    frontend_settings = {
                        k: v for k, v in slot_config.settings.items()
                        if k != 'sample_rate'
                    }
                    
                    if frontend_settings:
                        try:
                            osc.set_frontend(1, **frontend_settings)
                        except Exception as e:
                            print(f"    ⚠ Warning: Settings = {e}")
                    
                    # Note: sample_rate is platform-dependent and cannot be set directly
                    # It's determined by the Moku device (e.g., 125 MSa/s for Moku:Go)
                    if 'sample_rate' in slot_config.settings:
                        print(f"    ℹ Note: sample_rate is platform-dependent (not configurable)")
                
                # Configure waveform generator output (if specified)
                if slot_config.waveform_output:
                    waveform_config = slot_config.waveform_output
                    try:
                        channel = waveform_config.get('channel', 1)
                        enable = waveform_config.get('enable', True)
                        waveform_type = waveform_config.get('waveform_type', 'Square')
                        frequency = waveform_config.get('frequency', 1000)
                        amplitude = waveform_config.get('amplitude', 2.5)
                        offset = waveform_config.get('offset', 1.25)
                        duty = waveform_config.get('duty', None)  # Optional, for square waves
                        
                        if enable:
                            # Configure waveform generator output using Oscilloscope's built-in generator
                            # Moku API: generate_waveform(channel, type, amplitude=..., frequency=..., offset=..., duty=...)
                            # Note: waveform_type should be capitalized (e.g., 'Sine', 'Square', 'Triangle')
                            kwargs = {
                                'amplitude': amplitude,
                                'frequency': frequency,
                            }
                            if offset is not None:
                                kwargs['offset'] = offset
                            # Square waves require duty cycle parameter (even if not specified)
                            if waveform_type.lower() == 'square':
                                kwargs['duty'] = duty if duty is not None else 50  # Default 50% duty cycle
                            
                            osc.generate_waveform(channel, waveform_type, **kwargs)
                            print(f"    ✓ Waveform Generator Output{channel}: {waveform_type} @ {frequency} Hz, {amplitude}V amplitude", end="")
                            if offset is not None:
                                print(f", {offset}V offset", end="")
                            if waveform_type.lower() == 'square':
                                # Always show duty cycle for square waves
                                duty_value = duty if duty is not None else 50
                                print(f", {duty_value}% duty", end="")
                            print()
                        else:
                            print(f"    ℹ Waveform Generator Output{channel}: disabled")
                    except Exception as e:
                        print(f"    ⚠ Warning: Waveform generator configuration failed: {e}")
                        print(f"    ℹ Note: Check that waveform_type is valid (e.g., 'Sine', 'Square', 'Triangle')")
            
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
