---
name: restructure-agent-code
description: >-
  Restructure raw code from the OpenAI Agent Builder SDK into this project's
  canonical package layout (agent/, config/, guardrail/, model/, workflow/).
  Preserves existing code; only decomposes and wires in the newly pasted
  code, enforces naming conventions (no leading underscores), converts any
  MCP transport to MCPServerStreamableHttp, and sets up .env / .env.prod /
  .env.stage plus main.py.
  Use when the user asks (in English or Turkish) to "restructure agent
  code", "integrate agent builder output", "reorganize agent code",
  "agent builder çıktısını projeye entegre et",
  "openai agent builder kodunu yapılandır",
  "ajan kodunu paket yapısına uyarla", "agent kodunu yeniden düzenle",
  "agent builder'dan gelen kodu parçala", or pastes raw Agent Builder SDK
  code and requests organization.
  Do not use for arbitrary refactors of non-Agent-Builder code, for
  creating new agents from scratch, or for reviewing the canonical
  structure of an already-organized project.
---

# Restructure OpenAI Agent Builder Code

Take raw code produced by the OpenAI Agent Builder and decompose it into the project's canonical package structure. Preserve all existing code; only restructure the new code and wire it in.

## Canonical Project Structure

```
project_root/
├── .env                  # Default env (always loaded)
├── .env.prod             # Production overrides
├── .env.stage            # Staging overrides
├── main.py               # Entry point: load env → run workflow
├── pyproject.toml
├── agent/                # One agent instance per file
│   ├── __init__.py
│   ├── common.py         # DEFAULT_MODEL_SETTINGS, shared constants
│   └── <purpose>.py
├── config/               # Client, MCP, guardrails config, run config
│   ├── __init__.py
│   ├── client.py
│   ├── mcp.py
│   ├── guardrails_config.py
│   └── run_config.py
├── guardrail/            # Guardrails orchestration + helpers
│   ├── __init__.py
│   ├── run_and_apply.py
│   ├── scrubbing.py
│   └── result_helpers.py
├── model/                # One Pydantic BaseModel per file
│   ├── __init__.py
│   └── <schema>.py
└── workflow/             # Orchestration, handlers, helpers
    ├── __init__.py
    ├── run_workflow.py
    ├── handlers.py
    └── helpers.py
```

Every `__init__.py` re-exports the package's public symbols and defines `__all__`.

---

## Workflow

```
- [ ] Step 1: Inventory the raw Agent Builder code
- [ ] Step 2: Map each component to the correct package
- [ ] Step 3: Apply package templates
- [ ] Step 4: Configure environment files
- [ ] Step 5: Convert MCP to MCPServerStreamableHttp
- [ ] Step 6: Enforce naming conventions (strip leading underscores)
- [ ] Step 7: Wire up main.py
- [ ] Step 8: Verify against the final checklist
```

## Step 1 — Inventory the Raw Code

Read the full Agent Builder output and list every component:

- Agent definitions (`Agent(...)` instances)
- Pydantic schema classes (subclasses of `BaseModel`)
- Configuration objects (client, `RunConfig`, guardrails config)
- MCP server definitions
- Guardrails logic (runtime, scrubbing, result parsing)
- Workflow / orchestration logic (the main flow tying agents together)
- Helper / utility functions

## Step 2 — Map Components to Packages

| Component kind                   | Destination package        |
|----------------------------------|----------------------------|
| `Agent(...)` instance            | `agent/<purpose>.py`       |
| `ModelSettings`, shared agent constants | `agent/common.py`     |
| `AsyncOpenAI`, `context` namespace | `config/client.py`       |
| `MCPServer*` instance            | `config/mcp.py` (convert to Streamable HTTP) |
| Guardrails config dict           | `config/guardrails_config.py` |
| `RunConfig` with trace metadata  | `config/run_config.py`     |
| `run_and_apply_guardrails`       | `guardrail/run_and_apply.py` |
| PII / input scrubbing helpers    | `guardrail/scrubbing.py`   |
| Tripwire / safe-text helpers     | `guardrail/result_helpers.py` |
| `BaseModel` subclass             | `model/<snake_case>.py`    |
| `run_workflow()`                 | `workflow/run_workflow.py` |
| `handle_*()` functions           | `workflow/handlers.py`     |
| `run_agent()`, `build_user_message()`, cross-cutting utils | `workflow/helpers.py` |

If a component does not fit any existing package (e.g. `tools/`, `hooks/`, `middleware/`), create a new package under `snake_case/` with `__init__.py` and a re-export list.

## Step 3 — Apply Package Templates

Open the reference that matches the package being filled. Each reference contains the full code template, init pattern, and any responsibility rules:

- [references/agent-package.md](references/agent-package.md)
- [references/config-package.md](references/config-package.md)
- [references/guardrail-package.md](references/guardrail-package.md)
- [references/model-package.md](references/model-package.md)
- [references/workflow-package.md](references/workflow-package.md)

## Step 4 — Configure Environment Files

Create or update `.env`, `.env.prod`, `.env.stage`. Template and loading rules are in [references/environment-and-main.md](references/environment-and-main.md).

## Step 5 — Convert MCP

All MCP usage must be `MCPServerStreamableHttp` from `agents.mcp`. Replace any `MCPServerSse`, `MCPServerStdio`, or custom MCP transport. Place the instance in `config/mcp.py`. Template is in [references/config-package.md](references/config-package.md).

## Step 6 — Enforce Naming Conventions

| Category        | Convention             | Example                               |
|-----------------|------------------------|---------------------------------------|
| Modules         | `snake_case`           | `run_workflow.py`, `message_synthesizer.py` |
| Classes         | `PascalCase`           | `WorkflowInput`, `MessageSynthesizerAgentSchema` |
| Functions       | `snake_case`           | `run_workflow`, `build_user_message`  |
| Variables       | `snake_case`           | `conversation_history`                |
| Constants       | `UPPER_SNAKE_CASE`     | `RUN_CONFIG`, `DEFAULT_MODEL_SETTINGS`|
| Agent instances | `<purpose>_agent`      | `search_agent`, `fail_response_agent` |
| Handler funcs   | `handle_<action>`      | `handle_search`, `handle_missing_info`|

**CRITICAL — no leading underscores.** Strip any `_` prefix introduced by the Agent Builder:

- `_find_pii_guardrail` → `find_pii_guardrail`
- `_build_pii_only_config` → `build_pii_only_config`
- `_common.py` → `common.py`

## Step 7 — Wire Up `main.py`

Use the entry-point template in [references/environment-and-main.md](references/environment-and-main.md). Key rules:

- `load_env()` is called at module level **before** any project import.
- `main()` constructs a `WorkflowInput` and delegates to `run_workflow()`.

## Step 8 — Final Checklist

- [ ] Each agent is in its own file under `agent/`
- [ ] `agent/common.py` exists with `DEFAULT_MODEL_SETTINGS`
- [ ] `agent/__init__.py` re-exports every agent with `__all__`
- [ ] `config/client.py` has `client` and `context`
- [ ] `config/mcp.py` uses `MCPServerStreamableHttp`
- [ ] `config/guardrails_config.py` exists
- [ ] `config/run_config.py` has `RUN_CONFIG`
- [ ] `config/__init__.py` re-exports all config symbols with `__all__`
- [ ] `guardrail/` has `run_and_apply.py`, `scrubbing.py`, `result_helpers.py`
- [ ] `guardrail/__init__.py` re-exports `run_and_apply_guardrails`
- [ ] `model/` has one file per Pydantic schema
- [ ] `model/__init__.py` re-exports every model with `__all__`
- [ ] `workflow/run_workflow.py` contains the main orchestration
- [ ] `workflow/handlers.py` has `handle_*` functions
- [ ] `workflow/helpers.py` has `run_agent`, `build_user_message`, utilities
- [ ] `workflow/__init__.py` re-exports `run_workflow`
- [ ] `.env`, `.env.prod`, `.env.stage` exist with correct variables
- [ ] `main.py` calls `load_env()` before project imports
- [ ] No identifier starts with `_`
- [ ] All MCP is `MCPServerStreamableHttp`
- [ ] No existing code was modified beyond what these rules require
- [ ] All new packages have `__init__.py` with `__all__`

---

## Additional Resources

- Package templates: [references/agent-package.md](references/agent-package.md), [references/config-package.md](references/config-package.md), [references/guardrail-package.md](references/guardrail-package.md), [references/model-package.md](references/model-package.md), [references/workflow-package.md](references/workflow-package.md)
- Environment files and `main.py`: [references/environment-and-main.md](references/environment-and-main.md)
