
# Review
This directory is where humans and/or agents write out documents significant enough to stand on their own but not worth cluttering up a session handoff prompt.

So far these include:
- [[HVS_ENCODING_SCHEME]] - Quick visual reference
- [[HIERARCHICAL_VOLTAGE_ENCODING_ALTERNATIVES]] - Comprehensive analysis of encoding scheme alternatives

``` python
The Hierarchical Voltage Encoding Scheme

  Visual on Oscilloscope

  +2.5V ┤                                    ← STATE=5 (max normal state)
        │
  +2.0V ┤         ╔═══╗                     ← STATE=4 + status noise
        │         ║   ║
  +1.5V ┤    ╔════╝   ╚════╗                ← STATE=3 + status noise
        │    ║              ║
  +1.0V ┤  ══╝              ╚══              ← STATE=2 + status noise
        │  ░░░░░░░░░░░░░░░░░░░              (░ = 8-bit status "noise" ±50mV around base)
  +0.5V ┤══                                  ← STATE=1 + status noise
        │
   0.0V ┼══════════════════════════════════ ← STATE=0 (IDLE) + status noise
  ─────────────────────────────────────────
  -0.5V ┤         ═══                       ← FAULT! (negative voltage, magnitude shows last state)
        │
  -2.0V ┤═══                                ← FAULT from STATE=4

  Key Properties:
  - 200mV steps = Major state transitions (human-readable)
  - ±50mV "noise" = 8-bit status encoded as fine-grained voltage variation
  - Negative voltage = Fault condition (APP:STATUS[7] = 1)
  - Magnitude preserved = Last normal state visible even in fault
```