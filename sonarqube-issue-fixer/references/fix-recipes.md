# Fix Recipes

Read this in Step 4 before fixing a rule family for the first time in a run.

Every fix keeps observable behaviour: return values, raised exceptions, log text, public names and signatures, serialized field names. When a fix cannot keep it, it is an `ask`.

## Naming

- Follow the file's existing naming first. Where the file gives no lead, use the language's convention: `snake_case` (Python), `camelCase` (Java, Kotlin, JS/TS, C# locals), `PascalCase` (types; exported Go names), and do not start new names with `_`.
- Constants: `UPPER_SNAKE_CASE` in Python, Java, Kotlin and JS/TS; follow the file's existing constants if it has any.

## Duplicated literals (S1192)

1. Only the literal named in the finding; leave literals below the threshold alone.
2. Name the constant after its meaning (`DEFAULT_CURRENCY`), not its text (`TRY_STRING`). The same text with two meanings (a dict key and a log label) gets two constants, or stays a literal where it is part of a protocol (an API parameter name, a JSON key the other side defines).
3. Reuse an existing constant with the same meaning before adding one. Place new constants with the file's other constants (module top in Python, `private static final` in Java, top-level `const` in JS/TS).
4. Never replace by text across files with a script: the same text can be a message in one place and a protocol name in another. Example: `options["token"]`, a parameter name a client library defines, must not become an unrelated `ACCESS_TOKEN` constant.

## Unused code (S1481, S1854, S1128, S1144, S1068, S1172)

- Remove the declaration; keep the right-hand side only when it has a side effect (I/O, a write, a call that changes state): `result = save(x)` → `save(x)`. A call without side effects (`currency.upper()`, `len(x)`) goes too: a bare `currency.upper()` is itself a Sonar finding (S2201). If the call can raise on values the code really receives (`len(payload)` where the request body can be None), removing it changes which exception is raised: that is a decision. "Really receives" means what callers in the project pass, so check them: `key.strip()` whose callers all pass strings is removed.
- S1172 (`check-api`): a signature that a framework or base class requires (route handler, pytest fixture, Spring handler, event listener, interface or override) is a false positive; a parameter that callers outside the file pass is a decision; otherwise remove it and update the in-file callers.
- S1128 (`check-api`): in Python an unused import can be a re-export (`from pkg.models import User` in `__init__.py`, imported elsewhere as `from pkg import User`); grep for imports of that name from this module, and if any exists or the name is in `__all__`, it is a false positive. Java, Kotlin and JS/TS imports cannot be re-exported this way: remove them. An import kept for what the module does when it loads (registers signal handlers, plugins or routes, applies a polyfill or monkeypatch; often a project module whose name is never used) is a decision, not a removal: deleting it silently stops that setup.
- S5806 (`check-api`): renaming a module-level name that shadows a builtin (`id = 3`) breaks `from module import id` elsewhere; a local or parameter name is renamed within its scope.
- Cascade: after a removal, re-check the scope for names that only the removed code used.

## Complexity (S3776, S107)

- S3776: guard clauses and early returns, extract a well-named helper per responsibility, replace long `if/elif` chains with a lookup table, name compound conditions. Put the helper next to its caller and do not export it (Java `private`; Python: name it per Naming and keep it out of `__all__` and imports elsewhere). Measure again: the finding must drop to 15 or below. If it cannot without changing behaviour, edit the whole refactor back (a partial gain still leaves the finding open) and list it as a decision.
- S107 (`check-api`): introduce a parameter object (dataclass, record, interface) only when no caller outside the file uses the function; otherwise it is a decision.

## Exceptions (S5754, S2737, S112, S108, BROAD-EXCEPT, S2221)

- Bare `except:` or `except BaseException:` that does not re-raise (S5754, `fix`): replace it with `except Exception:`. Only `SystemExit`, `KeyboardInterrupt` and `GeneratorExit` stop being swallowed, which is what Sonar asks for; every other error is still caught. Exception: when the `try` body calls `sys.exit()` or raises `SystemExit` itself, the swallowed exit is intended: make it a decision. An exit raised deeper (a function called in the `try` body calls `sys.exit()`) is the planned change: fix it and say in the report that this exit now ends the program. Likewise when the `try` body can suspend (`await`, `async with`, `async for`, an async comprehension), `asyncio.CancelledError` (and `BaseExceptionGroup` on 3.11+) would stop being swallowed too, which changes task cancellation: make that one a decision instead. The new `except Exception:` then shows up as BROAD-EXCEPT, a decision below.
- `except SystemExit` that does not re-raise (S5754, `ask`): re-raising makes the program exit where it now carries on, so it is a decision.
- Broad catches (`except Exception`, `catch (Exception e)`; BROAD-EXCEPT, S2221) are `ask`, because narrowing can turn a swallowed error into a crash: do not change them in the run. Work out the exception list with the steps below and put it in the report's decisions list; narrow only after the user approves:
  1. List the calls in the `try` body. For each library, read its exception hierarchy (read-only): Python `.venv/lib/*/site-packages/<lib>/exceptions.py` or `errors.py`; Java the library's sources or Javadoc; JS/TS `node_modules/<lib>/`; Go the package's exported `Err*` values.
  2. Catch the library's base exception plus the standard exceptions the body can raise (dict access → `KeyError`; I/O → `OSError`; parsing → `ValueError`).
  3. If you cannot list them with confidence, leave the broad catch and report it: narrowing too far turns a handled error into a crash.
- An empty `catch` (S108): log or rethrow, or add a comment saying why ignoring is correct; never delete the `try`.
- S112: throw a specific existing exception type, or a new one if the project defines its own hierarchy.

## Security (ask first)

Do not change these in the run. In the report's decisions list, give the risk and the proposed change; fix them in a follow-up run once approved:
- S2068 (hard-coded credential): read it from an environment variable or the project's secret store; the old value stays in git history, so the user must rotate it. Test fixtures with fake values are false positives.
- S2077 (SQL): bind parameters instead of string formatting; keep the statement identical apart from the placeholders.
- S4790, S2245: a stronger hash or `secrets`/`SecureRandom` only when the value is used for security; checksums and cache keys are false positives.
- S4830, S4423: re-enable certificate verification or raise the TLS version; this can break calls to servers with bad certificates, so ask.

## TODO and FIXME (S1135, S1134)

Report them; do not delete the comment or do the TODO's work unless the user asks.

## False positives

When the finding is wrong for this code (a generated pattern, a protocol string, a framework-required signature), leave the code, and list the finding with a one-line reason so the user can mark it "false positive" in SonarQube.
