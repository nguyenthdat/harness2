# Network Traffic Interception & Proxy Workflows

## Title & Overview
- **Domain**: Application network communication, HTTP/HTTPS APIs, WebSockets, and custom TCP/UDP network streams.
- **Scope**: SSL/TLS decryption via proxy interception, Certificate Authority (CA) installation, traffic recording (.har, .mitm, .pcap), and passive network packet analysis.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Target application interacts with remote web services, REST APIs, or telemetry endpoints.
- Static analysis reveals network indicators (IP addresses, domain names, HTTP request paths).
- Need to inspect transmitted payloads, headers, auth tokens, or protocol negotiations in real time.

---

## Tooling & CLI/MCP Actions
- **Primary Proxy & Interception Tools**:
  - `mitmproxy` / `mitmdump`: Headless and interactive HTTP/HTTPS/WebSocket proxy.
  - REA Tool: `inspect_web_network_capture` (parses .har and network traces).
  - Packet Analysis: `tshark` (Wireshark CLI), `tcpdump`.
- **System Setup & Automation**:
  - Script: `profiles/re/agent/skills/tool-setup/scripts/setup_proxy_ca.py` (installs mitmproxy CA cert into system/user trust stores).

---

## Key Methodologies & Workflow (Placeholder)

### 1. Proxy Setup & Network Routing
- [ ] Launch `mitmdump` on listening interface:
  ```bash
  mitmdump -p 8080 -w /tmp/traffic_capture.mitm
  ```
- [ ] Configure guest VM / mobile device HTTP proxy settings pointing to proxy IP and port.
- [ ] For non-proxy-aware thick clients: Configure transparent proxying using `iptables` / packet filter redirection.

### 2. TLS Interception & Trust Configuration
- [ ] Provision mitmproxy CA certificate into guest operating system trust store using `setup_proxy_ca.py`.
- [ ] For Android: Push CA cert into system cert store (`/system/etc/security/cacerts/`) via Magisk/KernelSU module to bypass Android 7+ user-cert restrictions.
- [ ] For Certificate Pinning: Hook SSL validation libraries (OpenSSL, OkHttp, TrustManager) using Frida or dynamic scripts.

### 3. Traffic Recording & Format Export
- [ ] Capture live traffic during application operation.
- [ ] Export session captures as `.har`, `.mitm`, or `.pcap` files.
- [ ] Parse offline captures using `tshark`:
  ```bash
  tshark -r capture.pcap -Y "http.request" -T fields -e http.host -e http.request.uri
  ```

### 4. API & Payload Re-Examination
- [ ] Correlate intercepted HTTP requests with binary functions: Map request endpoints to corresponding client logic in disassembler.
- [ ] Decode compressed or serialized request bodies (JSON, Protobuf, MessagePack, gzip).
- [ ] Audit transmitted authentication tokens, API keys, and private data fields.

---

## Boundaries & Anti-Patterns
- **Do not intercept production infrastructure or third-party networks without authorization**: Limit interception strictly to target lab instances.
- **Do not tamper with live financial or operational transactions**: Maintain passive observation of data exchanges.
- **Do not execute live network requests against unknown C2 endpoints discovered in malware**: Capture traffic only within simulated sinkhole or isolated networks.
