# `guardrail/` Package Templates

| File               | Contents                                                       |
|--------------------|----------------------------------------------------------------|
| `run_and_apply.py` | `run_and_apply_guardrails()` — main entry point                |
| `scrubbing.py`     | PII scrubbing for conversation history and workflow input      |
| `result_helpers.py`| Tripwire detection, safe text extraction, fail output building |

## `guardrail/__init__.py`

```python
from guardrail.run_and_apply import run_and_apply_guardrails

__all__ = ["run_and_apply_guardrails"]
```

## Responsibility Split

- `run_and_apply.py` — orchestrates: scrub input → run guardrails → inspect result → return either the clean input or a fail output.
- `scrubbing.py` — pure helpers that transform conversation history / user input to remove PII or other disallowed content. No I/O, no agent calls.
- `result_helpers.py` — inspectors over the guardrails output (tripwire boolean, safe text extraction, fail output payload construction). No I/O.

`run_and_apply_guardrails` is the only symbol other packages should import from this package.
