# proj-pub-super-parent

> Use pub(super) for parent-module visibility and sibling submodule collaboration

## Why It Matters

`pub(super)` restricts item visibility to the immediate parent module (`super`). Items defined in a child file (like `lexer.rs` inside `parser/`) marked `pub(super)` are visible to the parent module (`parser/mod.rs`). Sibling submodules (like `ast.rs`) can then access them via the parent namespace (`super::lexer::...`), while the rest of the crate cannot see or depend on them.

This creates tight encapsulation within directory modules without leaking implementation details into the broader crate.

## Bad: Over-Exposing Internal Submodule Types to the Crate

```rust
// src/parser/mod.rs
pub mod lexer;
pub mod ast;

// src/parser/lexer.rs
pub fn internal_helper() {  // Visible to entire crate!
    // Helper only needed within parser directory module
}

pub(crate) struct Token {  // Visible to entire crate!
    // Only parser submodules need this
}
```

## Good: Scoped to Parent and Sibling Modules via `pub(super)`

```rust
// src/parser/mod.rs
mod ast;
mod lexer;

pub use ast::Ast;

// Sibling submodules access lexer types via super::lexer::Token
// Crate-external modules cannot access lexer or Token
```

```rust
// src/parser/lexer.rs
use super::ast::Span;

// Visible to parent `parser` module (and accessible to sibling `ast.rs` via super::lexer)
pub(super) struct Token {
    pub(super) kind: TokenKind,
    pub(super) span: Span,
}

pub(super) fn shared_helper() -> Token {
    Token { kind: TokenKind::Eof, span: Span::default() }
}

// Private implementation helper: visible only within lexer.rs
fn is_whitespace(c: char) -> bool {
    c.is_whitespace()
}
```

```rust
// src/parser/ast.rs
// Access sibling submodule's pub(super) item through parent-qualified path
use super::lexer::{shared_helper, Token};

pub struct Ast;

pub(super) fn parse_tokens(tokens: &[Token]) -> Ast {
    let _ = tokens;
    let _ = shared_helper();
    Ast
}
```

## Visibility Hierarchy

```text
src/
├── lib.rs           # Crate root
├── parser/
│   ├── mod.rs       # Parent module: pub(super) items in lexer.rs visible here
│   ├── lexer.rs     # Declares pub(super) items
│   └── ast.rs       # Accesses lexer items via super::lexer::...
└── codegen.rs       # CANNOT access parser's pub(super) internal items
```

## Pattern: Layered Visibility

```rust
// src/database/mod.rs
mod connection;
mod pool;
mod query;

// Only this module and its children can see
pub(super) struct RawConnection { /* ... */ }

// Entire crate can see
pub(crate) struct Pool { /* ... */ }

// External library consumers can see
pub struct Database { /* ... */ }
```

## Comparison of Rust Visibility Levels

| Visibility | Scope | Accessibility |
|---|---|---|
| `(private)` | Current module & descendants | Hidden from parent and siblings |
| `pub(super)` | Immediate parent module | Parent and siblings (via parent-qualified path `super::child::...`) |
| `pub(crate)` | Entire crate | Any module within the current crate |
| `pub(in path)` | Specific ancestor path | Modules within the specified ancestor tree |
| `pub` | Public API | Everywhere the declaring module path is accessible |

## When to Use pub(super)

- Helper functions and tokens shared between sibling files inside a directory module (`engine/`, `parser/`).
- Internal state machines or traits shared across child submodules without exposing them crate-wide.
- Test helpers located in sibling submodules within the same module tree.

## See Also

- [proj-mod-rs-dir](./proj-mod-rs-dir.md) - Structure multi-file modules with `mod.rs`
- [proj-pub-crate-internal](./proj-pub-crate-internal.md) - Crate visibility
- [proj-pub-use-reexport](./proj-pub-use-reexport.md) - Re-export patterns
- [proj-mod-by-feature](./proj-mod-by-feature.md) - Feature organization
