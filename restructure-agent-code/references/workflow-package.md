# `workflow/` Package Templates

| File              | Contents                                                        |
|-------------------|-----------------------------------------------------------------|
| `run_workflow.py` | `run_workflow()` — main orchestration function                  |
| `handlers.py`     | One `handle_*()` function per workflow step                     |
| `helpers.py`      | `run_agent()`, `build_user_message()`, utility functions        |

## `workflow/helpers.py` — `run_agent` Pattern

```python
from agents import Runner, TResponseInputItem
from agents.items import ToolApprovalItem

from config import RUN_CONFIG


async def run_agent(agent, input_items, conversation_history):
    result = await Runner.run(agent, input=input_items, run_config=RUN_CONFIG)
    conversation_history.extend(
        [
            item.to_input_item()
            for item in result.new_items
            if not isinstance(item, ToolApprovalItem)
        ]
    )
    return result
```

## `workflow/handlers.py` — Handler Pattern

```python
from agents import TResponseInputItem

from agent import some_agent
from workflow.helpers import run_agent


async def handle_some_step(conversation_history: list[TResponseInputItem]) -> dict:
    result = await run_agent(some_agent, [*conversation_history], conversation_history)
    return {"output_text": result.final_output_as(str)}
```

## Handlers That Use MCP

Wrap the agent call in `async with mcp_server:`:

```python
from config import mcp_server


async def handle_search(conversation_history, synthesized_message):
    async with mcp_server:
        result = await run_agent(search_agent, [...], conversation_history)
    return {"output_text": result.final_output_as(str)}
```

## `workflow/__init__.py`

```python
from workflow.run_workflow import run_workflow

__all__ = ["run_workflow"]
```

## Responsibility Split

- `run_workflow.py` — top-level orchestration: guardrails → routing → handler invocation → result composition.
- `handlers.py` — step-level logic (`handle_search`, `handle_missing_info`, …). One function per step. No cross-step branching.
- `helpers.py` — cross-cutting utilities (`run_agent`, `build_user_message`, tool result conversion). No agent-specific logic.
