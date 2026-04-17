---
name: git-commit-messaging
description: >-
  Generate standardized Conventional Commits-style Git commit messages (in
  English) by inspecting the current branch name, `git status`, and
  `git diff` / `git diff --cached`. Produces messages in the exact format
  `branch-name - type - description` using imperative mood and one of the
  standard types (feat, fix, refactor, docs, style, test, chore, perf).
  Use when the user asks (in English or Turkish) to "write a commit
  message", "draft commit", "generate commit message", "conventional
  commit", "commit mesajı yaz", "commit mesajı oluştur",
  "commit mesajı öner", "conventional commit oluştur",
  "branch için commit mesajı ver", or has staged changes and requests a
  summary of them.
  Do not use for pull request descriptions, changelogs, release notes,
  or full commit history rewriting.
---

# Git Commit Messaging Skill

This skill assists in analyzing project changes and generating standardized, clear, and simple Git commit messages.

## Format Specification

The generated commit message MUST strictly follow this structure:
`branch-name - type - description`

Example:
`feature/login-system - feat - add user authentication logic`

The `type` and `description` MUST always be in English.

## 1. Extracting Context

When tasked with generating a commit message, follow these steps to gather the necessary context:

### Branch Name
Determine the current branch name. If the user hasn't provided it, you can retrieve it by running:
`git branch --show-current`

### Change Analysis
Analyze the modifications to understand the scope and nature of the work:
- Check modified files using `git status`.
- Review the actual code changes using `git diff` or `git diff --cached`.

## 2. Determining the Change `[type]`

Use standard Conventional Commits types to classify the work. These are the most universally understood categories. The type should be completely lowercase:

*   **feat**: A new feature (e.g., adding a new component, route, or functionality).
*   **fix**: A bug fix.
*   **refactor**: A code change that neither fixes a bug nor adds a feature (e.g., restructuring code, renaming variables).
*   **docs**: Documentation-only changes.
*   **style**: Formatting changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc).
*   **test**: Adding missing tests or correcting existing tests.
*   **chore**: Changes to the build process, auxiliary tools, or library dependencies.
*   **perf**: A code change that improves overall performance.

## 3. Formulating the `[description]`

The description is critical. It must adhere to the following principles to ensure it is the most understandable, most preferred, and uses simple language:

1.  **Use the Imperative Mood:** Always describe what the commit will do if applied. For example, use "add feature" instead of "added feature" or "adds feature".
2.  **Be Clear and Direct:** State exactly what the change achieves without using overly complex vocabulary. Skip unnecessary filler words.
3.  **Keep it Concise:** Try to keep the description under 50 characters. Focus on the "what" and "why". Leave the "how" for the diff itself.
4.  **Formatting Rules:** Start with a lowercase letter and do not end with a period.

### Good Examples:
- `handle null user object in auth service`
- `update jwt expiration time to 24 hours`
- `remove deprecated image processing library`

### Bad Examples:
- `Fixed that annoying bug where the user would sometimes get a null pointer if they tried to log in` (Too long, not imperative)
- `Updates the user model` (Not imperative, starts with capital letter)

## Example Workflow Run

1.  **User Request:** "Generate a commit message for my staged changes."
2.  **Action:** You run `git branch --show-current` -> Output is `bugfix/cart-calculation`
3.  **Action:** You run `git diff --cached` -> Output shows a corrected math formula in `CartService.java`.
4.  **Analysis:** The type is `fix`. The best description is `correct total price calculation logic`.
5.  **Output to User:** `bugfix/cart-calculation - fix - correct total price calculation logic`
