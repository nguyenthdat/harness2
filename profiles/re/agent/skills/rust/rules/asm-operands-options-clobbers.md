# asm-operands-options-clobbers

> Specify every `asm!` operand and only the options or ABI clobbers whose preconditions the instructions actually satisfy.

## Why It Matters

Rust's `core::arch::asm!` macro communicates directly with LLVM's register allocator and optimizer. If operand constraints, options, or clobbers are omitted or inaccurately declared, the compiler makes incorrect assumptions:
- Misdeclaring `nomem` when the assembly reads or writes memory causes LLVM to reorder memory operations across the assembly boundary, leading to data races and stale reads.
- Omitting `preserves_flags` forces LLVM to assume condition codes are clobbered, destroying optimization opportunities; falsely adding `preserves_flags` when flags *are* modified corrupts subsequent conditional branches.
- Calling external subroutines in assembly without `clobber_abi("C")` corrupts caller-saved registers that LLVM relies on.

Accurately specifying operand constraints (`in`, `out`, `inout`, `inlateout`), register classes (`reg`, `vreg`, explicit registers), `clobber_abi`, and `options(...)` ensures sound compilation and optimal code generation.

## Operand Directions and Register Classes

| Operand Constraint | Direction / Behavior | Best Used When |
|-------------------|----------------------|----------------|
| `in(reg) expr` | Read-only input | Passing arguments to assembly instructions |
| `out(reg) expr` | Write-only output | Capturing results computed by assembly |
| `inout(reg) expr` | Read-write in same register | Modifying a value in place |
| `inlateout(reg) expr` | Read input, then write output | Input is read before output is written; allows LLVM to reuse register |
| `sym path` | Symbol address | Referencing functions or static variables directly |
| `const expr` | Compile-time integer/string constant | Immediate operands in instruction syntax |

## Options Matrix

| Option Flag | Meaning / Compiler Guarantee | Soundness Precondition |
|-------------|------------------------------|------------------------|
| `nomem` | Assembly does not access memory | Block only operates on registers and passed operands |
| `readonly` | Assembly reads memory, never mutates | No stores to pointers or globals |
| `nostack` | Stack pointer (`rsp`/`sp`) is untouched | No `push`/`pop` or stack frame modifications |
| `preserves_flags` | CPU condition flags are preserved | No arithmetic/comparisons that alter flags register |
| `pure` | No side effects; output is pure function of inputs | Must combine with `nomem`; output used or elided |
| `noreturn` | Execution does not return from block | Halts execution or jumps to another non-returning target |

## Bad

```rust
// BAD: Missing options(nomem, nostack) forces compiler to assume memory/stack are touched
// BAD: Using inout when inlateout would let LLVM reuse registers
// BAD: Calling external function without clobber_abi corrupts caller-saved registers
unsafe fn bad_asm_call(ptr: *const u8) {
    core::arch::asm!(
        "call some_c_function",
        in("rdi") ptr,
        // Missing clobber_abi("C")! Caller-saved registers rax, rcx, rdx, r8-r11 are clobbered!
    );
}
```

## Good

```rust
#[cfg(target_arch = "x86_64")]
use core::arch::asm;

/// Sound atomic bit-test-and-set using precise register operands and flags management.
#[inline(always)]
#[cfg(target_arch = "x86_64")]
pub unsafe fn bit_test_and_set(ptr: *mut u64, bit: usize) -> bool {
    let old_bit: u8;

    // SAFETY:
    // 1. `ptr` is valid, non-null, and 8-byte aligned for atomic memory access.
    // 2. `lock bts` atomically sets the bit and stores old value in carry flag.
    // 3. `setc` reads carry flag into output byte register.
    // 4. Memory operand explicitly declared via `in(reg) ptr`.
    // 5. `nostack` declared because no stack instructions are used.
    // 6. `preserves_flags` is OMITTED because `bts` and `setc` deliberately modify flags.
    unsafe {
        asm!(
            "lock bts [{ptr}], {bit}",
            "setc {out}",
            ptr = in(reg) ptr,
            bit = in(reg) bit,
            out = out(reg_byte) old_bit,
            options(nostack),
        );
    }

    old_bit != 0
}

/// Invoking a C ABI function with full clobber declaration.
#[inline(always)]
#[cfg(target_arch = "x86_64")]
pub unsafe fn invoke_c_helper(arg: u64) -> u64 {
    let mut result: u64;

    // SAFETY:
    // 1. `helper_func` adheres to standard C calling convention.
    // 2. `clobber_abi("C")` informs LLVM to save/restore all caller-saved registers (rax, rcx, rdx, etc.).
    unsafe {
        asm!(
            "call helper_func",
            in("rdi") arg,
            lateout("rax") result,
            clobber_abi("C"),
        );
    }

    result
}
```

## Key Points

- Add `nostack`, `nomem`/`readonly`, `preserves_flags`, or other options only after verifying every instruction and call satisfies the declared contract; omission may reduce optimization but a false declaration is unsound.
- Use `clobber_abi` when assembly performs calls under that ABI and follow Rust's operand restrictions for explicit outputs.
- Prefer register classes over fixed registers unless the instruction or calling convention requires a particular register.
- Choose `inout`, `lateout`, or `inlateout` from actual value liveness; do not optimize constraints by preference.

## See Also

- [asm-inline-last-resort](asm-inline-last-resort.md) - inline assembly as a target-gated last resort
- [asm-test-portable-fallback](asm-test-portable-fallback.md) - safe portable fallback and differential tests
- [unsafe-safety-comment](unsafe-safety-comment.md) - write safety comments for every unsafe block
