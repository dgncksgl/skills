# Audit Checklist

Read this when running a deep compliance audit on an existing skill, or when interpreting the output of `scripts/audit-skill.sh`.

## Scoring Rubric (100 points total)

### 1. Word Budget — 25 points

| SKILL.md word count | Score |
|---|---|
| ≤ 1000 words | 25 (ideal) |
| 1001–1500 words | 20 (good) |
| 1501–2000 words | 12 (acceptable) |
| > 2000 words | 0 (fail) |

### 2. Progressive Disclosure — 20 points

Check whether long content is correctly offloaded:

| Check | Points |
|---|---|
| Largest single table in SKILL.md has ≤ 10 data rows | 5 |
| Largest single list (bulleted or numbered) in SKILL.md has ≤ 15 items | 5 |
| SKILL.md has ≤ 3 code blocks (``` or ~~~); detailed examples are in references/ | 5 |
| references/ has ≥1 .md file (N/A, full points, when SKILL.md is ≤ 1000 words and the three checks above pass: nothing needs offloading) | 5 |

Tables and lists inside code blocks are examples, not content, and are not counted.

### 3. Scripts Token Efficiency — 20 points

| Check | Points |
|---|---|
| Deterministic logic moved to scripts/: SKILL.md code blocks hold < 5 `if`/`elif`/`case` lines | 10 |
| scripts/ contains ≥1 script | 5 |
| Every script is executable (chmod +x) | 5 |

If SKILL.md has no deterministic multi-branch logic and the skill ships no scripts, the two script checks are N/A and score full points: an empty `scripts/` directory adds nothing.

### 4. Description Quality — 35 points

| Check | Points |
|---|---|
| description field exists in frontmatter and is text | 5 |
| description ≤ 1024 characters (measured after YAML parsing) | 5 |
| Contains "Use when" clause | 5 |
| Contains "Do not use" clause (negative trigger) | 5 |
| Contains ≥3 double-quoted Turkish trigger phrases (a phrase counts if it has Turkish letters ç/ğ/ı/ö/ş/ü or ends with a Turkish verb such as `yaz`, `et`) | 5 |
| Contains an English trigger: a quoted English phrase, or ≥5 words of scenarios after "Use when" | 5 |
| Contains ≥1 domain noun (tool name, file type, rule ID, `/command`, `--flag`, framework) | 5 |

Not scored, but reported as WARN: the description appears to summarize the workflow (" then ", "→", "step N", "önce", "sonra", "ardından"). Keep steps in the body.

## Score Interpretation

| Score | Label | Action |
|---|---|---|
| 90–100 | Excellent | No action needed |
| 75–89 | Good | Minor improvements recommended |
| 50–74 | Needs Work | Refactor 2-3 areas |
| < 50 | Failing | Major rewrite required |

## Refactor Suggestion Templates

For each failed check, output a suggestion in this format:

```
[PRIORITY: HIGH/MEDIUM/LOW] <check name>
Current: <what was found>
Fix: <concrete action>
Example: <one-line example if applicable>
```

### Common Suggestions

**Word budget exceeded:**
```
[PRIORITY: HIGH] Word budget
Current: 2340 words in SKILL.md
Fix: Move rule-ID tables to references/rules-reference.md; move code examples to references/fix-patterns.md
Example: "See [Rules Reference](references/rules-reference.md) for full rule list."
```

**No Turkish triggers:**
```
[PRIORITY: HIGH] Turkish triggers
Current: Fewer than 3 double-quoted Turkish trigger phrases in description
Fix: Add ≥3 TR trigger phrases with correct diacritics
Example: 'or when user says "sonar sorunlarını çöz", "kod kokularını gider"'
```

**No negative trigger:**
```
[PRIORITY: MEDIUM] Negative trigger
Current: No "Do not use" clause found
Fix: Add at least one anti-scenario after the trigger list
Example: "Do not use for general refactoring unrelated to SonarQube rules."
```

**No domain noun:**
```
[PRIORITY: MEDIUM] Domain nouns
Current: Description uses only generic verbs ("fix", "improve", "help")
Fix: Name the specific tool, file type, or rule ID
Example: "Fix SonarQube rules S1172, S2095 in pom.xml projects"
```

**Inline branching logic:**
```
[PRIORITY: MEDIUM] Scripts
Current: SKILL.md code blocks contain ≥5 if/elif/case lines
Fix: Move that logic into a script and call it with one line
Example: language detection → scripts/detect-language.sh
```

A skill without deterministic logic needs no `scripts/` directory; never add an empty one.
