# UTM Hypervisor & QCOW2 Snapshot Management

This reference documents UTM.app virtualization and QCOW2 disk snapshot workflows on Apple Silicon macOS (`arm64`), covering command-line administration via `utmctl`, disk image manipulation with `qemu-img`, sandbox lifecycle management for malware analysis, and network topology configurations.

---

## 1. UTM as Core Hypervisor on Apple Silicon macOS

On Apple Silicon (M1/M2/M3/M4), UTM provides hardware-accelerated virtualization utilizing Apple's `Virtualization.framework` alongside QEMU emulation for cross-architecture targets.

Key characteristics:
- **Architecture**: Native `arm64` virtual machines run with near bare-metal execution speed through Apple Hypervisor / Virtualization framework. Cross-architecture guest VMs (e.g. `x86_64`) run via QEMU TCG emulation.
- **Management CLI**: `utmctl` is bundled inside `/Applications/UTM.app/Contents/MacOS/utmctl` or linked into `/opt/homebrew/bin/utmctl`.
- **Disk Backing**: UTM stores VM bundles (`.utm`) containing configuration plists and disk images (typically formatted as QCOW2 or raw disk images).

---

## 2. Command-Line VM Administration (`utmctl`)

The `utmctl` CLI tool enables automated control of UTM virtual machines without opening the graphical interface.

### Discovering and Querying VMs

```bash
# List all registered virtual machines (UUID, Status, Name)
utmctl list

# Inspect running status of a specific VM
utmctl status "Windows VM - FOR508"
utmctl status <VM_UUID>
```

### VM Lifecycle Operations

```bash
# Start or resume a virtual machine
utmctl start "Windows VM - FOR508"

# Suspend a virtual machine to memory
utmctl suspend "Windows VM - FOR508"

# Discard saved suspended state (forces normal cold boot)
utmctl discard-state "Windows VM - FOR508"

# Gracefully shut down or stop a virtual machine
utmctl stop "Windows VM - FOR508"

# Query assigned guest IP addresses (requires QEMU Guest Agent)
utmctl ip-address "Windows VM - FOR508"
```

### VM Snapshots via `utmctl`

UTM supports native VM snapshots (capturing disk state and memory state when suspended or stopped):

```bash
# List snapshots for a VM (supports --json for automated parsing)
utmctl snapshot list "Windows VM - FOR508"
utmctl snapshot list <VM_UUID> --json

# Create a new snapshot
utmctl snapshot create "Windows VM - FOR508" --name "clean_baseline"

# Restore a snapshot by name or snapshot identifier
utmctl snapshot restore "Windows VM - FOR508" --snapshot "clean_baseline"

# Delete a snapshot
utmctl snapshot delete "Windows VM - FOR508" --snapshot "clean_baseline"
```

---

## 3. QCOW2 Disk Format Architecture

QCOW2 (QEMU Copy-On-Write version 2/3) is the storage format used for flexible snapshotting and disk branching in virtualization pipelines.

### Copy-On-Write (COW) Overlays

A base disk image remains immutable, while guest modifications are written to a lightweight differential overlay.

```
+------------------------------------+
|        Base Disk Image             |  (Read-only master OS installation)
|        `base_win11.qcow2`          |
+------------------------------------+
                  ^
                  | Backing file pointer (-b base_win11.qcow2)
+------------------------------------+
|     Differential Overlay Disk      |  (Contains only modified sectors)
|       `analysis_target.qcow2`      |
+------------------------------------+
```

Creating a copy-on-write overlay using `qemu-img`:
```bash
# Create 64GB overlay linked to base_win11.qcow2
qemu-img create -f qcow2 -b /path/to/base_win11.qcow2 -F qcow2 /path/to/analysis_target.qcow2 64G
```

### Internal Snapshots vs External Differential Disks

| Feature | Internal Snapshots (`qemu-img snapshot`) | External Differential Disks (`-b backing`) |
|---|---|---|
| **Storage** | Single `.qcow2` file holds all states | Separate overlay `.qcow2` file per branch |
| **Creation** | `qemu-img snapshot -c <snap> disk.qcow2` | `qemu-img create -f qcow2 -b base.qcow2 overlay.qcow2` |
| **Rollback** | `qemu-img snapshot -a <snap> disk.qcow2` | Discard overlay file and recreate from base |
| **Integrity** | Corruption risks whole image file | Base disk remains strictly read-only and safe |
| **Best For** | Ad-hoc checkpoints during dynamic triage | Automated detonation pipelines & disposable sandboxes |

### Internal Snapshot Management Commands

```bash
# List internal snapshots in a QCOW2 image
qemu-img snapshot -l /path/to/disk.qcow2

# Create snapshot named "clean_state"
qemu-img snapshot -c clean_state /path/to/disk.qcow2

# Apply (restore) snapshot named "clean_state"
qemu-img snapshot -a clean_state /path/to/disk.qcow2

# Delete snapshot named "clean_state"
qemu-img snapshot -d clean_state /path/to/disk.qcow2

# Inspect QCOW2 image details and snapshots as JSON
qemu-img info --out=json /path/to/disk.qcow2
```

---

## 4. Malware Analysis Sandbox Lifecycle

A repeatable reverse engineering and dynamic detonation workflow follows a strict snapshot lifecycle:

```
+-----------------------+
|  1. Clean Baseline    |  OS installed, tools deployed, analysis agent primed
+-----------------------+
            |
            v
+-----------------------+
|  2. Snapshot Creation |  `utmctl snapshot create <VM> --name "baseline"`
+-----------------------+
            |
            v
+-----------------------+
|  3. Detonation / RE   |  Deploy sample, hook with Frida/IDA, capture network/memory
+-----------------------+
            |
            v
+-----------------------+
|  4. Triage & Evidence |  Dump memory, extract IOCs, harvest logs
+-----------------------+
            |
            v
+-----------------------+
|  5. Instant Rollback  |  `utmctl stop <VM>`
|                       |  `utmctl snapshot restore <VM> --snapshot "baseline"`
+-----------------------+
```

### Operational Rules for Detonation Sandboxes:
1. **Never Detonate on Base**: Always execute malware on a disposable snapshot or differential overlay.
2. **Cold Rollback**: Shut down or stop the VM (`utmctl stop <VM>`) before restoring snapshots to prevent filesystem inconsistencies or state conflicts.
3. **Verify State Restoration**: Confirm the VM returns to its pristine state before beginning the next sample analysis.

---

## 5. VM Networking Configuration

Selecting the appropriate network mode depends on whether the sample requires internet access, local isolation, or host debugging access.

### 1. Shared Network (NAT) with Port Forwarding (Recommended for Remote Debugging)
- **Topology**: Guest VM resides in an isolated private subnet behind macOS NAT.
- **Outbound**: Guest can connect outbound to the internet (or to a host proxy such as mitmproxy at `192.168.64.1` / default gateway).
- **Inbound**: Host cannot connect into the VM directly unless port forwarding rules are configured in UTM VM Settings:
  - Protocol: `TCP`
  - Host Port: `23946`
  - Guest Port: `23946`
  - Guest IP: (empty / all interfaces)
- **IDA Pro Connection**: Connect IDA Pro on host to `127.0.0.1:23946`.

### 2. Bridged Networking
- **Topology**: VM attaches directly to host physical interface (Wi-Fi or Ethernet) and receives a routable IP on the local LAN via DHCP.
- **Inbound**: Direct bidirectional communication between host and guest.
- **Obtaining IP**:
  ```bash
  utmctl ip-address <VM_NAME_OR_UUID>
  ```
- **IDA Pro Connection**: Connect IDA Pro to `<GUEST_IP>:23946`.

### 3. Isolated / Host-Only Network (Malware Containment)
- **Topology**: UTM Host-Only network. Guest has no route to the public internet or local LAN.
- **Safety**: Prevents malware from contacting real C2 servers, scanning internal networks, or leaking host identifiers.
- **Simulated Services**: Run `INetSim`, `fakedns`, or `mitmproxy` on the host to emulate DNS and HTTP C2 responses safely.

---

## 6. Companion Automation Script (`setup_utm.py`)

The companion automated helper provides high-level subcommands for this workflow:

```bash
# Check host status and list registered VMs
uv run profiles/re/agent/skills/tool-setup/scripts/setup_utm.py status

# List VMs as JSON
uv run profiles/re/agent/skills/tool-setup/scripts/setup_utm.py list-vms --json

# Manage UTM snapshots
uv run profiles/re/agent/skills/tool-setup/scripts/setup_utm.py snapshot-list "Windows VM"
uv run profiles/re/agent/skills/tool-setup/scripts/setup_utm.py snapshot-create "Windows VM" "clean_base"
uv run profiles/re/agent/skills/tool-setup/scripts/setup_utm.py snapshot-restore "Windows VM" "clean_base"

# Create differential QCOW2 disks
uv run profiles/re/agent/skills/tool-setup/scripts/setup_utm.py qcow2-create /tmp/overlay.qcow2 20 --backing /path/to/base.qcow2

# Manage internal QCOW2 snapshots
uv run profiles/re/agent/skills/tool-setup/scripts/setup_utm.py qcow2-snapshot /tmp/disk.qcow2 --create clean
uv run profiles/re/agent/skills/tool-setup/scripts/setup_utm.py qcow2-snapshot /tmp/disk.qcow2 --list
uv run profiles/re/agent/skills/tool-setup/scripts/setup_utm.py qcow2-snapshot /tmp/disk.qcow2 --restore clean
```
