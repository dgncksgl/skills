# Rules

Read this when `analyze` prints `review=<language>`, when you need a rule's threshold, or when you must say which rules a language was checked against.

Rule data (title, type, Sonar way membership, Main/Tests scope) for the rules the local tools map is in `scripts/data/rules.json`, generated on 2026-11-09 from SonarSource's own analyzer jars (sonar-python-plugin 5.32, sonar-java-plugin 8.46, sonar-javascript-plugin 14.4). rules.sonarsource.com no longer exists; for any other rule (the manual checklist, an imported issue) use the SonarQube server's rule page, not memory.

## Coverage per language

| Language | Tools | Sonar rules covered |
|---|---|---|
| Python | ruff 0.17.4, complexipy 8.3.0, built-in S1192 and S5754 | 41 ruff rules mapped to 33 Sonar way rules plus S1128 and BROAD-EXCEPT (see `ruff` in rules.json), S3776, S1192, S5754 |
| JavaScript, TypeScript | eslint-plugin-sonarjs 4.2.2 (SonarSource) plus ESLint's max-params | the 231 rules of the plugin's recommended config, which is SonarQube's Sonar way for JS/TS (the plugin has about 295; S1192, for example, is not in JS Sonar way), and S107; type-aware rules do not run. About 230 more Sonar way rules that SonarQube runs through other ESLint plugins (core ESLint, React, JSX a11y, TypeScript) are not checked |
| Java | PMD 7.29.0 (after install), lizard 1.25.1 | 19 PMD rules mapped to 17 Sonar way rules plus S2221 (see `pmd` in rules.json), S3776, S107 |
| Kotlin, Go, C#, Ruby, PHP, Scala, Rust, Swift | lizard 1.25.1 | S3776, S107 only: use the checklist below |

Findings marked `[not in Sonar way]` are this skill's own additions to Sonar way: unused imports (S1128, `check-api`: in Python an import can be a re-export) are fixed like the rest; broad catches (BROAD-EXCEPT in Python, S2221 in Java) are `ask` because narrowing can turn a handled error into a crash, so they go to the decisions list with the proposed exception list. List both apart in the report.

Test files are always scanned, so `sonar.test.exclusions` is ignored on purpose. For main code, the root build's `sonar.sources`, `sonar.inclusions` and `sonar.exclusions` are honoured, matched per Maven/Gradle module; a sub-module's own `sonar.*` properties are not read, so check them by hand when a sub-module sets its own. A test-folder file that `sonar.test.inclusions` leaves out is out of scope, as Sonar ignores it. A file is a test when it sits under `sonar.tests` and matches `sonar.test.inclusions` (when set). A project with Sonar settings but no `sonar.tests` (and no Maven/Gradle build, which declares `src/test` itself) has no test files for Sonar, so every file gets the main-code rules. Without any Sonar settings, the Maven/Gradle layout (`src/main`, `src/test`) and file names decide.

Scope: Sonar runs most rules on main code only. Every vulnerability rule (S2068, S2077, S4790, …) is `Main`, so a fake password in a file classified as a test (see below) is never a finding. `analyze` drops a finding when the rule's scope is `Main` and the file is a test, or `Tests` and the file is main code (for example S1192, S3776 in Java, and almost every JS/TS rule are `Main`).

## Thresholds (Sonar defaults)

| Rule | Default |
|---|---|
| S3776 Cognitive Complexity | > 15 per function |
| S107 parameters | Python > 13; Java, Kotlin and others > 7 |
| S1192 duplicated string | 3 or more occurrences in one file, literal of 5+ characters; Python also skips single words, format strings, colours, docstrings, f-strings and files named `test*` |
| S1541 / FunctionComplexity (cyclomatic) | not in Sonar way for Java or Python: do not refactor for it unless the user asks; then list functions with `uvx lizard@1.25.1 -C 10 -w <files>` and reduce them with the S3776 techniques |

PMD skips local variables named `unused*` or `ignored*` (S1481); Sonar does not, so check such names by hand. PMD's S1192 still counts literals passed to logging calls and parts of a string concatenation, which Sonar skips: treat those as false positives.

A project's quality profile can differ; when a Sonar report exists, its findings win.

## Manual checklist (review= languages, Java without PMD, files of a failed tool)

Read each scope file once and look only for these Sonar way rules:

| Rule | Look for | Action |
|---|---|---|
| S1192 | Same string literal (5+ chars) 3+ times in one main file | fix |
| S1481, S1854 | Local variable never read; value assigned and overwritten before use | fix |
| S1144, S1068 | Private method or field never used | fix |
| S1172 | Parameter never used | check-api |
| S1066 | `if` nested directly in an `if` with no `else` | fix |
| S108 | Empty block or empty `catch` without a comment | fix |
| S125 | Commented-out code | fix |
| S3358 | Nested ternary | fix |
| S112 | Throwing a generic `Exception`, `RuntimeException`, `Error` | fix |
| S2095 | Stream, connection or file not closed on every path | fix |
| S1155 | `size() == 0` instead of `isEmpty()` | fix |
| S1118 | Utility class (only static members) with a public constructor | fix |
| S2068 | Password or token literal in code | ask |
| S4790 | MD5 or SHA-1 used for security | ask |
| S2077 | SQL built by string concatenation | ask |
| S2259 | A value that can be null/nil dereferenced on some path | fix |
| S1763 | Code after `return`, `break`, `throw` or `continue` | fix |
| S1764 | The same expression on both sides of an operator (`a == a`) | fix |
| S1862 | An `if/else if` chain repeating the same condition | fix |
| S4973 | Strings or boxed numbers compared with `==` (Java, Kotlin `===`) | fix |
| S5852 | Regex with nested quantifiers that can backtrack catastrophically (`(a+)+`) | ask |
| S2092, S3330 | Cookie created without the `Secure` or `HttpOnly` flag | ask |
| S5122 | CORS allowing any origin (`*`) | ask |
| S2245 | `Random`/`Math.random` used for tokens, passwords or keys | ask |
| S1135, S1134 | TODO, FIXME | report |

Record each manual finding with the file, line and rule, like a tool finding, and say in the report that it came from reading, not from a tool.
