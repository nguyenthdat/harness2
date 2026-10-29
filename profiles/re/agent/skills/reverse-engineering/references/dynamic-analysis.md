# Dynamic Analysis & Runtime Observation

Actionable guidance for controlled runtime observation, debugger attachment, dynamic binary instrumentation (Frida), emulated execution (QEMU), and network proxy interception across isolated sandboxes.

---

## 1. Governance & Strict Policy Boundaries

Dynamic analysis is governed strictly by `profiles/re/agent/RULES.md`:

1. **Static is the Default**: Do not run, emulate, attach to, or detonate a target unless the parent explicitly requests dynamic analysis or static byte triage cannot answer the question.
2. **Static Contracts Override**: If the task specifies static analysis only, or if the deliverable is a schema JSON plus `evidence.md`, or if `tools.json` names only `file`, `strings`, and `objdump`, **do not execute, debug, emulate, or detonate under any circumstances**.
3. **No Host Execution**: Never launch a suspicious binary, installer, or untrusted payload on the host workstation. All dynamic runs must occur inside an isolated VM (UTM, QEMU, Android Emulator, iOS Research VM).
4. **Passive Observation Only**: Dynamic instrumentation is restricted to passive observation (tracing arguments, recording memory states, logging return values). **Never alter return values, modify control flow, disable security verifications, or inject exploit payloads.**

---

## 2. Debugger Workflows (GDB, LLDB, WinDbg)

Debuggers provide instruction-level visibility into registers, stack frames, and dynamic memory mappings.

### GDB (Linux ELF)
```bash
# Start target in GDB with ASLR disabled
gdb -q -ex "set disable-randomization on" target.bin

# Key commands:
(gdb) break *0x401230              # Hardware/software breakpoint at address
(gdb) run arg1 arg2                # Start process with arguments
(gdb) info registers rax rdi rsi   # Inspect register values
(gdb) x/16gx $rsp                  # Examine 16 64-bit words on stack
(gdb) x/s 0x403010                 # Examine string at address
(gdb) dump memory /tmp/dump.bin 0x400000 0x420000 # Dump memory range to file
```

### LLDB (macOS / iOS Mach-O)
```bash
# Launch under LLDB
lldb -- target_binary

# Key commands:
(lldb) breakpoint set --address 0x100003fa0
(lldb) process launch --stop-at-entry
(lldb) register read x0 x1 x2
(lldb) memory read --format x --size 8 --count 16 0x100004000
```

### WinDbg (Windows PE)
```text
bp TargetModule!FunctionAddress    ; Set breakpoint
g                                  ; Continue execution
r                                  ; Dump registers
dps rsp L10                        ; Dump stack with symbols
!address                           ; Enumerate virtual memory page protections
.dump /f C:\dump\unpacked.dmp      ; Write full process crash/memory dump
```

---

## 3. Dynamic Binary Instrumentation (Frida)

Frida injects a JavaScript runtime into the target process to observe function arguments and data transformations.

### Passive Call Tracing Pattern:
```javascript
// Passive inspection of function arguments and results
var targetFunc = Module.findExportByName("libtarget.so", "processData");
if (targetFunc) {
    Interceptor.attach(targetFunc, {
        onEnter: function(args) {
            console.log("[*] processData entered");
            console.log("    Arg0 (buffer): " + args[0]);
            console.log("    Arg1 (length): " + args[1].toInt32());
            console.log("    Memory preview: \n" + hexdump(args[0], { length: 32 }));
        },
        onLeave: function(retval) {
            console.log("[*] processData returned: " + retval);
        }
    });
}
```
*Rule*: The `onLeave` handler records the returned value for observation only; it must never replace or tamper with `retval`.

---

## 4. Hypervisors & Emulation Sandboxes

When dynamic execution is authorized, execute only within contained virtualization environments:

### 1. UTM Hypervisor (macOS Apple Silicon)
- Leverage `utmctl` and disposable snapshot mode (`setup_utm.py start-disposable <vm>`).
- All disk writes are backed by temporary copy-on-write overlays that are discarded on shutdown.
- Guest command execution occurs via QEMU Guest Agent without requiring network connectivity.

### 2. Android Studio Emulator with Rooted KernelSU
- Provisioned via `setup_android_emulator.py`.
- Run inside Google Play official arm64 system images with replaced GKI kernels (`kernel-ranchu`).
- Inspect logcat and application sandbox storage offline.

### 3. QEMU User-Mode Emulation
- For single-binary cross-architecture observation (e.g., running MIPS/ARM binaries on x86-64):
  ```bash
  qemu-arm-static -g 1234 ./target_arm_binary
  ```
  Connect GDB to port 1234 for instruction stepping without booting a full OS.

---

## 5. Network Proxy & Traffic Interception (mitmproxy)

For observing application HTTP/HTTPS and WebSocket communication:
- Start `mitmdump` on an isolated interface:
  ```bash
  mitmdump -p 8080 -w /tmp/traffic_capture.mitm
  ```
- Configure system CA certificate inside the emulator or research VM using `setup_proxy_ca.py`.
- Save traffic captures as `.mitm` or export to `.pcap` for static inspection via `inspect_web_network_capture` or `tshark`.

---

## 6. Process Memory Dumping & Unpacking

To extract in-memory artifacts (e.g., dynamically unpacked payloads or injected modules):
- On Linux: read `/proc/<pid>/maps` to find executable heap or anonymous RWX allocations, then read `/proc/<pid>/mem` at those offsets:
  ```bash
  cat /proc/<pid>/maps | grep "rwx"
  ```
- On Windows: use `procdump` or WinDbg `.dump` to write a minidump.
- Re-align headers and import tables statically using `pefile` or IDA Pro offline.
