# Moku:Go Network Tunneling Exploration

**Date:** 2025-11-07
**Purpose:** Explore network connectivity options for accessing Moku:Go (192.168.73.1) from Claude Code container environment
**Status:** Research Complete - Awaiting User Input for Final Recommendation

---

## Executive Summary

This document explores various tunneling and connectivity solutions to enable bidirectional communication between a containerized environment (Claude Code) and a Moku:Go device on a home network. The goal is to establish reliable, low-latency (<100ms) communication for instrument control via the Moku Python API.

**Key Findings:**
- Container has limited tools (no SSH, socat, ngrok, cloudflared) but **Python 3.11** with networking libraries available
- Moku:Go uses standard **HTTP on port 80** for API communication
- Multiple viable solutions exist, ranging from simple (direct port forwarding) to complex (cloud relay services)
- **Recommended approach depends on user's network infrastructure** (see clarifying questions below)

---

## Container Environment Assessment

### System Information
```
OS: Ubuntu 24.04.3 LTS (Noble Numbat)
Kernel: Linux 4.4.0 (runsc - gVisor sandbox)
Python: 3.11.14
Hostname: runsc
```

### Available Tools
✅ **Available:**
- `netcat` / `nc` (OpenBSD netcat)
- `curl` 8.5.0 (with OpenSSL, HTTP/2 support)
- `wget`
- Python 3.11.14 with standard library (socket, asyncio, http.server, json)
- TUN/TAP device (`/dev/net/tun`) - VPN capable

❌ **NOT Available:**
- SSH client
- socat
- ngrok
- cloudflared
- ip / ifconfig commands
- Specialized Python packages (paramiko, fabric, asyncssh, pyngrok, sshtunnel)

### Network Capabilities
- ✅ Can create Python sockets
- ✅ TUN/TAP device available (good for VPN solutions)
- ✅ HTTP/HTTPS client support (curl/wget)
- ❌ No native SSH tunneling
- ❌ Limited network diagnostic tools

**Assessment:** Container is network-capable but tool-limited. Solutions must rely on Python, netcat, or HTTP-based tools.

---

## Moku:Go Network Requirements

### Port Specifications
Based on official Liquid Instruments documentation:

| Port | Protocol | Purpose |
|------|----------|---------|
| **80** | TCP/HTTP | **Primary API communication** (critical) |
| 27181-27186 | TCP | iPad/Desktop app clients (optional) |
| 5353 | UDP | mDNS device discovery (optional) |
| 8090 | TCP | Local IPv6 proxy (USB connections only) |

**For API-only access:** Only **port 80 (HTTP)** is required.

### Protocol Details
- **API:** RESTful HTTP interface
- **SDK:** Python package `moku` (installable via pip)
- **Authentication:** Device IP address (192.168.73.1)
- **Bandwidth:** Low bandwidth (REST API)
- **Latency Requirement:** <100ms for instrument control

### Connectivity Options
1. **Network (WiFi/Ethernet):** IP address connection (192.168.73.1)
2. **USB:** IPv6 link-local address (requires port 8090 proxy)
3. **VPN:** Supported via manual IP connection

---

## Solution Options (Detailed)

### Option 1: Direct Public IP + Port Forwarding

**Setup Complexity:** ⭐⭐ (Low)
**Security:** ⚠️ (Requires careful configuration)
**Latency:** ⭐⭐⭐⭐⭐ (Best - direct connection)
**Cost:** Free

#### How It Works
1. Configure home router to forward public IP port → Moku (192.168.73.1:80)
2. Container connects directly to `http://<public-ip>:<port>`

#### Setup Instructions
```bash
# On home router (web interface):
# 1. Set static IP for Moku: 192.168.73.1
# 2. Add port forwarding rule:
#    External Port: 8080 (or your choice)
#    Internal IP: 192.168.73.1
#    Internal Port: 80
#    Protocol: TCP

# From container - test connection:
curl http://<your-public-ip>:8080

# Python API usage:
pip install moku
python3 << 'EOF'
from moku.instruments import Oscilloscope
osc = Oscilloscope('<your-public-ip>:8080')
print("Connected!")
EOF
```

#### Pros
- ✅ Lowest latency (direct connection)
- ✅ Simple setup
- ✅ No third-party services
- ✅ No bandwidth/time limits
- ✅ Works with existing container tools

#### Cons
- ❌ Exposes device to public internet
- ❌ Requires static IP or dynamic DNS
- ❌ No authentication on Moku HTTP API
- ❌ Firewall rules required
- ❌ Security risk if misconfigured

#### Security Hardening
1. **Change default port** (use non-standard high port)
2. **IP whitelist** (if router supports it) - only allow container's IP
3. **Fail2ban** or rate limiting (if available)
4. **VPN wrapper** (see Option 5)
5. **Network monitoring** for unauthorized access

---

### Option 2: Python Reverse TCP Tunnel

**Setup Complexity:** ⭐⭐⭐ (Medium)
**Security:** ⭐⭐⭐ (Good - encrypted options available)
**Latency:** ⭐⭐⭐⭐ (Low overhead)
**Cost:** Free

#### How It Works
1. Install Python tunnel package in container
2. Run client on home network (connects outbound to container)
3. Container receives incoming tunneled connections

#### Recommended Packages (2024-2025)

**Option A: turbo-tunnel** (Most Recent - Jan 2025)
```bash
# In container:
pip install turbo-tunnel

# Run tunnel server (listens on port 8080):
python3 -m turbo_tunnel server --port 8080

# On home network (near Moku):
pip install turbo-tunnel
python3 -m turbo_tunnel client --remote <container-ip>:8080 \
  --local 192.168.73.1:80 --forward-port 80
```

**Option B: pinggy** (Full-featured)
```bash
# In container:
pip install pinggy

# Python script for tunnel server:
cat > tunnel_server.py << 'EOF'
from pinggy import Pinggy
tunnel = Pinggy.create_tunnel(
    local_port=80,
    tunnel_type='tcp',
    auth_token='<your-token>'  # Optional
)
print(f"Tunnel URL: {tunnel.url}")
tunnel.start()
EOF
```

**Option C: pproxy** (Async, Multi-protocol)
```bash
pip install pproxy

# Start proxy server:
pproxy -l http://:8080 -r tunnel+http://192.168.73.1:80
```

#### Pros
- ✅ Pure Python (works in container)
- ✅ NAT traversal (no router config)
- ✅ Encryption available (SSL/TLS)
- ✅ Bidirectional communication
- ✅ Can be automated/scripted

#### Cons
- ❌ Requires Python installation on home network side
- ❌ More complex than direct port forward
- ❌ Two-machine setup (container + home relay)
- ❌ Additional dependencies

---

### Option 3: Cloudflare Tunnel (cloudflared)

**Setup Complexity:** ⭐⭐⭐ (Medium)
**Security:** ⭐⭐⭐⭐⭐ (Excellent - zero trust)
**Latency:** ⭐⭐⭐ (Cloudflare routing overhead)
**Cost:** Free (Cloudflare Free tier)

#### How It Works
1. Install `cloudflared` on home network (near Moku)
2. Configure tunnel to expose Moku:Go port 80
3. Container connects via Cloudflare subdomain

#### Setup Instructions

**On Home Network (one-time setup):**
```bash
# Install cloudflared (Linux):
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# Authenticate:
cloudflared tunnel login

# Create tunnel:
cloudflared tunnel create moku-tunnel

# Configure tunnel (config.yml):
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: <TUNNEL-ID>
credentials-file: /home/<user>/.cloudflared/<TUNNEL-ID>.json

ingress:
  - hostname: moku.yourdomain.com
    service: http://192.168.73.1:80
  - service: http_status:404
EOF

# Route DNS:
cloudflared tunnel route dns moku-tunnel moku.yourdomain.com

# Run tunnel (or install as service):
cloudflared tunnel run moku-tunnel
```

**From Container:**
```bash
# Test connection:
curl http://moku.yourdomain.com

# Python API:
pip install moku
python3 -c "from moku.instruments import Oscilloscope; osc = Oscilloscope('moku.yourdomain.com')"
```

#### Pros
- ✅ Excellent security (zero trust, encrypted)
- ✅ No port forwarding required
- ✅ Free custom domain
- ✅ DDoS protection
- ✅ Cloudflare CDN benefits
- ✅ Automatic HTTPS

#### Cons
- ❌ Requires `cloudflared` on home network (not in container)
- ❌ Cloudflare account required
- ❌ Custom domain needed (can use Cloudflare-provided)
- ❌ Latency overhead (Cloudflare routing)
- ❌ Subject to Cloudflare terms of service

---

### Option 4: Netcat Bidirectional Relay

**Setup Complexity:** ⭐⭐ (Low-Medium)
**Security:** ⚠️ (No encryption)
**Latency:** ⭐⭐⭐⭐ (Very low overhead)
**Cost:** Free

#### How It Works
Uses named pipes (mkfifo) to create bidirectional netcat relay between container and home network.

#### Setup Instructions

**On Home Network (relay machine):**
```bash
# Create named pipe:
mkfifo /tmp/moku_pipe

# Start bidirectional relay:
# Listen on port 8080, forward to Moku (192.168.73.1:80)
nc -l -p 8080 0</tmp/moku_pipe | nc 192.168.73.1 80 1>/tmp/moku_pipe

# Or with ncat (keep-alive for multiple connections):
mkfifo /tmp/moku_pipe
ncat -k -l 8080 < /tmp/moku_pipe | ncat 192.168.73.1 80 > /tmp/moku_pipe &
```

**From Container:**
```bash
# Test connection:
echo -e "GET / HTTP/1.1\r\nHost: moku\r\n\r\n" | nc <home-ip> 8080

# Python usage (HTTP library):
python3 << 'EOF'
import http.client
conn = http.client.HTTPConnection('<home-ip>:8080')
conn.request("GET", "/")
response = conn.getresponse()
print(response.status, response.reason)
EOF
```

#### Pros
- ✅ Minimal dependencies (netcat available in container)
- ✅ Very low overhead
- ✅ Simple concept
- ✅ No additional software needed

#### Cons
- ❌ No encryption (plaintext)
- ❌ No authentication
- ❌ Requires public IP or VPN
- ❌ Named pipes fragile (connection drops)
- ❌ Not suitable for production

---

### Option 5: VPN + Direct Connection

**Setup Complexity:** ⭐⭐⭐⭐ (High)
**Security:** ⭐⭐⭐⭐⭐ (Excellent)
**Latency:** ⭐⭐⭐⭐ (Low with good VPN)
**Cost:** Varies (free to $5-10/month)

#### How It Works
1. Set up VPN server on home network
2. Container connects to VPN
3. Access Moku directly via internal IP (192.168.73.1)

#### VPN Options

**Option A: WireGuard** (Recommended)
```bash
# Home network setup (requires root/admin access):
# Install WireGuard, generate keys, configure
# See: https://www.wireguard.com/quickstart/

# Container setup (TUN/TAP available!):
# 1. Install WireGuard (if possible in container)
# 2. Copy config file
# 3. Connect: wg-quick up wg0

# Or use Python WireGuard bindings:
pip install pywg
```

**Option B: OpenVPN**
```bash
# Home network: Install OpenVPN server
# Container: Use openvpn client (if installable)

# Moku officially supports VPN connections:
# https://liquidinstruments.helpjuice.com/can-i-use-mokulab-via-vpn
```

**Option C: Tailscale** (Easiest)
```bash
# Install Tailscale on home network machine
# Install Tailscale in container (if permitted)
# Both join same Tailscale network
# Access Moku via Tailscale IPs
```

#### Pros
- ✅ Best security (encrypted tunnel)
- ✅ Full network access (not just one port)
- ✅ Moku officially supports VPN
- ✅ No port forwarding needed
- ✅ Multiple devices can connect

#### Cons
- ❌ Most complex setup
- ❌ May require container privileges (TUN/TAP)
- ❌ VPN server setup required
- ❌ Ongoing maintenance
- ❌ May have cost (commercial VPN services)

---

### Option 6: Cloud Relay (VPS Middleman)

**Setup Complexity:** ⭐⭐⭐⭐ (High)
**Security:** ⭐⭐⭐ (Good with proper config)
**Latency:** ⭐⭐⭐ (Depends on VPS location)
**Cost:** $5-20/month (VPS hosting)

#### How It Works
1. Rent cloud VPS (AWS, DigitalOcean, Linode, etc.)
2. Home network establishes tunnel to VPS
3. Container connects to VPS public IP
4. VPS relays traffic to home network

#### Setup Instructions

**On VPS:**
```bash
# Install socat or nginx as reverse proxy
sudo apt install socat

# Forward VPS:80 to home network tunnel:
socat TCP-LISTEN:80,fork TCP:localhost:8080
```

**On Home Network:**
```bash
# Establish SSH reverse tunnel to VPS:
ssh -R 8080:192.168.73.1:80 user@vps-ip -N -f

# Or use autossh for reliability:
autossh -M 0 -R 8080:192.168.73.1:80 user@vps-ip -N
```

**From Container:**
```bash
curl http://<vps-ip>/
pip install moku
# Connect using VPS IP
```

#### Pros
- ✅ Full control over relay
- ✅ Can add authentication/encryption
- ✅ Multiple services can use same VPS
- ✅ Reliable (commercial hosting)
- ✅ Static IP included

#### Cons
- ❌ Monthly cost ($5-20)
- ❌ Requires VPS management
- ❌ Additional infrastructure
- ❌ Two tunnels (home→VPS, container→VPS)
- ❌ VPS becomes single point of failure

---

## Comparison Matrix

| Solution | Complexity | Security | Latency | Cost | NAT Bypass | Container-Friendly |
|----------|-----------|----------|---------|------|------------|-------------------|
| **Direct Port Forward** | ⭐⭐ | ⚠️ | ⭐⭐⭐⭐⭐ | Free | ❌ | ✅ |
| **Python Tunnel** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Free | ✅ | ✅ |
| **Cloudflare Tunnel** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Free | ✅ | ⚠️* |
| **Netcat Relay** | ⭐⭐ | ⚠️ | ⭐⭐⭐⭐ | Free | ❌ | ✅ |
| **VPN** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Varies | ✅ | ⚠️* |
| **Cloud VPS Relay** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | $5-20/mo | ✅ | ✅ |

\* Requires software installation on home network side, not in container itself

---

## Security Considerations

### Authentication
**Problem:** Moku HTTP API has no built-in authentication.

**Mitigations:**
1. **Network-level:** Use VPN or Cloudflare Access (identity verification)
2. **IP whitelist:** Restrict access to known IPs (router or VPS)
3. **Reverse proxy:** Add HTTP Basic Auth via nginx/Apache
4. **Firewall rules:** Only allow container IP to access

### Encryption
**Problem:** Moku API uses HTTP (not HTTPS) by default.

**Mitigations:**
1. **VPN tunnel:** All traffic encrypted at network layer
2. **Cloudflare Tunnel:** Provides HTTPS automatically
3. **Reverse proxy:** Terminate TLS at proxy, forward HTTP to Moku
4. **SSH tunnel:** Wrap HTTP in encrypted SSH tunnel

### Rate Limiting
**Problem:** Public exposure could allow abuse/DoS.

**Mitigations:**
1. **Router-level:** Connection rate limits (if available)
2. **Reverse proxy:** nginx rate limiting modules
3. **Cloudflare:** Built-in DDoS protection
4. **Monitoring:** Alert on unusual traffic patterns

### Defense in Depth
**Recommended Layers:**
1. **Firewall:** Only necessary ports open
2. **VPN:** Network-level encryption
3. **Reverse proxy:** Authentication + HTTPS
4. **Monitoring:** Log all connections
5. **Updates:** Keep all software patched

---

## Recommended Approach

**The best solution depends on your answers to the clarifying questions below.**

### Scenario-Based Recommendations

#### Scenario A: Static IP + Tech-Savvy User
**Recommendation:** Direct Port Forwarding + HTTP Basic Auth Proxy

**Why:** Lowest latency, full control, no ongoing costs.

**Stack:**
1. Port forward 8080 → nginx reverse proxy
2. nginx adds Basic Auth + forwards to Moku (192.168.73.1:80)
3. Container connects with credentials

#### Scenario B: Dynamic IP + Security-Conscious
**Recommendation:** Cloudflare Tunnel

**Why:** Free, excellent security, no port forwarding, works with dynamic IP.

**Setup Time:** 30-45 minutes

#### Scenario C: Multiple Services + Budget Available
**Recommendation:** Cloud VPS Relay + VPN

**Why:** Scalable, can host multiple services, professional setup.

**Monthly Cost:** $5-10 (DigitalOcean/Linode droplet)

#### Scenario D: Quick Testing / Temporary Solution
**Recommendation:** Python Tunnel (turbo-tunnel)

**Why:** Fast setup, pure Python, no infrastructure changes.

**Setup Time:** 15-20 minutes

---

## Clarifying Questions

**Please answer these questions for a specific recommendation:**

### 1. Network Infrastructure
- Do you have a **static public IP** address, or is it **dynamic**?
- Can you run an **SSH server** on your home network?
- Do you have any **cloud servers** (VPS, AWS, Azure, etc.) available?

### 2. Firewall & Port Forwarding
- How comfortable are you **exposing ports directly** to the internet? (1-5 scale)
- Can you **configure port forwarding** on your home router?
- Do you have concerns about **security/authentication** for exposed services?

### 3. Network Performance
- What's your typical **upload/download bandwidth**?
- Are you on a **residential or business** internet connection?

### 4. Existing Infrastructure
- Do you already use any **tunneling services** (ngrok, Cloudflare Tunnel, Tailscale, etc.)?
- Do you have any **existing VPN** infrastructure?

### 5. Use Case
- How **frequently** will you access the Moku from this container? (daily, weekly, rarely)
- Is this for **development/testing** or **production** use?
- How **latency-sensitive** is your application? (you mentioned <100ms - why?)

---

## Test Commands

### Connection Verification

**Test 1: HTTP GET Request**
```bash
# From container:
curl -v http://<target-ip>:80/
# Expected: HTTP 200 response or Moku API response
```

**Test 2: Python Socket Connection**
```python
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
result = sock.connect_ex(('<target-ip>', 80))
print("Connected!" if result == 0 else f"Failed: {result}")
sock.close()
```

**Test 3: Moku Python API**
```bash
pip install moku
python3 << 'EOF'
from moku.instruments import Oscilloscope
try:
    osc = Oscilloscope('<target-ip>')
    print(f"Connected to Moku! Device ID: {osc.get_serial()}")
    osc.relinquish_ownership()
except Exception as e:
    print(f"Connection failed: {e}")
EOF
```

**Test 4: Latency Measurement**
```bash
# From container (if ping available):
ping -c 10 <target-ip>

# Or using curl timing:
for i in {1..10}; do
  curl -w "Time: %{time_total}s\n" -o /dev/null -s http://<target-ip>/
done
```

---

## Next Steps

1. **Answer clarifying questions** above
2. **Choose solution** based on your infrastructure and requirements
3. **Test connection** using verification commands
4. **Implement monitoring** (log connections, alert on issues)
5. **Document your setup** for future reference
6. **Consider backup solution** (if primary tunnel fails)

---

## References

### Official Documentation
- [Moku Python API Documentation](https://apis.liquidinstruments.com/)
- [Moku VPN Support](https://liquidinstruments.helpjuice.com/can-i-use-mokulab-via-vpn)
- [Moku System Administrator's Guide](https://download.liquidinstruments.com/documentation/guide/hardware/moku/Guide-MokuSystemAdministrators.pdf)

### Tunneling Resources
- [Awesome Tunneling (GitHub)](https://github.com/anderspitman/awesome-tunneling) - Comprehensive list of ngrok alternatives
- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [WireGuard Quick Start](https://www.wireguard.com/quickstart/)

### Python Tunnel Packages
- [turbo-tunnel (PyPI)](https://pypi.org/project/turbo-tunnel/) - Latest, actively maintained
- [pinggy (PyPI)](https://pypi.org/project/pinggy/) - Feature-rich tunneling
- [pproxy (PyPI)](https://pypi.org/project/pproxy/) - Multi-protocol async proxy

---

**Document Version:** 1.0
**Last Updated:** 2025-11-07
**Author:** Claude Code (Anthropic)
**Status:** Awaiting user input for final recommendation
