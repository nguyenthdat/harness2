# proj-mod-rs-dir

> Structure multi-file modules as a directory with mod.rs based on cohesion

## Why It Matters

Rust module structure should be driven by concept cohesion rather than arbitrary line or file-count thresholds. A cohesive domain concept begins life as a single file (`foo.rs`). When that concept expands and requires another production file for a distinct sub-responsibility or a separate unit-test file (`tests.rs`), convert it into a directory module with `mod.rs` (`foo/mod.rs`).

Never coexist `foo.rs` and a `foo/` directory for the same module. The `mod.rs` file acts as the explicit entry point, encapsulating child submodules and presenting a clean, selective boundary to the rest of the codebase.

## Cohesion-Based Conversion

| Concept State | File Layout | Module Declaration |
|---|---|---|
| Single cohesive concept | `src/foo.rs` | `mod foo;` (in `lib.rs` / `main.rs`) |
| Multi-file concept (multiple production sub-responsibilities) | `src/foo/mod.rs`<br>`src/foo/bar.rs`<br>`src/foo/baz.rs` | `mod foo;` (in `lib.rs` / `main.rs`) |
| Concept with separate unit-test file | `src/foo/mod.rs`<br>`src/foo/tests.rs` | `mod foo;` (in `lib.rs` / `main.rs`) |

### When to Convert to a Directory Module

- **Trigger**: You are adding another production file focused on a distinct sub-responsibility of the concept (e.g., separating runtime, state, and types in an engine subsystem).
- **Trigger**: Unit tests have grown large enough to warrant a dedicated `tests.rs` file within the module directory.
- **Do NOT convert**: A single-concept module that fits naturally in a single file with inline unit tests (`src/config.rs`). Do not create a directory containing only a lonely `mod.rs`.

### Never Coexist `foo.rs` and `foo/`

```text
# Bad: Ambiguous, split module root
src/
├── engine.rs           # Module root outside folder
├── engine/
│   ├── api.rs
│   └── runtime.rs
└── lib.rs

# Good: Encapsulated directory module
src/
├── engine/
│   ├── mod.rs          # Clear module root and boundary facade
│   ├── api.rs
│   └── runtime.rs
└── lib.rs
```

## Directory Layout & Responsibility Child Names

Inside a directory module, give child files short, focused names reflecting their specific responsibility within the parent concept. Avoid repeating the parent module name as a prefix:

- Use `api.rs`, `runtime.rs`, `state.rs`, `types.rs` inside `engine/`, **not** `engine_api.rs`, `engine_runtime.rs`.
- Use `model.rs`, `repository.rs`, `service.rs` inside `user/`, **not** `user_model.rs`, `user_service.rs`.

### Example: Engine Layout (`api`, `runtime`, `state`, `types`)

```text
src/
├── engine/
│   ├── mod.rs          # Boundary facade, submodules, selective re-exports
│   ├── api.rs          # Public entry points and high-level interface
│   ├── runtime.rs      # Execution loop and runtime dispatch
│   ├── state.rs        # Engine state machine and lifecycle
│   ├── types.rs        # Core engine types and configuration
│   └── tests.rs        # Dedicated unit-test file (optional)
├── config.rs           # Single-concept module (stays single file)
├── error.rs            # Common error definitions
└── lib.rs              # Crate root: declares `mod engine; pub use engine::{Engine, EngineError};`
```

## Stable Boundary Re-exports and Visibility

`mod.rs` serves as a facade. It declares child submodules, keeps implementation details private, and selectively re-exports only what is intended for external use:

```rust
// src/lib.rs
mod engine;

// Crate-level facade: re-export only the primary types
pub use engine::{Engine, EngineError};
```

```rust
// src/engine/mod.rs

// 1. Declare child submodules (private by default)
mod api;
mod runtime;
mod state;
mod types;

#[cfg(test)]
mod tests;

// 2. Stable selective re-exports forming the module facade
pub use api::Engine;
pub use types::EngineError;

// 3. pub(crate) for crate-internal collaboration without public exposure
pub(crate) use types::EngineConfig;
```

### Visibility Rules

- **Private (default)**: Items defined in a child module are visible only within that child module and its own descendants. They are hidden from the parent module and sibling files.
- **`pub(super)`**: Exposes an item to the immediate parent module (`super`). Sibling submodules (e.g. `api.rs` accessing `runtime.rs` or `state.rs`) access it through the parent namespace (`super::runtime::Runtime`, `super::state::EngineState`).
- **`pub(crate)`**: Visible across the current crate, but hidden from external consumers of the library.
- **`pub`**: Deliberate public API surface exported to external consumers via re-exports.

```rust
// src/engine/state.rs

pub(super) struct EngineState {
    running: bool,
}

impl EngineState {
    pub(super) fn new() -> Self {
        Self { running: false }
    }

    pub(super) fn set_running(&mut self, val: bool) {
        self.running = val;
    }

    pub(super) fn is_running(&self) -> bool {
        self.running
    }
}
```

```rust
// src/engine/runtime.rs
use super::state::EngineState;
use super::types::{EngineConfig, EngineError};

pub(super) struct Runtime;

impl Runtime {
    pub(super) fn init(config: &EngineConfig) -> Result<Self, EngineError> {
        let _ = config;
        Ok(Self)
    }

    pub(super) fn execute(&self, state: &mut EngineState) -> Result<(), EngineError> {
        state.set_running(true);
        Ok(())
    }
}

// Private implementation helper: visible only within runtime.rs and its descendants
fn dispatch_internal() -> bool {
    true
}
```

```rust
// src/engine/api.rs
use super::runtime::Runtime;
use super::state::EngineState;
use super::types::{EngineConfig, EngineError};

/// High-level execution engine facade.
pub struct Engine {
    state: EngineState,
    runtime: Runtime,
}

impl Engine {
    pub fn new(config: EngineConfig) -> Result<Self, EngineError> {
        let state = EngineState::new();
        let runtime = Runtime::init(&config)?;
        Ok(Self { state, runtime })
    }

    pub fn step(&mut self) -> Result<(), EngineError> {
        self.runtime.execute(&mut self.state)
    }
}

impl Default for Engine {
    fn default() -> Self {
        Self::new(EngineConfig::default()).expect("default configuration is valid")
    }
}
```

## Testing Conventions

### 1. Inline Unit Tests

The default for unit testing is `#[cfg(test)] mod tests` at the bottom of the file under test, using `use super::*;` to access private items:

```rust
// src/engine/state.rs

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn state_transition_works() {
        let mut state = EngineState::new();
        state.set_running(true);
        assert!(state.is_running());
    }
}
```

### 2. Separate Unit-Test File (`tests.rs`)

When unit tests for a directory module become extensive, separate them into `tests.rs` inside the module folder:

```text
src/engine/
├── mod.rs
├── api.rs
├── runtime.rs
├── state.rs
├── types.rs
└── tests.rs            # Neutral name; never engine_tests.rs
```

```rust
// src/engine/mod.rs
#[cfg(test)]
mod tests;
```

```rust
// src/engine/tests.rs
use super::*;
use super::types::EngineConfig;

#[test]
fn engine_pipeline_smoke_test() {
    let config = EngineConfig::default();
    let mut engine = Engine::new(config).unwrap();
    assert!(engine.step().is_ok());
}
```

### 3. Integration Tests (`tests/` directory)

Place end-to-end integration tests in the crate-root `tests/` directory. Integration tests compile as separate external crates and interact strictly with the public API facade:

```text
my_crate/
├── src/
│   ├── engine/
│   │   └── mod.rs
│   └── lib.rs
└── tests/
    └── engine_integration.rs   # External black-box integration test
```

```rust
// tests/engine_integration.rs
use my_crate::{Engine, EngineError};

#[test]
fn runs_engine_integration_test() {
    let mut engine = Engine::default();
    assert_eq!(engine.step(), Ok(()));
}
```

### 4. Doctests

Place doctests in `///` doc comments on public items (`functions`, `structs`, `traits`). They serve as verified, executable examples of the public API:

```rust
// src/engine/api.rs

/// High-level execution engine facade.
///
/// # Examples
///
/// ```
/// use my_crate::Engine;
///
/// let mut engine = Engine::default();
/// assert!(engine.step().is_ok());
/// ```
pub struct Engine;
```

## Scope Boundaries & Non-Triggers

- **Single-file modules**: Do not create a directory and `mod.rs` for a single concept that fits cleanly in one `.rs` file.
- **Cargo Workspaces**: Workspaces are for multiple distinct crates with independent publication or distinct compilation units; do not split internal modules into separate workspace crates without an architectural packaging need.
- **No arbitrary thresholds**: Never split or group modules based on arbitrary line counts (e.g. 300 lines) or file counts. Base structure solely on cohesive responsibilities.

## Enforcing with Clippy

To enforce the `mod.rs` layout style across the codebase via Clippy:

```toml
# Cargo.toml
[lints.clippy]
self_named_module_files = "warn"
```

## See Also

- [proj-flat-small](./proj-flat-small.md) - Single-file modules for single concepts
- [proj-mod-by-feature](./proj-mod-by-feature.md) - Feature-based module grouping
- [proj-pub-use-reexport](./proj-pub-use-reexport.md) - Boundary re-export patterns
- [proj-pub-crate-internal](./proj-pub-crate-internal.md) - Crate-internal visibility
- [proj-pub-super-parent](./proj-pub-super-parent.md) - Parent-only visibility
- [test-cfg-test-module](./test-cfg-test-module.md) - Unit test module structure
- [test-integration-dir](./test-integration-dir.md) - Integration tests in `tests/`
- [test-doctest-examples](./test-doctest-examples.md) - Executable doc tests
