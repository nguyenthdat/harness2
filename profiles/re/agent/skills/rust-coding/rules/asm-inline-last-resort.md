# asm-inline-last-resort

> Treat `asm!`, `global_asm!`, and `naked_asm!` as a last resort: gate strictly by target architecture and document comprehensive safety contracts.

## Why It Matters

Inline assembly (`core::arch::asm!`, `core::arch::global_asm!`, `core::arch::naked_asm!`) bypasses Rust's type system, borrow checker, and compiler code generator. Writing incorrect assembly introduces immediate undefined behavior: register corruption, stack misalignment, memory clobber violations, cache incoherency, or CPU instruction faults on unsupported hardware.

Inline assembly should only be used when:
1. No compiler intrinsic (`core::arch::x86_64::*`, `core::arch::aarch64::*`), portable SIMD, or standard library abstraction exists for the operation.
2. Low-level hardware control is required (e.g., custom context switching, system control registers, hypervisor calls, or hardware cycle counters like `rdtsc`/`cntvct_el0`).
3. An extreme hot-path micro-optimization yields measurable, benchmark-proven speedups that LLVM cannot generate.

Whenever inline assembly is used, it must be guarded by strict `#[cfg(target_arch = "...")]` gates, accompanied by a verified `# Safety` contract and `// SAFETY:` inline justification, and paired with a safe portable fallback (see `asm-test-portable-fallback`).

## Bad

```rust
// BAD: No architecture gating (fails to compile on non-x86_64)
// BAD: No safety comment explaining register and CPU requirements
// BAD: Unsafe function with no # Safety doc contract
pub unsafe fn read_cycle_counter() -> u64 {
    let low: u32;
    let high: u32;
    core::arch::asm!(
        "rdtsc",
        out("eax") low,
        out("edx") high,
    );
    ((high as u64) << 32) | (low as u64)
}
```

## Good

```rust
#[cfg(target_arch = "x86_64")]
use core::arch::asm;

/// Reads the current value of the processor's time-stamp counter (TSC).
///
/// # Safety
///
/// - The host CPU must support the `rdtsc` instruction (guaranteed on all standard `x86_64` targets).
/// - Caller must account for out-of-order execution if strict cycle ordering is required
///   (e.g., pairing with `lfence` or using `rdtscp`).
#[inline(always)]
#[cfg(target_arch = "x86_64")]
pub unsafe fn read_tsc() -> u64 {
    let low: u32;
    let high: u32;

    // SAFETY:
    // 1. `rdtsc` is supported on x86_64 and takes no input operands.
    // 2. Output registers `eax` (low 32-bits) and `edx` (high 32-bits) are accurately specified.
    // 3. `nomem` option asserts that rdtsc does not read or write arbitrary memory.
    // 4. `nostack` option asserts that the instruction does not push/pop the stack pointer.
    unsafe {
        asm!(
            "rdtsc",
            out("eax") low,
            out("edx") high,
            options(nomem, nostack, preserves_flags)
        );
    }

    ((high as u64) << 32) | (low as u64)
}

/// AArch64 hardware cycle counter implementation
#[inline(always)]
#[cfg(target_arch = "aarch64")]
pub unsafe fn read_tsc() -> u64 {
    let count: u64;

    // SAFETY:
    // 1. `cntvct_el0` is standard virtual timer counter register on AArch64.
    // 2. Output register is bound to a 64-bit general-purpose register.
    // 3. `nomem` and `nostack` options accurately describe register-only read.
    unsafe {
        core::arch::asm!(
            "mrs {0}, cntvct_el0",
            out(reg) count,
            options(nomem, nostack, preserves_flags)
        );
    }

    count
}
```

## Hierarchy of Low-Level Primitives

Before reaching for raw assembly, exhaust alternatives in order of preference:

1. **Standard Safe Rust**: High-level algorithms, iterators, `core::sync::atomic`.
2. **Standard Intrinsics**: `core::arch::x86_64::*`, `core::arch::aarch64::*` (standardized intrinsics verified by LLVM).
3. **Portable/vector abstractions**: stable intrinsics or a repository-approved crate supported by target toolchains; verify `std::simd` availability before use.
4. **Target-Gated Inline Assembly (`asm!`)**: Unavoidable hardware/register manipulation with strict safety comments.

## Key Points

- Never leave inline assembly un-gated; always specify `#[cfg(target_arch = "...")]`.
- Provide a safe portable fallback for non-supported architectures (see `asm-test-portable-fallback`).
- Always write a `# Safety` section on the containing `unsafe fn` and an inline `// SAFETY:` block detailing invariant validity.
- Use `options(...)` flags (`nomem`, `nostack`, `preserves_flags`, `pure`, `readonly`) to allow compiler optimization and prevent LLVM miscompilations.

## See Also

- [asm-operands-options-clobbers](asm-operands-options-clobbers.md) - specify exact operand directions and options
- [asm-test-portable-fallback](asm-test-portable-fallback.md) - provide safe portable fallback and differential tests
- [unsafe-safety-comment](unsafe-safety-comment.md) - require safety comments on all unsafe code
- [opt-simd-portable](opt-simd-portable.md) - use portable SIMD before raw architecture assembly
