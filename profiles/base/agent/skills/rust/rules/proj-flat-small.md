# proj-flat-small

> Keep single-concept modules flat in src/ without artificial directory layers

## Why It Matters

Over-organizing code with premature directory hierarchies, empty `mod.rs` files, and single-file folders adds cognitive overhead and navigation friction. Rust modules should be organized around cohesive domain concepts, not speculative architectural layers.

Start flat: let each cohesive concept live in a single file in `src/`. Promote a concept to a directory module (`foo/mod.rs`) only when that specific concept expands into multiple production sub-responsibilities or requires a dedicated unit-test file (`tests.rs`).

## Bad: Premature Layering and One-File Directories

```text
src/
├── core/
│   └── mod.rs           # Pure passthrough re-export
├── domain/
│   ├── mod.rs
│   └── models/
│       ├── mod.rs       # Single-file directory wrapper
│       └── user.rs
├── infrastructure/
│   ├── mod.rs
│   └── database/
│       ├── mod.rs
│       └── connection.rs
└── main.rs
```

## Bad: Prefixed Flat Fan-Out

```text
src/
├── config.rs
├── user_model.rs        # Flat sprawl with artificial name prefixes
├── user_repository.rs
├── user_service.rs
└── lib.rs
```

## Good: Flat Single Concepts, Directory Modules When Cohesion Warrants

```text
src/
├── config.rs            # Single cohesive concept: stays flat
├── database.rs          # Single cohesive concept: stays flat
├── error.rs             # Common error types: stays flat
├── user/                # Multi-responsibility concept: directory module
│   ├── mod.rs           # Boundary facade and re-exports
│   ├── model.rs         # User types and validation
│   ├── repository.rs    # Persistence operations
│   └── service.rs       # Business logic
├── lib.rs
└── main.rs
```

## Cohesion-Based Evolution

Rather than counting files or lines, evolve structure as responsibilities change:

### Stage 1: Single Cohesive Concepts in `src/`

Every distinct concept starts as a single file containing its data types, implementation, and inline unit tests:

```text
src/
├── main.rs
├── lib.rs
├── config.rs
├── database.rs
├── order.rs
└── user.rs
```

### Stage 2: Cohesion-Driven Promotion to Directory Module

When a concept divides into multiple sub-responsibilities (e.g. `order` expands to include distinct modeling, state machine, and discount logic) or needs a separate `tests.rs` file, convert that specific module into a directory module with `mod.rs`:

```text
src/
├── main.rs
├── lib.rs
├── config.rs            # Still a single concept -> stays single file
├── database.rs          # Still a single concept -> stays single file
├── user.rs              # Still a single concept -> stays single file
└── order/               # Multi-responsibility concept -> directory module
    ├── mod.rs           # Module boundary and re-exports
    ├── model.rs         # Order entities
    ├── state.rs         # Order state machine
    └── discount.rs      # Calculation rules
```

**Never coexist `order.rs` and `order/`.** The module root is `order/mod.rs`.

## Signs You Need a Directory Module

- A concept splits into distinct collaborator sub-responsibilities (e.g., separating lexer, parser, and AST).
- You find yourself adding module prefixes to flat files (`order_model.rs`, `order_state.rs`).
- Unit tests for the module grow extensive enough to warrant a separate `tests.rs` file within the module.

## Signs of Over-Structuring

- Directories containing only a single `mod.rs` with no sibling submodules.
- `mod.rs` files that only re-export a single child file without adding boundary value.
- Deep nesting for simple concepts (e.g., `src/domain/user/services/impl/user_service.rs`).
- Abstract layers (`core/`, `domain/`, `infrastructure/`) created before distinct modules exist.

## See Also

- [proj-mod-rs-dir](./proj-mod-rs-dir.md) - Structure multi-file modules with `mod.rs`
- [proj-mod-by-feature](./proj-mod-by-feature.md) - Feature-based module organization
- [proj-pub-use-reexport](./proj-pub-use-reexport.md) - Clean boundary re-exports
- [proj-lib-main-split](./proj-lib-main-split.md) - Library and binary split
