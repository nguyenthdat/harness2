# test-tmp-path-filesystem

> Use the standard `tmp_path` fixture for all filesystem-dependent tests; never hardcode `/tmp`.

## Why It Matters

Hardcoding `/tmp/test.txt` causes file collisions during parallel test runs (`pytest -n auto`) and leaves orphan files. `tmp_path` provides a unique, isolated `pathlib.Path` directory per test run.

## Bad

```python
# Bad: Shared hardcoded path causes collision in parallel tests
def test_file_writer():
    path = "/tmp/test_output.json"
    write_output(path, {"status": "ok"})
    assert os.path.exists(path)
```

## Good

```python
from pathlib import Path

# Good: tmp_path provides unique isolated directory
def test_file_writer(tmp_path: Path):
    target_file = tmp_path / "output.json"
    write_output(target_file, {"status": "ok"})
    assert target_file.is_file()
    assert target_file.read_text(encoding="utf-8") == '{"status": "ok"}'
```

## See Also

- [sec-pathlib-traversal](sec-pathlib-traversal.md) - Safe filesystem path handling
- [test-monkeypatch-clean](test-monkeypatch-clean.md) - Monkeypatching environment
