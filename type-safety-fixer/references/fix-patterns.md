# Fix Patterns (per Language)

Detailed code patterns for each common type mismatch. SKILL.md lists the fix *strategies*; this file shows the concrete *code*. Open when you need a pattern example to reproduce.

## Python

### Pattern 1 — `dict` literal where TypedDict expected

```python
# Warning: Expected 'Prompt', got 'dict[str, str]'
agent = Agent(prompt={"id": "abc", "version": "1"})

# Fix: import and construct the TypedDict
from library import Prompt
agent = Agent(prompt=Prompt(id="abc", version="1"))
```

### Pattern 2 — `None` where concrete type expected

```python
# Warning: Expected 'str', got 'None'
value: str = some_dict.get("key")
```

Fix options in order of preference:

```python
# A. Provide a default (preferred when a sensible default exists)
value: str = some_dict.get("key", "")

# B. Guard with assertion (preferred when the key is guaranteed)
raw = some_dict.get("key")
assert raw is not None
value: str = raw

# C. Widen the receiving type (preferred when None is valid downstream)
value: str | None = some_dict.get("key")
```

### Pattern 3 — `list[dict]` where `list[TypedDict]` expected

```python
# Warning: Expected 'list[SomeTypedDict]', got 'list[dict]'
items: list[SomeTypedDict] = [
    {"role": "user", "content": [{"type": "input_text", "text": "hi"}]}
]

# Fix: construct TypedDict objects — find nested types in library source
from library import SomeTypedDict, ContentItem
items: list[SomeTypedDict] = [
    SomeTypedDict(
        role="user",
        content=[ContentItem(type="input_text", text="hi")],
    )
]
```

### Pattern 4 — Mixed-type value where specific type expected

```python
# Warning: Expected 'str', got 'str | bool | None'
result = do_something(state["key"])

# Fix: extract and narrow with isinstance
extracted = state["key"]
assert isinstance(extracted, str)
result = do_something(extracted)
```

### Pattern 5 — `Any` flowing into a typed parameter

```python
# Warning: Expected 'int', got 'Any'
result = compute(payload["count"])

# Fix: annotate the intermediate variable
count: int = int(payload["count"])
result = compute(count)
```

### Pattern 6 — Subtype expected, supertype supplied

```python
# Warning: Expected 'Dog', got 'Animal'
dog: Dog = some_animal()

# Fix: narrow with isinstance
a = some_animal()
assert isinstance(a, Dog)
dog: Dog = a
```

### Pattern 7 — Literal type mismatch

```python
# Warning: Expected 'Literal["on", "off"]', got 'str'
set_state(config["mode"])

# Fix: assert against the literal set
mode = config["mode"]
assert mode in ("on", "off")
set_state(mode)
```

## TypeScript

### Pattern 1 — Object literal missing properties

```typescript
// Warning: Type '{ key: string; }' is not assignable to type 'LibraryConfig'.
//          Property 'id' is missing.
const config = { key: "value" };
loader.apply(config);

// Fix: satisfies operator (TS 4.9+)
const config = { key: "value", id: "c1" } satisfies LibraryConfig;
loader.apply(config);
```

### Pattern 2 — `undefined` where concrete type expected

```typescript
// Warning: Type 'undefined' is not assignable to type 'string'.
const name: string = map.get(key);

// Fix A: nullish coalescing default
const name: string = map.get(key) ?? "";

// Fix B: narrowing guard (preferred when absence is an error)
const raw = map.get(key);
if (raw === undefined) {
  throw new Error(`missing ${key}`);
}
const name: string = raw;
```

### Pattern 3 — `as` cast between unrelated types (AVOID)

```typescript
// BAD — silences the error but is wrong
const cfg = rawObject as LibraryConfig;

// Good — construct the typed object
const cfg: LibraryConfig = {
  id: rawObject.id,
  name: rawObject.name,
  enabled: rawObject.enabled ?? false,
};
```

### Pattern 4 — Non-null assertion (`!`) — use sparingly

```typescript
// Only acceptable when the framework guarantees non-null
const el = document.getElementById("root")!;
```

## Java

### Pattern 1 — Raw collection to generic

```java
List<String> items = (List<String>) rawList;
```

### Pattern 2 — Optional unwrap

```java
String value = optional.orElse("default");
String value = optional.orElseThrow(() -> new IllegalStateException("required"));
```

### Pattern 3 — Autoboxing / widening

```java
long ts = Integer.parseInt(s);
```

## Kotlin

### Pattern 1 — Nullable to non-null

```kotlin
val name: String = map[key] ?: ""
val name: String = requireNotNull(map[key]) { "missing $key" }
```

### Pattern 2 — Smart cast after check

```kotlin
val x: Any = ...
if (x is String) {
    println(x.length)
}
```

## Go

### Pattern 1 — Interface to concrete with type assertion

```go
s, ok := v.(string)
if !ok {
    return fmt.Errorf("expected string, got %T", v)
}
```

### Pattern 2 — Error wrapping preserves type

```go
if err != nil {
    return fmt.Errorf("open %s: %w", path, err)
}
```

## C#

### Pattern 1 — Nullable reference type

```csharp
string name = map.GetValueOrDefault(key) ?? string.Empty;
```

### Pattern 2 — Pattern matching narrowing

```csharp
if (value is string s)
{
    Console.WriteLine(s.Length);
}
```

## Anti-Patterns (All Languages)

| Anti-pattern                            | Why it fails |
|-----------------------------------------|--------------|
| `cast(X, value)` (Python)               | Produces the "inheritance hierarchy" warning; hides real mismatch |
| `value as X` when X is unrelated (TS)   | Silences the compiler; runtime error at first use |
| `(X) value` between unrelated types (Java) | `ClassCastException` at runtime |
| `# type: ignore` with no comment        | Buries the problem; next engineer can't tell why |
| Changing the annotation to `Any` / `any` | Erases all downstream type safety |
