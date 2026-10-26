# ffi-uniffi-swift-kotlin

> Evaluate UniFFI for representable Rust APIs consumed by Swift or Kotlin, with explicit lifecycle, threading, async, and error contracts.

## Why It Matters

Handwritten C ABI/JNI bridges require explicit pointer ownership, marshalling, panic containment, error mapping, and lifecycle coordination. UniFFI can generate Swift and Kotlin bindings for supported Rust types and reduce this boilerplate. It does not make arbitrary Rust APIs representable or automatically prove memory safety, thread safety, cancellation, executor behavior, or semantic compatibility; review generated scaffolding and the boundary contract.

## Bad

```rust
// Fragile manual C ABI exports for mobile integration
#[no_mangle]
pub unsafe extern "C" fn auth_client_login(
    client_ptr: *mut c_void,
    username: *const c_char,
    out_token: *mut *mut c_char,
) -> i32 {
    // Risk 1: Panicking here causes UB across the C boundary
    // Risk 2: Manual pointer dereferences with no lifetime or null checks
    // Risk 3: Swift/Kotlin must remember to call a custom free function for out_token
    // Risk 4: No native Swift/Kotlin error types or async support
    todo!()
}
```

## Good

When the repository's pinned UniFFI version supports the required surface, its established integration mode can generate reviewed bindings from Rust types:

```rust
use std::sync::Arc;

uniffi::setup_scaffolding!();

#[derive(Debug, thiserror::Error, uniffi::Error)]
pub enum AuthError {
    #[error("Network failure: {reason}")]
    Network { reason: String },
    #[error("Invalid credentials")]
    InvalidCredentials,
}

#[derive(Debug, Clone, uniffi::Record)]
pub struct UserProfile {
    pub id: u64,
    pub username: String,
    pub email: String,
}

#[derive(uniffi::Object)]
pub struct AuthClient {
    base_url: String,
}

#[uniffi::export]
impl AuthClient {
    #[uniffi::constructor]
    pub fn new(base_url: String) -> Arc<Self> {
        Arc::new(Self { base_url })
    }

    /// Verify how the repository's pinned UniFFI version maps this async method
    /// to Swift and Kotlin, including cancellation and executor behavior.
    pub async fn login(&self, username: String, token: String) -> Result<UserProfile, AuthError> {
        if token.is_empty() {
            return Err(AuthError::InvalidCredentials);
        }

        // Perform authentication...
        Ok(UserProfile {
            id: 101,
            username,
            email: "user@example.com".to_string(),
        })
    }
}
```

## Generated Client Experience

### Swift (iOS / macOS)
```swift
let client = AuthClient(baseUrl: "https://api.example.com")
do {
    let profile = try await client.login(username: "alice", token: "secret_tok")
    print("Welcome \(profile.username), email: \(profile.email)")
} catch AuthError.InvalidCredentials {
    print("Authentication failed")
}
```

### Kotlin (Android / JVM)
```kotlin
val client = AuthClient("https://api.example.com")
try {
    val profile = client.login("alice", "secret_tok") // Coroutine suspend call
    println("Welcome ${profile.username}, email: ${profile.email}")
} catch (e: AuthException.InvalidCredentials) {
    println("Authentication failed")
}
```

## When to Use UniFFI vs Other Boundaries

| Requirement | Candidate | Verify before choosing |
|-------------|-----------|------------------------|
| **Supported Rust API consumed by Swift/Kotlin** | `UniFFI` | supported type surface, generated API, threading, errors, async/cancellation |
| **Existing C/C++ ABI** | narrow C ABI or `cxx` where applicable | ownership, panic/exception containment, layout and toolchain |
| **Runtime-specific extension** | established project binding technology | runtime lifecycle, packaging, and maintenance support |

## Key Points

- Use the UniFFI integration mode already established by the repository and its pinned version; do not assume a particular macro or generated-name surface.
- Keep exported records, enums, objects, callbacks, errors, and async functions within the version's supported interface model.
- Define ownership, thread affinity, cancellation, executor interaction, and error translation explicitly; generated bindings do not remove these design obligations.
- Never let raw pointers escape when a reviewed high-level binding accurately represents the contract; use a narrow C ABI only when required.

## See Also

- [unsafe-extern-block](unsafe-extern-block.md) - safe and unsafe extern blocks for low-level C ABI
- [type-repr-transparent](type-repr-transparent.md) - use `#[repr(transparent)]` for FFI wrappers
- [err-thiserror-lib](err-thiserror-lib.md) - structured error types with thiserror
- [type-enum-states](type-enum-states.md) - strongly typed enums across boundaries
