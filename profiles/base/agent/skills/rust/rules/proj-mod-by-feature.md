# proj-mod-by-feature

> Organize modules by cohesive feature or subsystem, not technical layer

## Why It Matters

Feature-based and subsystem-based organization groups related types, logic, and persistence together within a cohesive module. Layer-based organization (dumping all handlers into one directory, all models into another, all services into a third) scatters cohesive concepts across the repository, making changes ripple through multiple folders and obscuring domain boundaries.

## Bad: Layered / Type-Based Sprawl

```text
src/
├── controllers/
│   ├── user_controller.rs
│   ├── order_controller.rs
│   └── product_controller.rs
├── models/
│   ├── user.rs
│   ├── order.rs
│   └── product.rs
├── services/
│   ├── user_service.rs
│   ├── order_service.rs
│   └── product_service.rs
└── repositories/
    ├── user_repository.rs
    ├── order_repository.rs
    └── product_repository.rs
```

## Good: Feature-Based Cohesive Modules

```text
src/
├── user/                # Feature directory module
│   ├── mod.rs           # Encapsulation boundary and public re-exports
│   ├── model.rs         # Domain entities and validation
│   ├── repository.rs    # Database operations
│   ├── service.rs       # Business logic
│   └── handler.rs       # Transport / HTTP handlers
├── order/               # Feature directory module
│   ├── mod.rs
│   ├── model.rs
│   ├── repository.rs
│   ├── service.rs
│   └── handler.rs
├── config.rs            # Single-concept module stays flat
├── error.rs             # Common crate errors
└── lib.rs
```

## Benefits

| Aspect | Layer-Based | Feature-Based |
|---|---|---|
| Finding code | Search across disjoint folders | One directory per feature |
| Adding a feature | Touch multiple folder trees | Create or extend one cohesive module |
| Understanding a concept | Jump across distant layers | All related logic is co-located |
| Deleting / refactoring | Hunt across codebase | Localized to feature directory |
| Encapsulation | Everything must be public to reach across layers | Internal helpers stay private or `pub(super)` |

## Module Boundary and Re-exports

The feature root (`mod.rs`) acts as a stable facade, re-exporting the primary API while keeping child submodules private:

```rust
// src/user/mod.rs
mod handler;
mod model;
mod repository;
mod service;

// Stable public exports
pub use handler::router;
pub use model::{CreateUserRequest, User, UserId};

// Crate-internal shared service
pub(crate) use service::UserService;
```

## Cross-Cutting Concerns

Shared utilities and cross-cutting infrastructure can live in a dedicated `shared/` directory module or top-level single files:

```text
src/
├── user/
├── order/
├── shared/              # Cross-cutting concerns
│   ├── mod.rs
│   ├── database.rs      # Connection pool
│   ├── error.rs         # Common error types
│   └── middleware.rs    # Auth, logging
└── lib.rs
```

## Single-Concept Modules Stay Flat

A feature or utility that represents a single cohesive concept does not need a folder hierarchy:

```text
src/
├── user/
│   ├── mod.rs
│   ├── model.rs
│   └── repository.rs
├── config.rs            # Cohesive single concept -> single file
├── telemetry.rs         # Cohesive single concept -> single file
└── lib.rs
```

## See Also

- [proj-mod-rs-dir](./proj-mod-rs-dir.md) - Structure multi-file modules with `mod.rs`
- [proj-flat-small](./proj-flat-small.md) - Single-file modules for single concepts
- [proj-pub-use-reexport](./proj-pub-use-reexport.md) - Clean public API facades
- [proj-lib-main-split](./proj-lib-main-split.md) - Lib/main separation
