---
name: delete-unused-branches
description: Delete local Git branches whose work is already fully merged into the default branch (handles squash/rebase merges, which `git branch --merged` misses). Use when the user asks to "delete unused branches", "clean up branches", "remove merged/stale local branches", or "prune branches". Verifies each branch is safe before deleting and lists anything uncertain for the user to decide.
---

# Delete unused branches

Clean up local-only branches that have already been merged, while protecting any
branch that still has unique unmerged work. The hard part is that squash- and
rebase-merged branches are **not** ancestors of the default branch, so
`git branch --merged` reports them as unmerged. This skill uses GitHub PR state
plus content verification instead.

## Safety rules (never violate)

- **Never** delete the currently checked-out branch or the default branch
  (`main`/`master`).
- Only delete a branch once its content is confirmed to be in the default branch.
- A branch that is **ahead of its remote** (has unpushed commits) is only safe if
  those extra commits' changes are *also* already in the default branch — verify
  this explicitly.
- Anything you cannot confirm is merged → **list it, do not delete it.** Offer to
  ask the user about each uncertain branch.
- Always record each deleted branch's tip SHA in the final report so it can be
  recovered (`git branch <name> <sha>` or via `git reflog`).

## Procedure

### 1. Sync and survey

```
git fetch --prune                # drop remote-tracking refs deleted on GitHub
git branch -vv                   # local branches + tracking info (note "ahead N")
```

Determine the default branch (don't hardcode `main`):

```
git symbolic-ref --quiet --short refs/remotes/origin/HEAD   # e.g. origin/main
```
Fall back to `main`, then `master`, if that fails.

### 2. Get authoritative merge status from GitHub

```
gh pr list --state all --limit 100 --json number,title,headRefName,state,mergedAt \
  --jq '.[] | [.state, .headRefName, (.mergedAt // "-"), (.number|tostring), .title] | @tsv'
```

Match each local branch (except the current branch and the default branch) to PRs
by `headRefName`. A branch is a **merge candidate** if it has a `MERGED` PR.

If `gh` is unavailable or there's no GitHub remote, skip this step and rely on the
content check in step 3 (a branch is safe only if step 3 shows it adds nothing new
to the default branch); otherwise treat it as uncertain.

### 3. Verify content is actually in the default branch

For each merge candidate, confirm it introduces nothing that the default branch
lacks. The reliable squash-aware check: list the files the branch changes relative
to the default branch's tip and confirm none of the branch's *own* work is missing.

- Quick pass — files differing between the branch and the default branch tip:
  ```
  git diff --stat <default>..<branch>
  ```
  Files here are normally the default branch's **newer** work that the branch lacks
  (expected, harmless). What matters is that none of the **branch's own** changes
  are missing from the default branch.

- For a branch that is **ahead of its remote**, check the unpushed commits
  specifically. Get them with `git log <remote-tracking>..<branch> --oneline` (or
  inspect `git log <default>..<branch>`), then confirm their touched files are
  identical in the default branch:
  ```
  git diff --stat <default> <branch> -- <file1> <file2> ...
  ```
  Empty output ⇒ that content is already in the default branch ⇒ safe. Non-empty
  ⇒ the branch has unique unmerged work ⇒ **uncertain, flag it.**

### 4. Classify

- **Safe to delete**: `MERGED` PR (or fully contained in default branch) **and** no
  unique unmerged content.
- **Uncertain**: no PR / `CLOSED` (not merged) PR, or unpushed commits whose content
  isn't in the default branch, or any case you can't confirm. List these; don't
  delete. Ask the user per-branch if they want guidance.

### 5. Delete and report

Squash/rebase-merged branches aren't ancestors of the default branch, so
`git branch -d` will refuse them. Use `-D` for the confirmed-safe set only:

```
git branch -D <branch1> <branch2> ...
```

Then report:
- A table of every local branch: PR #, state, and "in default branch?".
- Which branches were deleted, **with their tip SHAs** (from the `-D` output) for
  recovery.
- Any uncertain branches left untouched, and why — so the user can decide.

## Notes

- All commands work in both PowerShell and Bash; no shell-specific syntax is needed.
- `git branch -vv` flags ahead/behind state — always check it before deleting; an
  "ahead N" branch is the classic case of local work that was never pushed or merged.
