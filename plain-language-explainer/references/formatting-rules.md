# Formatting Rules

Read this when deciding whether an explanation should contain a table, a code
block, or a file path — and how to keep it readable once it does.

## The test every element must pass

> Does this make the point faster to understand than a plain sentence?

If yes, use it. If it is there to look thorough, delete it.

## Tables

Use a table when comparing **3 or more things across the same 2-3 attributes**.
Do not use one to list facts that have no comparison in them.

| Rule | Detail |
|---|---|
| Size | 5 rows max, 3 columns max |
| Headers | Plain words: "What changes", "Why it matters" — not "delta", "impact factor" |
| Cells | A few words each. A full sentence means it belongs in prose |
| Numbers | Add the unit and meaning in the header, not in every cell |

Good use: comparing three options the user must choose between.
Bad use: a "before / after / notes" grid holding one item.

## Code blocks

Allowed whenever code is the clearest answer — showing a call, a config value,
a shape of data, or the exact line that broke.

- Show the **shortest version that makes the point**. Cut everything else and
  mark the gap with `...`.
- Put a one-line label above it saying what to look at.
- Keep it tidy: real indentation, real names, no pseudo-code hybrids.
- Add a short inline comment only on the line that matters.
- If the block is over ~15 lines, explain in prose and show only the key lines.

Example of the shape to aim for:

Only the part that changed:

```python
# before: the model name was fixed here
agent = Agent(model="gpt-4o")

# after: it comes from config, so the provider can change
agent = Agent(model=settings.llm.model)
```

## File paths, class names, line numbers

Give them when the user may want to open the file, review it, or ask for a
change there. Put the path **after** the plain-language sentence, not inside it.

- Good: "The model name now comes from configuration. It lives in `config/settings.py`."
- Bad: "`config/settings.py` wires `ModelSettings` into `ClientFactory.__init__`
  so the adapter in `services/model_client.py` resolves at runtime."

One or two paths in an explanation is help. Five is a wall.

## Emphasis

Bold the thing the user must not miss, once or twice per explanation.
Bolding every other phrase is the same as bolding nothing.
