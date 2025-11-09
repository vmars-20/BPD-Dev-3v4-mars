#!/usr/bin/env python3
"""
moku_read: Read device state as MokuConfig (validated Pydantic model)

Usage:
    python scripts/moku_read.py <device-ip>
    python scripts/moku_read.py <device-ip> > output.json
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

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
    from moku.instruments import MultiInstrument
except ImportError:
    print("Error: moku library not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/moku_read.py <device-ip>", file=sys.stderr)
        sys.exit(1)
    
    device_ip = sys.argv[1]
    
    # Try to connect and detect platform
    platform_id_map = {
        1: "Moku:Lab",
        2: "Moku:Go",
        3: "Moku:Pro",
        4: "Moku:Delta",
    }
    
    platform_map = {
        1: MOKU_LAB_PLATFORM,
        2: MOKU_GO_PLATFORM,
        3: MOKU_PRO_PLATFORM,
        4: MOKU_DELTA_PLATFORM,
    }
    
    moku = None
    platform_id = None
    
    # Try each platform
    for pid in [2, 1, 3, 4]:  # Go, Lab, Pro, Delta
        try:
            moku = MultiInstrument(
                device_ip,
                platform_id=pid,
                force_connect=False,
                persist_state=True
            )
            platform_id = pid
            break
        except Exception:
            continue
    
    if moku is None:
        print(f"Error: Could not connect to {device_ip}", file=sys.stderr)
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
        platform = platform_map[platform_id].model_copy()
        platform.ip_address = device_ip
        
        # Create MokuConfig
        if not slots:
            # Empty device - use model_construct to bypass validation
            config = MokuConfig.model_construct(
                platform=platform,
                slots={},
                routing=routing,
                metadata={
                    'exported_at': datetime.now(timezone.utc).isoformat(),
                    'source': 'moku_read',
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
                    'source': 'moku_read'
                }
            )
        
        # Output as JSON (validated Pydantic model)
        print(json.dumps(config.model_dump(), indent=2))
    
    finally:
        # Disconnect
        try:
            moku.relinquish_ownership()
        except Exception:
            pass


if __name__ == "__main__":
    main()
