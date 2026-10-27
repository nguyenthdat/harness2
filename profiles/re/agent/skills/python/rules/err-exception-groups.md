# err-exception-groups

> Use `except*` (Python 3.11+) or `exceptiongroup` backport to handle concurrent failures in `ExceptionGroup`.

## Why It Matters

Concurrent tasks (e.g. in `asyncio.TaskGroup`) can fail simultaneously with multiple independent exceptions. A standard `except SpecificError:` cannot catch individual exceptions embedded in an `ExceptionGroup`, masking failures.

## Bad

```python
# Bad (Python 3.11+): Standard except cannot selectively unpack ExceptionGroup
import asyncio

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(step1())
            tg.create_task(step2())
    except ValueError:
        # Will NEVER catch ValueError if raised inside TaskGroup (it raises ExceptionGroup)!
        print("Caught value error")
```

## Good

```python
# Good (Python 3.11+): Use except* to handle sub-exceptions individually
import asyncio

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(step1())
            tg.create_task(step2())
    except* ValueError as eg:
        print(f"Handled ValueErrors: {eg.exceptions}")
    except* ConnectionError as eg:
        print(f"Handled ConnectionErrors: {eg.exceptions}")
```

## See Also

- [async-taskgroups-cancellation](async-taskgroups-cancellation.md) - TaskGroup cancellation semantics
- [proj-version-compatibility](proj-version-compatibility.md) - Version compatibility check for 3.11+
