# Browser JavaScript & WebAssembly Reverse Engineering

## Title & Overview
- **Domain**: Web client bundles, Chrome/Firefox browser extensions, Electron renderer scripts, and WebAssembly (WASM) modules.
- **Scope**: Source map reconstruction, JavaScript bundle unminification/beautification, AST deobfuscation, WebAssembly binary format (`.wasm`), Wasm-to-C/WAT translation, and browser extension security review.

---

## Trigger Conditions & Detection Indicators
When to open this reference:
- Target files include:
  - Web packages: `.js`, `.mjs`, `.bundle.js`, `manifest.json` (Chrome Extension MV2/MV3).
  - WebAssembly: `.wasm` binary starting with magic `\x00asm` (`0x6D736100`).
  - Electron archives: `app.asar` containing bundled frontend JavaScript.
- Minified or obfuscated JavaScript code: single-line files, variable mangling (`a, b, c`), string array encoding, Webpack runtime headers (`webpackJsonp`).

---

## Tooling & CLI/MCP Actions
- **Primary Decompilers & Analyzers**:
  - REA Tool: `analyze_javascript_application` (built-in parser for JS/Electron trees).
  - WebAssembly Tools: `wasm2wat` (WABT suite), `wasm-decompile`, Ghidra WASM plugin.
- **Command-Line & Node.js Utilities**:
  - AST Deobfuscation: Babel (`@babel/parser`, `@babel/traverse`, `@babel/generator`), Webcrack, Synchrony.
  - Source Map Unpackers: `shuji`, `restore-source-tree`, `sourcemapper`.
  - Electron unpacker: `npx asar extract app.asar <out_dir>`.

---

## Key Methodologies & Workflow (Placeholder)

### 1. Source Map Detection & Tree Restoration
- [ ] Check end of `.js` files for `//# sourceMappingURL=<url_or_data_uri>`.
- [ ] If inline Base64 source map exists: Extract and decode to recover original project source directory and unminified files.
- [ ] If external `.map` file exists: Run source map extractor to rebuild complete TypeScript/ES6 project structure.

### 2. JavaScript AST Deobfuscation & String Decoding
- [ ] Identify obfuscator signatures: Obfuscator.io (string arrays with rotation functions), JSFuck, JJencode.
- [ ] Parse AST using Babel: Write transform plugins to evaluate constant expressions and resolve string array lookup functions.
- [ ] Reconstruct Control Flow: Unflatten switch-case state machines into sequential statements.
- [ ] Rename mangled variables with semantic names based on API usages.

### 3. WebAssembly (WASM) Module Disassembly
- [ ] Verify WASM header: magic `0x6D736100` and version `0x00000001`.
- [ ] Convert WASM binary to readable WebAssembly Text format using `wasm2wat module.wasm -o module.wat`.
- [ ] Generate C-like pseudocode using `wasm-decompile module.wasm -o module.dcmp`.
- [ ] Map WASM linear memory imports and exports (`env.memory`).
- [ ] Trace JS-WASM boundary bindings (`Emscripten`, `wasm-bindgen`).

### 4. Browser Extension Privilege & IPC Analysis
- [ ] Parse `manifest.json`: Review `permissions`, `host_permissions`, `content_scripts`, `background` service workers.
- [ ] Audit message passing channels: `chrome.runtime.onMessage`, `chrome.runtime.onConnectExternal`.
- [ ] Check for insecure DOM manipulation and cross-site scripting sinks (`innerHTML`, `eval`, `Function`).

---

## Boundaries & Anti-Patterns
- **Do not dump multi-megabyte minified JS bundles into LLM context**: Run local AST extractors or pretty-printers first, and extract only targeted functions.
- **Do not execute untrusted JavaScript scripts via Node.js or browser**: Obfuscators may incorporate anti-debugging or payload detonation code.
- **Do not treat WASM decompilation as full C source**: WASM strips high-level struct definitions unless DWARF debug sections are retained.
