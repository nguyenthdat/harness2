---
name: platform-language-defaults
description: Choose default implementation languages by platform when a new project is unconstrained; preserve established repository contracts.
---

# Platform Language Defaults

Use only when the repository and user have not selected a language or runtime.

- New portable native core, systems service, or performance-sensitive library: Rust.
- Automation, data transformation, and operational scripts: Python managed with uv.
- Web UI and browser-facing TypeScript: Bun for runtime/package/test/build where compatible.
- Android UI and Android platform integration: Kotlin.
- macOS and iOS UI/platform integration: Swift.
- Objective-C and C/C++: maintain existing code, ABI/platform integration, or a verified dependency constraint; do not choose them over Rust/Swift for an unconstrained new core or Apple UI.
- Preserve existing lockfiles, build systems, language boundaries, and deployment runtime. Never migrate solely to enforce these defaults.
- Cross-language Rust APIs consumed by Swift or Kotlin should use UniFFI when the API is representable and supported. Use a narrow reviewed C ABI only when UniFFI cannot meet the boundary.
- Internal native socket RPC should evaluate Cap'n Proto first when its supported implementations, capability model, and operational constraints fit. Prefer gRPC with Protobuf for interoperable service ecosystems; use JSON-RPC/OpenAPI for human/web compatibility or when existing contracts require them.