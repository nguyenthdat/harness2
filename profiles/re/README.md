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

## Dynamic

Quyết định nằm ở `profiles/re/agent/RULES.md`.

Static là mặc định. Dynamic (debugger, Frida, emulator, proxy) khi parent yêu cầu, hoặc khi byte không đủ để trả lời, và chỉ trên target parent chỉ định.

Hợp đồng static của task vẫn thắng. Task ghi static-only, hoặc chỉ tên `file`, `strings`, `objdump`, hoặc deliverable là schema JSON cộng `evidence.md` của `static-artifact-analysis`, thì không chạy, không debug, không emulate, không detonate.

Plan này không phải hướng dẫn Frida.

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
