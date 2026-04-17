# `model/` Package Templates

One Pydantic `BaseModel` per file. The file name is the class name in `snake_case`.

## File Template

`model/workflow_input.py`:

```python
from pydantic import BaseModel


class WorkflowInput(BaseModel):
    input_as_text: str
```

## `model/__init__.py`

Re-export every model:

```python
from model.message_synthesizer_agent_schema import MessageSynthesizerAgentSchema
from model.workflow_input import WorkflowInput

__all__ = [
    "WorkflowInput",
    "MessageSynthesizerAgentSchema",
]
```

## Rules

- One class per file — if the Agent Builder defines multiple `BaseModel`s in one module, split them.
- File name in `snake_case`, class name in `PascalCase`.
- Agent-facing schemas (structured output types) live here; so do request/response bodies.
- No business logic — keep models declarative.
