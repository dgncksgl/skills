# Type Warning Formats (per Checker)

Reference table for recognising type warnings across different IDEs and type checkers. Read this when the warning format in the user's output isn't obviously one of the common patterns, or when adapting a custom checker's output.

## Canonical Warning Formats

| IDE / Checker       | Warning Format                                               | Mismatch Signal |
|---------------------|--------------------------------------------------------------|-----------------|
| PyCharm / Pyright   | `Expected type 'X', got 'Y' instead`                         | Types `X` and `Y` explicit |
| mypy                | `Incompatible types in assignment (expression has type "Y", variable has type "X")` | Types in quoted form |
| mypy (arg)          | `Argument N to "fn" has incompatible type "Y"; expected "X"` | Function argument |
| mypy (return)       | `Incompatible return value type (got "Y", expected "X")`     | Return value |
| TypeScript (tsc)    | `Type 'X' is not assignable to type 'Y'`                     | Assignment / parameter |
| TypeScript (TS2345) | `Argument of type 'X' is not assignable to parameter of type 'Y'` | Function argument |
| TypeScript (TS2322) | `Type 'undefined' is not assignable to type 'string'`        | Null / undefined |
| IntelliJ (Java)     | `Required type: X Provided: Y`                               | Assignment |
| javac               | `incompatible types: Y cannot be converted to X`             | Assignment / argument |
| Kotlin (kotlinc)    | `Type mismatch. Required: X Found: Y`                        | Assignment |
| Go (gopls)          | `cannot use X (type Y) as type Z`                            | Assignment / argument |
| Go (compile)        | `cannot convert X (untyped Y constant) to type Z`            | Literal conversion |
| C# (Roslyn)         | `Cannot implicitly convert type 'X' to 'Y'`                  | Assignment |
| C# (CS1503)         | `Argument N: cannot convert from 'X' to 'Y'`                 | Function argument |
| Rust (rustc)        | `expected X, found Y`                                        | Assignment / argument |

## Extraction Pattern

From any of the formats above, the fix workflow only needs three pieces:

1. **Expected type** — `X` (what the API requires)
2. **Actual type** — `Y` (what you gave it)
3. **Location** — file + line + column

Every warning can be reduced to this triplet. SKILL.md Step 4 is built around it.

## Secondary Warnings to Recognise

These appear *after* a misguided fix and indicate the fix itself is wrong:

| Warning                                                              | Cause |
|----------------------------------------------------------------------|-------|
| `Cast may be a mistake because they are not in the same inheritance hierarchy` | `cast()` used between unrelated types — replace with a constructor or narrowing |
| `Unnecessary isinstance check; X is always Y`                        | The narrowing was already implied — remove the check |
| `Unused type: ignore comment`                                        | `# type: ignore` left behind after an actual fix — remove |

## Per-Language Null Representation

| Language    | "Absent" value terminology  |
|-------------|-----------------------------|
| Python      | `None`, `Optional[X]`, `X \| None` |
| TypeScript  | `null`, `undefined`, `X \| null`, `X \| undefined`, `X?` |
| Java        | `null`, `Optional<X>`       |
| Kotlin      | `null`, `X?`                |
| Go          | `nil`, `*X` pointer         |
| C#          | `null`, `X?` (C# 8+ NRT)    |
| Rust        | `Option<X>`, `None`         |
