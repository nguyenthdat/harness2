---
name: tool-setup
description: >-
  Detect the host and, only when the parent asks, install an allowlisted
  reverse-engineering tool set with that OS package manager. Linux prefers
  KVM, macOS prefers Parallels, and Windows prefers VMware. Android covers
  the emulator, a su check, and a local KernelSU Image that may replace only
  an emulator kernel-ranchu. iOS tooling is macOS only. Does not install IDA,
  download KernelSU, or write a kernel on a physical device. Use when a
  needed tool, emulator, or hypervisor is missing, or the parent asks to
  prepare this machine. Do not use to launch a sample, rewrite mcp.json, or
  run rea setup or rea doctor.
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
- `tools` maps each name to `present` and `path`.
- `hypervisor.preferred` is `kvm` on Linux, `parallels` on macOS, and `vmware`
  on Windows. `hypervisor.present` is that hypervisor, not QEMU.
  `hypervisor.qemu_present` is separate. Do not prefer QEMU over the platform
  hypervisor.
- `android.su` is `null` unless `--probe-android` was passed.
- `ios.supported` is true only on macOS. Elsewhere `ios.reason` is
  `iOS tooling runs on macOS only`.
- `kernelsu.status` is `manual` when
  `/Users/datnguyen/Projects/android-emu-ksu/download/Image` is absent.
  `kernelsu.path` is that path. That is `kernelsu: manual`. Do not fetch a
  GitHub release or any other kernel.

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

- static: radare2, apktool, mitmproxy, and tshark where that OS packages them.
  Winget ids that are not known are `unmapped`.
- dynamic: on Linux, `qemu-kvm` and `qemu-system-x86` when KVM is the
  preferred hypervisor and those packages exist. On macOS do not install
  Parallels. On Windows do not install VMware. The paid hypervisor is
  `manual`.
- android: `android-platform-tools` on brew, or `adb` on apt, plus an
  emulator package only when the distro package exists. No system image
  download. KernelSU replacement is below.
- ios: if `os` is not `darwin`, the program exits 2, installs nothing, and
  the reason is `iOS tooling runs on macOS only`. On macOS do not install
  Xcode. Report whether `simctl` is missing.

Never install IDA, `ida-mcp`, or a Frida server binary onto a device.

### KernelSU

Replacement runs only inside this program, and only when `--install android`
was passed. The only source is a regular file named `Image` already in
`/Users/datnguyen/Projects/android-emu-ksu/download/`. If it is absent, stop
at `kernelsu: manual` and the path.

The destination must be a regular file named `kernel-ranchu` inside an SDK
`system-images` directory under `ANDROID_HOME` or
`~/Library/Android/sdk/system-images`. The program replaces every such file
under those roots. It writes a sibling `kernel-ranchu.orig` first when that
backup is missing. It does not write a kernel on a physical device.

If `kernelsu.cold_boot` is set, tell the parent that text. A cold boot is
required, then `adb shell su -c id` is the check. Do not cold-boot. Do not
start the emulator.

`--probe-android` may run `adb shell su -c id` only when `adb devices`
already shows exactly one device in state `device`. It does not start an
emulator and it does not flash a device.

## 3. Never

- Do not launch a sample.
- Do not rewrite `mcp.json` or run `rea setup` or `rea doctor`.
- Do not download KernelSU, a kernel, or a system image.
- Do not follow notes about bypass, Play Integrity, banking, or root
  detection. This skill does not perform those steps.
