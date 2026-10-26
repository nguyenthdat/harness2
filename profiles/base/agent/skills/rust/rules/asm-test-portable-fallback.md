# asm-test-portable-fallback

> For an architecture-specific optimization, keep a portable reference path when supported targets or testing require one, and compare both implementations over bounded high-value cases.

## Why It Matters

Target-specific assembly can break cross-compilation and hide edge-case errors. A safe reference implementation is valuable when the crate promises multiple targets or needs differential verification. It is not mandatory for code whose explicit platform contract requires the instruction path, and Miri does not execute inline assembly or prove assembly correctness. Choose CI targets, emulation, property-test counts, and sanitizers from the risk and available infrastructure rather than prescribing millions of cases.

## Architecture Pattern

Structure target-optimized code with a clean facade and internal portable/optimized modules:

```rust
// In src/crypto/fast_crc32.rs

pub fn crc32(data: &[u8]) -> u32 {
    #[cfg(target_arch = "x86_64")]
    {
        if is_x86_feature_detected!("sse4.2") {
            // SAFETY: Verified SSE4.2 hardware support at runtime
            return unsafe { x86_64::crc32_sse42(data) };
        }
    }

    #[cfg(target_arch = "aarch64")]
    {
        if std::arch::is_aarch64_feature_detected!("crc") {
            // SAFETY: Verified ARM CRC hardware extension at runtime
            return unsafe { aarch64::crc32_arm(data) };
        }
    }

    // Default universal safe fallback
    portable::crc32_portable(data)
}

pub(crate) mod portable {
    /// Pure safe Rust reference implementation of CRC32.
    pub fn crc32_portable(data: &[u8]) -> u32 {
        let mut crc = !0u32;
        for &b in data {
            crc = (crc >> 8) ^ TABLE[((crc ^ b as u32) & 0xFF) as usize];
        }
        !crc
    }

    const TABLE: [u32; 256] = { /* const table */ [0; 256] };
}

#[cfg(target_arch = "x86_64")]
pub(crate) mod x86_64 {
    use core::arch::asm;

    /// # Safety
    /// Caller must guarantee SSE4.2 is supported by the CPU.
    pub unsafe fn crc32_sse42(data: &[u8]) -> u32 {
        let mut crc = !0u32;
        let mut ptr = data.as_ptr();
        let mut len = data.len();

        // SAFETY: asm loop reads data within bounds, leaves registers clean
        while len >= 8 {
            unsafe {
                asm!(
                    "crc32q ({ptr}), {crc}",
                    ptr = inout(reg) ptr,
                    crc = inout(reg) crc,
                    options(nostack, readonly),
                );
            }
            len -= 8;
        }
        // ... process trailing bytes with portable logic ...
        !crc
    }
}
```

## Differential Testing with Proptest

Always write differential test suites in `tests/` that verify equivalence between optimized assembly paths and the safe portable fallback across edge cases:

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    // Test specific known edge cases
    #[test]
    fn test_edge_cases() {
        let empty: &[u8] = &[];
        assert_eq!(crc32(empty), portable::crc32_portable(empty));

        let small = [0x42; 7];
        assert_eq!(crc32(&small), portable::crc32_portable(&small));

        let unaligned = [0xFF; 127];
        assert_eq!(crc32(&unaligned), portable::crc32_portable(&unaligned));
    }

    // Randomized differential property tests comparing implementations
    proptest! {
        #[test]
        fn test_assembly_matches_portable(data in proptest::collection::vec(any::<u8>(), 0..4096)) {
            let actual = crc32(&data);
            let expected = portable::crc32_portable(&data);
            prop_assert_eq!(actual, expected, "Assembly optimization deviated from portable reference");
        }
    }
}
```

## Key Points

- Provide a portable path when the supported-target contract or verification strategy requires it; otherwise declare the platform restriction explicitly.
- Use runtime feature detection or compile-time target features according to deployment guarantees.
- Compare optimized and reference implementations across deterministic edge cases and a bounded property corpus when the operation is amenable to it.
- Run architecture-specific code on suitable hardware or trusted emulation; use Miri only for executable Rust paths, not as evidence about skipped assembly.

## See Also

- [asm-inline-last-resort](asm-inline-last-resort.md) - inline assembly as a target-gated last resort
- [asm-operands-options-clobbers](asm-operands-options-clobbers.md) - specify exact operand directions and options
- [test-proptest-properties](test-proptest-properties.md) - property-based testing with proptest
- [unsafe-miri-ci](unsafe-miri-ci.md) - run cargo miri test in CI
