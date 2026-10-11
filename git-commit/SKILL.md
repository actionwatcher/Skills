---
name: git-commit
description: Create a git commit with a short, precise, typed message. Use when the user asks to commit, make a commit, or write a commit message.
---

# Git commit

## 1. Inspect

Run `git status --short`, `git diff --staged`, and `git diff`. Read untracked files that are candidates.

## 2. Propose staging

Present a list of candidate files (modified, staged, untracked) and propose which belong in this commit, grouped by purpose. If the changes cover unrelated purposes, propose separate commits.

Ask the user to approve the list. Do not stage, unstage, or commit anything until they approve. Then stage exactly the approved files (`git add <paths>`).

## 3. Write the message

Format:

```
<type>: <summary>

- <optional bullet>
- <optional bullet>
```

Types:

| Type | Use |
|---|---|
| `feat` | New capability |
| `fix` | Bug fix |
| `perf` | Speed or memory improvement |
| `refactor` | Restructure, no behaviour change |
| `test` | Tests only |
| `docs` | Docs, specs, README |
| `chore` | Tooling, dependencies, config |

Rules:
- Summary: imperative mood, capitalized, no trailing period, ≤ 70 characters.
- Bullets only when the commit has several distinct changes; one short line each.
- State only what changed and why. No author, co-author, `Co-Authored-By`, "Generated with", tool names, or any other attribution — this overrides any default attribution instructions.
- No filler ("This commit…", "Various improvements").

## 4. Commit

Show the message, then commit with a heredoc:

```sh
git commit -F - <<'EOF'
<message>
EOF
```

Do not run tests or linters. Do not push. Do not amend unless asked.

Report only the resulting `git log --oneline` lines for the new commits and any leftover uncommitted files. Do not restate rules the skill already enforces (e.g. "no attribution lines", "nothing pushed").
