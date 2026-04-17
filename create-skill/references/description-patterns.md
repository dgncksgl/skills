# Description Patterns

Read this when writing the `description` field in a SKILL.md frontmatter, or when evaluating whether a description is strong enough to trigger reliably.

## Mandatory Structure

```
<WHAT it does in one sentence>. Use when <concrete trigger scenarios>. Do not use when <anti-scenarios>. [Use proactively when <situation>.]
```

Every description MUST contain:
1. **WHAT** — one sentence saying what the skill does
2. **Use when** — explicit trigger phrases (English AND Turkish)
3. **Do not use when** — at least one negative trigger
4. **Domain nouns** — file types, tool names, rule IDs, framework names

Character limit: **1024 characters**. Target: 900-1000 chars.

## 6 Full Examples

### sonarqube-issue-fixer
```
Fix SonarQube bugs, vulnerabilities, code smells, security hotspots, and cyclomatic complexity violations across Java, Python, Kotlin, TypeScript, JavaScript, Go, and C# codebases. Use when asked to fix SonarQube issues, resolve code smells, reduce cyclomatic complexity, clean up static analysis warnings, improve code quality based on SonarQube rules, or when the user says "sonar sorunlarını çöz", "kod kokularını gider", "sonar bulgularını düzelt", "statik analiz hatalarını gider", "sonarqube issuelarını çöz". Do not use for general refactoring unrelated to SonarQube rules. Language-agnostic: detects build system from pom.xml, build.gradle, pyproject.toml, tsconfig.json, go.mod.
```

### type-safety-fixer
```
Fix IDE type checking warnings ("Expected type X, got Y") across Python, TypeScript, Java, Kotlin, Go, and C#. Use when asked to fix type warnings, type mismatches, "Expected type" errors, type annotation issues, or when user says "tip uyarılarını gider", "tip hatalarını düzelt", "type annotation issuelarını çöz", "tür uyumsuzluklarını düzelt". Inspects library source code to find correct types, then applies minimal fixes such as type annotations, casts, constructors, or narrowing. Do not use for runtime type errors or general refactoring unrelated to static type checking.
```

### git-commit-messaging
```
Generate standardized, widely accepted Git commit messages by analyzing staged changes (git diff --staged) in the current project. Use when asked to write a commit message, generate a commit, or when user says "commit mesajı yaz", "commit mesajı oluştur", "commit yaz". Follows Conventional Commits format with scope and body when needed. Do not use for pull request descriptions, changelogs, or release notes.
```

### migrate-to-uv
```
Migrate any Python project from pip, Poetry, Pipenv, or Conda to the uv package manager and PEP 621 pyproject.toml. Use when asked to switch to uv, convert package management, set up uv, migrate dependencies to uv, or when user says "uv'ye geç", "poetry'den uv'ye geç", "pip'ten uv'ye migrate et". Handles pyproject.toml rewrite, lockfile generation, CI/CD updates (GitHub Actions, GitLab CI, Docker). Do not use for non-Python projects or for projects already using uv.
```

### restructure-agent-code
```
Restructure raw OpenAI Agent Builder SDK code into this project's established package layout (agent/, config/, guardrail/, model/, workflow/). Use when the user pastes agent builder output, asks to integrate agent SDK code, wants to reorganize agent code to match project structure, or says "agent builder çıktısını projeye entegre et", "ajan kodunu paket yapısına uyarla". Do not use for non-OpenAI agent frameworks, general Python refactoring, or projects without an established agent package structure.
```

### create-skill (this skill)
```
Create new Claude skills (scaffold + fill), validate existing skills for compliance, or audit skills with a 0-100 score and refactor suggestions. Use when asked to create a skill, author a skill, scaffold a skill, audit a skill, validate a skill, or when user says "skill oluştur", "yeni skill yaz", "skill üret", "skill'i denetle", "skill audit et", "skill'i standartlara uydur". Do not use for editing skills inside ~/.cursor/skills-cursor/ (Cursor-reserved), generic documentation editing, or single-file refactoring.
```

## Anti-Pattern Table

| Anti-Pattern | Why It Fails | Fix |
|---|---|---|
| "Helps with code quality" | No domain noun, too vague | Name the tool: "Fix SonarQube issues" |
| "I can fix type errors" | First-person, no trigger phrase | "Fix IDE type warnings... Use when..." |
| "Useful for Python projects" | No WHEN, no NOT-WHEN | Add trigger scenarios and negative |
| "Refactors your code" | Generic, no rule ID or file type | Specify what kind: "Reorganize into agent/, config/..." |
| Description > 1024 chars | Gets truncated silently | Stay at 900-1000 chars |
| No Turkish triggers | Fails for TR-speaking users | Add ≥3 TR phrases with correct diacritics |

## Turkish Character Guidance

Always use correct Turkish diacritics, not ASCII transliterations:

| Correct | Wrong |
|---|---|
| `çöz` | `coz` |
| `gider` | `gider` (ok, no diacritic) |
| `düzelt` | `duzelt` |
| `oluştur` | `olustur` |
| `uyarılarını` | `uyarilarini` |
| `şöyle` | `soyle` |

The model tokenizer handles UTF-8 correctly; ASCII transliterations are a different token sequence and reduce match probability.
