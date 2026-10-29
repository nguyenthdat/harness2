# Reverse Engineering & Binary Analysis Architecture

Tài liệu kiến trúc tổng thể cho profile Reverse Engineering (`profiles/re`). Mô tả mô hình phân tầng **3-Tier Progressive Disclosure Funnel**, lý do loại bỏ micro-skills (4 nút thắt cổ chai), ma trận quyết định tham chiếu vs skill, danh mục tài liệu tham chiếu phân cấp (`references/`) và kịch bản tự động hóa (`scripts/`).

---

## 1. Kiến trúc phân tầng 3-Tier Progressive Disclosure

Thay vì chia nhỏ thành hàng chục micro-skills gây phân mảnh và nhầm lẫn cho LLM router, profile chuẩn hóa thành **2 core skills** duy nhất trong `profiles/re/agent/skills/`:
1. `reverse-engineering`: Core skill bao quát toàn bộ quy trình dịch ngược mã nhị phân (ELF, PE, Mach-O), managed runtimes (.NET, JVM, Android DEX), mobile (iOS, Android, Unity IL2CPP), firmware, WebAssembly, dynamic instrumentation và các mục tiêu phân tích chuyên sâu.
2. `tool-setup`: Quản lý phát hiện môi trường, cài đặt công cụ, cấu hình máy ảo, hypervisor và emulator.

Quy trình phân tích tuân thủ phễu 3 tầng:

```text
┌──────────────────────────────────────────────────────────────────┐
│ Tier 1: Core Entrypoint (reverse-engineering/SKILL.md)           │
│ - Phương pháp luận cốt lõi, nguyên tắc kiểm chứng giả thuyết     │
│ - Bảng định tuyến tham chiếu 3 nhánh (Static, Dynamic, Objective)│
│ - Dung lượng gọn nhẹ (~1.5k tokens)                              │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ Tier 2: Mandatory Pre-Triage (scripts/auto_triage.py)            │
│ - Quét header, magic bytes, container, compiler signatures       │
│ - Nhận diện tự động: Go, Rust, C++, .NET, JVM, Unity, WASM, PCAP │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ Tier 3: Selective Progressive Disclosure (references/<cat>/<ref>)│
│ - Tải ĐÚNG MỘT file tham chiếu kỹ thuật chuyên sâu theo domain   │
│ - 01-static-architectures/  (C++, Rust, Go, .NET/JVM, Unity...)  │
│ - 02-dynamic-instrumentation/ (Debuggers, Frida, Unpack, Proxy)  │
│ - 03-objectives/ (Diffing, Protocols, Crypto/Algo, Contracts)    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Vì sao Micro-Skills thất bại trong Reverse Engineering (4 Bottlenecks)

Việc duy trì 18–20 micro-skills riêng lẻ dẫn đến 4 vấn đề nghiêm trọng:

### 1. Pre-Triage Blindness (Mù định dạng trước phân tích)
Người dùng hoặc hệ thống giao việc thường chỉ cung cấp một đường dẫn tệp nhị phân (`/tmp/sample.bin`, file ELF đã strip symbol, hoặc buffer không rõ nguồn gốc). Agent không thể biết trước tệp đó được viết bằng Go hay Rust để kích hoạt `go-reverse` hay `rust-reverse`. Việc định tuyến skill trước khi đọc byte vi phạm nguyên lý cơ bản của kỹ thuật đảo ngược: **phải đọc byte để xác định định dạng**.

### 2. Polyglot Targets (Ứng dụng đa ngôn ngữ & đa tầng runtime)
Các ứng dụng thực tế hiện đại không bao giờ chỉ gồm một ngôn ngữ duy nhất:
- **Android APK**: Chứa giao diện Java/Kotlin (DEX), kết nối qua JNI tới thư viện native C++ (`libnative.so`), bên trong có thể nhúng module Rust hoặc engine Unity/Flutter.
- **Unity Game**: Giao diện C# biên dịch qua IL2CPP thành mã máy native C++ (`libil2cpp.so`/`GameAssembly.dll`) kết hợp file siêu dữ liệu `global-metadata.dat`.
- **Electron Desktop**: Bao gồm tiến trình Node.js (JavaScript), Chromium renderer, và các C++ native addons (`.node`).
Việc chia micro-skills buộc agent phải liên tục chuyển đổi ngữ cảnh, gây mất dấu vết phân tích và làm tràn context window.

### 3. Methodology Duplication (Trùng lặp phương pháp luận)
Mọi tác vụ reverse engineering đều chia sẻ cùng một phương pháp luận cốt lõi:
- Băm định danh (SHA-256) và xác minh tính toàn vẹn.
- Phân tích luồng điều khiển (CFG) và cấu trúc hàm.
- Truy vết tham chiếu chéo (`xrefs`) từ chuỗi ký tự và hằng số tới mã sử dụng.
- Phân biệt giữa quan sát thực tế (observation) và suy đoán (hypothesis).
Tách thành nhiều skill khiến các nguyên tắc này bị sao chép lặp lại nhiều lần, gây khó khăn cho việc duy trì nhất quán.

### 4. Router Confusion (Xung đột và loãng context của LLM Router)
Khi profile chứa quá nhiều skill, mô tả của các skill cạnh tranh nhau trong system prompt của mô hình ngôn ngữ. Router dễ bị đánh lừa bởi từ khóa (ví dụ: thấy chuỗi "iOS" trong mô tả task về Android liền kích hoạt `ios-reverse`), dẫn đến kích hoạt sai skill và lãng phí vòng lặp giải quyết.

---

## 3. Ma trận quyết định: Khi nào giữ trong `references/` vs Khi nào tách Skill

| Tiêu chí | Giữ trong `references/` của `reverse-engineering` | Tách thành Skill độc lập |
|---|---|---|
| **Mục tiêu phân tích** | Mọi tác vụ phân tích, đọc hiểu, dịch ngược cấu trúc, giải mã logic nhị phân | Chuẩn bị hạ tầng, cài đặt môi trường, cấu hình VM/OS |
| **Hợp đồng đầu ra** | Báo cáo phân tích kỹ thuật, Evidence ID, JSON schema, phát hiện logic | Thay đổi trạng thái máy chủ, khởi chạy máy ảo, cấu hình proxy |
| **Quyền can thiệp hệ thống** | Đọc tĩnh (Read-only), phân tích an toàn, quan sát bị động trong sandbox | Cài đặt package hệ thống, thay đổi kernel, ghi cấu hình (`tool-setup`) |
| **Ngữ cảnh kích hoạt** | Kích hoạt có điều kiện sau bước Pre-Triage trong cùng phiên | Được gọi độc lập trước khi bắt đầu phiên phân tích |

---

## 4. Quản lý ngữ cảnh và Băng thông phân tích

Khi xử lý các mục tiêu có sản lượng phân tích lớn (Heavy Output Targets):
1. **Inlined Rust Standard Library**: Hàng trăm hàm monomorphized và panic handlers. Agent ghi nhận chuỗi panic và cắt tỉa (prune) các nhánh cold path, chỉ giữ lại luồng logic chính.
2. **Bundle JavaScript khổng lồ (>100k dòng)**: Lưu trữ kết quả phân rã trung gian vào tệp tạm thời trong workspace; chỉ trích xuất hàm mục tiêu và Evidence ID vào sổ ghi chép (ledger).
3. **Binary Diff diện rộng**: Lọc bỏ các hàm có độ tương đồng tuyệt đối (`similarity = 1.00`), chỉ tập trung phân tích các khối lệnh được thêm/sửa có độ tương đồng từ `0.50` đến `0.99`.

---

## 5. Danh mục tài liệu tham chiếu phân cấp (`references/`)

Tất cả tài liệu tham chiếu được chuẩn hóa cấu trúc thành các placeholder sẵn sàng mở rộng, chia làm 3 nhóm chuyên đề và 1 danh mục công cụ gốc:

### 1. Static Architectures (`references/01-static-architectures/`)
- `native-cpp-abi.md`: Calling conventions (x64 SysV/MSVC, ARM64), vtable layout, phục hồi RTTI MSVC/Itanium, layout bộ nhớ STL.
- `native-rust.md`: Con trỏ béo `&str`/`&[T]`, tối ưu niche cho `Option`/`Result`, mẫu `core::panicking`, demangling legacy/v0, và bóc tách metadata `.dep-v0`.
- `native-golang.md`: ABI thanh ghi Go 1.17+, giải mã cấu trúc `.gopclntab`, mở rộng stack `runtime.morestack`, interface `iface`/`eface`, và type descriptors.
- `managed-dotnet-jvm.md`: Hợp nhất .NET CLR và JVM/Dalvik: metadata streams (`#~`, `#Strings`), ECMA-335, DEX format, JADX, Smali, ProGuard/R8, P/Invoke & JNI bridges.
- `unity-il2cpp.md`: Ghép nối binary native (`GameAssembly.dll`/`libil2cpp.so`) với `global-metadata.dat`, Il2CppDumper, struct `Il2CppObject`/`Il2CppClass`.
- `mobile-ios.md`: Cấu trúc IPA, giải mã Mach-O FairPlay DRM (`LC_ENCRYPTION_INFO`), runtime Objective-C (`objc_msgSend`), Swift 5 ABI, và entitlements.
- `browser-js-wasm.md`: Chrome/Firefox extensions (Manifest V2/V3), Webpack bundles, bóc tách Electron ASAR, AST deobfuscation qua Babel, và WebAssembly (`wasm2wat`).
- `firmware-iot.md`: Định dạng firmware (uImage, SquashFS, TRX), công cụ trích xuất (`binwalk`, `unblob`), kiến trúc nhúng (MIPS delay slots, ARM Thumb mode, RISC-V), và tính địa chỉ nạp base address.

### 2. Dynamic Instrumentation (`references/02-dynamic-instrumentation/`)
- `debugger-workflows.md`: Hướng dẫn vận hành GDB (pwndbg/gef), LLDB, WinDbg, x64dbg, phần cứng/phần mềm breakpoint, và kiểm soát luồng thực thi trong VM.
- `frida-hooking.md`: Dynamic Binary Instrumentation bằng Frida, mẫu script hook native C/C++, Java ART, Objective-C/Swift, và logging đối số bị động.
- `unpacking-memory-dump.md`: Phát hiện Original Entry Point (OEP), kỹ thuật tail jump, trích xuất memory dump qua `dump_memory.py`, và phục hồi Import Address Table (IAT).
- `network-traffic-proxy.md`: Đánh chặn mạng HTTPS/WebSocket qua `mitmproxy`, cài đặt CA trust store, xuất file `.mitm`/`.pcap`, và phân tích qua `tshark`.

### 3. Objectives & Deliverables (`references/03-objectives/`)
- `vuln-research-patch.md`: Kỹ thuật diff nhị phân (BinDiff, Ghidra BSim), thuật toán so khớp đồ thị hàm, phương pháp luận phân tích bản vá bảo mật (patch analysis) và chuyển giao symbol.
- `protocol-recovery.md`: Khung giao thức nhị phân proprietary, giải mã Protobuf wire format không cần file `.proto`, dịch ngược gRPC và phân tích luồng PCAP.
- `algorithm-recovery.md`: Nhận diện hằng số mật mã (AES, SHA, MD5, CRC32, ChaCha20), phân tích thuật toán mã hóa tùy biến/XOR, trích xuất key/IV và giả lập Python giải mã.
- `static-artifact-contract.md`: Hướng dẫn chi tiết thực hiện hợp đồng schema JSON cộng `evidence.md`, phân tích span giới hạn và chạy script kiểm tra tự động `check_deliverables.py`.

### 4. Tools Catalog (`references/tools-catalog.md`)
- `tools-catalog.md`: Ma trận định tuyến và hướng dẫn CLI/MCP cho IDA Pro, Ghidra (`rea`), radare2, Binary Ninja, JADX, Apktool, mitmproxy, tshark, Frida.

---

## 6. Danh mục kịch bản tự động hóa (`scripts/`)

Các công cụ Python tiêu chuẩn đi kèm skill `reverse-engineering` trong thư mục `profiles/re/agent/skills/reverse-engineering/scripts/`:
- `auto_triage.py`: Quét tự động header, magic bytes, section và chuỗi ký tự để nhận diện compiler/runtime và xuất đề xuất reference dạng JSON.
- `dump_memory.py`: Công cụ trích xuất bộ nhớ tiến trình an toàn trên Linux (`/proc/<pid>/mem`) và macOS (LLDB core dump) phục vụ unpacking và phân tích heap.
- `elf_triage.py`: Phân tích nhanh ELF header, segment LOAD deltas, section offset mapping, và giải mã XOR lặp.
- `elf_symbols.py`: Liệt kê symbol và cô lập span địa chỉ của hàm application code phục vụ disassembly có giới hạn.
- `check_deliverables.py`: Kiểm tra tự động tính hợp lệ của schema JSON và các trích dẫn bằng chứng trong `evidence.md`.

---

## Tối ưu hóa công cụ cài đặt theo nền tảng (OS) & vai trò

Mục này cung cấp ma trận công cụ reverse engineering toàn diện, được phân loại theo vai trò phân tích (Static RE, Dynamic RE, Android Lab, iOS Lab, Hypervisor) và tương thích chi tiết theo từng hệ điều hành / package manager (`brew`, `apt-get`, `dnf`, `pacman`, `winget`).

### 1. Phân loại theo vai trò phân tích

- **Static RE (Phân tích tĩnh)**:
  - `radare2` (`r2`): Khung phân tích nhị phân mã nguồn mở, disassembly, hex edit, scriptable.
  - `jadx`: Dịch ngược APK, DEX, Java class ra mã nguồn Java chất lượng cao với GUI/CLI.
  - `apktool`: Giải nén, phân rã tài nguyên APK (`res/`, `AndroidManifest.xml`) và mã Smali; build lại APK.
  - `binwalk`: Trích xuất firmware, phân tích định dạng tệp nhị phân nén, filesystem carving.
  - `tshark`: CLI engine của Wireshark để phân tích pcap, protocol dump, trích xuất payload mạng tĩnh.
  - `ghidra` (hoặc `rea-agents`): Bộ SRE đa nền tảng mạnh mẽ với decompiler tiên tiến cho ARM, x86, MIPS.
  - `ida-mcp`: Giao diện Model Context Protocol cho IDA Pro (khi môi trường có bản quyền IDA).

- **Dynamic RE (Phân tích động)**:
  - `frida-tools` (`frida`, `frida-trace`, `frida-ps`): Dynamic binary instrumentation, hook JavaScript trực tiếp vào runtime bộ nhớ.
  - `mitmproxy` (`mitmdump`, `mitmweb`): HTTPS/TLS proxy đánh chặn, giải mã và chỉnh sửa lưu lượng mạng HTTP/1, HTTP/2, WebSocket. Hỗ trợ tự động hóa cài đặt System CA cho Android emulator / iOS Simulator và sinh kịch bản Frida bypass SSL Pinning (`setup_proxy_ca.py`).
  - `qemu` (`qemu-system-*`, `qemu-user-*`): Giả lập đa kiến trúc CPU phục vụ phân tích cross-platform.

- **Android Lab (Emulator + KernelSU Rooting)**:
  - `android-platform-tools` (`adb`): Android Debug Bridge điều khiển thiết bị, shell, port forwarding.
  - `emulator`: Trình giả lập Android Studio chính thức chạy phần cứng tăng tốc (HAXM / Hypervisor.Framework / KVM).
  - `cmdline-tools` (`avdmanager`, `sdkmanager`): Quản lý tạo/xóa AVD, tải và cập nhật system image.
  - **Google Play arm64-v8a System Images**: Image sản xuất thực tế có Play Store (API 34, 35, 36, 37.0).
  - **KernelSU GKI Kernel Replacement**: Thay thế `kernel-ranchu` bằng nhân GKI Linux hỗ trợ KernelSU (`Image` từ AnyKernel3 zip: `6.6.66-android15-*`, `6.12.58-android16-*` được tải tự động từ official GitHub releases).
  - **KernelSU Manager APK**: Ứng dụng quản trị quyền root mức nhân (`KernelSU_Next_*.apk` tải tự động từ GitHub releases).
  - **Tài liệu tham chiếu & Kịch bản tự động**:
    - Phương pháp rooting: Thay thế nhân Linux GKI (KernelSU) trên emulator Google Play image chính thức của Android Studio.
    - Cache tài nguyên KernelSU: `~/.cache/android-ksu/` (hoặc biến môi trường `ANDROID_KSU_CACHE_DIR`, tự động tải từ official GitHub releases khi thiếu).
    - Kịch bản tự động hóa: `profiles/re/agent/skills/tool-setup/scripts/setup_android_emulator.py` (hỗ trợ `download`, `create-avd`, `patch-kernel`, `cold-boot`, `wait-boot`, `install-apk`, `verify-root`, `setup-all`)

- **iOS Lab (macOS only)**:
  - Xcode Command Line Tools (`xcrun`, `lldb`).
  - `xcrun simctl`: Điều khiển iOS Simulator chuẩn (boot, install, launch, capture) - unrooted.
  - **Rooted iOS Research VM (`vphone-cli`)**: Giải pháp chính cho máy ảo iOS có root ([vphone-cli](https://github.com/Lakr233/vphone-cli)). Khởi chạy virtual iPhone (iOS 26) trên macOS Apple Silicon thông qua `Virtualization.framework` và cơ chế Private Cloud Compute (PCC) research VM (`csrutil allow-research-guests enable`, `sudo VPhoneEscalator allow ...`).
  - **Jailbreak Firmware Patch (`make fw_patch_jb` / `JB=1`)**: Bộ 112 patch cung cấp quyền root hoàn chỉnh, SSH, Sileo package manager, TrollStore và hỗ trợ Frida server / dynamic runtime instrumentation phục vụ nghiên cứu bảo mật chuyên sâu.
  - `blacktop/ipsw` ([ipsw](https://github.com/blacktop/ipsw)): Công cụ dòng lệnh CLI chuyên dụng để tải trực tiếp firmware Apple IPSW, giải nén kernelcache (`ipsw kernel dec`), phân rã dyld shared cache (`ipsw dyld split`), phân tích Mach-O.
  - `https://ipsw.me/`: Cổng tra cứu và tải trực tiếp file IPSW chính thức từ Apple CDN theo từng model thiết bị và phiên bản iOS.
  - `frida`: Hook runtime trên iOS Simulator, rooted research VM (`vphone-cli`), hoặc thiết bị vật lý jailbreak.

- **Hypervisor & VM Snapshot Sandboxing**:
  - **macOS**: UTM.app (`utmctl`) là hypervisor nòng cốt trên Apple Silicon (`arm64`), tận dụng Apple `Virtualization.framework` và QEMU engine cho máy ảo cross-arch. Hỗ trợ vòng đời snapshot máy ảo (`utmctl snapshot`), quản lý phân vùng copy-on-write overlay / internal snapshot định dạng QCOW2 (`qemu-img snapshot`), và kịch bản tự động hóa `profiles/re/agent/skills/tool-setup/scripts/setup_utm.py`.
  - **Linux**: KVM (`/dev/kvm`), `qemu-kvm`. Tối ưu tốc độ ảo hóa native phần cứng.
  - **Windows**: VMware Workstation (`vmrun`) hoặc Hyper-V / WSL2.

- **IDA Pro Remote Debugging (Docker IPC & UTM VM Setup)**:
  - Cung cấp kiến trúc server debug phân tán (`linux_server`, `win64_remote.exe`, `android_server`, `armlinux_server`) tự động phân giải qua `$IDADIR/dbgsrv` hoặc `/Applications/IDA*.app/Contents/MacOS/dbgsrv`.
  - Thiết lập remote debugging qua Docker container với namespace isolation và IPC sharing: `--ipc=host`, `--pid=host`, `--cap-add=SYS_PTRACE`, `--security-opt seccomp=unconfined`, `-p 23946:23946`.
  - Thiết lập port forwarding qua Shared NAT hoặc Bridged Network trên UTM VM (`127.0.0.1:23946`), cấu hình tường lửa Windows (`win64_remote.exe`) và vô hiệu hóa ASLR Linux.
  - Tự động hóa và tài liệu tra cứu: `setup_utm.py ida-server-info` và `profiles/re/agent/skills/tool-setup/references/ida-remote-debugging.md`.

### 2. Ma trận gói cài đặt theo Package Manager

| Công cụ | macOS (`brew`) | Debian/Ubuntu (`apt-get`) | Fedora/RHEL (`dnf`) | Arch Linux (`pacman`) | Windows (`winget`) |
| --- | --- | --- | --- | --- | --- |
| `radare2` | `radare2` | `radare2` | `radare2` | `radare2` | `radare2.radare2` |
| `jadx` | `jadx` | `jadx` | `jadx` | `jadx` | `Skylot.Jadx` |
| `apktool` | `apktool` | `apktool` | `apktool` | `android-apktool` | `iBotPeaches.Apktool` |
| `binwalk` | `binwalk` | `binwalk` | `binwalk` | `binwalk` | Thủ công / WSL2 |
| `tshark` | `wireshark` | `tshark` | `wireshark-cli` | `wireshark-cli` | `WiresharkFoundation.Wireshark` |
| `frida-tools`| `pipx install frida-tools` | `pipx install frida-tools` | `pipx install frida-tools` | `frida-tools` | `pip install frida-tools` |
| `mitmproxy` | `mitmproxy` | `mitmproxy` | `mitmproxy` | `mitmproxy` | `Mitmproxy.Mitmproxy` |
| `qemu` | `qemu` | `qemu-system-x86 qemu-kvm` | `qemu-kvm` | `qemu-desktop` | `SoftwareFreedomConservancy.QEMU` |
| `adb` | `android-platform-tools` | `adb` | `android-tools` | `android-tools` | `Google.PlatformTools` |
| `cmdline-tools`| `android-commandlinetools` | SDK Manager | SDK Manager | `android-sdk-cmdline-tools-latest` | Android Studio SDK |
| `ipsw` | `blacktop/tap/ipsw` | Thủ công / GitHub releases | Thủ công / GitHub releases | `ipsw` (AUR) | GitHub releases |

---

## 7. Tài liệu & Nguồn tham khảo

- https://github.com/trilwu/secskills/tree/main/secskills-core/skills
- https://github.com/zhaoxuya520/reverse-skill/tree/main/skills
- https://github.com/morluto/awesome-reverse-engineering
- https://github.com/mandiant/VM-Packages
- https://github.com/OWASP/mastg
- https://github.com/frida/frida
- https://github.com/mitmproxy/mitmproxy
- https://github.com/Lakr233/vphone-cli
- https://github.com/blacktop/ipsw
- https://ipsw.me/
