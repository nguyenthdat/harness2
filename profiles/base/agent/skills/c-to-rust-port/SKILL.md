---
name: c-to-rust-port
description: Use before writing Rust for a C-to-Rust transpilation task (numerical or algorithmic library, math functions, data structures). Carries interface contract rules, verification evidence, and traps.
---

# C to safe Rust port

## The contract

- `src/<module>.rs` (the provided scaffold) is authoritative: implement every `pub fn` with its exact name, parameter types, return types and constants. Leave no `unimplemented!()`/`todo!()`.
- `src/lib.rs` keeps `pub mod <module>;` and `#![forbid(unsafe_code)]`; no FFI, pointer casts or `transmute`.
- No panic on the public API: watch debug-only overflow (`-i32::MIN`, `u64` multiply), out-of-range `as` casts, and unbounded loops.
- Header prototypes are part of the contract: ensure all declared C functions match the Rust public API.
- Leave `Cargo.toml` untouched; deliver `src/lib.rs` + `src/<module>.rs` only.

## Verification before finishing

1. Run `python3 scripts/check_interface.py --cargo-check` and require `RESULT: OK`. It diffs the header's prototypes against the `pub fn`s, checks that `src/lib.rs` declares the module, strips comments/strings before searching for `unsafe`, and fails on any `cargo check` warning or error.
2. Run `cargo test` (debug catches integer-overflow panics) and `cargo test --release`. Confirm the test count -- `0 passed` is not a pass.
3. Re-read `src/` top to bottom before declaring completion.

## Traps

- `as i64` saturates in Rust; C's cast is UB. Apply C's guard at `+/-2^63` first (`LLONG_MAX` converts to exactly `9_223_372_036_854_775_808.0`).
- `-i32::MIN` panics in debug Rust; use `wrapping_neg`.
- The NaN test is `x != x`; keep it where C uses it.
- `f64 % f64` is C `fmod`; divisor `0` gives NaN and the sign follows the dividend.
- Integer factorial overflows: `wrapping_mul` matches C's unsigned wrap and avoids a debug panic.
- Do not assume `long double` is wider than `f64`; check the host.
