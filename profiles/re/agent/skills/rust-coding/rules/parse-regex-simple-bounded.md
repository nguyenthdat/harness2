# parse-regex-simple-bounded

> Restrict regular expressions to simple, flat lexical patterns with input length bounds and compile-time or one-time initialization.

## Why It Matters

Regular expressions are powerful for flat lexical matching (e.g. validating token formats, hex hashes, or simple identifier patterns), but they are frequently abused for recursive or nested syntax (HTML, XML, JSON, math expressions) where they fail on edge cases and cause subtle bugs.

Furthermore, executing unbounded regexes against arbitrary user inputs can cause severe CPU exhaustion or algorithmic complexity denial of service (ReDoS), and recompiling `Regex::new(...)` on every invocation in a hot path introduces massive CPU and allocation overhead.

When regex is appropriate:
1. **Scope to flat patterns only**: Use regex strictly for non-nested lexical checks (e.g., alphanumeric slugs, SHA-256 hashes, ISO-8601 dates).
2. **Compile once**: Initialize regexes once using `std::sync::LazyLock` (stable since Rust 1.80 / Rust 2024) instead of compiling per call.
3. **Bound input lengths**: Enforce a maximum input byte/char length *before* executing the regex engine.
4. **Anchor patterns**: Use `^` and `$` (or `\A` and `\z`) to avoid unintended substring matches.

## Bad

```rust
use regex::Regex;

// BAD: Recompiles regex on every function call in a hot path
// BAD: No input length check (vulnerable to resource exhaustion on multi-megabyte strings)
// BAD: Unanchored regex matches substring anywhere
fn is_valid_username_bad(input: &str) -> bool {
    let re = Regex::new(r"[a-z0-9_]+").unwrap(); // Compiles every call!
    re.is_match(input) // Matches even if input is "invalid###username!!!"
}

// BAD: Using regex to parse nested structured documents
fn extract_html_tags(html: &str) -> Vec<String> {
    let re = Regex::new(r"<div class='content'>(.*?)</div>").unwrap();
    // Breaks on nested <div>, attributes, newlines, comments
    todo!()
}
```

## Good

```rust
use std::sync::LazyLock;
use regex::Regex;

const MAX_USERNAME_LEN: usize = 64;

// One-time static compilation using standard library LazyLock
static USERNAME_REGEX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^[a-z0-9][a-z0-9_\-]{2,63}$").expect("valid username regex")
});

#[derive(Debug, PartialEq, Eq)]
pub struct ValidUsername(String);

#[derive(Debug, thiserror::Error)]
pub enum UsernameError {
    #[error("input exceeds maximum allowed length of {0} bytes")]
    TooLong(usize),
    #[error("username does not match required lexical format")]
    InvalidFormat,
}

impl ValidUsername {
    pub fn parse(input: &str) -> Result<Self, UsernameError> {
        // 1. Guard against unbounded input length before regex execution
        if input.len() > MAX_USERNAME_LEN {
            return Err(UsernameError::TooLong(MAX_USERNAME_LEN));
        }

        // 2. Perform anchored, precompiled regex match
        if !USERNAME_REGEX.is_match(input) {
            return Err(UsernameError::InvalidFormat);
        }

        Ok(Self(input.to_string()))
    }
}
```

## When to Avoid Regex

| Use Case | Why Avoid Regex | Recommended Alternative |
|----------|-----------------|-------------------------|
| **HTML / XML parsing** | Cannot handle nesting or arbitrary tag attributes | `scraper`, `quick-xml` |
| **JSON / YAML / TOML** | Escapes, multiline strings, nested objects | `serde_json`, `toml`, `serde_yaml` |
| **URLs & Query params** | RFC 3986 encoding, userinfo, ports, relative paths | `url::Url` |
| **Arithmetic / DSLs** | Precedence, parenthesized expressions | `pest` (PEG grammar) |
| **Simple prefix/suffix** | Regex overhead for constant string matching | `str::starts_with`, `str::strip_prefix` |

## Key Points

- Always use `std::sync::LazyLock` (or `once_cell::sync::Lazy` on older MSRVs) to initialize `Regex` statics.
- Check input length (`input.len() <= MAX_ALLOWED`) before invoking regex match methods on untrusted input.
- Anchor patterns with `^` and `$` to validate whole strings rather than partial substrings.
- For structured formats, prefer standard parsers (`serde_json`, `url`) or `pest` before resorting to regex.

## See Also

- [parse-standard-format-first](parse-standard-format-first.md) - use standard format parsers first
- [parse-pest-custom-grammar](parse-pest-custom-grammar.md) - use pest for non-trivial grammars
- [type-newtype-validated](type-newtype-validated.md) - encapsulate validated strings in newtypes
- [api-parse-dont-validate](api-parse-dont-validate.md) - parse into types at boundaries
