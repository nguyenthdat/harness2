---
name: tool-setup
description: >-
  Detect the host and, only when the parent asks, install an allowlisted
  reverse-engineering tool set with that OS package manager. Linux prefers
  KVM, macOS prefers Parallels, and Windows prefers VMware. Android covers
  the emulator, a su check, avdmanager/sdkmanager, and automated KernelSU
  patching that replaces an emulator kernel-ranchu on Google Play images.
  Provides setup_android_emulator.py for automated download, AVD creation,
  patching, cold boot, and root verification. iOS tooling is macOS only.
  Does not install IDA or write a kernel on a physical device.
---

# Tool setup

Detect first. Install only after the parent asks to prepare this machine, and
only the one profile that matches the task.

## 1. Detect

On Windows, macOS, and Linux run the same command. Do not call `python3`.
Do not add a shell script, PowerShell script, or batch file.

From this skill's directory:

`uv run scripts/detect_host.py`

From the repository root the same program is
`uv run profiles/re/agent/skills/tool-setup/scripts/detect_host.py`.

Read the single JSON object on stdout.

- `os` is `linux`, `darwin`, or `windows`.
- `package_manager` is the first of `brew`, `apt-get`, `dnf`, `pacman`, and
  `winget` that exists, or `null`.
- `tools` maps each name to `present` and `path`. Monitored tools include
  `radare2`, `jadx`, `apktool`, `binwalk`, `frida`, `mitmproxy`, `tshark`,
  `adb`, `emulator`, `avdmanager`, `sdkmanager`, `qemu`, `prlctl`, `vmrun`,
  `xcrun`, `ida-mcp`, and `vphone`.
- `hypervisor.preferred` is `kvm` on Linux, `parallels` on macOS, and `vmware`
  on Windows. `hypervisor.present` is that hypervisor, not QEMU.
  `hypervisor.qemu_present` is separate. Do not prefer QEMU over the platform
  hypervisor.
- `android.su` is `null` unless `--probe-android` was passed.
- `android.setup_script` reports the path to `setup_android_emulator.py`.
- `ios.supported` is true only on macOS. Elsewhere `ios.reason` is
  `iOS tooling runs on macOS only`.
- `ios.simctl` indicates availability of Xcode `simctl`.
- `ios.vphone_present` indicates presence of `vphone` or `vphone-cli`.
- `ios.rooted_vm_supported` indicates whether the host architecture supports
  rooted Apple Silicon virtual machines (`arm64`/`aarch64`).
- `ios.rooted_vm_solution` points to `https://github.com/Lakr233/vphone-cli`.
- `kernelsu.status` is `available`.
- `kernelsu.auto_download` is `true`.
- `kernelsu.cache_dir` reports the active cache directory (`~/.cache/android-ksu` or
  `ANDROID_KSU_CACHE_DIR`).
A missing tool is not permission to fetch a random installer.

## 2. Install

Skip this step unless the parent asked. Pass one flag:

- static: `uv run scripts/detect_host.py --install static`
- dynamic: `uv run scripts/detect_host.py --install dynamic`
- android: `uv run scripts/detect_host.py --install android`
- ios: `uv run scripts/detect_host.py --install ios`

The program installs only through the detected package manager, and only
packages that manager already knows. Commands are argument lists inside the
program. It never uses `sudo`. If the manager needs root, it installs nothing
and puts the exact command in `needs_root`. Show that command to the parent.
Do not run it yourself and do not prefix `sudo`.

Then run `uv run scripts/detect_host.py` again with no install flag. Report
what is present, missing, manual, and unsupported.

### Profiles

- static: `radare2`, `apktool`, `mitmproxy`, `tshark`, `binwalk`, `jadx` where
  that OS packages them. Winget ids that are not known are `unmapped`.
- dynamic: on Linux, `qemu-kvm` and `qemu-system-x86` when KVM is the
  preferred hypervisor and those packages exist. On macOS do not install
  Parallels. On Windows do not install VMware. The paid hypervisor is
  `manual`.
- android: `android-platform-tools` on brew, or `adb` on apt, plus an
  emulator package only when the distro package exists.
- ios: if `os` is not `darwin`, the program exits 2, installs nothing, and
  the reason is `iOS tooling runs on macOS only`. On macOS do not install
  Xcode. Report whether `simctl` is missing. For rooted iOS research VMs on
  Apple Silicon, use `vphone-cli` (see section 5).
Never install IDA, `ida-mcp`, or a Frida server binary onto a device.

---

## 3. Android Studio KernelSU Emulator Rooting Procedure

Production-grade Android security analysis (dynamic Frida hooking, Play Integrity API
testing, unmasking root detection) requires root on **Google Play images** rather than
AOSP / Google APIs images via Android Studio KernelSU GKI rooting methodology.

### System Requirements
- Host: Apple Silicon macOS (M1/M2/M3/M4, `arm64-v8a`) or Linux/Windows equivalent.
- Android SDK: Command-line tools (`avdmanager`, `sdkmanager`), platform tools (`adb`), emulator.
- System Image: `system-images;android-36;google_apis_playstore;arm64-v8a` (or `android-37.0`).
- KernelSU Assets: GKI kernel `Image` (or AnyKernel3 zip e.g., `6.6.66-android15-*.zip`, `6.12.58-android16-*.zip`) and `KernelSU_Next_*.apk` automatically downloaded from official GitHub releases to `~/.cache/android-ksu/` (or custom directory specified via `--download-dir`).
### Manual Step-by-Step Procedure

1. **Check Emulator Kernel Version**:
   ```bash
   adb shell uname -r
   # Example: 6.6.66-android15-8 or 6.12.58-android16
   ```

2. **Obtain KernelSU GKI Kernel (`Image`)**:
   Kernel zips are automatically fetched by `setup_android_emulator.py` into `~/.cache/android-ksu/`. If extracted manually from AnyKernel3 zip:
   ```bash
   unzip -p ~/.cache/android-ksu/6.6.66-android15-*.zip Image > /tmp/Image
   ```

3. **Locate and Replace `kernel-ranchu`**:
   The emulator kernel is inside the Android SDK system image directory:
   ```bash
   SYS_IMG="$HOME/Library/Android/sdk/system-images/android-36/google_apis_playstore/arm64-v8a"
   cp "$SYS_IMG/kernel-ranchu" "$SYS_IMG/kernel-ranchu.orig"
   cp /tmp/Image "$SYS_IMG/kernel-ranchu"
   ```

4. **Cold Boot the Emulator**:
   A cold boot is mandatory to bypass emulator kernel caching from quickboot snapshots:
   ```bash
   emulator -avd <AVD_NAME> -no-snapshot-load
   ```

5. **Wait for Device & Boot Completion**:
   ```bash
   adb wait-for-device
   while [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" != "1" ]; do sleep 2; done
   ```

6. **Install KernelSU Manager APK**:
   ```bash
   adb install -r ~/.cache/android-ksu/KernelSU_Next_*.apk
   ```

7. **Verify Root Access**:
   ```bash
   adb shell su -c id
   # Output must be: uid=0(root) gid=0(root) groups=0(root) context=u:r:su:s0
   ```

## 4. Automated Emulator Setup Script (`setup_android_emulator.py`)

The companion automated script implements the full workflow cleanly:
`uv run profiles/re/agent/skills/tool-setup/scripts/setup_android_emulator.py <subcommand>`

Supported subcommands:
- `list`: Inspects SDK path, tools, installed system images, AVDs, and KernelSU assets in cache directory (`~/.cache/android-ksu/`).
- `download [--kernel-version <ver>] [--apk-only] [--kernel-only]`: Automatically downloads the matching KernelSU GKI kernel AnyKernel3 zip from WildKernels and Manager APK from KernelSU-Next GitHub releases.
- `create-avd [--name <name>] [--system-image <pkg>] [--device <device>]`: Creates AVD with `avdmanager`.
- `patch-kernel [--system-image-path <path>] [--kernel-source <image_or_zip>]`: Backs up `kernel-ranchu` to `.orig` and replaces it with KernelSU GKI `Image` (auto-downloading matching kernel zip from GitHub releases if missing, extracting `Image`).
- `cold-boot [--avd <name>] [--headless]`: Starts emulator with `-no-snapshot-load` (and optional `-no-window -no-audio`).
- `wait-boot [--serial <serial>] [--timeout <sec>]`: Waits for `sys.boot_completed == 1`.
- `install-apk [--apk <path>] [--serial <serial>]`: Installs `KernelSU_Next_*.apk` via `adb install -r` (auto-downloading Manager APK from GitHub releases if missing).
- `verify-root [--serial <serial>]`: Runs `adb shell su -c id` and confirms `uid=0`.
- `setup-all [--avd <name>] [--headless] [--timeout <sec>]`: Executes end-to-end download/patch, boot, install, and verification.
All subcommands support `--json` for structured automation.
---

## 5. iOS Rooted Research Virtual Machine (`vphone-cli`)

For dynamic analysis requiring a rooted iOS environment (kernel/jailbreak-level inspection,
Frida server injection, tweaking system daemons, SSL unpinning):

### Unrooted Simulator vs Rooted Research VM
- **Standard iOS Simulator (`xcrun simctl`)**: Runs simulator Mach-O binaries in macOS userland; unrooted, lacks full iOS kernel/security sandbox isolation, and cannot run arm64e iOS device binaries or substrate-based jailbreak tweaks.
- **Rooted iOS Research VM (`vphone-cli`)**: Bootstrapped by [vphone-cli](https://github.com/Lakr233/vphone-cli) (by Lakr233). Boots virtual iPhone (iOS 26) on Apple Silicon macOS leveraging Apple's `Virtualization.framework` and Private Cloud Compute (PCC) research VM infrastructure.

### Host Prerequisites
- **Host**: macOS 15+ running on Apple Silicon (M1/M2/M3/M4, `arm64`).
- **Research Guest Entitlements / AMFI Policy**: Requires enabling research guest capability:
  ```bash
  sudo csrutil allow-research-guests enable
  ```
  (Requires reboot in Recovery OS if prompted by macOS).

### Rooted VM Setup & Jailbreak Firmware Patch
- Build or acquire `vphone-cli`:
  ```bash
  git clone https://github.com/Lakr233/vphone-cli.git
  cd vphone-cli
  make
  ```
- Use the **Jailbreak (JB) firmware patch variant** (`make fw_patch_jb` or `JB=1`, 112 patches) which provides:
  - Full root shell access (`ssh root@<vm-ip>`).
  - Sileo package manager and APT repository support.
  - TrollStore integration for installing and resigning arbitrary research payloads.
  - Frida server / dynamic runtime hooking support directly within the virtualized iOS environment.

## 6. Never

- Do not launch an untrusted malware sample outside isolated sandbox conditions.
- Do not rewrite `mcp.json` or run `rea setup` or `rea doctor`.
- Do not flash a physical connected device with emulator kernels.
