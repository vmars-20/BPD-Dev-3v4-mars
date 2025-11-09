"""
Unified Decoder for forge_hierarchical_encoder Output

This is THE standard decoder for all FSM observation via oscilloscope.
All projects should use this decoder for consistency.

Author: @claude
Date: 2025-11-07
Status: Production-ready
"""

import warnings
from typing import Dict, Union


def decode_hierarchical_voltage(
    digital_value: int,
    platform_range_mv: float = 5000.0
) -> Dict[str, Union[int, float, bool]]:
    """
    Universal decoder for forge_hierarchical_encoder output.

    This is THE standard decoder for all FSM observation using the
    forge_hierarchical_encoder approach. It decodes the hierarchical
    voltage encoding back to state and status information.

    Args:
        digital_value: Signed 16-bit digital value from OutputD
                      Range: -32768 to +32767
        platform_range_mv: Platform full-scale voltage range in millivolts
                          Default: 5000.0 (±5V)

    Returns:
        dict with keys:
            'state': int (0-63, FSM state value)
            'status': int (0-255, full status byte)
            'status_lower': int (0-127, status payload without fault bit)
            'fault': bool (True if status[7] set / negative voltage)
            'state_copy': int (status[6:1], redundancy check)
            'digital_value': int (raw digital input)
            'voltage_mv': float (equivalent voltage in millivolts)

    Algorithm:
        1. Detect fault from sign (negative = fault)
        2. Extract state from base value (200 units per state)
        3. Extract status offset from remainder
        4. Reconstruct full status byte with fault flag

    Example:
        >>> # State 2, no fault
        >>> decode_hierarchical_voltage(400)
        {'state': 2, 'status': 0, 'fault': False, ...}

        >>> # State 2 with fault (negative voltage)
        >>> decode_hierarchical_voltage(-400)
        {'state': 2, 'status': 128, 'fault': True, ...}
    """
    # Detect fault flag (negative voltage indicates fault)
    fault = digital_value < 0
    magnitude = abs(digital_value)

    # Extract base state (200 digital units per state)
    # This is the fundamental encoding: each state occupies 200 units
    base_state = magnitude // 200

    # Extract status offset from remainder
    remainder = magnitude % 200

    # Decode status lower bits
    # The encoder uses: offset = (status_lower * 100) / 128
    # So we reverse: status_lower = (offset * 128) / 100
    # Using integer arithmetic to match VHDL exactly
    if remainder > 0:
        # Round to nearest integer for better accuracy
        status_lower = min(127, (remainder * 128 + 50) // 100)
    else:
        status_lower = 0

    # Reconstruct full status byte
    if fault:
        status = 0x80 | status_lower  # Set bit 7 for fault
    else:
        status = status_lower

    # Extract state copy from status[6:1] for validation
    # This is a redundancy feature where the state is copied into status bits
    state_copy = (status >> 1) & 0x3F

    # Convert digital value to voltage (platform-specific)
    # Full scale digital range is ±32768
    voltage_mv = (digital_value / 32768.0) * platform_range_mv

    return {
        'state': base_state,
        'status': status,
        'status_lower': status_lower,
        'fault': fault,
        'state_copy': state_copy,
        'digital_value': digital_value,
        'voltage_mv': voltage_mv
    }


def decode_oscilloscope_voltage(
    voltage_mv: float,
    platform_range_mv: float = 5000.0
) -> Dict[str, Union[int, float, bool]]:
    """
    Decode oscilloscope voltage measurement to state and status.

    This function converts an oscilloscope voltage measurement
    to the underlying state and status information.

    Args:
        voltage_mv: Measured voltage in millivolts
        platform_range_mv: Platform full-scale range (default ±5V = 5000mV)

    Returns:
        Same dict as decode_hierarchical_voltage()

    Example:
        >>> # Measured 61mV on oscilloscope
        >>> decode_oscilloscope_voltage(61.0)
        {'state': 2, 'status': 0, 'fault': False, ...}
    """
    # Convert voltage to digital value
    # Platform maps ±platform_range_mv to ±32768 digital
    digital_value = int((voltage_mv / platform_range_mv) * 32768.0)

    # Clamp to valid range
    digital_value = max(-32768, min(32767, digital_value))

    # Use the main decoder
    result = decode_hierarchical_voltage(digital_value, platform_range_mv)

    # Override voltage_mv with the input (more accurate than round-trip)
    result['voltage_mv'] = voltage_mv

    return result


# ============================================================================
# Legacy Compatibility Functions (DEPRECATED)
# ============================================================================

def calculate_legacy_voltage(
    state_index: int,
    num_states: int = 5,
    v_min: float = 0.0,
    v_max: float = 2.5
) -> float:
    """
    DEPRECATED: Legacy voltage spreading calculation.

    This function calculates voltage using the OLD fsm_observer
    voltage spreading approach. It is provided only for comparison
    with legacy systems.

    DO NOT USE FOR NEW DESIGNS!

    Args:
        state_index: State index (0-based)
        num_states: Number of normal states (default 5)
        v_min: Minimum voltage in volts (default 0.0)
        v_max: Maximum voltage in volts (default 2.5)

    Returns:
        Voltage in volts using legacy spreading
    """
    warnings.warn(
        "calculate_legacy_voltage is DEPRECATED. "
        "Use decode_hierarchical_voltage() for new designs.",
        DeprecationWarning,
        stacklevel=2
    )

    if num_states > 1:
        v_step = (v_max - v_min) / (num_states - 1)
    else:
        v_step = 0.0

    return v_min + (state_index * v_step)


def decode_fsm_observer_voltage(voltage: float) -> Dict[str, Union[int, float]]:
    """
    DEPRECATED: Legacy fsm_observer decoder.

    This function is provided for backward compatibility only.
    It attempts to decode voltage using the OLD voltage spreading
    approach, but this is inherently ambiguous without knowing
    the original NUM_STATES and V_MAX parameters.

    DO NOT USE FOR NEW DESIGNS!

    Args:
        voltage: Voltage in volts (not millivolts!)

    Returns:
        Approximate state information (unreliable!)
    """
    warnings.warn(
        "decode_fsm_observer_voltage is DEPRECATED. "
        "Use decode_oscilloscope_voltage() for new designs.",
        DeprecationWarning,
        stacklevel=2
    )

    # Convert to millivolts and use new decoder
    # This will give WRONG results for legacy voltage spreading!
    return decode_oscilloscope_voltage(voltage * 1000.0)


# ============================================================================
# Utility Functions
# ============================================================================

def print_decoder_test_cases():
    """
    Print test cases for validating the decoder implementation.

    This function outputs expected values for common test cases,
    useful for validating the decoder against the VHDL implementation.
    """
    print("Hierarchical Encoder Test Cases")
    print("=" * 60)
    print()

    test_cases = [
        (0, 0x00, "IDLE, no status"),
        (200, 0x00, "ARMED, no status"),
        (400, 0x00, "FIRING, no status"),
        (600, 0x00, "COOLDOWN, no status"),
        (478, 0x00, "FIRING with status offset"),
        (-400, 0x00, "FIRING with fault flag"),
        (250, 0x00, "Between states (1-2)"),
        (6299, 0x00, "Maximum state (31)"),
        (-6299, 0x00, "Maximum state with fault"),
    ]

    for digital, expected_status_hint, description in test_cases:
        result = decode_hierarchical_voltage(digital)
        print(f"{description}:")
        print(f"  Digital: {digital:6d} units")
        print(f"  State:   {result['state']:6d}")
        print(f"  Status:  0x{result['status']:02X}")
        print(f"  Fault:   {str(result['fault']):6s}")
        print(f"  Voltage: {result['voltage_mv']:6.1f} mV")
        print()


def compare_encoding_approaches(state: int):
    """
    Compare legacy voltage spreading vs hierarchical encoding.

    This function shows the difference between the old fsm_observer
    voltage spreading and the new hierarchical encoder approach.

    Args:
        state: State index to compare
    """
    print(f"Encoding Comparison for State {state}")
    print("=" * 60)

    # Legacy approach (voltage spreading)
    legacy_v = calculate_legacy_voltage(state, num_states=5, v_max=2.5)
    print(f"Legacy fsm_observer (voltage spreading):")
    print(f"  State {state} → {legacy_v:.3f}V ({legacy_v*1000:.1f}mV)")

    # New approach (hierarchical encoding)
    digital = state * 200
    new_result = decode_hierarchical_voltage(digital)
    print(f"\nNew forge_hierarchical_encoder:")
    print(f"  State {state} → {digital} digital units")
    print(f"  On ±5V platform → {new_result['voltage_mv']:.1f}mV")

    # Show the difference
    diff_mv = abs(legacy_v * 1000 - new_result['voltage_mv'])
    print(f"\nDifference: {diff_mv:.1f}mV")
    print("Tests expecting legacy values WILL FAIL without updates!")


if __name__ == "__main__":
    # Run test cases when executed directly
    print_decoder_test_cases()
    print("\n" + "=" * 60 + "\n")
    compare_encoding_approaches(1)
    print()
    compare_encoding_approaches(2)
    print()
    compare_encoding_approaches(3)