# iter-collections-specialized

> Use specialized collections (`deque`, `defaultdict`, `Counter`) instead of inefficient list/dict workarounds.

## Why It Matters

Using `list.pop(0)` or `list.insert(0, x)` has $O(N)$ complexity because every element must shift in memory. `collections.deque` provides $O(1)$ appends and pops from both ends. `Counter` and `defaultdict` simplify counting and grouping.

## Bad

```python
# Bad: O(N) queue operations with list
queue = []
queue.append("job1")
item = queue.pop(0)  # O(N) shift of entire list!

# Bad: Verbose manual frequency counting
counts = {}
for word in words:
    if word not in counts:
        counts[word] = 0
    counts[word] += 1
```

## Good

```python
from collections import deque, Counter, defaultdict

# Good: O(1) double-ended queue
queue = deque()
queue.append("job1")
item = queue.popleft()  # O(1) pop

# Good: Counter handles frequency aggregation natively in C
word_counts = Counter(words)

# Good: defaultdict eliminates manual membership checks
grouped = defaultdict(list)
for user in users:
    grouped[user.role].append(user)
```

## See Also

- [iter-dict-views-operations](iter-dict-views-operations.md) - Set operations on dict views
- [perf-slots-memory](perf-slots-memory.md) - Memory optimization with slots
