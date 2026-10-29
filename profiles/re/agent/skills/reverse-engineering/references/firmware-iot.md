# Firmware & Embedded IoT Reverse Engineering

Actionable guidance for reverse engineering firmware images (`.bin`, `.img`), carving embedded filesystems, triaging bootloaders and kernels, and disassembling embedded architectures (MIPS, ARM, RISC-V).

---

## 1. Firmware Containers & Magic Signatures

Firmware images pack bootloaders, kernel partitions, device trees, and root filesystems into structured containers or contiguous flash dumps:

| Container / Filesystem | Magic Bytes | Description |
|---|---|---|
| **U-Boot uImage** | `0x27051956` (`\x27\x05\x19\x56`) | Standard U-Boot header (image name, load address, entry point, CRC) |
| **Broadcom TRX** | `HDR0` (`0x30524448`) | Broadcom router firmware container with partition offsets |
| **SquashFS (Little-Endian)**| `hsqs` (`0x73717368`) | Read-only compressed filesystem (LZMA, XZ, GZIP) |
| **SquashFS (Big-Endian)**   | `sqsh` (`0x68737173`) | Read-only compressed filesystem on big-endian MIPS/PPC |
| **CramFS** | `0x28cd3d45` / `0x453dcd28` | Legacy compressed ROM filesystem |
| **JFFS2** | `0x1985` (`\x85\x19`) | Journaling Flash File System v2 for raw NAND/NOR |
| **Flattened Device Tree (DTB)**| `0xd00dfeed` (`\xd0\x0d\xfe\xed`)| Open Firmware device tree describing hardware peripherals |
| **GZIP Compressed Data** | `\x1f\x8b\x08` | Often wraps raw Linux kernels (`vmlinux`) |
| **LZMA Stream** | `\x5d\x00\x00` | Common compression for embedded kernels and squashfs |

---

## 2. Filesystem Carving & Extraction

### REA MCP Tools
- `inspect_firmware_regions`: Analyzes firmware layout, partition markers, detected magic, and container bounds without extraction.
- `extract_firmware`: Uses host-installed extraction backends (`binwalk` or `unblob`) to carve partitions into an absolute output directory.

### CLI Tools
```bash
# Scan and report embedded signatures without extracting
binwalk firmware.bin

# Recursive extraction of all partitions and filesystems
binwalk -e -M firmware.bin -C /tmp/firmware_extracted

# Modern alternative: unblob
unblob --extract-dir /tmp/firmware_extracted firmware.bin
```

### Non-Standard SquashFS Implementations
Vendors frequently modify SquashFS compression headers or block sizes to hinder standard extraction:
- Use `sasquatch` (patched SquashFS tool supporting non-standard vendor formats).
- Or inspect the kernel's `squashfs` driver in Ghidra to extract custom compression flags and magic constants.

---

## 3. Bootloaders, Kernels & Device Trees

### U-Boot Environment Triage
- Embedded U-Boot environments contain key-value configuration strings:
  - `bootargs`: Linux kernel command line arguments (e.g., `console=ttyS0,115200 root=/dev/mtdblock3 init=/bin/sh`).
  - `bootcmd`: Boot sequence execution commands (`tftp`, `bootm`).
  - `ipaddr` / `serverip`: Default network configuration.

### Kernel Recovery
- Search for the kernel version banner string:
  ```text
  Linux version 4.9.11 (gcc version 7.3.0) #1 PREEMPT Mon Oct 12 10:20:00 UTC 2020
  ```
- Uncompressed kernels contain the system call table, driver initialization routines, and symbol strings in `.kallsyms` (if not stripped).

---

## 4. Embedded CPU Architectures & Disassembly Nuances

### 1. MIPS (MIPS32 / MIPS64)
- **Endianness**: Verify whether target is Big-Endian (`mips`) or Little-Endian (`mipsel`).
- **Branch Delay Slots**: In MIPS architecture, the instruction immediately following a branch or jump executes **before** the branch takes effect:
  ```asm
  jal  target_function    ; jump and link (call)
  add  $a0, $s0, $zero    ; executed in branch delay slot (sets first argument!)
  ```
  *Pitfall*: Do not overlook the delay slot instruction; it frequently prepares arguments or completes critical arithmetic.
- **Registers**:
  - `$a0` - `$a3`: Function arguments 1 through 4.
  - `$v0` - `$v1`: Return values.
  - `$ra`: Return address (Link register).
  - `$gp`: Global pointer (base for accessing static variables).

### 2. ARM32 (ARM vs Thumb Mode)
- **Mode Switching (Interworking)**:
  - ARM mode: Fixed 32-bit instructions.
  - Thumb / Thumb-2 mode: 16-bit or 32-bit compact instructions.
  - The least significant bit (bit 0) of a target address selects the execution mode:
    - Target `0x10001` -> Executes in **Thumb mode** at `0x10000`.
    - Target `0x10000` -> Executes in **ARM mode** at `0x10000`.
  - In Ghidra, toggle the `TMode` register (`0` for ARM, `1` for Thumb) to fix incorrect disassembly.

### 3. RISC-V (RV32I / RV64I)
- Modular RISC architecture with standard 32 general-purpose registers:
  - `a0` - `a7`: Function arguments and return values (`a0`, `a1`).
  - `ra`: Return address (`x1`).
  - `sp`: Stack pointer (`x2`).
  - `gp`: Global pointer (`x3`).

---

## 5. Base Address Calculation for Bare-Metal Firmware

Bare-metal firmware (microcontrollers, bootloaders, IoT sensors) lacks ELF headers specifying loading memory addresses.

### Pointer Delta Method:
1. Search for ASCII strings in the binary (e.g., `"Firmware Initialized"` at file offset `0x4200`).
2. Search memory for 32-bit / 64-bit pointers that match the file offset with a constant offset:
   - Example: Pointer found with value `0x80004200`.
   - Base address candidate: `0x80004200 - 0x4200 = 0x80000000`.
3. Check the vector table at offset `0x00`:
   - In ARM Cortex-M, initial SP is at `0x00`, Reset Vector (entry point) is at `0x04`. If Reset Vector is `0x08000181`, the base address is `0x08000000` (bit 0 indicates Thumb mode).

---

## 6. Operational Boundaries

1. **Static Firmware Analysis Only**: Do not flash devices, write to EEPROMs, or execute unknown embedded binaries.
2. **No Exploit Payloads**: Focus on architecture recovery, configuration parsing, vulnerability identification, and logic analysis.
