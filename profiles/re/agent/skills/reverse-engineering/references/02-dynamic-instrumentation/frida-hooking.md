# Dynamic Binary Instrumentation & Frida Hooking

## Title & Overview
- **Domain**: Dynamic Binary Instrumentation (DBI) using Frida across native libraries, Android Dalvik/ART, and iOS/macOS runtimes.
- **Scope**: Passive function interception, argument and return value logging, memory inspection, Java/ObjC method hooking, and bypass of certificate pinning for research observation.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Target requires function-level runtime tracing without full debugger overhead.
- Analyzing Android applications with Java/Kotlin methods or JNI native interactions.
- Analyzing iOS applications with Objective-C selectors or Swift methods.
- Need to passively observe decrypted strings, API calls, or cryptographic inputs/outputs in real time.

---

## Tooling & CLI/MCP Actions
- **Primary Tooling**:
  - `frida-tools`: `frida`, `frida-trace`, `frida-ps`.
  - Android agent: `frida-server` running on rooted Android Emulator.
  - iOS agent: `frida-server` running on jailbroken test device or corellium/vphone VM.
  - Helper script: `profiles/re/agent/skills/tool-setup/scripts/setup_android_emulator.py`.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Frida Session Setup & Process Attachment
- [ ] Connect to remote device/VM: `frida-ps -U` or `frida-ps -H <ip:port>`.
- [ ] Choose injection mode:
  - Spawn mode (hooks before entrypoint): `frida -U -f com.example.app -l script.js`.
  - Attach mode (attaches to running process): `frida -U -n process_name -l script.js`.

### 2. Native Interception (Interceptor API)
- [ ] Resolve target symbol: `Module.findExportByName("libtarget.so", "targetFunc")` or module base address offset.
- [ ] Attach `Interceptor.attach`:
  ```javascript
  Interceptor.attach(targetFunc, {
      onEnter: function(args) {
          console.log("[*] Target entered");
          console.log("    Arg0: " + args[0] + " | " + hexdump(args[0], { length: 32 }));
      },
      onLeave: function(retval) {
          console.log("[*] Target returned: " + retval);
      }
  });
  ```
- [ ] Strictly passive: Record values; do not overwrite `retval` or memory buffers.

### 3. Java Runtime Hooking (Android Dalvik/ART)
- [ ] Use `Java.perform(function() { ... })` wrapper.
- [ ] Locate class: `var TargetClass = Java.use("com.example.TargetClass");`.
- [ ] Hook target method and log arguments/return values:
  ```javascript
  TargetClass.targetMethod.implementation = function(arg1, arg2) {
      console.log("[*] Java method invoked: arg1=" + arg1);
      var ret = this.targetMethod(arg1, arg2);
      console.log("    Returned: " + ret);
      return ret;
  };
  ```

### 4. Objective-C & Swift Hooking (Apple iOS/macOS)
- [ ] Objective-C method interception via `ObjC.classes.TargetClass['- methodName:']`.
- [ ] Swift method interception: Resolve mangled Swift symbols using `Module.findExportByName`.
- [ ] Inspect Foundation objects: `ObjC.Object(args[2]).toString()`.

---

## Boundaries & Anti-Patterns
- **Do not modify control flow or bypass security gates maliciously**: Use hooks exclusively for passive data logging and protocol analysis.
- **Do not introduce heavy synchronization locks in high-frequency hooks**: Hooking tight loops (e.g. per-byte decryptors) via Frida will cause target deadlocks; use debugger tracepoints or batch logging instead.
- **Do not run Frida against production endpoints or unisolated hosts**: Perform DBI strictly in contained lab environments.
