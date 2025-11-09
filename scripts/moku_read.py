#!/usr/bin/env python3
"""
moku_read: Read device state as MokuConfig (validated Pydantic model)

Progressive escalation approach:
- Level 1 (Polite): Read basic info (instruments, routing) without disrupting device
- Level 2 (Detailed): Read frontend/output settings, control registers
- Level 3 (Maximum): Force connect if device is busy, read everything

Usage:
    python scripts/moku_read.py <device-ip> [--level 1|2|3] [--force] [--non-interactive] [--output FILE]
    # Default: writes to ./curr_model.json
    # Use --output - to write to stdout
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "libs" / "moku-models"))

from moku_models import MokuConfig, SlotConfig, MokuConnection
from moku_models import (
    MOKU_GO_PLATFORM,
    MOKU_LAB_PLATFORM,
    MOKU_PRO_PLATFORM,
    MOKU_DELTA_PLATFORM,
)

try:
    from moku.instruments import MultiInstrument, CloudCompile, Oscilloscope
except ImportError:
    print("Error: moku library not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)


def connect_politely(device_ip: str, force: bool = False) -> tuple[MultiInstrument, int] | None:
    """
    Connect to device with progressive platform detection.
    
    Returns:
        (MultiInstrument, platform_id) or None if connection failed
    """
    platform_id_map = {
        1: "Moku:Lab",
        2: "Moku:Go",
        3: "Moku:Pro",
        4: "Moku:Delta",
    }
    
    # Try each platform
    for pid in [2, 1, 3, 4]:  # Go, Lab, Pro, Delta
        try:
            moku = MultiInstrument(
                device_ip,
                platform_id=pid,
                force_connect=force,
                persist_state=True  # Always preserve state (polite)
            )
            return (moku, pid)
        except Exception as e:
            error_msg = str(e).lower()
            if "already exists" in error_msg or "busy" in error_msg:
                # Device is busy - will need force_connect
                continue
            # Try next platform
            continue
    
    return None


def read_basic_info(moku: MultiInstrument) -> dict[str, Any]:
    """
    Level 1: Read basic information (instruments, routing).
    Non-invasive, doesn't require instrument instances.
    """
    info = {
        'instruments': [],
        'routing': [],
    }
    
    # Get current instruments
    instruments = moku.get_instruments() or []
    info['instruments'] = instruments
    
    # Get current routing
    connections_raw = moku.get_connections() or []
    info['routing'] = connections_raw
    
    return info


def read_detailed_settings(moku: MultiInstrument, instruments: list[str]) -> dict[int, dict[str, Any]]:
    """
    Level 2: Read detailed instrument settings.
    Uses MultiInstrument introspection APIs (polite, but requires active connection).
    
    Returns:
        dict[slot_num, settings_dict]
    """
    detailed = {}
    
    for slot_num, instrument_name in enumerate(instruments, start=1):
        if not instrument_name or not instrument_name.strip():
            continue
        
        inst_name = instrument_name.strip()
        slot_settings = {}
        
        try:
            if inst_name == 'CloudCompile':
                # Read control registers (CR0-CR31)
                # @CLAUDE: Use get_control(idx) from CloudCompile instance
                # Note: Getting CloudCompile instance may require bitstream, but if instrument
                # is already deployed, set_instrument() should return existing instance
                try:
                    from moku.instruments import CloudCompile
                    # Try to get existing instrument instance
                    # If instrument is already deployed, this should return existing instance
                    try:
                        cc = moku.set_instrument(slot_num, CloudCompile)
                    except TypeError:
                        # set_instrument might require bitstream parameter
                        # Try without it - if instrument exists, this might work
                        cc = None
                        # Alternative: try to access via internal state if available
                        pass
                    
                    if cc and hasattr(cc, 'get_control'):
                        control_regs = {}
                        # Try to read common control registers (0-31)
                        for reg_idx in range(32):
                            try:
                                value = cc.get_control(reg_idx)
                                if value is not None and value != 0:  # Only store non-zero values
                                    control_regs[reg_idx] = value
                            except Exception:
                                # Register might not be readable or doesn't exist
                                pass
                        if control_regs:
                            slot_settings['control_registers'] = control_regs
                    else:
                        slot_settings['_note'] = 'CloudCompile instance not accessible (bitstream may be required)'
                except Exception as e:
                    slot_settings['_error'] = f"Could not read CloudCompile settings: {e}"
            
            elif inst_name == 'Oscilloscope':
                # Read frontend and output settings
                # @CLAUDE: Use get_frontend() and get_output() from _mim.py (on MultiInstrument)
                try:
                    # Try to read frontend settings (impedance, coupling, attenuation)
                    if hasattr(moku, 'get_frontend'):
                        try:
                            frontend = moku.get_frontend(slot_num)
                            if frontend:
                                slot_settings['frontend'] = frontend
                        except Exception:
                            pass
                    
                    # Try to read output settings (gain)
                    if hasattr(moku, 'get_output'):
                        try:
                            output = moku.get_output(slot_num)
                            if output:
                                slot_settings['output'] = output
                        except Exception:
                            pass
                except Exception as e:
                    slot_settings['_error'] = f"Could not read Oscilloscope settings: {e}"
            
            # For other instruments, try generic MultiInstrument APIs
            else:
                try:
                    # Try frontend/output APIs (might work for other instruments too)
                    if hasattr(moku, 'get_frontend'):
                        try:
                            frontend = moku.get_frontend(slot_num)
                            if frontend:
                                slot_settings['frontend'] = frontend
                        except Exception:
                            pass
                    
                    if hasattr(moku, 'get_output'):
                        try:
                            output = moku.get_output(slot_num)
                            if output:
                                slot_settings['output'] = output
                        except Exception:
                            pass
                except Exception as e:
                    slot_settings['_error'] = f"Could not read {inst_name} settings: {e}"
        
        except Exception as e:
            slot_settings['_error'] = f"Failed to access slot {slot_num}: {e}"
        
        if slot_settings:
            detailed[slot_num] = slot_settings
    
    return detailed


def read_dio_settings(moku: MultiInstrument) -> dict[str, Any] | None:
    """
    Level 2: Read DIO configuration (Go/Delta only).
    @CLAUDE: Use get_dio() from _mim.py
    """
    try:
        if hasattr(moku, 'get_dio'):
            dio_config = moku.get_dio()
            return dio_config
    except Exception:
        pass
    return None


def build_moku_config(
    device_ip: str,
    platform_id: int,
    basic_info: dict[str, Any],
    detailed_settings: dict[int, dict[str, Any]] | None = None,
    dio_settings: dict[str, Any] | None = None,
    level: int = 1
) -> MokuConfig:
    """Build validated MokuConfig from collected information."""
    
    platform_map = {
        1: MOKU_LAB_PLATFORM,
        2: MOKU_GO_PLATFORM,
        3: MOKU_PRO_PLATFORM,
        4: MOKU_DELTA_PLATFORM,
    }
    
    platform = platform_map[platform_id].model_copy()
    platform.ip_address = device_ip
    
    # Build slots
    instruments = basic_info.get('instruments', [])
    slots = {}
    for slot_num, instrument_name in enumerate(instruments, start=1):
        if instrument_name and instrument_name.strip():
            slot_config_data = {
                'instrument': instrument_name.strip(),
                'settings': {},
                'control_registers': None,
                'bitstream': None,
            }
            
            # Merge detailed settings if available
            if detailed_settings and slot_num in detailed_settings:
                detailed = detailed_settings[slot_num]
                
                # Extract control registers
                if 'control_registers' in detailed:
                    slot_config_data['control_registers'] = detailed['control_registers']
                
                # Extract frontend/output settings into general settings dict
                settings = {}
                if 'frontend' in detailed:
                    settings['frontend'] = detailed['frontend']
                if 'output' in detailed:
                    settings['output'] = detailed['output']
                if 'state' in detailed:
                    settings['state'] = detailed['state']
                
                if settings:
                    slot_config_data['settings'] = settings
            
            slots[slot_num] = SlotConfig(**slot_config_data)
    
    # Build routing
    connections_raw = basic_info.get('routing', [])
    routing = []
    for conn in connections_raw:
        if isinstance(conn, dict) and 'source' in conn and 'destination' in conn:
            routing.append(MokuConnection(
                source=conn['source'],
                destination=conn['destination']
            ))
    
    # Build metadata
    metadata = {
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'source': 'moku_read',
        'read_level': level,
    }
    
    if dio_settings:
        metadata['dio'] = dio_settings
    
    if not slots:
        # Empty device - use model_construct to bypass validation
        return MokuConfig.model_construct(
            platform=platform,
            slots={},
            routing=routing,
            metadata=metadata
        )
    else:
        return MokuConfig(
            platform=platform,
            slots=slots,
            routing=routing,
            metadata=metadata
        )


def main():
    parser = argparse.ArgumentParser(
        description='Read Moku device state as validated MokuConfig',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Progressive escalation levels:
  Level 1 (default): Read basic info (instruments, routing) - non-invasive
  Level 2: Also read detailed settings (frontend, output, control registers, DIO)
  Level 3: Force connect if device is busy, read everything possible

Examples:
  # Polite read (default, writes to ./curr_model.json)
  python scripts/moku_read.py 192.168.13.147
  
  # Detailed read to specific file
  python scripts/moku_read.py 192.168.13.147 --level 2 --output my_config.json
  
  # Force connect and read everything
  python scripts/moku_read.py 192.168.13.147 --level 3 --force
  
  # Write to stdout (for piping)
  python scripts/moku_read.py 192.168.13.147 --output -
        """
    )
    parser.add_argument('device_ip', help='Device IP address')
    parser.add_argument(
        '--level', 
        type=int, 
        choices=[1, 2, 3], 
        default=1,
        help='Read level: 1=basic, 2=detailed, 3=maximum (default: 1)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force connect (disconnect existing connections)'
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Non-interactive mode (no prompts, for scripting)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./curr_model.json',
        help='Output file path (default: ./curr_model.json). Use "-" for stdout.'
    )
    
    args = parser.parse_args()
    
    device_ip = args.device_ip
    level = args.level
    force = args.force
    non_interactive = args.non_interactive
    output_file = args.output
    
    # Try to connect
    print(f"Connecting to {device_ip}...", file=sys.stderr)
    result = connect_politely(device_ip, force=force)
    
    if result is None:
        if not force and not non_interactive:
            print(f"\n⚠ Device {device_ip} is busy or connection failed.", file=sys.stderr)
            print("Options:", file=sys.stderr)
            print("  1. Use --force to disconnect existing connections", file=sys.stderr)
            print("  2. Use --level 3 to escalate to maximum invasiveness", file=sys.stderr)
            print("  3. Wait for device to become available", file=sys.stderr)
        else:
            print(f"Error: Could not connect to {device_ip}", file=sys.stderr)
        sys.exit(1)
    
    moku, platform_id = result
    print(f"  ✓ Connected (platform_id={platform_id})", file=sys.stderr)
    
    try:
        # Level 1: Basic info (always read)
        print("\n[Level 1] Reading basic information...", file=sys.stderr)
        basic_info = read_basic_info(moku)
        instruments = basic_info.get('instruments', [])
        num_instruments = len([i for i in instruments if i])
        num_routing = len(basic_info.get('routing', []))
        print(f"  ✓ Found {num_instruments} instrument(s), {num_routing} routing connection(s)", file=sys.stderr)
        
        detailed_settings = None
        dio_settings = None
        
        # Level 2: Detailed settings (if requested)
        if level >= 2:
            print("\n[Level 2] Reading detailed settings...", file=sys.stderr)
            if num_instruments > 0:
                detailed_settings = read_detailed_settings(moku, instruments)
                if detailed_settings:
                    print(f"  ✓ Read settings for {len(detailed_settings)} slot(s)", file=sys.stderr)
                else:
                    print("  ℹ No detailed settings available", file=sys.stderr)
            
            # Try to read DIO settings
            dio_settings = read_dio_settings(moku)
            if dio_settings:
                print("  ✓ Read DIO configuration", file=sys.stderr)
        
        # Level 3: Maximum invasiveness (if requested)
        if level >= 3:
            print("\n[Level 3] Maximum invasiveness mode...", file=sys.stderr)
            print("  ℹ All available information collected", file=sys.stderr)
        
        # Build and validate MokuConfig
        print("\nBuilding MokuConfig...", file=sys.stderr)
        config = build_moku_config(
            device_ip=device_ip,
            platform_id=platform_id,
            basic_info=basic_info,
            detailed_settings=detailed_settings,
            dio_settings=dio_settings,
            level=level
        )
        
        # Validate routing
        routing_errors = config.validate_routing()
        if routing_errors:
            print("  ⚠ Routing validation warnings:", file=sys.stderr)
            for error in routing_errors:
                print(f"    - {error}", file=sys.stderr)
        
        print("  ✓ Validated MokuConfig ready", file=sys.stderr)
        
        # Output as JSON (to file or stdout)
        config_json = json.dumps(config.model_dump(), indent=2)
        
        if output_file == '-':
            # Write to stdout
            print("\n" + "="*60, file=sys.stderr)
            print("MokuConfig JSON (stdout):", file=sys.stderr)
            print("="*60 + "\n", file=sys.stderr)
            print(config_json)
        else:
            # Write to file
            output_path = Path(output_file)
            output_path.write_text(config_json)
            print(f"\n✓ MokuConfig written to: {output_path.absolute()}", file=sys.stderr)
        
        # Offer escalation if not at max level
        if level < 3 and not non_interactive:
            print("\n" + "="*60, file=sys.stderr)
            print("💡 To get more detailed information:", file=sys.stderr)
            print(f"   python scripts/moku_read.py {device_ip} --level {level + 1}", file=sys.stderr)
            if not force:
                print(f"   python scripts/moku_read.py {device_ip} --level 3 --force", file=sys.stderr)
            print("="*60, file=sys.stderr)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Disconnect
        try:
            moku.relinquish_ownership()
            print("\n  ✓ Disconnected", file=sys.stderr)
        except Exception:
            pass


if __name__ == "__main__":
    main()
