---
name: clean-pr-commits
description: Rewrite the commit history of a pull request branch into a small set of coherent, well-messaged commits grouped by intent — squashing out dead ends and reverted experiments — without changing the resulting tree. Use when the user asks to "clean up the commits", "tidy the history", "regroup/reorder commits", "rewrite the commits on PR N", or "squash out the churn". Preserves a rebase-friendly multi-commit history rather than collapsing everything into one.
---

# Clean up the commits on a PR

Rewrite a PR branch's history so that each commit is one coherent unit of intent, then
force-push. **The final tree must not change** — this is a history rewrite, not a code
change.

Invoked as `/clean-pr-commits <PR number>`, or with no argument to use the PR for the
current branch.

## The goal

Someone reading `git log` a year from now should see the decisions, not the journey.

- **Group by intent**, not by file or by chronology.
- **Squash dead ends out entirely.** If something was tried, then reverted or replaced, no
  commit should mention it. The exception: if the failure is itself the finding (e.g. "this
  API silently ignores the input"), keep that knowledge in the message of the commit that
  works around it.
- **Do not squash everything into one commit.** The user wants a reviewable, rebase-friendly
  series. If the whole PR genuinely is one idea, one commit is fine — but say so.
- **Order by dependency.** If commit B is inert or broken without commit A, A comes first.

## Prerequisites

- `gh` authenticated; the branch is pushed and has an open PR.
- **A clean working tree.** If there are uncommitted changes, stop and ask — a rewrite will
  destroy them.
- The branch is yours to rewrite. If others may have it checked out, warn the user that a
  force-push is coming.

## Steps

### 1. Establish the base and capture the original state

```
BASE=$(gh pr view <N> --json baseRefName --jq .baseRefName)
git fetch origin
ORIG=$(git rev-parse HEAD)
```

Record `$ORIG`. **Before touching anything**, save the final content somewhere outside the
repo (the session scratchpad) — the full diff against the base, plus any files that will
need rebuilding by hand:

```
git diff $BASE $ORIG > "$SCRATCH/net.patch"
git show $ORIG:path/to/file > "$SCRATCH/final/file"
```

This is the safety net. `git reset --hard` later is only safe because of it. `$ORIG` also
stays reachable via reflog and via the remote until you force-push.

### 2. Understand what actually changed

```
git log $BASE..HEAD --oneline
git diff $BASE --stat
```

Read the **net** diff, not the individual commits. A 7-commit PR with a 4-file net diff is
mostly churn. Look specifically for:

- Settings added and later removed (they should vanish entirely).
- Files created and later deleted (every edit to them is noise; only the deletion matters —
  or nothing at all if the file never existed at the base).
- Experiments, "test:", "wip", "fix typo", "revert" commits.

### 3. Propose the grouping before rewriting

Tell the user the planned commits — subject lines and what goes in each — and why anything
is being dropped. Rewriting history is destructive and easy to get subtly wrong; a few
seconds of confirmation is cheap. Proceed once they agree, or immediately if they already
told you to just do it.

### 4. Rebuild the history

```
git reset --hard $BASE
```

Then create each commit in order. Two ways to reconstruct content:

- **Whole files:** `git checkout $ORIG -- <paths>`, or copy from the scratchpad.
- **Part of a file** (one file spanning several commits): restore the base version and
  re-apply the intermediate states by editing. `git add -p` is interactive and unavailable,
  so hand-editing is normal. This is the laborious case; expect it when one config file
  carries several unrelated concerns.

Write real commit messages (see below). Never use `git rebase -i`, `git add -i`, or anything
that opens an editor — pass messages with `git commit -F -` and a heredoc.

To reuse an earlier commit's content but change its message:

```
git cherry-pick <sha>          # note: -q is not a valid flag
git commit --amend -F - <<'EOF'
...new message...
EOF
```

### 5. Verify — this is the part that matters

**Tree equality.** The rewrite must produce the same result:

```
git diff --quiet $ORIG HEAD && echo IDENTICAL || git diff $ORIG HEAD
```

If it differs, either fix it or be able to state exactly what differs and why it is
intentional (e.g. you deliberately moved a comment into a commit message). Never report a
difference you have not looked at.

**Per-commit consistency.** Check the intermediate commits, not just the tip. A commit that
removes a trigger but leaves a condition referencing it is broken history even though the
tip is fine:

```
for c in $(git rev-list $BASE..HEAD); do
  git show $c:<config file> | grep -c '<thing that should be gone>'
done
```

**Build and test at the tip.** Run the project's own commands (check `CLAUDE.md`,
`package.json`, `Makefile`). Do not push a rewrite you have not built.

### 6. Push and reconcile the PR

```
git push --force-with-lease
```

Always `--force-with-lease`, never bare `--force`. If it is rejected, someone else pushed —
stop and tell the user rather than overwriting.

Then check whether the PR body still describes the new commit structure, and update it if it
references commits that no longer exist. Re-check CI after the push.

### 7. Report

State the before/after commit count, what was squashed out and why, the ordering rationale,
and the verification results. Mention that a force-push happened so any other checkout needs
`git reset --hard origin/<branch>` rather than a pull.

## Commit messages

Subject: imperative mood, no trailing period, ideally under ~70 chars. Body wrapped at ~80.

The body should explain **why**, not restate the diff. The most valuable content is what a
reader cannot recover from the code:

- The constraint that forced the approach.
- What was tried that did not work, when that knowledge prevents someone re-trying it.
- Evidence for non-obvious claims — run IDs, error strings, measured numbers.
- Consequences and accepted trade-offs.

Prefer durable evidence in messages over in-code comments when it will age (CI run IDs and
log links expire; a commit message aging is expected and fine).

Preserve any trailers the repo uses (`Co-Authored-By:` and similar) on rewritten commits.

## Rules

- **Never change behaviour.** If you notice a bug while rewriting, tell the user; do not fix
  it in the same pass.
- **Never rewrite the default branch**, or a branch whose PR is already merged.
- Stop and ask if the working tree is dirty, if the branch has merge commits from the base
  (offer to rebase first), or if the PR already has review comments anchored to commits that
  are about to disappear.
- Report failures honestly. If tree equality could not be achieved, say so with the diff.
