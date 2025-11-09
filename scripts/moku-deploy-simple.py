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
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to deployment config (YAML/JSON)"),
    force: bool = typer.Option(False, "-D", help="Force mode: disconnect all, overwrite, no compatibility checking"),
):
    """
    Deploy configuration to Moku device.
    
    Default (interactive): Politely request information, always get user permission.
    -D (force): Force disconnect all connections, overwrite state, no compatibility checking.
    """
    # Load config
    if config:
        print(f"Loading config from {config}...")
        desired_config = load_config(config)
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


if __name__ == "__main__":
    app()
