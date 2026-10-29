# Kế hoạch chọn skill

## Mục đích

Plan này chọn skill nào được viết trong `profiles/re`. Không copy repo upstream vào profile. Không một skill cho mỗi tool.

Đây là chỉ mục cho người đọc. Agent không lấy file này làm quy trình.

Static là mặc định. Dynamic chỉ theo `profiles/re/agent/RULES.md`. Hợp đồng static của một task vẫn thắng plan này.

Thân đã viết: `malware-analysis`, `reverse-engineering`, `static-artifact-analysis`.

Placeholder, chưa có thân: `il2cpp`, `dotnet`, `jvm`, `javascript`, `android`, `apple`, `ios`, `desktop`, `obfuscation`, `browser-extension`, `tools`.

## Vì sao hai nguồn này

secskills là danh sách họ phân tích. Hạt nhân reverse ở đó rõ: binary, .NET, iOS, macOS, IL2CPP, JavaScript làm rối, extension, unpack, VM. Phần còn lại của cùng thư mục là audit source, web, AI, vận hành. Profile lấy họ từ danh sách này, không lấy cả repo.

reverse-skill là router và lớp tool. Nó rộng sang pentest, CTF, cloud, Active Directory. Profile không lấy độ rộng đó. Lấy đường đi: loại file này thì mở skill nào, tool nào đứng cạnh. `skills/INDEX.md` là mục lục. Trên `main` có 49 thư mục, cộng file INDEX.

Họ lấy từ secskills. Route tool lấy từ reverse-skill. Chỗ reverse-skill có exploit, repackage, hook, hoặc bypass thì bỏ phần đó khi viết thân.

Sáu link cuối chỉ để trích dẫn, không thành skill. awesome-reverse-engineering là chỉ mục tool theo câu hỏi, nguồn tên cho `tools`. VM-Packages là hạng mục gói FLARE-VM; không nhận Exploitation, Shellcode, Payload Development, Credential Access. capa-rules là namespace năng lực cho `malware-analysis`. MASTG là danh mục tool mobile; không nhập pentest. Frida và mitmproxy là tool, không phải skill pack.

## secskills

30 thư mục, API contents trên `main`, mỗi tên một hàng. Cột Việc chỉ có bốn giá trị.

| Skill upstream | Trong profile | Việc | Giai đoạn |
| --- | --- | --- | --- |
| analyzing-binaries | `reverse-engineering` | đã có | đã xong |
| analyzing-dotnet-assemblies | `dotnet` | đã có | sóng 1 |
| analyzing-ios-binaries | `ios` | đã có | sóng 1 |
| analyzing-macos-binaries | `apple` | đã có | sóng 1 |
| reversing-browser-extensions | `browser-extension` | đã có | sóng 1 |
| reversing-obfuscated-javascript | `javascript`, `obfuscation` | đã có | sóng 1 |
| reversing-unity-il2cpp | `il2cpp` | đã có | sóng 1 |
| devirtualizing-vm-protected-code | `obfuscation`, không tách file | gộp vào skill đã có | sóng 1 |
| reversing-xamarin-maui | `dotnet` | gộp vào skill đã có | sóng 1 |
| reviewing-cryptography | `reverse-engineering` | gộp vào skill đã có | không sóng riêng |
| unpacking-protected-binaries | `obfuscation`, không tách file | gộp vào skill đã có | sóng 1 |
| analyzing-firmware-images | `firmware` | sóng 2 (placeholder sau) | sóng 2 |
| analyzing-go-binaries | `go` | sóng 2 (placeholder sau) | sóng 2 |
| analyzing-rust-binaries | `rust` | sóng 2 (placeholder sau) | sóng 2 |
| diffing-binary-patches | `binary-diff` | sóng 2 (placeholder sau) | sóng 2 |
| reversing-flutter-apps | `flutter` | sóng 2 (placeholder sau) | sóng 2 |
| reversing-network-protocols | `protocol` | sóng 2 (placeholder sau) | sóng 2 |
| reversing-react-native-apps | `react-native` | sóng 2 (placeholder sau) | sóng 2 |
| auditing-code-for-vulnerabilities | không tạo | ngoài phạm vi | không làm |
| auditing-mcp-servers | không tạo | ngoài phạm vi | không làm |
| auditing-php-applications | không tạo | ngoài phạm vi | không làm |
| auditing-supply-chain | không tạo | ngoài phạm vi | không làm |
| hunting-web-backdoors | không tạo | ngoài phạm vi | không làm |
| maintaining-engagement-state | không tạo | ngoài phạm vi | không làm |
| mapping-attack-techniques | không tạo | ngoài phạm vi | không làm |
| orchestrating-vulnerability-research | không tạo | ngoài phạm vi | không làm |
| reporting-security-findings | không tạo | ngoài phạm vi | không làm |
| reviewing-code-changes | không tạo | ngoài phạm vi | không làm |
| securing-ai-systems | không tạo | ngoài phạm vi | không làm |
| vetting-agent-extensions | không tạo | ngoài phạm vi | không làm |

`reviewing-cryptography` đi vào thân `reverse-engineering` khi thân đó được sửa. Không skill riêng, không mở lại thân đó trong sóng 1.

`reversing-obfuscated-javascript` không thành file mới. Bundle và ASAR ở `javascript`. Phần làm rối ở `obfuscation`.

Mười hai hàng ngoài phạm vi là audit source, PHP, web, supply chain, AI, MCP, review diff source, và vận hành (engagement, báo cáo, ATT&CK, điều phối nghiên cứu lỗ hổng). Không tạo skill.

`android`, `jvm`, `desktop`, `tools` không có hàng secskills. Chúng ở bảng reverse-skill và ở sóng 1.

## reverse-skill

49 thư mục trên `main`, cộng `INDEX.md`. Một nhóm một hàng khi cùng một quyết định. Tên dưới đây là tên thư mục thật.

### Giữ, trỏ vào skill hiện có

| Thư mục | Trong profile |
| --- | --- |
| apk-reverse | `android` |
| mobile-reverse | `android`, `ios` |
| dotnet-reverse | `dotnet` |
| js-reverse | `javascript` |
| browser-extension-reverse | `browser-extension` |
| macos-reverse | `apple` |
| ida-reverse, ghidra-reverse, radare2, binary-ninja-reverse | `tools`, `reverse-engineering` |
| malware-analysis | `malware-analysis` |
| go-rust-reverse | sóng 2: `go`, `rust` |
| firmware-pentest | sóng 2: `firmware`; không lấy phần exploit |
| protocol-reverse | sóng 2: `protocol` |
| binary-diff | sóng 2: `binary-diff` |
| thick-client | `desktop` |
| reverse-engineering | `reverse-engineering` đã có |

`reverse-engineering` có thư mục con `dsl-vm-reverse`. Không tách file. Khi viết `obfuscation`, chỉ lấy ranh giới VM/DSL, không copy bước.

`firmware-pentest` chỉ để nhận dạng và đọc image. `patch-diff-exploit` không đi cùng `binary-diff`.

### Ngoài phạm vi

Một hàng, không tạo skill:

api-security, attack-chain, browser-automation, cloud-k8s, code-audit, ctf-sandbox, database-security, edr-bypass-re, email-security, hardware-security, identity-federation, llm-security, ot-ics, patch-diff-exploit, pentest-tools, pwn-chain, radio-sdr, supply-chain-security, threat-hunting, threat-intelligence, wifi-wireless, windows-ad.

`pentest-tools` có thư mục con `src-hunter`. Cả nhánh ngoài phạm vi. Không lấy playbook.

`digital-forensics` cũng không tạo skill. Memory, disk, và IR rộng hơn profile này. Sample vẫn ở `malware-analysis`.

### Hạ tầng

Không phải skill phân tích: config, scripts, tests, references, ops, field-journal, case-review, diagram-generator, docs-generator.

## Ba giai đoạn

### Sóng 0, xong

Mười một placeholder đã có. `profiles/re/agent/RULES.md` đã có. Ba thân `malware-analysis`, `reverse-engineering`, `static-artifact-analysis` không viết lại ở sóng 1.

`tool-setup` is a real skill, not a placeholder and not part of the wave-1 body order.

### Sóng 1

Viết thân các placeholder đã có, theo thứ tự. Xong một thân rồi mới sang thân sau. Không thêm thư mục.

1. `tools`. Đọc ida-reverse, ghidra-reverse, radare2, binary-ninja-reverse. Catalog tên. Không một skill mỗi tool. awesome-reverse-engineering chỉ để đối chiếu tên.
2. `browser-extension`. Đọc reversing-browser-extensions và browser-extension-reverse.
3. `il2cpp`. Đọc reversing-unity-il2cpp.
4. `android`. Đọc apk-reverse và nửa Android của mobile-reverse. secskills không có thư mục Android.
5. `ios`. Đọc analyzing-ios-binaries và nửa iOS của mobile-reverse.
6. `dotnet`. Đọc analyzing-dotnet-assemblies, reversing-xamarin-maui, dotnet-reverse.
7. `javascript`. Đọc reversing-obfuscated-javascript và js-reverse.
8. `obfuscation`. Đọc unpacking-protected-binaries, devirtualizing-vm-protected-code, và phần làm rối của reversing-obfuscated-javascript.
9. `jvm`. Hai nguồn không có thư mục JVM. Viết từ ranh giới placeholder hiện có: `.jar`, `.class`, tên ProGuard hoặc R8 chưa phải behavior. Không bịa quy trình từ repo khác.
10. `apple`. Đọc analyzing-macos-binaries và macos-reverse.
11. `desktop`. Đọc thick-client.

Mỗi thân đọc skill upstream tương ứng, rồi viết lại ngắn cho profile này: khi nào mở, artifact nào, cái gì chưa phải behavior. Không copy lệnh hook, repackage, bypass, exploit.

### Sóng 2

Chỉ tạo placeholder khi sóng 1 xong. Chưa viết thân.

| Profile | Đọc khi tạo placeholder |
| --- | --- |
| `firmware` | analyzing-firmware-images, firmware-pentest, không phần exploit |
| `go` | analyzing-go-binaries, go-rust-reverse |
| `rust` | analyzing-rust-binaries, go-rust-reverse |
| `flutter` | reversing-flutter-apps |
| `react-native` | reversing-react-native-apps |
| `protocol` | reversing-network-protocols, protocol-reverse |
| `binary-diff` | diffing-binary-patches, binary-diff |

Không tạo `binary-diff` từ patch-diff-exploit.
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
  - **macOS**: UTM.app (`utmctl`) là hypervisor nòng cốt trên Apple Silicon (`arm64`), tận dụng Apple `Virtualization.framework` và QEMU engine cho máy ảo cross-arch. Hỗ trợ vòng đời snapshot máy ảo (`utmctl snapshot`), quản lý phân vùng copy-on-write overlay / internal snapshot định dạng QCOW2 (`qemu-img snapshot`), và kịch bản tự động hóa `profiles/re/agent/skills/tool-setup/scripts/setup_utm.py`. Dự phòng Parallels Desktop (`prlctl`).
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

## Dynamic

Quyết định nằm ở `profiles/re/agent/RULES.md`.

Static là mặc định. Dynamic (debugger, Frida, emulator, proxy) khi parent yêu cầu, hoặc khi byte không đủ để trả lời, và chỉ trên target parent chỉ định.

Hợp đồng static của task vẫn thắng. Task ghi static-only, hoặc chỉ tên `file`, `strings`, `objdump`, hoặc deliverable là schema JSON cộng `evidence.md` của `static-artifact-analysis`, thì không chạy, không debug, không emulate, không detonate.

Plan này không phải hướng dẫn Frida.

## Framework viết harness

Chưa thành skill và không nằm trong allowlist của `tool-setup`. Bốn framework đầu cho firmware hoặc malware không có source. OSS-Fuzz-Gen và CKGFuzzer chỉ khi đã có source C/C++ hoặc header biên dịch được. Plan này chỉ ghi framework nào trả lời câu hỏi nào. Không có lệnh build, không có lệnh fuzz.

|Framework|Câu hỏi nó trả lời|Repo|
|---|---|---|
|Qiling + UnicornAFL|Firmware và malware. Qiling, trên Unicorn, hiểu PE và ELF, mock syscall hoặc Windows API bằng Python. Chạy binary đến ngay trước parser hoặc decryptor, chụp snapshot, rồi bơm input từ AFL++ vào thanh ghi hoặc bộ nhớ.|https://github.com/qilingframework/qiling và https://github.com/AFLplusplus/unicornafl|
|LibAFL, mode QEMU hoặc Frida|Fuzzer viết bằng Rust, khi cần tốc độ và hộp đen phức tạp hơn AFL++ thường.|https://github.com/AFLplusplus/LibAFL|
|TinyInst và WinAFL|PE hoặc DLL Windows đóng, fuzz trong bộ nhớ, không cần source. TinyInst là lớp instrumentation. WinAFL dùng nó cho persistent mode.|https://github.com/googleprojectzero/TinyInst và https://github.com/googleprojectzero/winafl|
|Hopper (`hopper-fuzzer`)|Thư viện động `.so` hoặc `.dll` không có source. Tự suy ràng buộc tham số và ghép lời gọi API thành harness.|https://github.com/FuzzAnything/hopper|
|OSS-Fuzz-Gen|Đã có source C/C++, driver, hoặc header cộng mã giả từ Ghidra/IDA mà biên dịch lại được. LLM đọc AST và call graph, sinh `LLVMFuzzerTestOneInput`, tự biên dịch, đọc lỗi biên dịch hoặc crash giả do con trỏ sai hoặc struct chưa khởi tạo, rồi sửa harness.|https://github.com/google/oss-fuzz-gen|
|CKGFuzzer|Thư viện C/C++ phải gọi API đúng thứ tự. Code knowledge graph cộng LLM sinh driver cho chuỗi kiểu `init_ctx` rồi `parse_header` rồi `process_body` rồi `free_ctx`.|https://github.com/security-pride/CKGFuzzer|

Ánh xạ plan: Qiling gắn với sóng 2 `firmware` và với `malware-analysis`. WinAFL chỉ cho target Windows. Hopper không phải disassembler Hopper. Không tải kernel, không viết harness trong sóng 1. Hai framework này chỉ khi có source hoặc header biên dịch được. Không dùng chúng cho binary đóng. Không đưa vào sóng 1.

## Nguồn

https://github.com/trilwu/secskills/tree/main/secskills-core/skills
https://github.com/zhaoxuya520/reverse-skill/tree/main/skills
https://github.com/zhaoxuya520/reverse-skill/blob/main/skills/INDEX.md
https://github.com/morluto/awesome-reverse-engineering
https://github.com/mandiant/VM-Packages
https://github.com/mandiant/capa-rules
https://github.com/OWASP/mastg
https://github.com/frida/frida
https://github.com/mitmproxy/mitmproxy
https://github.com/qilingframework/qiling
https://github.com/AFLplusplus/unicornafl
https://github.com/AFLplusplus/LibAFL
https://github.com/googleprojectzero/TinyInst
https://github.com/googleprojectzero/winafl
https://github.com/FuzzAnything/hopper
https://github.com/google/oss-fuzz-gen
https://github.com/security-pride/CKGFuzzer
https://github.com/Lakr233/vphone-cli
https://github.com/blacktop/ipsw
https://ipsw.me/
