#!/usr/bin/env python3
"""
Validate MokuConfig YAML files against Pydantic models.

Usage:
    python scripts/validate_moku_config.py path/to/config.yaml
"""

import sys
from pathlib import Path
import yaml
from moku_models import MokuConfig, MOKU_GO_PLATFORM


def validate_config(yaml_path: Path) -> tuple[bool, str]:
    """
    Validate a MokuConfig YAML file.

    Returns:
        (success: bool, message: str)
    """
    try:
        # Load YAML
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Fix platform reference (YAML has string, model expects object)
        if 'platform' in data and isinstance(data['platform'], str):
            platform_name = data['platform']
            if platform_name == 'moku_go':
                data['platform'] = MOKU_GO_PLATFORM
            else:
                return False, f"Unknown platform: {platform_name}"

        # Remove non-Pydantic fields
        non_model_fields = ['description', 'physical_connections']
        for field in non_model_fields:
            if field in data:
                del data[field]

        # Remove description from slots
        if 'slots' in data:
            for slot_config in data['slots'].values():
                if 'description' in slot_config:
                    del slot_config['description']

        # Remove description from routing
        if 'routing' in data:
            for route in data['routing']:
                if 'description' in route:
                    del route['description']

        # Validate with Pydantic
        config = MokuConfig.from_dict(data)

        # Run routing validation
        routing_errors = config.validate_routing()
        if routing_errors:
            return False, f"Routing validation failed:\n" + "\n".join(f"  - {err}" for err in routing_errors)

        return True, f"✓ Valid MokuConfig: {config.platform.name}, {len(config.slots)} slots, {len(config.routing)} routes"

    except Exception as e:
        return False, f"✗ Validation failed: {e}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_moku_config.py path/to/config.yaml")
        sys.exit(1)

    yaml_path = Path(sys.argv[1])
    if not yaml_path.exists():
        print(f"Error: File not found: {yaml_path}")
        sys.exit(1)

    success, message = validate_config(yaml_path)
    print(message)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
