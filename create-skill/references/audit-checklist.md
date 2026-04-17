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
| No single table > 10 rows in SKILL.md | 5 |
| No single list > 15 items in SKILL.md | 5 |
| Detailed code examples are in references/ | 5 |
| references/ directory exists and has ≥1 .md file | 5 |

### 3. Scripts Token Efficiency — 20 points

| Check | Points |
|---|---|
| scripts/ directory exists | 5 |
| ≥1 script is executable (chmod +x) | 5 |
| Deterministic logic (≥5 branches) moved to scripts/ | 10 |

If there is no deterministic multi-branch logic in the skill, award full 10 points by default.

### 4. Description Quality — 35 points

| Check | Points |
|---|---|
| description field exists in frontmatter | 5 |
| description ≤ 1024 characters | 5 |
| Contains "Use when" clause | 5 |
| Contains "Do not use" clause (negative trigger) | 5 |
| Contains ≥1 Turkish trigger phrase (ç/ğ/ı/ö/ş/ü chars present) | 5 |
| Contains ≥1 English trigger phrase | 5 |
| Contains ≥1 domain noun (tool name, file type, rule ID, framework) | 5 |

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
Current: No Turkish characters found in description
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

**scripts/ empty or missing:**
```
[PRIORITY: LOW] Scripts
Current: scripts/ directory is empty
Fix: Move any ≥5-branch if/else logic from SKILL.md into a script
Example: language detection → scripts/detect-language.sh
```
