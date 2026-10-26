# type-enum-over-string-actions

> Model closed sets of tasks, API operations, action commands, and protocol events as typed enums with exhaustive matching and typed serialization.

## Why It Matters

Passing operations, actions, or event types as raw strings (`"create_order"`, `"refund_payment"`, `"restart_service"`) is an anti-pattern known as stringly-typed programming. Raw strings allow typos, case inconsistencies, and invalid actions to compile silently, shifting failure discovery from compile time to production runtime.

By modeling closed action sets as Rust enums:
1. **Compile-Time Exhaustiveness**: The compiler forces all `match` statements across your codebase to handle every variant. When a new action is added, compilation fails until every handler is updated.
2. **Associated Payloads**: Each action variant carries only the exact strongly-typed data fields it requires (e.g., `Action::Transfer { from: AccountId, to: AccountId, amount: u64 }`), eliminating nullable "grab-bag" payload structs.
3. **Safe Serialization**: With Serde, actions serialize and deserialize cleanly using structured tagging (`#[serde(rename_all = "snake_case")]`, `#[serde(tag = "action")]`), automatically rejecting invalid actions at API boundaries.

## Bad

```rust
// Stringly-typed action dispatcher: prone to typos, silent runtime fallthroughs
fn execute_task_bad(action: &str, payload: &serde_json::Value) -> Result<(), String> {
    match action {
        "start_job" => {
            let job_id = payload.get("job_id").and_then(|v| v.as_u64())
                .ok_or("missing job_id")?;
            // ...
            Ok(())
        }
        "cancel_job" => {
            let job_id = payload.get("job_id").and_then(|v| v.as_u64())
                .ok_or("missing job_id")?;
            let reason = payload.get("reason").and_then(|v| v.as_str())
                .unwrap_or("unspecified");
            // ...
            Ok(())
        }
        // Easy to miss new actions, typo strings ("start-job" vs "start_job"),
        // or fail at runtime
        _ => Err(format!("unrecognized action: {action}")),
    }
}
```

## Good

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "action", rename_all = "snake_case")]
pub enum TaskAction {
    StartJob {
        job_id: u64,
        priority: Priority,
    },
    CancelJob {
        job_id: u64,
        reason: String,
    },
    PauseJob {
        job_id: u64,
    },
    UpdateConfig {
        workers: u32,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Priority {
    Low,
    Normal,
    High,
}

/// Dispatch actions exhaustively. The compiler guarantees all variants are handled.
pub fn execute_task(action: TaskAction) -> Result<(), Box<dyn std::error::Error>> {
    match action {
        TaskAction::StartJob { job_id, priority } => {
            println!("Starting job {job_id} with priority {priority:?}");
            // Handle start logic with strongly typed fields
            Ok(())
        }
        TaskAction::CancelJob { job_id, reason } => {
            println!("Cancelling job {job_id} due to: {reason}");
            // Handle cancellation logic
            Ok(())
        }
        TaskAction::PauseJob { job_id } => {
            println!("Pausing job {job_id}");
            // Handle pause logic
            Ok(())
        }
        TaskAction::UpdateConfig { workers } => {
            println!("Updating worker count to {workers}");
            // Handle config logic
            Ok(())
        }
    }
}
```

## Serde JSON Representation

The `#[serde(tag = "action")]` attribute produces and accepts clean, idiomatic JSON payloads:

```json
{
  "action": "cancel_job",
  "job_id": 42,
  "reason": "user requested shutdown"
}
```

If an unknown action string is received at the boundary, Serde returns a descriptive error before execution reaches domain code:

```rust
let invalid_json = r#"{"action": "unknown_op", "job_id": 1}"#;
let res: Result<TaskAction, _> = serde_json::from_str(invalid_json);
assert!(res.is_err()); // "unknown variant `unknown_op`, expected one of `start_job`, `cancel_job`, `pause_job`, `update_config`"
```

## Key Points

- Use an enum for a closed operation set owned by the program. Preserve strings at intentionally open, user-defined, plugin, or forward-compatible boundaries and validate them there.
- Attach the payload required by each variant instead of a grab-bag record of optional fields.
- Avoid wildcard matches when executing an owned closed enum so additions surface at compile time.
- Choose Serde tagging from the wire contract; do not impose internally tagged snake_case JSON on an established protocol.
- For public library APIs intended for extension, evaluate `#[non_exhaustive]` and its downstream matching trade-off.

## See Also

- [type-no-stringly](type-no-stringly.md) - avoid stringly-typed APIs with newtypes and enums
- [type-enum-states](type-enum-states.md) - model mutually exclusive states with enums
- [pat-exhaustive-enum](pat-exhaustive-enum.md) - exhaustively match owned enums
- [serde-enum-representation](serde-enum-representation.md) - choose appropriate Serde enum wire tagging
