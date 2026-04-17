# Environment Files and `main.py`

## Environment Files

Three files are managed:

- `.env` — base configuration, always loaded
- `.env.prod` — production overrides (only variables that differ from `.env`)
- `.env.stage` — staging overrides (only variables that differ from `.env`)

### `.env` (base)

```
OPENAI_API_KEY=<key>
MCP_SERVER_URL=<url>
```

### `.env.prod`

```
MCP_SERVER_URL=<production_url>
```

### `.env.stage`

```
MCP_SERVER_URL=<staging_url>
```

If the Agent Builder code introduces new environment variables, add them to **all three** files (or at minimum to `.env`).

## `main.py` Entry Point

```python
import asyncio
import os

from dotenv import load_dotenv


def load_env():
    load_dotenv(".env")
    env = os.getenv("ENV", "dev")
    if env != "dev":
        load_dotenv(f".env.{env}", override=True)


load_env()

from model import WorkflowInput
from workflow import run_workflow


async def main():
    user_text = await asyncio.to_thread(input, "Mulk aramanizi yazin: ")
    result = await run_workflow(WorkflowInput(input_as_text=user_text))
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

## Entry Point Rules

1. `load_env()` is called at **module level**, before any project import.
2. Project imports (`from model import ...`, `from workflow import ...`) come **after** `load_env()`.
3. `main()` constructs a `WorkflowInput` and delegates to `run_workflow()`.
4. No business logic in `main.py` — it is a thin launcher.
