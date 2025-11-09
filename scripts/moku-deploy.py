#!/usr/bin/env python3
"""
moku-deploy: Moku device deployment and discovery utility

Generic bitstream deployment tool with device discovery support.
Uses Pydantic models from libs/moku-models/ for all configuration.

Usage:
    # Discover devices on network
    uv run python scripts/moku-deploy.py discover

    # List cached devices
    uv run python scripts/moku-deploy.py list

    # Deploy bitstream (by IP)
    uv run python scripts/moku-deploy.py deploy --device 192.168.1.100 --bitstream path/to/bitstream.tar

    # Deploy bitstream (by name)
    uv run python scripts/moku-deploy.py deploy --device Lilo --bitstream path/to/bitstream.tar

    # Deploy with config file (JSON or YAML)
    uv run python scripts/moku-deploy.py deploy --device 192.168.1.100 --config deployment.yaml

    # Dry-run mode (validate without deploying)
    uv run python scripts/moku-deploy.py deploy --device 192.168.1.100 --config deployment.yaml --dry-run
"""

import json
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
    force: bool = typer.Option(False, "--force", "-f", help="Force connection"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate configuration without deploying"),
):
    """Deploy bitstream to Moku device."""

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

            deployment_config = MokuConfig.model_validate(data)
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
        deployment_config = MokuConfig(
            platform=MOKU_GO_PLATFORM,
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
    for slot_num, slot_config in deployment_config.slots.items():
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
        for slot_num, slot_config in deployment_config.slots.items():
            console.print(f"  Slot {slot_num}: {slot_config.instrument}")
            if slot_config.bitstream:
                console.print(f"    Bitstream: {Path(slot_config.bitstream).name}")
            if slot_config.settings:
                console.print(f"    Settings: {slot_config.settings}")

        console.print(f"\nConnections ({len(deployment_config.routing)}):")
        for conn in deployment_config.routing:
            console.print(f"  {conn.source} → {conn.destination}")

        console.print("\n" + "=" * 80)
        console.print("[green]✓ Configuration validated successfully![/green]")
        console.print("[yellow]Use without --dry-run to deploy to hardware[/yellow]")
        console.print("=" * 80)
        return

    # Deploy to hardware
    console.print("\n" + "=" * 80)
    console.print("Moku Deployment")
    console.print("=" * 80)
    console.print(f"Target IP: {ip}")
    console.print(f"Slots: {[s for s in deployment_config.slots.keys()]}")
    console.print(f"Connections: {len(deployment_config.routing)}")
    console.print()

    try:
        # Connect to device
        console.print("[1/3] Connecting to device...")
        moku = MultiInstrument(ip, platform_id=2, force_connect=force)
        console.print(f"  ✓ Connected")

        # Deploy instruments
        console.print("\n[2/3] Deploying instruments...")
        from moku.instruments import CloudCompile, Oscilloscope

        for slot_num, slot_config in deployment_config.slots.items():
            if slot_config.instrument == 'CloudCompile':
                if not slot_config.bitstream:
                    console.print(f"  [yellow]Slot {slot_num}: No bitstream specified[/yellow]")
                    continue

                console.print(f"  Slot {slot_num}: CloudCompile")
                console.print(f"    Bitstream: {Path(slot_config.bitstream).name}")

                # Deploy CloudCompile with custom bitstream
                moku.set_instrument(slot_num, CloudCompile, bitstream=slot_config.bitstream)
                console.print(f"  ✓ Deployed to slot {slot_num}")

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
        console.print("\n[3/3] Configuring routing...")
        if deployment_config.routing:
            connections = [conn.to_dict() for conn in deployment_config.routing]
            moku.set_connections(connections)
            console.print(f"  ✓ Configured {len(connections)} connection(s)")

            for conn in deployment_config.routing:
                console.print(f"    {conn.source} → {conn.destination}")
        else:
            console.print("  (No routing configured)")

        console.print("\n" + "=" * 80)
        console.print("[green]✓ Deployment successful![/green]")
        console.print("=" * 80)
        console.print(f"\nAccess device at: http://{ip}")

        # Keep connection alive (optional in interactive mode)
        try:
            input("\nPress Enter to disconnect...")
        except (EOFError, KeyboardInterrupt):
            pass

        moku.relinquish_ownership()

    except Exception as e:
        console.print(f"\n[red]✗ Deployment failed: {e}[/red]")
        logger.exception("Deployment error")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
