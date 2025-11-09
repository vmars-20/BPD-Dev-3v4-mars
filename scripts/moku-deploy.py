#!/usr/bin/env python3
"""
moku-deploy: Moku device deployment and discovery utility

Handoff-friendly deployment tool with state-aware deployment and session management.
Uses Pydantic models from libs/moku-models/ for all configuration.

Key Features:
- State-aware deployment: Retrieves current device state before deploying
- State comparison: Compares desired vs current state (both as MokuConfig objects)
- Safe defaults: Fails if states don't match (unless -I or -F)
- Interactive mode (-I): Prompts user on state mismatches
- Force mode (-F): Overrides without prompting
- Debug mode (-D): Enables MOKU_LOG and verbose logging

Usage:
    # Discover devices on network
    uv run python scripts/moku-deploy.py discover

    # List cached devices
    uv run python scripts/moku-deploy.py list

    # Deploy with state checking (fails if device state differs)
    uv run python scripts/moku-deploy.py deploy --device 192.168.1.100 --config deployment.yaml

    # Interactive mode (prompts on state mismatch)
    uv run python scripts/moku-deploy.py deploy --device 192.168.1.100 --config deployment.yaml -I

    # Force mode (overrides without prompting)
    uv run python scripts/moku-deploy.py deploy --device 192.168.1.100 --config deployment.yaml -F

    # Debug mode (enables MOKU_LOG and verbose logging)
    uv run python scripts/moku-deploy.py deploy --device 192.168.1.100 --config deployment.yaml -D
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
import yaml
from loguru import logger
from rich.console import Console
from rich.table import Table
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "libs" / "moku-models"))

from moku_models import (
    MokuConfig,
    MokuConnection,
    MokuDeviceCache,
    MokuDeviceInfo,
    SlotConfig,
    MOKU_GO_PLATFORM,
    MOKU_LAB_PLATFORM,
    MOKU_PRO_PLATFORM,
    MOKU_DELTA_PLATFORM,
)

# Platform string identifier to platform object mapping
PLATFORM_MAP = {
    "moku_go": MOKU_GO_PLATFORM,
    "moku_lab": MOKU_LAB_PLATFORM,
    "moku_pro": MOKU_PRO_PLATFORM,
    "moku_delta": MOKU_DELTA_PLATFORM,
}

# Platform ID mapping (moku library platform_id values)
# platform_id: 1=Lab, 2=Go, 3=Pro, 4=Delta
# Use platform name as key (Pydantic models aren't hashable)
PLATFORM_ID_MAP = {
    "Moku:Go": 2,
    "Moku:Lab": 1,
    "Moku:Pro": 3,
    "Moku:Delta": 4,
}

# Platform name to platform object mapping
PLATFORM_NAME_TO_OBJECT = {
    "Moku:Go": MOKU_GO_PLATFORM,
    "Moku:Lab": MOKU_LAB_PLATFORM,
    "Moku:Pro": MOKU_PRO_PLATFORM,
    "Moku:Delta": MOKU_DELTA_PLATFORM,
}

# Reverse mapping: platform_id -> platform name
PLATFORM_ID_TO_NAME = {v: k for k, v in PLATFORM_ID_MAP.items()}

try:
    from moku.instruments import MultiInstrument
    from moku import Moku
except ImportError:
    print("Error: moku library not installed. Run: uv sync")
    sys.exit(1)


# Initialize Typer app
app = typer.Typer(
    name="moku-deploy",
    help="Moku device deployment and discovery utility",
    add_completion=False,
)

# Initialize Rich console
console = Console()

# Cache file path
CACHE_DIR = Path.home() / ".moku-deploy"
CACHE_FILE = CACHE_DIR / "device_cache.json"


def load_cache() -> MokuDeviceCache:
    """Load device cache from disk."""
    try:
        if not CACHE_FILE.exists():
            return MokuDeviceCache()
        with open(CACHE_FILE) as f:
            data = json.load(f)
        return MokuDeviceCache.from_cache_dict(data)
    except Exception as e:
        logger.warning(f"Could not load device cache: {e}")
        return MokuDeviceCache()


def save_cache(cache: MokuDeviceCache) -> None:
    """Save device cache to disk."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache.to_cache_dict(), f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save device cache: {e}")


def humanize_time_ago(timestamp_str: str) -> str:
    """Convert ISO timestamp to human-readable 'time ago' format."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())

        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        else:
            days = seconds // 86400
            return f"{days}d ago"
    except Exception:
        return timestamp_str


def retrieve_current_state(moku: MultiInstrument, platform) -> MokuConfig:
    """
    Retrieve current device state as MokuConfig object.

    Uses introspection APIs:
    - get_instruments() → slot configurations
    - get_connections() → routing configuration

    Args:
        moku: Connected MultiInstrument instance
        platform: Platform object (MokuGoPlatform, etc.)

    Returns:
        MokuConfig representing current device state
    """
    # Get current instruments
    instruments = moku.get_instruments()
    # instruments is a list[str] like ['CloudCompile', 'Oscilloscope', '', ''] or None if empty
    if instruments is None:
        instruments = []

    # Build slots dict
    slots = {}
    for slot_num, instrument_name in enumerate(instruments, start=1):
        if instrument_name and instrument_name.strip():
            slots[slot_num] = SlotConfig(
                instrument=instrument_name.strip(),
                settings={},  # We don't retrieve settings (would need per-instrument APIs)
                bitstream=None,  # Can't retrieve bitstream path from device
                control_registers=None,  # Would need CloudCompile-specific API
            )

    # Get current routing
    connections_raw = moku.get_connections()
    # connections_raw is list[dict] with 'source' and 'destination' keys, or None if empty
    if connections_raw is None:
        connections_raw = []
    routing = [
        MokuConnection(source=conn['source'], destination=conn['destination'])
        for conn in connections_raw
    ]

    # Create MokuConfig from current state
    # Use model_construct to bypass validation since empty slots is valid for retrieved state
    # (device might have no instruments deployed)
    if not slots:
        # Device has no instruments - create a minimal valid config for comparison
        # We'll use model_construct to bypass the "at least one slot" validator
        current_state = MokuConfig.model_construct(
            platform=platform,
            slots={},  # Empty slots is valid for retrieved state
            routing=routing,
            metadata={
                'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'source': 'device_introspection',
                'note': 'Device has no instruments deployed'
            }
        )
    else:
        # Normal validation path when slots exist
        current_state = MokuConfig(
            platform=platform,
            slots=slots,
            routing=routing,
            metadata={
                'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'source': 'device_introspection'
            }
        )

    return current_state


def compare_states(current: MokuConfig, desired: MokuConfig) -> dict:
    """
    Compare current and desired device states.

    Returns a dictionary with differences:
    {
        'slots': {'added': [...], 'removed': [...], 'changed': [...]},
        'routing': {'added': [...], 'removed': [...], 'unchanged': [...]},
        'identical': bool
    }

    Args:
        current: Current device state (MokuConfig)
        desired: Desired deployment state (MokuConfig)

    Returns:
        Dictionary describing differences
    """
    diff = {
        'slots': {'added': [], 'removed': [], 'changed': []},
        'routing': {'added': [], 'removed': [], 'unchanged': []},
        'identical': True
    }

    # Compare slots
    current_slots = set(current.slots.keys())
    desired_slots = set(desired.slots.keys())

    # Added slots (in desired but not in current)
    for slot_num in desired_slots - current_slots:
        diff['slots']['added'].append((slot_num, desired.slots[slot_num]))
        diff['identical'] = False

    # Removed slots (in current but not in desired)
    for slot_num in current_slots - desired_slots:
        diff['slots']['removed'].append((slot_num, current.slots[slot_num]))
        diff['identical'] = False

    # Changed slots (same slot number, different instrument)
    for slot_num in current_slots & desired_slots:
        current_slot = current.slots[slot_num]
        desired_slot = desired.slots[slot_num]
        if current_slot.instrument != desired_slot.instrument:
            diff['slots']['changed'].append((
                slot_num,
                current_slot.instrument,
                desired_slot.instrument
            ))
            diff['identical'] = False

    # Compare routing
    # Normalize connections for comparison (sort by source, then destination)
    def normalize_conn(conn: MokuConnection) -> tuple:
        return (conn.source, conn.destination)

    current_routing = {normalize_conn(c) for c in current.routing}
    desired_routing = {normalize_conn(c) for c in desired.routing}

    # Added connections
    for conn_tuple in desired_routing - current_routing:
        conn = next(c for c in desired.routing if normalize_conn(c) == conn_tuple)
        diff['routing']['added'].append(conn)
        diff['identical'] = False

    # Removed connections
    for conn_tuple in current_routing - desired_routing:
        conn = next(c for c in current.routing if normalize_conn(c) == conn_tuple)
        diff['routing']['removed'].append(conn)
        diff['identical'] = False

    # Unchanged connections
    for conn_tuple in current_routing & desired_routing:
        conn = next(c for c in current.routing if normalize_conn(c) == conn_tuple)
        diff['routing']['unchanged'].append(conn)

    return diff


def display_state_diff(diff: dict) -> None:
    """Display state differences in a human-readable format."""
    console.print("\n[bold yellow]State Comparison:[/bold yellow]")

    if diff['identical']:
        console.print("[green]✓ Current state matches desired state[/green]")
        return

    # Display slot differences
    if diff['slots']['added']:
        console.print("\n[bold]Slots to ADD:[/bold]")
        for slot_num, slot_config in diff['slots']['added']:
            console.print(f"  Slot {slot_num}: {slot_config.instrument}")

    if diff['slots']['removed']:
        console.print("\n[bold]Slots to REMOVE:[/bold]")
        for slot_num, slot_config in diff['slots']['removed']:
            console.print(f"  Slot {slot_num}: {slot_config.instrument}")

    if diff['slots']['changed']:
        console.print("\n[bold]Slots to CHANGE:[/bold]")
        for slot_num, current_instr, desired_instr in diff['slots']['changed']:
            console.print(f"  Slot {slot_num}: {current_instr} → {desired_instr}")

    # Display routing differences
    if diff['routing']['added']:
        console.print("\n[bold]Routing to ADD:[/bold]")
        for conn in diff['routing']['added']:
            console.print(f"  {conn.source} → {conn.destination}")

    if diff['routing']['removed']:
        console.print("\n[bold]Routing to REMOVE:[/bold]")
        for conn in diff['routing']['removed']:
            console.print(f"  {conn.source} → {conn.destination}")

    if diff['routing']['unchanged']:
        console.print(f"\n[dim]Unchanged routing: {len(diff['routing']['unchanged'])} connection(s)[/dim]")


@app.command()
def discover(timeout: int = typer.Option(2, help="Discovery timeout in seconds")):
    """Discover Moku devices on the network via zeroconf."""
    console.print("[bold blue]Discovering Moku devices...[/bold blue]")

    cache = MokuDeviceCache()
    discovered_devices = []
    zc = Zeroconf()

    def on_service_state_change(zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                # Get IPv4 address
                addresses = info.parsed_addresses()
                ipv4_addresses = [addr for addr in addresses if ':' not in addr]
                ip = ipv4_addresses[0] if ipv4_addresses else addresses[0]

                now = datetime.now(timezone.utc).isoformat()
                device_info = MokuDeviceInfo(
                    ip=ip,
                    port=info.port,
                    zeroconf_name=name,
                    last_seen=now
                )
                discovered_devices.append(device_info)
                cache.add_device(device_info)

    # Start discovery
    browser = ServiceBrowser(zc, "_moku._tcp.local.", handlers=[on_service_state_change])
    import time
    time.sleep(timeout)
    zc.close()

    if not discovered_devices:
        console.print("[yellow]No Moku devices found on the network[/yellow]")
        return

    # Connect to each device to get metadata
    for device in discovered_devices:
        try:
            moku = Moku(ip=device.ip, force_connect=False, connect_timeout=5)
            device.canonical_name = moku.name()
            device.serial_number = moku.serial_number()
            moku.relinquish_ownership()
            cache.add_device(device)
        except Exception as e:
            logger.warning(f"Could not retrieve metadata for {device.ip}: {e}")

    # Save cache
    save_cache(cache)

    # Display results
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name")
    table.add_column("IP Address")
    table.add_column("Serial Number")
    table.add_column("Port")

    for device in discovered_devices:
        table.add_row(
            device.canonical_name or "N/A",
            device.ip,
            device.serial_number or "N/A",
            str(device.port)
        )

    console.print(table)
    console.print(f"\n[green]Found {len(discovered_devices)} device(s)[/green]")
    console.print(f"Cache saved to: {CACHE_FILE}")


@app.command()
def list():
    """List cached devices."""
    cache = load_cache()

    if not cache.devices:
        console.print("[yellow]No cached devices found. Run 'discover' first.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Name")
    table.add_column("IP Address")
    table.add_column("Serial Number")
    table.add_column("Last Seen")

    for device in cache.devices.values():
        table.add_row(
            device.canonical_name or "N/A",
            device.ip,
            device.serial_number or "N/A",
            humanize_time_ago(device.last_seen)
        )

    console.print("[bold]Cached Devices:[/bold]")
    console.print(table)


@app.command()
def deploy(
    device: str = typer.Option(..., "--device", "-d", help="Device IP address or name"),
    bitstream: Optional[Path] = typer.Option(None, "--bitstream", "-b", help="Path to bitstream file"),
    slot: int = typer.Option(2, "--slot", "-s", help="Slot number (1-4)"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to deployment config (JSON or YAML)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force connection (override busy device)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate configuration without deploying"),
    interactive: bool = typer.Option(False, "--interactive", "-I", help="Interactive mode: prompt on state mismatch"),
    force_deploy: bool = typer.Option(False, "--force-deploy", "-F", help="Force mode: override state mismatch without prompting"),
    debug: bool = typer.Option(False, "--debug", "-D", help="Debug mode: enable MOKU_LOG and verbose logging"),
):
    """
    Deploy bitstream to Moku device with state-aware deployment.

    This command:
    1. Retrieves current device state (instruments, routing)
    2. Compares with desired state
    3. Fails if states differ (unless -I or -F)
    4. Deploys if states match or override is confirmed
    """
    # Enable debug mode if requested
    if debug:
        os.environ['MOKU_LOG'] = '1'
        logger.info("Debug mode enabled: MOKU_LOG=1")
        console.print("[bold blue]Debug mode: MOKU_LOG enabled, verbose logging active[/bold blue]")
        
        # Also enable moku library debug logging if available
        try:
            from moku.logging import enable_debug_logging
            enable_debug_logging()
            logger.info("Moku library debug logging enabled")
        except (ImportError, AttributeError):
            # Moku library debug logging not available, continue without it
            pass

    # Resolve device identifier to IP
    cache = load_cache()
    device_info = cache.find_by_identifier(device)

    if device_info:
        ip = device_info.ip
        console.print(f"[blue]Using cached device: {device_info.canonical_name or ip}[/blue]")
    elif '.' in device and device.replace('.', '').isdigit():
        # Looks like an IP address
        ip = device
    else:
        console.print(f"[red]Device '{device}' not found. Run 'discover' first or use IP address.[/red]")
        raise typer.Exit(1)

    # Load deployment config or create from arguments
    if config:
        console.print(f"[blue]Loading config from {config}...[/blue]")
        try:
            # Support both JSON and YAML formats
            if config.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(config.read_text())
            else:
                data = json.loads(config.read_text())

            # Handle string platform identifiers
            if isinstance(data.get('platform'), str):
                platform_str = data['platform'].lower()
                if platform_str in PLATFORM_MAP:
                    # Replace string with platform object
                    data['platform'] = PLATFORM_MAP[platform_str].model_dump()
                    console.print(f"[blue]Platform: {platform_str}[/blue]")
                else:
                    console.print(f"[red]Unknown platform: {platform_str}[/red]")
                    console.print(f"[yellow]Available platforms: {', '.join(PLATFORM_MAP.keys())}[/yellow]")
                    raise typer.Exit(1)

            desired_config = MokuConfig.model_validate(data)

            # Override bitstream if -b argument provided
            if bitstream:
                bitstream_path = Path(bitstream).absolute()
                if slot in desired_config.slots:
                    # Override bitstream for specified slot
                    slot_config = desired_config.slots[slot]
                    if slot_config.instrument == 'CloudCompile':
                        slot_config.bitstream = str(bitstream_path)
                        console.print(f"[blue]Overriding bitstream for slot {slot}: {bitstream_path.name}[/blue]")
                    else:
                        console.print(f"[yellow]Warning: Slot {slot} is {slot_config.instrument}, not CloudCompile. Bitstream override ignored.[/yellow]")
                else:
                    # Find first CloudCompile slot and override it
                    cloudcompile_slots = desired_config.get_instrument_slots('CloudCompile')
                    if cloudcompile_slots:
                        override_slot = cloudcompile_slots[0]
                        desired_config.slots[override_slot].bitstream = str(bitstream_path)
                        console.print(f"[blue]Overriding bitstream for slot {override_slot}: {bitstream_path.name}[/blue]")
                    else:
                        console.print(f"[yellow]Warning: No CloudCompile slots found in config. Bitstream override ignored.[/yellow]")

        except Exception as e:
            console.print(f"[red]Failed to load config: {e}[/red]")
            raise typer.Exit(1)
    elif bitstream:
        # Create minimal config from arguments (for bitstream-only deployment)
        console.print(f"[blue]Creating deployment config...[/blue]")
        console.print("[yellow]Warning: Using default Moku:Go platform settings[/yellow]")
        console.print("[yellow]Consider using --config with full YAML specification[/yellow]")

        # When using bitstream without config, we create a minimal config
        # Default to Moku:Go platform
        platform = MOKU_GO_PLATFORM.model_copy()
        platform.ip_address = ip

        desired_config = MokuConfig(
            platform=platform,
            slots={
                slot: SlotConfig(
                    instrument='CloudCompile',
                    bitstream=str(bitstream.absolute())
                )
            },
            routing=[
                MokuConnection(source=f'Slot{slot}OutA', destination='Output1'),
                MokuConnection(source=f'Slot{slot}OutB', destination='Output2'),
            ],
            metadata={
                'deployed_at': datetime.now(timezone.utc).isoformat(),
                'target_ip': ip
            }
        )
    else:
        console.print("[red]Must provide either --bitstream or --config[/red]")
        raise typer.Exit(1)

    # Validate bitstream exists
    for slot_num, slot_config in desired_config.slots.items():
        if slot_config.bitstream:
            bitstream_path = Path(slot_config.bitstream)
            if not bitstream_path.exists():
                if dry_run:
                    # In dry-run mode, warn but continue
                    console.print(f"[yellow]Warning: Bitstream not found: {bitstream_path}[/yellow]")
                else:
                    # In deployment mode, this is an error
                    console.print(f"[red]Bitstream not found: {bitstream_path}[/red]")
                    raise typer.Exit(1)

    # Dry-run mode: Display config and exit
    if dry_run:
        console.print("\n" + "=" * 80)
        console.print("[yellow]DRY RUN MODE - No hardware deployment will occur[/yellow]")
        console.print("=" * 80)
        console.print(f"Target IP: {ip}")
        console.print(f"\nSlots to deploy:")
        for slot_num, slot_config in desired_config.slots.items():
            console.print(f"  Slot {slot_num}: {slot_config.instrument}")
            if slot_config.bitstream:
                console.print(f"    Bitstream: {Path(slot_config.bitstream).name}")
            if slot_config.settings:
                console.print(f"    Settings: {slot_config.settings}")

        console.print(f"\nConnections ({len(desired_config.routing)}):")
        for conn in desired_config.routing:
            console.print(f"  {conn.source} → {conn.destination}")

        console.print("\n" + "=" * 80)
        console.print("[green]✓ Configuration validated successfully![/green]")
        console.print("[yellow]Use without --dry-run to deploy to hardware[/yellow]")
        console.print("=" * 80)
        return

    # Deploy to hardware with state checking
    console.print("\n" + "=" * 80)
    console.print("Moku Deployment (State-Aware)")
    console.print("=" * 80)
    console.print(f"Target IP: {ip}")
    console.print(f"Slots: {[s for s in desired_config.slots.keys()]}")
    console.print(f"Connections: {len(desired_config.routing)}")
    console.print()

    try:
        # Determine platform_id from platform name
        platform_name = desired_config.platform.name
        platform_id = PLATFORM_ID_MAP.get(platform_name)
        
        if platform_id is None:
            # Fallback: try to match by platform name (case-insensitive)
            platform_name_lower = platform_name.lower()
            if 'go' in platform_name_lower:
                platform_id = 2
            elif 'lab' in platform_name_lower:
                platform_id = 1
            elif 'pro' in platform_name_lower:
                platform_id = 3
            elif 'delta' in platform_name_lower:
                platform_id = 4
            else:
                console.print("[yellow]Warning: Could not determine platform_id, defaulting to Moku:Go (2)[/yellow]")
                platform_id = 2

        # Connect to device with persist_state=True for state introspection
        console.print("[1/4] Connecting to device...")
        try:
            moku = MultiInstrument(
                ip,
                platform_id=platform_id,
                force_connect=force,
                persist_state=True  # Enable state retention for introspection
            )
            console.print(f"  ✓ Connected (persist_state=True)")
        except Exception as e:
            error_msg = str(e)
            # Check if this is the "API Connection already exists" error
            if "API Connection already exists" in error_msg or "already exists" in error_msg.lower():
                if not force:
                    console.print(f"\n[red]✗ Connection failed: Device is already connected[/red]")
                    console.print("[yellow]Another process or session is connected to this device.[/yellow]")
                    console.print("[yellow]Use --force (-f) to override the existing connection.[/yellow]")
                    console.print(f"\n[yellow]Example:[/yellow]")
                    console.print(f"  uv run python scripts/moku-deploy.py deploy -d {ip} -c <config> --force")
                    raise typer.Exit(1)
                else:
                    # Force was already set, but still failed - re-raise
                    raise
            else:
                # Some other error - re-raise
                raise

        # Retrieve current device state
        console.print("\n[2/4] Retrieving current device state...")
        platform_copy = desired_config.platform.model_copy()
        platform_copy.ip_address = ip
        current_state = retrieve_current_state(moku, platform_copy)
        console.print(f"  ✓ Retrieved state: {len(current_state.slots)} slot(s), {len(current_state.routing)} connection(s)")

        # Compare states
        console.print("\n[3/4] Comparing states...")
        state_diff = compare_states(current_state, desired_config)
        display_state_diff(state_diff)

        # Handle state mismatch
        if not state_diff['identical']:
            if force_deploy:
                console.print("\n[bold yellow]Force mode (-F): Overriding state mismatch[/bold yellow]")
            elif interactive:
                console.print("\n[yellow]State mismatch detected![/yellow]")
                response = typer.prompt(
                    "Proceed with deployment? This will change the device state. (yes/no)",
                    default="no"
                )
                if response.lower() not in ['yes', 'y']:
                    console.print("[yellow]Deployment cancelled by user[/yellow]")
                    moku.relinquish_ownership()
                    raise typer.Exit(0)
                console.print("[green]User confirmed: proceeding with deployment[/green]")
            else:
                console.print("\n[red]✗ State mismatch detected![/red]")
                console.print("[yellow]Current device state does not match desired deployment.[/yellow]")
                console.print("[yellow]Use -I (interactive) to prompt, or -F (force) to override.[/yellow]")
                moku.relinquish_ownership()
                raise typer.Exit(1)
        else:
            console.print("\n[green]✓ States match - safe to deploy[/green]")

        # Deploy instruments
        console.print("\n[4/4] Deploying instruments...")
        from moku.instruments import CloudCompile, Oscilloscope

        for slot_num, slot_config in desired_config.slots.items():
            if slot_config.instrument == 'CloudCompile':
                if not slot_config.bitstream:
                    console.print(f"  [yellow]Slot {slot_num}: No bitstream specified[/yellow]")
                    continue

                console.print(f"  Slot {slot_num}: CloudCompile")
                console.print(f"    Bitstream: {Path(slot_config.bitstream).name}")

                # Deploy CloudCompile with custom bitstream
                moku.set_instrument(slot_num, CloudCompile, bitstream=slot_config.bitstream)
                console.print(f"  ✓ Deployed to slot {slot_num}")

                # Apply control registers if specified
                if slot_config.control_registers:
                    cc = moku.get_instrument(slot_num)
                    if hasattr(cc, 'set_controls'):
                        cc.set_controls(slot_config.control_registers)
                        console.print(f"    Applied {len(slot_config.control_registers)} control register(s)")

            elif slot_config.instrument == 'Oscilloscope':
                console.print(f"  Slot {slot_num}: Oscilloscope")
                osc = moku.set_instrument(slot_num, Oscilloscope)

                # Apply settings if provided
                if 'timebase' in slot_config.settings:
                    timebase = slot_config.settings['timebase']
                    osc.set_timebase(*timebase)
                    console.print(f"    Timebase: {timebase}")

                console.print(f"  ✓ Deployed to slot {slot_num}")

            else:
                console.print(f"  [yellow]Slot {slot_num}: {slot_config.instrument} (not yet supported)[/yellow]")

        # Configure routing
        if desired_config.routing:
            console.print("\n[5/4] Configuring routing...")
            connections = [conn.to_dict() for conn in desired_config.routing]
            moku.set_connections(connections)
            console.print(f"  ✓ Configured {len(connections)} connection(s)")

            for conn in desired_config.routing:
                console.print(f"    {conn.source} → {conn.destination}")
        else:
            console.print("\n[5/4] No routing changes needed")

        console.print("\n" + "=" * 80)
        console.print("[green]✓ Deployment successful![/green]")
        console.print("=" * 80)
        console.print(f"\nAccess device at: http://{ip}")

        # Keep connection alive (optional in interactive mode)
        if interactive:
            try:
                input("\nPress Enter to disconnect...")
            except (EOFError, KeyboardInterrupt):
                pass

        moku.relinquish_ownership()

    except typer.Exit:
        # Re-raise typer.Exit to preserve exit codes
        raise
    except Exception as e:
        error_msg = str(e)
        
        # Check for connection already exists error (in case it wasn't caught earlier)
        if "API Connection already exists" in error_msg or "already exists" in error_msg.lower():
            if not force:
                console.print(f"\n[red]✗ Deployment failed: Device is already connected[/red]")
                console.print("[yellow]Another process or session is connected to this device.[/yellow]")
                console.print("[yellow]Use --force (-f) to override the existing connection.[/yellow]")
                console.print(f"\n[yellow]Example:[/yellow]")
                console.print(f"  uv run python scripts/moku-deploy.py deploy -d {ip} -c <config> --force")
            else:
                console.print(f"\n[red]✗ Deployment failed: {e}[/red]")
        else:
            console.print(f"\n[red]✗ Deployment failed: {e}[/red]")
        
        if debug:
            logger.exception("Deployment error (debug mode)")
        else:
            logger.exception("Deployment error")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
