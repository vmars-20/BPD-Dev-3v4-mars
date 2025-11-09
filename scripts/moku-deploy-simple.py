#!/usr/bin/env python3
"""
moku-deploy: Simple Moku device deployment utility

Two modes:
- Default (interactive): Politely request information, always get user permission
- -D (force): Force disconnect all connections, overwrite state, no compatibility checking

Config reading: stdin → stdout (validated Pydantic model), with -i/-o for files
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "libs" / "moku-models"))

from moku_models import MokuConfig

try:
    from moku.instruments import MultiInstrument, CloudCompile, Oscilloscope
except ImportError:
    print("Error: moku library not installed. Run: uv sync")
    sys.exit(1)

app = typer.Typer(name="moku-deploy", help="Simple Moku device deployment utility")


def load_config(input_path: Optional[Path] = None) -> MokuConfig:
    """Load MokuConfig from file or stdin."""
    if input_path:
        content = input_path.read_text()
        if input_path.suffix.lower() in ['.yaml', '.yml']:
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)
    else:
        # Read from stdin
        content = sys.stdin.read()
        try:
            data = yaml.safe_load(content)
        except:
            data = json.loads(content)
    
    return MokuConfig.model_validate(data)


@app.command()
def deploy(
    device: str = typer.Option(..., "--device", "-d", help="Device IP address"),
    input_file: Optional[Path] = typer.Option(None, "-i", "--input", help="Input config file (YAML/JSON), defaults to stdin"),
    force: bool = typer.Option(False, "-D", help="Force mode: disconnect all, overwrite, no compatibility checking"),
):
    """
    Deploy configuration to Moku device.
    
    Reads config from stdin by default, or -i for file.
    
    Default (interactive): Politely request information, always get user permission.
    -D (force): Force disconnect all connections, overwrite state, no compatibility checking.
    """
    # Load config (from stdin by default, or -i for file)
    if input_file:
        print(f"Loading config from {input_file}...")
        desired_config = load_config(input_file)
    else:
        print("Reading config from stdin...")
        desired_config = load_config()
    
    # Validate config
    errors = desired_config.validate_routing()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print(f"\nConfiguration loaded:")
    print(f"  Platform: {desired_config.platform.name}")
    print(f"  Slots: {list(desired_config.slots.keys())}")
    print(f"  Routing: {len(desired_config.routing)} connections")
    
    # Get user permission (unless force mode)
    if not force:
        print("\n" + "=" * 60)
        print("INTERACTIVE MODE: Requesting permission")
        print("=" * 60)
        print(f"Target device: {device}")
        print(f"This will deploy the configuration above to the device.")
        response = typer.prompt("Proceed with deployment? (yes/no)", default="no")
        if response.lower() not in ['yes', 'y']:
            print("Deployment cancelled by user")
            sys.exit(0)
        print("User confirmed: proceeding with deployment")
    else:
        print("\n" + "=" * 60)
        print("FORCE MODE (-D): Disconnecting all, overwriting state")
        print("=" * 60)
    
    # Determine platform_id
    platform_name = desired_config.platform.name
    platform_id_map = {
        "Moku:Go": 2,
        "Moku:Lab": 1,
        "Moku:Pro": 3,
        "Moku:Delta": 4,
    }
    platform_id = platform_id_map.get(platform_name, 2)  # Default to Go
    
    # Connect to device
    print(f"\nConnecting to {device} (platform_id={platform_id})...")
    try:
        moku = MultiInstrument(
            device,
            platform_id=platform_id,
            force_connect=force,  # Force disconnect all if -D
            persist_state=False if force else True  # Don't persist if forcing
        )
        print("  ✓ Connected")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        if not force and "already exists" in str(e).lower():
            print("\nDevice is already connected. Use -D to force disconnect.")
        sys.exit(1)
    
    try:
        # Deploy instruments
        print("\nDeploying instruments...")
        for slot_num, slot_config in desired_config.slots.items():
            if slot_config.instrument == 'CloudCompile':
                if not slot_config.bitstream:
                    print(f"  Slot {slot_num}: No bitstream specified, skipping")
                    continue
                
                print(f"  Slot {slot_num}: CloudCompile ({Path(slot_config.bitstream).name})")
                cc = moku.set_instrument(slot_num, CloudCompile, bitstream=slot_config.bitstream)
                print(f"    ✓ Deployed")
                
                # Apply control registers if specified
                if slot_config.control_registers:
                    for reg_num, reg_value in sorted(slot_config.control_registers.items()):
                        try:
                            cc.set_control(reg_num, reg_value)
                        except Exception as e:
                            print(f"    ⚠ Warning: Could not set control register {reg_num}: {e}")
            
            elif slot_config.instrument == 'Oscilloscope':
                print(f"  Slot {slot_num}: Oscilloscope")
                osc = moku.set_instrument(slot_num, Oscilloscope)
                # Apply settings if specified
                if slot_config.settings:
                    try:
                        osc.set_frontend(1, **slot_config.settings)
                    except Exception as e:
                        print(f"    ⚠ Warning: Could not apply settings: {e}")
                print(f"    ✓ Deployed")
            
            else:
                print(f"  Slot {slot_num}: {slot_config.instrument} (not implemented, skipping)")
        
        # Configure routing
        if desired_config.routing:
            print("\nConfiguring routing...")
            connections = []
            for conn in desired_config.routing:
                connections.append({
                    'source': conn.source,
                    'destination': conn.destination
                })
            moku.set_connections(connections)
            print(f"  ✓ Configured {len(connections)} connections")
        
        print("\n" + "=" * 60)
        print("✓ Deployment complete")
        print("=" * 60)
    
    finally:
        # Graciously disconnect
        print("\nDisconnecting...")
        try:
            moku.relinquish_ownership()
            print("  ✓ Disconnected")
        except Exception as e:
            print(f"  ⚠ Warning during disconnect: {e}")


@app.command()
def read(
    input_file: Optional[Path] = typer.Option(None, "-i", "--input", help="Input config file (YAML/JSON)"),
    output_file: Optional[Path] = typer.Option(None, "-o", "--output", help="Output file (JSON)"),
):
    """
    Read and validate MokuConfig, output validated Pydantic model.
    
    Reads from stdin by default, or -i for file.
    Outputs to stdout by default, or -o for file.
    """
    # Load config
    config = load_config(input_file)
    
    # Validate
    errors = config.validate_routing()
    if errors:
        print("Validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    # Output as JSON (validated Pydantic model)
    output = json.dumps(config.model_dump(), indent=2)
    
    if output_file:
        output_file.write_text(output)
        print(f"Validated config written to {output_file}", file=sys.stderr)
    else:
        print(output)


@app.command()
def show(
    input_file: Optional[Path] = typer.Option(None, "-i", "--input", help="Input config file (YAML/JSON), defaults to stdin"),
):
    """
    Display MokuConfig as ASCII art visualization.
    
    Reads from stdin by default, or -i for file.
    Shows platform, slots, instruments, and routing in visual format.
    """
    # Load config
    config = load_config(input_file)
    
    # Validate
    errors = config.validate_routing()
    if errors:
        print("Validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    
    # ASCII Art Output
    print("\n" + "=" * 70)
    print(" MOKU CONFIGURATION")
    print("=" * 70)
    
    # Platform Info
    platform = config.platform
    print(f"\n📡 Platform: {platform.name}")
    if platform.ip_address:
        print(f"   IP: {platform.ip_address}")
    print(f"   Clock: {platform.clock_mhz} MHz")
    print(f"   Slots: {platform.slots}")
    print(f"   Inputs: {len(platform.analog_inputs)} ({', '.join([inp.port_id for inp in platform.analog_inputs])})")
    print(f"   Outputs: {len(platform.analog_outputs)} ({', '.join([out.port_id for out in platform.analog_outputs])})")
    
    # Slots Visualization
    print("\n" + "-" * 70)
    print(" SLOTS")
    print("-" * 70)
    
    if not config.slots:
        print("  (empty)")
    else:
        for slot_num in sorted(config.slots.keys()):
            slot_config = config.slots[slot_num]
            print(f"\n  ┌─ Slot {slot_num} ──────────────────────────────────────────────┐")
            print(f"  │ Instrument: {slot_config.instrument:<50} │")
            
            if slot_config.bitstream:
                bitstream_name = Path(slot_config.bitstream).name
                print(f"  │ Bitstream:  {bitstream_name:<50} │")
            
            if slot_config.control_registers:
                regs_str = ", ".join([f"CR{r}={v}" for r, v in sorted(slot_config.control_registers.items())[:3]])
                if len(slot_config.control_registers) > 3:
                    regs_str += f" ... (+{len(slot_config.control_registers)-3} more)"
                print(f"  │ Registers:   {regs_str:<50} │")
            
            if slot_config.settings:
                settings_str = str(slot_config.settings)[:50]
                if len(str(slot_config.settings)) > 50:
                    settings_str += "..."
                print(f"  │ Settings:    {settings_str:<50} │")
            
            print(f"  └──────────────────────────────────────────────────────────────┘")
    
    # Routing Visualization
    print("\n" + "-" * 70)
    print(" ROUTING")
    print("-" * 70)
    
    if not config.routing:
        print("  (no routing configured)")
    else:
        # Group by source
        routing_by_source = {}
        for conn in config.routing:
            if conn.source not in routing_by_source:
                routing_by_source[conn.source] = []
            routing_by_source[conn.source].append(conn.destination)
        
        for source in sorted(routing_by_source.keys()):
            destinations = routing_by_source[source]
            arrow = "─" * (50 - len(source) - len(destinations[0]) - 5)
            if len(destinations) == 1:
                print(f"  {source:<20} {arrow}→ {destinations[0]}")
            else:
                print(f"  {source:<20} {arrow}→ {destinations[0]}")
                for dest in destinations[1:]:
                    print(f"  {' ':<20} {'─' * 50}→ {dest}")
    
    # Metadata
    if config.metadata:
        print("\n" + "-" * 70)
        print(" METADATA")
        print("-" * 70)
        for key, value in config.metadata.items():
            if isinstance(value, str) and len(value) > 50:
                value = value[:47] + "..."
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 70 + "\n")


@app.command()
def export(
    device: str = typer.Option(..., "--device", "-d", help="Device IP address"),
    output_file: Optional[Path] = typer.Option(None, "-o", "--output", help="Output file (JSON), defaults to stdout"),
    force: bool = typer.Option(False, "-D", help="Force mode: disconnect all connections"),
):
    """
    Export current device state as validated MokuConfig.
    
    Connects to device, reads current state, outputs as validated Pydantic model.
    Outputs to stdout by default, or -o for file.
    """
    from datetime import datetime, timezone
    from moku_models import SlotConfig, MokuConnection
    
    # Determine platform (try common ones)
    platform_id_map = {
        1: "Moku:Lab",
        2: "Moku:Go", 
        3: "Moku:Pro",
        4: "Moku:Delta",
    }
    
    # Try to connect and detect platform
    print(f"Connecting to {device}...")
    platform_id = 2  # Default to Go
    moku = None
    
    for pid in [2, 1, 3, 4]:  # Try Go, Lab, Pro, Delta
        try:
            moku = MultiInstrument(
                device,
                platform_id=pid,
                force_connect=force,
                persist_state=True
            )
            platform_id = pid
            platform_name = platform_id_map[pid]
            print(f"  ✓ Connected (platform: {platform_name})")
            break
        except Exception as e:
            if "already exists" in str(e).lower() and not force:
                print(f"  Device is already connected. Use -D to force disconnect.")
                sys.exit(1)
            continue
    
    if moku is None:
        print("  ✗ Could not connect to device")
        sys.exit(1)
    
    try:
        # Get current instruments
        instruments = moku.get_instruments() or []
        slots = {}
        for slot_num, instrument_name in enumerate(instruments, start=1):
            if instrument_name and instrument_name.strip():
                slots[slot_num] = SlotConfig(
                    instrument=instrument_name.strip(),
                    settings={},
                    bitstream=None,
                    control_registers=None,
                )
        
        # Get current routing
        connections_raw = moku.get_connections() or []
        routing = []
        for conn in connections_raw:
            if isinstance(conn, dict) and 'source' in conn and 'destination' in conn:
                routing.append(MokuConnection(
                    source=conn['source'],
                    destination=conn['destination']
                ))
        
        # Get platform object
        from moku_models import (
            MOKU_GO_PLATFORM,
            MOKU_LAB_PLATFORM,
            MOKU_PRO_PLATFORM,
            MOKU_DELTA_PLATFORM,
        )
        platform_map = {
            1: MOKU_LAB_PLATFORM,
            2: MOKU_GO_PLATFORM,
            3: MOKU_PRO_PLATFORM,
            4: MOKU_DELTA_PLATFORM,
        }
        platform = platform_map[platform_id].model_copy()
        platform.ip_address = device
        
        # Create MokuConfig
        if not slots:
            # Empty device - use model_construct to bypass validation
            config = MokuConfig.model_construct(
                platform=platform,
                slots={},
                routing=routing,
                metadata={
                    'exported_at': datetime.now(timezone.utc).isoformat(),
                    'source': 'device_export',
                    'note': 'Device has no instruments deployed'
                }
            )
        else:
            config = MokuConfig(
                platform=platform,
                slots=slots,
                routing=routing,
                metadata={
                    'exported_at': datetime.now(timezone.utc).isoformat(),
                    'source': 'device_export'
                }
            )
        
        # Output as JSON (validated Pydantic model)
        output = json.dumps(config.model_dump(), indent=2)
        
        if output_file:
            output_file.write_text(output)
            print(f"\n✓ Exported config to {output_file}", file=sys.stderr)
        else:
            print(output)
    
    finally:
        # Graciously disconnect
        try:
            moku.relinquish_ownership()
        except Exception as e:
            print(f"  ⚠ Warning during disconnect: {e}", file=sys.stderr)


if __name__ == "__main__":
    app()
