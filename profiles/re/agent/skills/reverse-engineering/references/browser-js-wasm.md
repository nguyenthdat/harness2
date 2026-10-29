# Browser Extensions, JavaScript Bundles & WebAssembly

Actionable reference for reverse engineering Chrome/Firefox extensions (Manifest V2/V3), bundled JavaScript applications (Webpack, Vite, Electron/ASAR), Babel AST deobfuscation, and WebAssembly (WASM).

---

## 1. Browser Extensions (Manifest V2 vs V3)

### Structure of an Extension (`.crx` / `.xpi` / Unpacked Folder)
Extensions are ZIP containers containing `manifest.json`, background workers, content scripts, popup HTML, and asset files.

### Manifest Differences
- **Manifest V2 (Legacy)**:
  - Background page: `"background": { "scripts": ["bg.js"], "persistent": true }`.
  - Network Interception: `"permissions": ["webRequest", "webRequestBlocking"]`.
- **Manifest V3 (Modern)**:
  - Service worker: `"background": { "service_worker": "background.js", "type": "module" }`. Non-persistent; terminates when idle.
  - Declarative Network Requests: `"declarativeNetRequest"` replacing blocking web requests.

### Execution Contexts & IPC
1. **Content Scripts**: Injected into web pages, access the DOM, but execute in an isolated JavaScript world. Cannot access page-level JS variables directly.
2. **Background Service Worker**: Has full access to `chrome.*` extension APIs (storage, tabs, cookies, webRequest).
3. **IPC Bridge**: Content scripts communicate with the background worker using:
   ```javascript
   // Content script sending message
   chrome.runtime.sendMessage({ action: "get_config", payload: query }, response => { ... });

   // Background worker listening
   chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => { ... });
   ```

---

## 2. JavaScript Bundles & Electron / ASAR

### Webpack / Vite Bundler Anatomy
Modern production JavaScript is minified and bundled into self-executing closures:
```javascript
// Typical Webpack bundle header
(function(modules) {
    var installedModules = {};
    function __webpack_require__(moduleId) {
        if (installedModules[moduleId]) return installedModules[moduleId].exports;
        var module = installedModules[moduleId] = { exports: {} };
        modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
        return module.exports;
    }
    return __webpack_require__(0);
})([
    /* 0 */ function(module, exports, __webpack_require__) { ... },
    /* 1 */ function(module, exports, __webpack_require__) { ... }
]);
```
- **Module ID Triage**: Search for strings or API endpoints, note the enclosing function array index or object key, and trace references to `__webpack_require__(target_id)`.

### Source Maps Recovery
Check the end of bundled `.js` files for:
```text
//# sourceMappingURL=bundle.js.map
```
Or an inline base64 string:
```text
//# sourceMappingURL=data:application/json;charset=utf-8;base64,...
```
If a `.map` file exists, use tools like `source-map-unpack` or `shuji` to regenerate the original, unminified source code directory tree.

### Electron & ASAR Archives
Electron desktop applications package JavaScript, HTML, and assets into an uncompressed archive `resources/app.asar`.
- **Extraction**:
  ```bash
  npx asar extract app.asar /tmp/extracted_app
  ```
- **REA Inspection**:
  - `analyze_javascript_application` directly analyzes an ASAR or extracted folder, reporting module graphs, dependencies, and findings.
  - `inspect_electron_fuses`: Checks Electron executable fuses (e.g., `EnableNodeCliInspectArguments` - if disabled, passing `--inspect` on launch is ignored).

---

## 3. AST Deobfuscation with Babel

Obfuscated JavaScript frequently uses string array proxies, control flow flattening, and computed property names.

### Deobfuscation Pipeline
Use `@babel/parser`, `@babel/traverse`, and `@babel/generator`:
1. **Extract and Evaluate String Array**: Locate the string array function (usually at the top of the bundle) and its shuffle/rotation routine. Execute it in a sandbox to recover the string lookup function.
2. **Replace Call Expressions**: Traverse the AST and replace calls to the lookup function `_0xabc(12)` with literal string nodes (`t.stringLiteral("target_string")`).
3. **Constant Folding & Dead Code Elimination**: Evaluate binary expressions with literal operands (`10 * 2` -> `20`, `"a" + "b"` -> `"ab"`), eliminate `if (false)` blocks.
4. **Member Expression Normalization**: Simplify `window["localStorage"]["getItem"]` to `window.localStorage.getItem`.

---

## 4. WebAssembly (WASM)

### Format & Signatures
- **Magic**: `\0asm` (`0x00 0x61 0x73 0x6D`).
- **Version**: `0x01 0x00 0x00 0x00` (Version 1).
- **Binary Sections**:
  - ID `1`: Type section (function signatures).
  - ID `2`: Import section (functions, tables, memories imported from JS host).
  - ID `3`: Function section (type signature indices).
  - ID `6`: Global section.
  - ID `7`: Export section (functions, memory exported to JS host).
  - ID `10`: Code section (function bodies containing stack bytecode).
  - ID `11`: Data section (static initial memory segment).

### Disassembly & Inspection
- **WABT CLI Tools**:
  ```bash
  # Disassemble binary WASM to WebAssembly Text format (WAT)
  wasm2wat module.wasm -o module.wat
  # Inspect section headers
  wasm-objdump -h module.wasm
  # Disassemble specific function with offsets
  wasm-objdump -d module.wasm
  ```
- **REA MCP**: `inspect_wasm_artifact` validates WASM binaries, extracts sections, exports/imports, and generates WAT without external tooling.

### JS-WASM Interface Boundary
In JavaScript host code or loader scripts, WASM modules are instantiated via `WebAssembly.instantiate(buffer, importObject)` or `WebAssembly.instantiateStreaming(source, importObject)`:
- **Imports**: The `importObject` specifies host JavaScript functions, memory objects, and global variables imported by WASM bytecode.
- **Exports**: The resolved `instance.exports` exposes callable WASM functions and exported memory buffers (`exports.memory.buffer`) back to JavaScript.
- Inspect the loader script to identify how parameters are serialized into WASM linear memory before invocation.
