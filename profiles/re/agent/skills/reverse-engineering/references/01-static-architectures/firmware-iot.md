# Embedded Firmware & IoT Binary Reverse Engineering

## Title & Overview
- **Domain**: Embedded systems, IoT devices, router firmware, and bare-metal microcontrollers (MIPS, ARM, RISC-V, Xtensa, PowerPC).
- **Scope**: Firmware image unpacking, file system carving (SquashFS, JFFS2, UBIFS), bootloader analysis (U-Boot), bare-metal memory map reconstruction, NVRAM parsing, and hardware peripheral mapping.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Target is a raw flash dump, update package (`.bin`, `.img`, `.trx`, `.chk`, `.pkg`).
- Magic bytes indicate firmware containers:
  - U-Boot image header: `\x27\x05\x19\x56`
  - SquashFS filesystem: `hsqs`, `sqsh`, `shsq`, `qshs`
  - JFFS2 filesystem: `\x85\x19`
  - TRX firmware header: `HDR0` (`0x30524448`)
- Binary contains embedded Linux kernels (`vmlinux`, `zImage`) or bare-metal RTOS (FreeRTOS, VxWorks, eCos, ThreadX).

---

## Tooling & CLI/MCP Actions
- **Primary Firmware Unpackers & Analyzers**:
  - `binwalk` / `unblob`: Signature scanning, filesystem extraction, and entropy calculation.
  - REA Tools: `inspect_firmware_regions`, `extract_firmware`.
  - QEMU User/System: `qemu-mips-static`, `qemu-arm-static` for cross-architecture emulation.
- **Decompilers**:
  - Headless IDA Pro MCP / Ghidra: Multi-architecture decompilation (MIPS32/64, ARM Thumb/ARM32, RISC-V).

---

## Key Methodologies & Workflow (Placeholder)

### 1. Entropy Analysis & Image Carving
- [ ] Calculate entropy scan across image to detect compressed or encrypted partitions.
- [ ] Run `binwalk -eM <firmware.bin>` or `unblob <firmware.bin>` to recursively extract nested archives.
- [ ] Identify bootloader header (U-Boot, RedBoot), kernel image (`zImage`, `uImage`), and root filesystem.

### 2. Embedded Filesystem Extraction
- [ ] Mount or extract root filesystem (`squashfs-tools`, `sasquatch`, `ubireader_extract_files`).
- [ ] Audit init scripts and daemon startups: `/etc/init.d/`, `/etc/rc.local`, `/etc/inittab`.
- [ ] Extract configuration databases: default NVRAM tables, web server CGI roots (`/www/`, `/htdocs/`).

### 3. Bare-Metal & RTOS Firmware Reversing
- [ ] Determine load base address (VMA) for bare-metal images lacking header metadata.
- [ ] Reconstruct vector table: Reset vector, exception handlers, interrupt service routines (ISRs).
- [ ] Map Memory-Mapped I/O (MMIO) peripheral registers against processor datasheet (UART, SPI, I2C, Watchdog).
- [ ] Identify RTOS task creation APIs (`xTaskCreate` in FreeRTOS, `taskSpawn` in VxWorks).

### 4. IoT Web Daemons & Network Services Triage
- [ ] Locate proprietary web servers (GoAhead, Boa, mini_httpd, lighttpd).
- [ ] Identify custom CGI binaries handling administrative actions and command processing.
- [ ] Audit string formatting and system execution sinks (`system()`, `popen()`, `execve()`) for command injection flaws.

---

## Boundaries & Anti-Patterns
- **Do not load multi-megabyte flash dumps directly into decompilers as a single file**: Flash dumps contain multiple disjoint partitions (bootloader, kernel, filesystem); carve partitions first.
- **Do not assume standard Linux libc semantics on bare metal**: Bare-metal RTOS implementations often omit dynamic linking and use custom libc stubs.
- **Do not execute embedded binaries on host workstation**: Cross-architecture binaries require emulation or matching target hardware.
