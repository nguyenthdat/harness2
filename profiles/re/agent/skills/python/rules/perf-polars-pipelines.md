# perf-polars-pipelines

> Prefer Polars for new tabular processing workloads; use lazy execution (`scan_*`), columnar expression pushdowns, and native streaming instead of eager in-memory loads or row-iterating Python UDFs.

## Why It Matters

Polars is a multithreaded, columnar DataFrame library with a Rust query engine. Prefer it for new tabular pipelines that fit its expression model; benchmark end-to-end runtime and peak memory rather than claiming universal gains over pandas.

To achieve maximum performance and avoid common migration traps:
1. **Lazy Execution**: Start pipelines with `pl.scan_parquet()`, `pl.scan_csv()`, or `pl.scan_ipc()`. Polars builds a query graph and applies query optimization—including predicate pushdown (filtering rows at scan time) and projection pushdown (reading only referenced columns)—minimizing disk I/O and RAM usage.
2. **Columnar Expressions vs Row UDFs**: Prefer `pl.col(...)`, `pl.when().then(...)`, and built-in expressions over row loops or `.map_elements()`. Use a Python UDF only when native expressions cannot represent the required operation; specify its return dtype and measure its cost.
3. **Null vs NaN Semantics**:
   - In Polars, `null` represents missing or absent data (tracked via Arrow validity bitmasks).
   - `NaN` is a floating-point not-a-number value, distinct from null. Use `.is_nan()` / `.fill_nan()` deliberately; it is not removed by `.drop_nulls()`.
   - Unlike legacy pandas where `NaN` was used for missing values, Polars treats them distinctly. Use `.is_null()`, `.is_not_null()`, `.fill_null()`, or `.drop_nulls()` for missing data.
4. **Strict Schema & Types**: Polars enforces strict column types. There is no silent fallback to generic `object` dtypes. Parse schemas explicitly when scanning CSVs or JSON.
5. **No DataFrame Index**: Polars deliberately lacks a row index. In pandas, `df.loc[]`, `set_index()`, and multi-indexes add memory and complexity. In Polars, treat index-like identifiers as regular explicit columns.
6. **Timezone Awareness**: Datetime columns distinguish between timezone-naive (`pl.Datetime`) and timezone-aware types (`pl.Datetime(time_zone="UTC")`). Use `.dt.convert_time_zone(...)` or `.dt.replace_time_zone(...)` deliberately.
7. **Streaming & Out-of-Core Processing**: Prefer `.sink_parquet()` when the output belongs on disk; current Polars uses `.collect(engine="streaming")` when a materialized result is required. Collection still holds the final result in RAM; joins, sorts, aggregations, and unsupported streaming operations can require substantial working memory. Inspect the plan and measure peak RSS.
8. **Existing Repositories**: Preserve pandas-dependent contracts unless migration is requested or justified by measurements. Keep conversion at explicit boundaries; avoid repeated pandas/Polars round-trips.
9. **Ordering & Parallelism**: Group/join output order is not a contract unless explicitly established. Sort by sufficient keys when deterministic ordering matters. Polars already parallelizes work: avoid nesting process/thread pools by default; use `spawn`, not `fork`, if multiprocessing is required around an initialized native runtime.

## Bad

```python
# Bad: Eager loading of entire dataset into memory with pandas-style row iterations
import polars as pl

# 1. Eager read loads all columns and rows before filtering
df = pl.read_csv("large_events.csv")

# 2. Row-by-row Python UDF destroys Rust vectorization and acquires GIL
def categorize_row(row: dict) -> str:
    return "high" if row["amount"] > 1000.0 else "standard"

df = df.with_columns(
    pl.struct(["amount"]).map_elements(categorize_row, return_dtype=pl.String)  # Slow!
)

# 3. Confusing NaN with null and writing back eagerly
df = df.filter(df["user_id"] != float("nan"))
df.write_csv("output.csv")
```

## Good

```python
# Good: Lazy evaluation, expression pushdown, and native streaming
import polars as pl
from pathlib import Path

def process_event_metrics(input_path: Path, output_path: Path) -> None:
    # 1. Lazy scan enables projection and predicate pushdown
    q = (
        pl.scan_parquet(input_path)
        # Predicate pushdown: filter applied at reader level
        .filter(
            pl.col("event_type").is_in(["purchase", "refund"]),
            pl.col("user_id").is_not_null(),
        )
        # Columnar expressions: executed in parallel Rust kernels without GIL
        .with_columns(
            tier=pl.when(pl.col("amount") > 1000.0)
            .then(pl.lit("high"))
            .otherwise(pl.lit("standard")),
            # Explicit timezone conversion
            event_ts=pl.col("timestamp").dt.convert_time_zone("UTC"),
        )
        # Aggregation over explicit columns (no row index needed)
        .group_by(["user_id", "tier"])
        .agg(
            total_amount=pl.col("amount").sum(),
            event_count=pl.len(),
        )
        .sort("total_amount", descending=True)
    )

    # 2. Stream directly to destination without loading entire result into Python memory
    q.sink_parquet(output_path)
```

## Migration Considerations (Pandas to Polars)

| Pandas Pattern | Polars Equivalent | Semantic Difference |
|----------------|-------------------|---------------------|
| `pd.read_parquet(...)` | `pl.scan_parquet(...)` | Polars returns a `LazyFrame`; call `.collect()` or `.sink_*`. |
| `df.apply(fn, axis=1)` | `pl.when(...).then(...)` or expressions | Avoid `.map_elements()`; use native expression combinations. |
| `df.set_index("id")` | Keep `"id"` as explicit column | Polars has no row index; select or join directly by column. |
| `df.isna()` | `pl.col(...).is_null()` | Missing data is `null`; `NaN` is a distinct floating-point value. |
| `df.reset_index()` | Preserve meaningful index values as explicit columns during conversion | Polars has no implicit pandas index to recover later. |
| In-place `df['col'] = ...` | `df.with_columns(...)` | This operation returns a new frame; do not assume every Polars object/API is immutable. |

## See Also

- [perf-rust-library-selection](perf-rust-library-selection.md) - Selecting Rust-backed tools
- [perf-generators-memory](perf-generators-memory.md) - Streaming pipelines and memory bounds
- [conc-threadpool-executor](conc-threadpool-executor.md) - Thread pools for GIL-releasing native kernels

## Sources

- [Polars lazy sources and sinks](https://docs.pola.rs/user-guide/lazy/sources_sinks/)
- [Polars streaming](https://docs.pola.rs/user-guide/concepts/streaming/)
- [Pandas migration semantics](https://docs.pola.rs/user-guide/migration/pandas/)
- [Multiprocessing and native thread pools](https://docs.pola.rs/user-guide/misc/multiprocessing/)
