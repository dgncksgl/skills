# `agent/` Package Templates

Each agent instance lives in its own file named after its purpose in `snake_case`.

## Agent File Template

`agent/<purpose>.py`:

```python
from agents import Agent

from agent.common import DEFAULT_MODEL_SETTINGS

<purpose>_agent = Agent(
    name="<Purpose> Agent",
    instructions="""...""",
    model="gpt-5-mini",
    model_settings=DEFAULT_MODEL_SETTINGS,
)
```

## Shared Settings

`agent/common.py`:

```python
from agents import ModelSettings
from openai.types.shared.reasoning import Reasoning

DEFAULT_MODEL_SETTINGS = ModelSettings(
    store=True,
    reasoning=Reasoning(
        effort="low",
        summary="auto",
    ),
)
```

## Agent Using MCP

```python
from config import mcp_server

search_agent = Agent(
    name="Search Agent",
    instructions="""...""",
    model="gpt-5-mini",
    model_settings=DEFAULT_MODEL_SETTINGS,
    mcp_servers=[mcp_server],
)
```

## Agent With Structured Output

```python
from model import SomeSchema

some_agent = Agent(
    name="Some Agent",
    instructions="""...""",
    model="gpt-5-mini",
    model_settings=DEFAULT_MODEL_SETTINGS,
    output_type=SomeSchema,
)
```

## `agent/__init__.py`

Re-export every agent instance:

```python
from agent.search import search_agent
from agent.message_synthesizer import message_synthesizer_agent

__all__ = [
    "search_agent",
    "message_synthesizer_agent",
]
```
