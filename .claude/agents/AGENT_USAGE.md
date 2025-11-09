# Using Agents in Cursor

**Purpose:** Guide for invoking and using the specialized agents defined in `.claude/agents/`

---

## Available Agents

| Agent | Purpose | Key Commands |
|-------|---------|--------------|
| **cocotb-integration-test** | Create progressive CocoTB test suites (P1/P2/P3) | Restructure tests, create test infrastructure |
| **deployment-orchestrator** | Deploy packages to Moku hardware | `/deploy`, `/discover` |
| **hardware-debug** | Debug FSMs and monitor hardware state | `/debug-fsm`, `/monitor-state`, `/trace-signals` |

---

## How Cursor Uses Agents

**Important:** Cursor doesn't automatically invoke agents. Instead, agents are **documentation/instructions** that guide AI assistants (like me) to act in specific roles.

### Method 1: Direct Reference (Recommended)

Simply reference the agent by name in your request:

```
"Act as the cocotb-integration-test agent and restructure my tests..."
```

```
"Using the deployment-orchestrator agent, deploy my package..."
```

```
"As the hardware-debug agent, debug the FSM state..."
```

### Method 2: Load Agent File

I can read the agent definition file directly:

```
"Read .claude/agents/cocotb-integration-test/agent.md and follow its instructions..."
```

### Method 3: Explicit Role Assignment

Tell me to adopt a specific agent's role:

```
"You are now the hardware-debug agent. Monitor the FSM state on device 192.168.1.100"
```

---

## Agent Details

### 1. cocotb-integration-test

**Location:** `.claude/agents/cocotb-integration-test/agent.md`

**When to use:**
- Creating new CocoTB test suites
- Restructuring existing tests to follow forge-vhdl standards
- Setting up progressive testing (P1/P2/P3)

**Example usage:**
```
I have CocoTB tests in examples/basic-probe-driver/vhdl/tests/ that need to follow forge-vhdl standards.

Please read:
- libs/forge-vhdl/CLAUDE.md (testing standards)
- examples/basic-probe-driver/vhdl/tests/test_bpd_fsm_observer.py (existing tests)

Then restructure to forge-vhdl progressive pattern.
```

**What it does:**
- Analyzes existing tests
- Creates constants file with all configuration
- Splits tests into P1/P2/P3 levels
- Creates progressive orchestrator
- Updates test_configs.py
- Ensures <20 line output for P1 tests

---

### 2. deployment-orchestrator

**Location:** `.claude/agents/deployment-orchestrator/agent.md`

**When to use:**
- Deploying packages to Moku hardware
- Discovering devices on network
- Configuring routing and control registers

**Example usage:**
```
Act as the deployment-orchestrator agent.

Deploy the DS1140_PD package to device 192.168.1.100:
- Package location: forge/apps/DS1140_PD/
- Use Slot 2 for custom instrument
- Deploy oscilloscope to Slot 1 for monitoring
- Configure default routing pattern
```

**What it does:**
- Reads manifest.json and control_registers.json
- Discovers Moku devices on network
- Connects to device
- Deploys CloudCompile + Oscilloscope
- Sets control registers
- Configures routing
- Verifies deployment

**Commands (conceptual):**
- `/deploy <app_name> --device <ip>` - Deploy package
- `/discover` - Find Moku devices

---

### 3. hardware-debug

**Location:** `.claude/agents/hardware-debug/agent.md`

**When to use:**
- Debugging FSM state machines
- Monitoring hardware state via oscilloscope
- Analyzing timing characteristics
- Diagnosing faults

**Example usage:**
```
As the hardware-debug agent, debug the FSM state for DS1140_PD:
- Device: 192.168.1.100
- Check current state
- Monitor transitions for 30 seconds
- Analyze timing characteristics
```

**What it does:**
- Connects to oscilloscope on deployed device
- Reads FSM state voltage (OutC → Osc Ch1)
- Decodes voltage to state name
- Monitors state transitions
- Analyzes timing (cycle counts, durations)
- Detects faults (negative voltages, stuck states)

**Commands (conceptual):**
- `/debug-fsm <app_name> --device <ip>` - Debug FSM state
- `/monitor-state <app_name> --device <ip> --duration <seconds>` - Continuous monitoring
- `/trace-signals <app_name> --device <ip> --channels <ch1,ch2>` - Multi-channel capture
- `/analyze-timing <app_name> --device <ip>` - Timing analysis

---

## Agent Workflow Examples

### Example 1: Full Test Restructuring

```
User: "I need to restructure my CocoTB tests to follow forge-vhdl standards"

Assistant: [Reads cocotb-integration-test agent.md]
           [Analyzes existing tests]
           [Creates P1/P2/P3 structure]
           [Updates test_configs.py]
```

### Example 2: Deploy and Debug

```
User: "Deploy DS1140_PD and then debug its FSM"

Assistant: [As deployment-orchestrator]
           [Deploys package to hardware]
           
           [As hardware-debug]
           [Monitors FSM state]
           [Reports current state and transitions]
```

### Example 3: Iterative Development

```
User: "I modified my YAML spec, regenerate tests and redeploy"

Assistant: [As cocotb-integration-test]
           [Regenerates test structure]
           
           [As deployment-orchestrator]
           [Redeploys to hardware]
           
           [As hardware-debug]
           [Validates FSM behavior]
```

---

## Agent Registration

All agents are registered in `.claude/manifest.json`:

```json
"agents": [
  {
    "name": "cocotb-integration-test",
    "path": ".claude/agents/cocotb-integration-test",
    "description": "CocoTB progressive testing following forge-vhdl standards",
    "scope": "monorepo-level"
  },
  {
    "name": "deployment-orchestrator",
    "path": ".claude/agents/deployment-orchestrator",
    "description": "Hardware deployment workflows",
    "scope": "monorepo-level"
  },
  {
    "name": "hardware-debug",
    "path": ".claude/agents/hardware-debug",
    "description": "FSM debugging and monitoring",
    "scope": "monorepo-level"
  }
]
```

---

## Best Practices

1. **Be explicit:** Always mention which agent you want to use
2. **Provide context:** Give the agent all necessary information (file paths, device IPs, etc.)
3. **Chain agents:** You can use multiple agents in sequence for complex workflows
4. **Read agent docs:** Each agent.md file contains detailed instructions and examples

---

## Troubleshooting

**Q: How do I know which agent to use?**
A: Check the agent descriptions above or read the agent.md files directly.

**Q: Can I use multiple agents at once?**
A: Yes, but typically you'll use them sequentially (e.g., deploy → debug).

**Q: Do agents execute commands automatically?**
A: No, agents are instructions for AI assistants. I'll follow the agent's instructions to help you accomplish tasks.

**Q: Can I create new agents?**
A: Yes! Create a new directory in `.claude/agents/` with an `agent.md` file, then add it to `.claude/manifest.json`.

---

**Last Updated:** 2025-11-06
**Maintained By:** BPD-Dev team

