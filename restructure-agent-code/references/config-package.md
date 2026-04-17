# `config/` Package Templates

| File                   | Contents                                          |
|------------------------|---------------------------------------------------|
| `client.py`            | `AsyncOpenAI` client instance and `context` namespace |
| `mcp.py`               | `MCPServerStreamableHttp` instance                |
| `guardrails_config.py` | Guardrails configuration dict                     |
| `run_config.py`        | `RunConfig` with trace metadata                   |

## `config/client.py`

```python
from types import SimpleNamespace

from openai import AsyncOpenAI

client = AsyncOpenAI()
context = SimpleNamespace(guardrail_llm=client)
```

## `config/mcp.py`

Always use `MCPServerStreamableHttp`:

```python
import os

from agents.mcp import MCPServerStreamableHttp

mcp_server = MCPServerStreamableHttp(
    params={"url": os.environ["MCP_SERVER_URL"]},
    name="hemlak_mcp",
    cache_tools_list=True,
    client_session_timeout_seconds=30,
)
```

If the Agent Builder output uses `MCPServerSse`, `MCPServerStdio`, or any other transport, convert it to this pattern. The URL must come from the `MCP_SERVER_URL` environment variable.

## `config/run_config.py`

```python
from agents import RunConfig

RUN_CONFIG = RunConfig(
    trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "<workflow_id_from_builder>",
    }
)
```

## `config/__init__.py`

```python
from config.client import client, context
from config.guardrails_config import guardrails_config
from config.mcp import mcp_server
from config.run_config import RUN_CONFIG

__all__ = [
    "mcp_server",
    "client",
    "context",
    "guardrails_config",
    "RUN_CONFIG",
]
```

## Adding a New Config Component

If the Agent Builder code introduces a new config component (e.g. cache config, new API client):

1. Create a new file under `config/` following the same pattern.
2. Add the symbol to `config/__init__.py` and `__all__`.
