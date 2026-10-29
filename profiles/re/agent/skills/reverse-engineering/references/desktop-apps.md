# Desktop Thick Client Applications

Actionable reference for reverse engineering installed desktop client applications across Windows, macOS, and Linux. Covers framework identification, packaging layouts, local persistence, IPC channels, and static triage.

---

## 1. Desktop Framework Identification

When analyzing an installed desktop application directory, identify the core runtime framework before choosing disassemblers or decompilers:

| Framework | Core Artifacts / Signatures | Analysis Route |
|---|---|---|
| **Electron** | `resources/app.asar`, `electron.exe` / `Electron Framework`, `LICENSE.electron.txt` | `analyze_javascript_application`, `inspect_electron_fuses` |
| **Qt (C++)** | `QtCore.dll` / `libQt5Core.so`, `QtGui`, `QtWidgets`, embedded `.qrc` resources | Native decompiler (IDA/Ghidra) + Qt string/slot parsers |
| **WPF / .NET** | Managed PE (`IMAGE_COR20_HEADER`), `.baml` compiled XAML resources | `ilspycmd`, `dnSpy`, `inspect_managed_artifact` |
| **Win32 / MFC** | Unmanaged PE, `mfc*.dll`, rich `.rsrc` section (dialog templates, menus) | `open_binary`, `inspect_pe_resources`, IDA/Ghidra |
| **macOS Native** | `Contents/MacOS/<exec>`, `Contents/Resources/*.nib`, `Info.plist` | `open_bundle_resources`, `class-dump`, IDA/Ghidra |
| **Java Desktop** | `*.jar` in `lib/`, bundled JRE/JDK, launch stub executable | `jadx`, standard Java decompilers |

---

## 2. Directory Triage with REA MCP

When the installation path is provided and the framework is unconfirmed:
```json
{
  "path": "/path/to/installed/app/dir",
  "detail": "summary"
}
```
Use `inspect_desktop_application` to inventory files, identify candidates, check omitted subdirectories, and detect framework components. Follow up with `inspect_analysis_view` kind `desktop-application` to inspect files flagged with `has_issues: true` or retrieve specific manifest entries.

---

## 3. Framework-Specific Triage

### 1. Electron Applications
- **ASAR Extraction**: Unpack `resources/app.asar` to examine main process scripts and renderer bundles.
- **Fuses Check**: Run `inspect_electron_fuses` on the Electron executable. Check whether `EnableNodeCliInspectArguments` is disabled (prevents attaching node inspector).
- **Process Boundaries**:
  - `main` process: Direct Node.js access, file system, native modules (`.node` C++ addons).
  - `renderer` process: Chromium web UI, isolated by default.
  - `preload` script: Exposes specific APIs across the context bridge via `contextBridge.exposeInMainWorld`.

### 2. Qt Applications (C++)
- **Signals and Slots**: Qt's event mechanism uses `QMetaObject`. Disassembly reveals static arrays of strings representing signal and slot names.
- **Qt Resource System (`.qrc`)**: Embedded UI layouts, QML scripts, images, and translations are compiled into the binary or stored in `.rcc` files:
  - Magic for binary RCC: `\x71\x72\x65\x73` (`qres`).
  - Extract embedded QML and assets using RCC extractors.

### 3. Windows Presentation Foundation (WPF)
- UI definitions written in XAML are compiled into binary BAML (`.baml`) resources embedded in managed PE resources.
- Decompile with `ilspycmd` or `dnSpy` to reconstitute human-readable XAML tags, event handlers, and data bindings.

---

## 4. Local Data Persistence & Offline Storage

Desktop applications persist local configurations, credentials, sessions, and state across standard locations:

### Storage Formats:
1. **SQLite Databases**: Common for caching, history, and message storage (`.sqlite`, `.db`, `.db3`).
   - Use `inspect_sqlite_database` to inspect tables and schemas offline.
2. **LevelDB / IndexedDB**: Used by Electron and Chromium-based apps (stored in `Local Storage/leveldb/`).
   - Structured key-value storage containing session states.
3. **Windows Registry**: Look for static key paths in strings (`Software\<Vendor>\<AppName>`).
4. **OS Credential Stores**:
   - Windows Credential Manager / DPAPI (`CryptProtectData`).
   - macOS Keychain (`SecItemAdd`, `SecItemCopyMatching`).
   - Linux Secret Service API (Freedesktop / D-Bus).

---

## 5. Inter-Process Communication (IPC)

Desktop applications frequently use multi-process architectures communicating over local IPC channels:
- **Named Pipes**:
  - Windows: `\\.\pipe\<pipename>`. Inspect xrefs to `CreateNamedPipeA/W` or `CreateFileA/W`.
  - Unix / macOS: Named FIFOs or Unix domain sockets (`/tmp/<name>.sock` or `/var/run/`).
- **Electron IPC**:
  - Main process handles: `ipcMain.on(...)`, `ipcMain.handle(...)`.
  - Renderer requests: `ipcRenderer.send(...)`, `ipcRenderer.invoke(...)`.
- **Windows Messages**:
  - `WM_COPYDATA` (`0x004A`): Inter-process data transfer between window handles.
  - Custom registered window messages via `RegisterWindowMessageW`.

---

## 6. Analysis Boundaries

1. **Do Not Launch the Application**: Analysis is performed strictly offline on disk artifacts.
2. **Package Label vs Behavior**: A folder name, package manifest, or dependency listing is an observation, not proof that the code was executed.
3. **Target Selection**: If the parent task says "my app" without naming a path, ask which application before inspecting unrelated directories.
