# iter-dict-views-operations

> Use dictionary view set operations (`dict.keys() & set`) instead of creating intermediate sets.

## Why It Matters

`dict.keys()` and `dict.items()` return dynamic dictionary view objects that support set operations (union `|`, intersection `&`, difference `-`, symmetric difference `^`) directly without allocating intermediate `set()` copies.

## Bad

```python
# Bad: Allocating extra sets just to compute key intersections
dict_a = {"a": 1, "b": 2, "c": 3}
dict_b = {"b": 20, "c": 30, "d": 40}

# Allocates 2 full sets in memory
common_keys = set(dict_a.keys()).intersection(set(dict_b.keys()))
```

## Good

```python
# Good: Direct view operations avoid intermediate allocations
dict_a = {"a": 1, "b": 2, "c": 3}
dict_b = {"b": 20, "c": 30, "d": 40}

# Dictionary keys views support set operators natively
common_keys = dict_a.keys() & dict_b.keys()  # {'b', 'c'}
missing_keys = dict_a.keys() - dict_b.keys()  # {'a'}
```

## See Also

- [iter-collections-specialized](iter-collections-specialized.md) - Specialized collections
- [perf-str-join-builder](perf-str-join-builder.md) - String join efficiency
