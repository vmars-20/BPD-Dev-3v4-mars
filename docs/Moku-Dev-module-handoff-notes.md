## @CLAUDE Annotations in Source Files
### @CLAUDE Annotations in Source Files

Key source files now contain inline comments guiding LLMs to important APIs:

**`moku/instruments/_mim.py`** (Session Introspection):
```python
# @CLAUDE: This is the KEY FILE for Moku session introspection!
#
# IMPORTANT APIS:
# - get_instruments() → Query instruments in each slot
# - get_connections() → Query MCC routing
# - get_frontend() → Query input settings (impedance, coupling, attenuation)
# - get_output() → Query output settings (gain)
# - get_dio() → Query DIO configuration (Go/Delta only)
```

**`moku/__init__.py`** (Session Management):
```python
# @CLAUDE: KEY APIS FOR SESSION HANDOFFS:
# - claim_ownership(persist_state=True) → Server-side state retention
# - relinquish_ownership() → Clean session termination
# - Context manager support → Automatic cleanup
```

**`moku/session.py`** (HTTP Session Keys):

**`moku/session.py`** (HTTP Session Keys):
```python
# @CLAUDE: This file handles HTTP API communication and session key management
# - session_key: Exclusive access token from claim_ownership()
# - sk_name = "Moku-Client-Key": HTTP header for session key
```

**`moku/instruments/_cloudcompile.py`** (Control Registers):
```python
# @CLAUDE: CloudCompile instrument - Custom FPGA bitstreams
# - set_control(idx, value) → Set single CR0-CR31 register
# - get_control(idx) → Read single register value
# - set_controls({...}) → Bulk set multiple registers
```

### 3-Tier AI Documentation

**Tier 1: `llms.txt`** (~800-1000 tokens)
- Quick orientation for AI assistants
- Key classes, basic usage, common tasks
- Pointers to Tier 2 for deeper context