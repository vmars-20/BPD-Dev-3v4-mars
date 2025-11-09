---
created: 2025-11-07
type: network-exploration-task
purpose: explore-tunneling-options
---

# 🌐 WEB UI TASK: Explore Network Tunneling Options for Moku Hardware

## Copy This Entire Message to a NEW Claude Code Web UI Session:

```
I need help exploring network connectivity options for accessing Moku hardware from your container environment.

CONTEXT:
- I have a Moku:Go device on my home network (192.168.73.1)
- I have full administrative control of my network
- I can place the device on a public IP if needed
- The device runs a web interface and accepts Python SDK connections
- We need bidirectional communication for instrument control

TASK: Explore tunneling/connectivity options

Please investigate:

1. **Your Container Environment**
   - Run: uname -a
   - Run: ip addr show
   - Run: cat /etc/os-release
   - Check what tools are available: which ssh, which socat, which ngrok, which cloudflared
   - Check Python packages: pip list | grep -E "(paramiko|fabric|asyncssh)"

2. **Potential Solutions to Research**
   - SSH reverse tunneling (if you have SSH client)
   - ngrok TCP tunnels (if available or installable)
   - Cloudflare Tunnels (cloudflared)
   - WebSocket proxy bridges
   - SOCKS proxy over SSH
   - Tailscale/WireGuard (probably not in container)
   - Direct public IP exposure with port forwarding

3. **Ask Me These Questions**
   Please use the AskUserQuestion tool to ask:
   - What ports does the Moku use? (HTTP, HTTPS, custom SDK ports?)
   - Can I run an SSH server on my network?
   - Do I have a static public IP or dynamic?
   - Am I comfortable exposing ports directly?
   - Do I have a VPS/cloud server I could use as relay?
   - What's my upload/download bandwidth?

4. **Security Considerations**
   Please evaluate:
   - Authentication methods for each approach
   - Encryption requirements
   - Firewall implications
   - Rate limiting needs

5. **Document Findings**
   Create a report at:
   Obsidian/Project/network-tunneling-exploration.md

   Include:
   - Executive summary of options
   - Detailed setup instructions for top 3 approaches
   - Pros/cons matrix
   - Security assessment
   - Recommended approach with rationale
   - Test commands to verify connectivity

CONSTRAINTS:
- You're in a container with limited tools
- We need reliable bidirectional communication
- Latency should be <100ms for instrument control
- Solution should be reproducible (not one-off hacks)

TIME BUDGET: 45-60 minutes

OUTPUT: Create comprehensive report in Obsidian/Project/network-tunneling-exploration.md

Note: This is an exploration task - no actual tunnels need to be established, just research and documentation.
```

## Expected Activities

The Web UI will:
1. ✅ Examine its container environment
2. ✅ Check available tools and packages
3. ✅ Ask clarifying questions about your network
4. ✅ Research tunneling approaches
5. ✅ Write comprehensive report

## Key Information to Provide

When asked, you can share:
- Moku uses ports 80 (HTTP) and possibly 443 (HTTPS)
- Python SDK likely uses HTTP/HTTPS REST API
- You can run SSH server
- You can get public IP if needed
- Typical home broadband speeds

## Success Criteria

Good exploration includes:
- Multiple viable options presented
- Clear setup instructions
- Security properly considered
- Practical recommendations
- Test/verification steps

## After Exploration Completes

The Web UI will create:
```
Obsidian/Project/network-tunneling-exploration.md
```

Review this locally and choose best approach for Phase 2/3 testing.

---

## Why This Works

- Each Web UI session gets its own branch
- They don't interfere with each other
- Main branch is just a starting point
- You can run multiple explorations in parallel

## Container Hints for Web UI

The Web UI is likely running in:
- Ubuntu/Debian container
- Limited networking tools
- Can install Python packages with pip
- Might have apt-get access (worth trying)
- Probably no systemd/services