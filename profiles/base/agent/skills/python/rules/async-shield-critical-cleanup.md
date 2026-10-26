# async-shield-critical-cleanup

> Give essential cleanup explicit task ownership; use `shield` only when caller cancellation must not cancel that owned task.

## Why It Matters

When a caller is cancelled, `asyncio.shield()` prevents cancellation from being forwarded to the inner task, but the outer await still raises `CancelledError`. Retain a strong task reference and decide who supervises completion; do not claim that `shield` makes rollback complete before the cancelled caller exits.

## Bad

```python
import asyncio

# Bad: If cancellation occurs during rollback, state is left corrupted
async def transfer_funds(tx):
    try:
        await tx.execute()
    except asyncio.CancelledError:
        # If cancelled here, rollback is aborted midway!
        await tx.rollback()
        raise
```

## Good

```python
import asyncio

async def transfer_funds(tx, rollback_tasks: set[asyncio.Task[None]]):
    try:
        await tx.execute()
    except asyncio.CancelledError:
        rollback = asyncio.create_task(tx.rollback())
        rollback_tasks.add(rollback)  # Longer-lived owner retains the task.
        rollback.add_done_callback(rollback_tasks.discard)
        try:
            await asyncio.shield(rollback)
        except asyncio.CancelledError:
            # Caller cancellation propagates; rollback continues under its owner.
            pass
        raise
```

## See Also

- [async-taskgroups-cancellation](async-taskgroups-cancellation.md) - TaskGroup cancellation semantics
- [err-context-managers](err-context-managers.md) - Context managers for cleanup
