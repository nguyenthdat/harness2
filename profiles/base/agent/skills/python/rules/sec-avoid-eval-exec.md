# sec-avoid-eval-exec

> Never execute untrusted code with `eval()` or `exec()`; use restricted AST evaluators or dedicated expression parsers.

## Why It Matters

`eval()` and `exec()` execute arbitrary Python bytecode in the current runtime context, giving untrusted inputs full capability to invoke system commands, read credentials, or corrupt memory (CWE-95). When dynamic formula evaluation is required, parse expressions into an AST, validate node types against a strict whitelist, enforce recursion limits, and reject boolean and non-numeric constants.

## Bad

```python
# Bad: Direct evaluation of dynamic user expressions executes arbitrary code
def compute_user_formula(formula_str: str, x: float) -> float:
    return eval(formula_str)  # Attacker can execute __import__('os').system('...')!
```

## Good

```python
import ast
import operator
import math

SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

def safe_eval_expr(
    formula_str: str, x_val: float, *, max_chars: int = 256, max_nodes: int = 50
) -> float:
    if len(formula_str) > max_chars or not math.isfinite(x_val):
        raise ValueError("invalid formula input")
    tree = ast.parse(formula_str, mode="eval")
    node_count = 0

    def _eval(node: ast.AST) -> float:
        nonlocal node_count
        node_count += 1
        if node_count > max_nodes:
            raise ValueError("Expression too complex")

        if isinstance(node, ast.Expression):
            return _eval(node.body)
        
        # AST Constant check: ensure numeric and explicitly reject booleans
        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float) and type(node.value) is not bool:
                try:
                    value = float(node.value)
                except OverflowError as error:
                    raise ValueError("numeric constant is too large") from error
                if math.isfinite(value):
                    return value
            raise ValueError(f"invalid constant: {node.value!r}")

        if isinstance(node, ast.Name):
            if node.id == "x":
                return float(x_val)
            raise ValueError(f"Unsupported variable: {node.id}")

        if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPS:
            op_fn = SAFE_OPS[type(node.op)]
            return float(op_fn(_eval(node.operand)))

        if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPS:
            op_fn = SAFE_OPS[type(node.op)]
            left = _eval(node.left)
            right = _eval(node.right)
            res = float(op_fn(left, right))
            if not math.isfinite(res):
                raise ValueError("Arithmetic result is not finite")
            return res

        raise ValueError(f"Unsupported syntax element: {type(node).__name__}")

    return _eval(tree)
```

## See Also

- [sec-avoid-pickle-untrusted](sec-avoid-pickle-untrusted.md) - Preventing code execution vulnerabilities
- [sec-subprocess-shell-false](sec-subprocess-shell-false.md) - Safe subprocess execution
