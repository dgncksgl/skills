# SonarQube Rules Reference (per Language)

Commonly enforced rules, grouped by language. SKILL.md enumerates the general categories; this file lists the specific rule IDs the agent should recognise and fix.

## Cross-Language Rules

| Rule ID | Name                                         | Fix Summary |
|---------|----------------------------------------------|-------------|
| S1192   | String literals should not be duplicated     | Extract to a named constant after 3+ occurrences |
| S1854   | Unused assignments should be removed         | Delete the assignment; remove cascaded dead code |
| S1481   | Unused local variables should be removed     | Delete or use the variable |
| S125    | Commented-out code should be removed         | Delete the commented block |
| S3776   | Cognitive Complexity of functions too high   | Extract helpers, apply guard clauses, flatten nesting |
| S1541   | Cyclomatic Complexity too high               | Split method; prefer dispatch table over long switch |
| S107    | Methods should not have too many parameters  | Introduce a parameter object |
| S1186   | Methods should not be empty                  | Add a clear `// intentionally empty` or throw `UnsupportedOperationException` |
| S2068   | Hardcoded credentials                        | Read from environment / secret store |
| S2077   | SQL queries should not be vulnerable to injection | Use parameterized queries / prepared statements |
| S4790   | Hashing data is security-sensitive           | Replace MD5/SHA1 (for security) with SHA-256+ or bcrypt/argon2 for passwords |

## Java / Kotlin

| Rule ID | Name                                              | Fix Summary |
|---------|---------------------------------------------------|-------------|
| S1155   | Collection.isEmpty() should be used               | Replace `.size() == 0` with `.isEmpty()` |
| S2095   | Resources should be closed                        | Use try-with-resources |
| S4042   | Use Files.delete instead of File.delete           | Switch to NIO |
| S2184   | Math operands should be cast before assignment    | Cast `int` to `long`/`double` before multiplication |
| S2159   | Silly equality checks should not be made          | Remove comparisons that are always true/false |
| S1066   | Collapsible if statements                         | Combine with `&&` |
| S1149   | Synchronized classes (Vector, Hashtable) deprecated | Use `ArrayList` / `HashMap` with explicit sync |
| S2440   | Classes with only static methods should not be instantiated | Make constructor private |
| S1118   | Utility classes should not have public constructors | Make constructor private |
| S2637   | `@NonNull` annotated fields should not be null    | Initialise in constructor |
| S112    | Generic exceptions should never be thrown         | Use a specific exception type |

## Python

| Rule ID | Name                                              | Fix Summary |
|---------|---------------------------------------------------|-------------|
| S5754   | `SystemExit` should be re-raised                  | Let `SystemExit` propagate |
| S5806   | Builtin names should not be shadowed              | Rename variables like `list`, `dict` |
| S5807   | Overly permissive regex                           | Tighten pattern / use `re.escape` |
| S5445   | Insecure temporary file creation                  | Use `tempfile.NamedTemporaryFile` |
| S5632   | Exceptions should inherit from `Exception`        | Inherit from `Exception`, not `BaseException` |
| S5708   | `except:` without an exception type               | Specify exception types |
| S1542   | Function / method names should follow naming conv | Use `snake_case` |
| S5886   | Function return type must match annotations       | Align return type with actual returns |

## TypeScript / JavaScript

| Rule ID | Name                                              | Fix Summary |
|---------|---------------------------------------------------|-------------|
| S1172   | Unused function parameters should be removed      | Remove or prefix with `_` (but the SKILL.md naming rule forbids creating new `_`-prefixed identifiers — prefer removal) |
| S1488   | Local variables should not be declared and then immediately returned | Return the expression directly |
| S3353   | `const` should be used for immutable variables    | Replace `let`/`var` with `const` |
| S1121   | Assignments should not be made from within sub-expressions | Extract the assignment |
| S3358   | Ternary operators should not be nested            | Extract to `if/else` or named variables |
| S4327   | `this` should not be assigned to variables        | Use arrow functions |
| S2138   | `undefined` should not be passed as the value of optional parameters | Omit the argument |

## Go

| Rule ID | Name                                              | Fix Summary |
|---------|---------------------------------------------------|-------------|
| S1005   | Error return values should be checked             | Handle or explicitly ignore with `_` |
| S4144   | Functions should not have identical implementations | Deduplicate |
| S3776   | Cognitive complexity                              | Extract helpers |
| S1764   | Identical expressions on both sides of an operator | Fix the typo |

## C#

| Rule ID | Name                                              | Fix Summary |
|---------|---------------------------------------------------|-------------|
| S1481   | Unused local variables                            | Remove |
| S1172   | Unused parameters                                 | Remove |
| S4487   | Unread private fields                             | Remove |
| S3241   | Methods returning `void` not used in interfaces   | Return the computed value |
| S1066   | Collapsible if statements                         | Combine |
| S1117   | Local variables should not shadow class fields    | Rename local |

## How to Use This Reference

1. After `scripts/scan-sources.sh` lists target files, inspect each file for patterns matching the rules above.
2. Apply the "Fix Summary" action; verify against `SKILL.md` → "Fix Principles" (preserve behavior, minimal change, no new warnings).
3. Record the rule ID in the final summary report table.
