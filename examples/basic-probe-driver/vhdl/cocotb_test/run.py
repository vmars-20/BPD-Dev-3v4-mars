#!/usr/bin/env python3
"""
CocoTB Test Runner for Basic Probe Driver

Uses shared forge_cocotb infrastructure with BPD-specific MCC utilities.

Usage:
    python run.py fsm_observer              # Run single test (P1 default)
    TEST_LEVEL=P2_INTERMEDIATE python run.py fsm_observer  # Run P2 tests
    python run.py --all                      # Run all tests
    python run.py --list                     # List available tests

Author: Moku Instrument Forge Team
Date: 2025-11-06
"""

import sys
from pathlib import Path

# Add forge_cocotb to path
FORGE_VHDL = Path(__file__).parent.parent.parent.parent / "libs" / "forge-vhdl"
sys.path.insert(0, str(FORGE_VHDL))

# Import shared runner infrastructure
from forge_cocotb.runner import main as runner_main
from forge_cocotb.mcc_utils import copy_sources_for_mcc

# Import local test configs
sys.path.insert(0, str(Path(__file__).parent))
from test_configs import TESTS_CONFIG


def mcc_post_test_hook(config, test_name: str):
    """
    BPD-specific: Copy sources to mcc/in/ directory after successful test.

    This prepares VHDL sources for MCC synthesis upload.
    """
    # Copy sources with BPD-specific exclusions
    mcc_dir = copy_sources_for_mcc(
        config.sources,
        test_name,
        output_dir=Path.cwd() / "mcc" / "in",
        exclude_patterns=[]  # Use defaults (test_stub, tb_wrapper, etc.)
    )

    # Optional: Could add BPD-specific manifest notes here
    # with open(mcc_dir / "BPD_NOTES.txt", 'w') as f:
    #     f.write("BPD-specific deployment notes...\n")


if __name__ == "__main__":
    sys.exit(runner_main(
        tests_config=TESTS_CONFIG,
        post_test_hook=mcc_post_test_hook
    ))
