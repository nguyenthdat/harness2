# proj-pub-use-reexport

> Use pub use for stable module boundary facades and clean public APIs

## Why It Matters

`pub use` re-exports items from private submodules at module (`mod.rs`) and crate (`lib.rs`) boundaries. This provides a stable, ergonomic facade while keeping internal submodule organization flexible. Callers import from the boundary, allowing internal files to be refactored or moved without breaking consumer code.

## Bad: Exposing Raw Submodule Paths

```rust
// lib.rs - Deep internal module paths exposed
pub mod error;
pub mod config;
pub mod client;
pub mod types;

// Consumers must write:
use my_crate::error::MyError;
use my_crate::config::Config;
use my_crate::client::http::HttpClient;
use my_crate::types::request::Request;
```

## Good: Stable Boundary Facade

```rust
// lib.rs - Clean facade with selective re-exports
mod error;
mod config;
mod client;
mod types;

pub use client::http::HttpClient;
pub use config::Config;
pub use error::MyError;
pub use types::request::Request;

// Consumers write:
use my_crate::{Config, HttpClient, MyError, Request};
```

## Pattern: Directory Module Boundary Re-exports

In a multi-file directory module, `mod.rs` keeps child submodules private and selectively re-exports items meant for parent or external callers:

```rust
// src/engine/mod.rs
mod api;
mod runtime;
mod state;
mod types;

// Stable boundary: re-export primary facade items
pub use api::Engine;
pub use types::EngineError;

// Internal items (Runtime, EngineState) remain private to engine/ or pub(crate)
```

## Pattern: Selective Re-export

```rust
// src/lib.rs
mod internal;

// Only re-export what callers need
pub use internal::{
    PublicStruct,
    PublicTrait,
    public_function,
};

// Keep implementation details hidden:
// internal::helper_function is NOT exported
```

## Pattern: Rename on Re-export

```rust
mod v1 {
    pub struct Client { /* old implementation */ }
}

mod v2 {
    pub struct Client { /* new implementation */ }
}

// Re-export with clear names
pub use v2::Client;
pub use v1::Client as LegacyClient;
```

## Pattern: Prelude Module

```rust
// src/lib.rs
pub mod prelude {
    pub use crate::{
        Client,
        Config,
        Error,
        Request,
        Response,
    };
}

// Users can glob import common items
use my_crate::prelude::*;
```

## Pattern: Feature-Gated Re-exports

```rust
// src/lib.rs
mod core;
mod serde_impl;
mod async_impl;

pub use core::*;

#[cfg(feature = "serde")]
pub use serde_impl::*;

#[cfg(feature = "async")]
pub use async_impl::*;
```

## Comparison: Internal Structure vs Public API

```text
// Internal structure in src/
src/
├── transport/
│   ├── mod.rs
│   ├── http.rs          // HttpClient
│   └── grpc.rs          // GrpcClient
├── auth/
│   ├── mod.rs
│   └── token.rs         // Token
└── lib.rs
```

```rust
// Public API in lib.rs
pub use auth::Token;
pub use transport::{GrpcClient, HttpClient};

// Callers see a flat, clean surface:
// my_crate::HttpClient
// my_crate::GrpcClient
// my_crate::Token
```

## Re-export External Types

```rust
// Re-export dependencies users need to construct or interact with types
pub use bytes::Bytes;
pub use http::{Method, StatusCode};
```

## Glob Re-exports

Use sparingly:

```rust
// Acceptable for internal cohesive modules
pub use internal::*;

// Avoid for external crates - pollutes namespace and leaks dependencies
// pub use serde::*;
```

## See Also

- [proj-mod-rs-dir](./proj-mod-rs-dir.md) - Structure multi-file modules with `mod.rs`
- [proj-flat-small](./proj-flat-small.md) - Single-file modules for single concepts
- [proj-prelude-module](./proj-prelude-module.md) - Prelude pattern
- [proj-pub-crate-internal](./proj-pub-crate-internal.md) - Internal crate visibility
- [proj-pub-super-parent](./proj-pub-super-parent.md) - Parent-only visibility
- [api-non-exhaustive](./api-non-exhaustive.md) - API stability
