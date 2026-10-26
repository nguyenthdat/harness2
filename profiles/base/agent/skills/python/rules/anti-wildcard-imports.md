# anti-wildcard-imports

> Never use wildcard imports (`from module import *`); import explicit names or modules.

## Why It Matters

Wildcard imports pollute the local namespace, hide where names originated, silently shadow local variables, and break static analysis and refactoring tools.

## Bad

```python
# Bad: Wildcard import hides origins and can shadow builtins
from os import *
from math import *

# Which module does 'pow' come from? Builtin, os, or math?
result = pow(2, 3)
```

## Good

```python
import math
from os import PathLike

# Good: Explicit imports are clear and statically analyzable
result = math.pow(2, 3)
```

## See Also

- [api-explicit-all-exports](api-explicit-all-exports.md) - Explicit exports with __all__
- [anti-shadowing-builtins](anti-shadowing-builtins.md) - Avoiding shadowing built-in functions
