---
name: fix-github-issue
description: Pick an open GitHub issue, fix it end-to-end, and open a Draft PR — then loop to the next. Use when the user asks to "fix a bug", "work through open issues", "fix github issues", "grab an issue and fix it", or "start the bug-fixing loop". Works in any Git repo with a GitHub remote; language- and stack-agnostic. Builds and tests until green, pushes a `Fix_<issueNum>` branch, and opens a draft PR for review.
---

# Fix a GitHub issue (loop)

Work open GitHub issues one at a time: choose one, fix it, verify it builds and
tests pass, push a `Fix_<issueNum>` branch, and open a **Draft** PR. Then return
to step 1 for the next issue until the user stops or no suitable issues remain.

## Prerequisites (check once at the start)

- A Git repo with a GitHub remote and `gh` authenticated (`gh auth status`).
- The working tree is clean, or the user has told you what to do with pending
  changes. **Never** start on a dirty tree — stash or ask first.
- Start each issue from the up-to-date default branch. Always `fetch` explicitly
  before switching/pulling — don't rely on a stale local view of `origin/<default>`:
  ```
  git fetch origin
  git switch <default> && git pull --ff-only
  ```
  Detect the default branch with
  `git symbolic-ref --quiet --short refs/remotes/origin/HEAD` (fall back to
  `main`, then `master`). Do not hardcode `main`. Do this at the start of **every**
  loop iteration, not just the first — a prior iteration's push or someone else's
  commit may have moved `origin/<default>` since you last checked.

## The loop

### 1. Survey open issues

```
gh issue list --state open --limit 50 \
  --json number,title,labels,assignees,createdAt \
  --jq 'sort_by(.number) | .[] | [(.number|tostring), .title, ([.labels[].name]|join(",")), ([.assignees[].login]|join(","))] | @tsv'
```

Skip issues that are already assigned to someone else, blocked, or that a
`Fix_<n>` branch/PR already exists for (`gh pr list --state all --json headRefName`).

### 2. Choose an issue to fix

Work strictly **FIFO — oldest issue number first** among the remaining
(unassigned-to-others, unblocked, no-existing-PR) issues. Do not pick based on
perceived difficulty, clarity, or bug-vs-enhancement — take the oldest one as-is.
The only exception is scope: if step 3/4 investigation reveals the oldest issue
is far too large or ambiguous to fix in this pass (see the "much larger than
expected" rule below), surface that to the user and ask whether to skip it or
pause, rather than silently reordering. Announce which issue you're picking (its
number) before diving in. If the user named a specific issue, use that one
instead of the FIFO pick.

Announce the pick as a **bold headline on its own line**, as the first thing you
say once the issue is chosen and before moving on to step 3:

```
**Fix #42 — login redirect loop**
```

Use a short few-word description derived from the issue title. Repeat this
headline each time the loop advances to a new issue, so the transcript stays
scannable when one chat covers several issues.

Do **not** try to rename the chat. There is no `/rename` command in Claude Code,
and slash commands can't be invoked from inside a skill anyway — emitting one as
text just produces an "invalid command" message. The chat title is generated
automatically by the client from the early conversation; the headline above is
what makes the current issue obvious. The user can rename the chat themselves
from the UI if they want.

### 3. Ask questions only if genuinely blocked

Read the issue body and comments (`gh issue view <n> --comments`). Investigate the
code first — most ambiguity resolves by reading. Use `AskUserQuestion` **only** for
decisions that are the user's to make and that you cannot settle from the issue or
the code (e.g. desired behavior when the spec is contradictory, or which of several
valid fixes they prefer). Don't ask for things you can verify yourself.

### 4. Make the fix

- Create the branch first: `git switch -c Fix_<issueNum>`.
- Reproduce the bug if feasible (a failing test is the best repro), then fix root
  cause, not symptoms. Match the surrounding code's style and idioms.
- Add or update a test that would have caught the bug when it's reasonable to do so.
- Keep the change scoped to the issue. Note unrelated problems for the user rather
  than fixing them in the same PR.

### 5. Build → test → fix, in a loop

Discover the project's own commands rather than guessing — check `CLAUDE.md`,
`README`, `package.json` scripts, `Makefile`, `.sln`/`.csproj`, etc. Run the
build, then the tests. If either fails, fix and re-run. **Do not proceed until the
build is clean and the relevant tests pass.** Run linters/formatters if the project
has them. Honor any project-specific instructions in `CLAUDE.md` (e.g. stopping
background servers when done).

### 6. Commit and push the branch

```
git add -A
git commit -m "Fix #<issueNum>: <concise summary>"
git push -u origin Fix_<issueNum>
```

End commit messages with the co-author trailer:
```
Co-Authored-By: Claude Opus [version] <noreply@anthropic.com>
```
Only commit and push once the build and tests are green (step 5).

### 7. Open a Draft PR

```
gh pr create --draft --base <default> --head Fix_<issueNum> \
  --title "Fix #<issueNum>: <concise summary>" \
  --body "<body>"
```

The body should summarize the root cause, the fix, and how it was verified
(build/test results), and close the issue with `Closes #<issueNum>`. End the body
with:
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Report the PR URL. Then **return to step 1** for the next issue, resetting to the
default branch first (see Prerequisites). Continue until the user says to stop or
there are no more suitable open issues.

## Rules

- One issue per branch/PR — never bundle unrelated fixes.
- Always open the PR as a **Draft** so the user reviews before merge; do not merge.
- Never push directly to the default branch.
- If a fix turns out to be much larger than expected or needs a product decision,
  pause and surface it to the user instead of forcing it through.
- Faithfully report failures — if tests still fail or a step was skipped, say so
  with the output rather than claiming success.
