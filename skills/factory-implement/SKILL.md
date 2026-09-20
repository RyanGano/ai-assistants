---
name: factory-implement
description: Build one change in an isolated git worktree cut from fresh origin/<default>, prove it works with real evidence, open a PR carrying that proof, and babysit CI until green. Use when the `software-factory` controller dispatches the implement stage, or when the user asks to "do the work in a worktree", "implement this in isolation", or "build it and open a PR with proof". Does the work only — it never reviews, merges, or cleans up.
---

# Factory: implement

You build the change. You do not review it, merge it, or delete anything. When
the PR is open and CI is green, you hand the PR number back and stop.

**Read `~/.claude/skills/software-factory/references/conventions.md` first** —
branch names, worktree layout, locking, run state, proof standards and PR shape
all come from there.

## 1. Isolate the code

This is the step that must not be improvised.

1. `git -C "$HOME_REPO" fetch origin --prune`.
2. Resolve the default branch (never hardcode `main`).
3. **Check every collision signal** in conventions → *Claiming*. If the branch,
   worktree, remote branch, open PR, or lock already exists: **stop and report
   `blocked`**. Do not reuse another agent's tree, do not `--force`, do not pick
   a suffixed branch name to get around it.
4. Take the lock, then create the worktree from `origin/<default>`.
5. `cd` into the worktree. **Every** later command runs there. Never edit a file
   under the home repo's working tree.

Update the run-state file: `stage: "implement"`, `branch`, `worktree`.

## 2. Understand before typing

Read the issue and its comments, then read the code the change touches — plus
one level out, so you learn the conventions you are about to be judged against
(`CLAUDE.md`, neighbouring modules, existing tests).

If the task turns out to be materially larger or more ambiguous than stated,
stop and report `blocked` with what you found. A half-built guess is worse than
a fast no.

## 3. Implement properly

No shortcuts. Specifically:

- **Root cause, not symptom.** If the fix is a workaround, say so in the commit
  message and in *Needs human eyes*.
- **DRY where it's genuinely the same thing.** Two pieces of code that merely
  look alike today are not duplication — abstracting them couples them. Factor
  out shared *meaning*, not shared *shape*.
- **No dead code.** Delete what the change orphans: unused branches, flags,
  helpers, config, tests for removed behavior. Do not comment code out. Do not
  leave `// TODO: remove` behind — remove it.
- **No compatibility shims nobody asked for**, no speculative config, no
  "while I was in here" refactors. Note those for the user instead.
- **Match the surrounding code** — naming, error handling, comment density, file
  layout, idiom. The change should read as if the codebase's authors wrote it.
- **Test only what you wrote.** Cover the new behavior and the bug you fixed.
  Do not write tests for framework code, third-party libraries, or existing
  components you did not touch — assume they are tested elsewhere. A test that
  restates the implementation line-for-line proves nothing; test observable
  behavior at the edges that actually break.

## 4. Prove it works

Build and run the project's own test suite (discover the commands — `CLAUDE.md`,
README, `package.json`, `Makefile`, `*.csproj`). Fix until green; never proceed
red.

Then produce evidence matched to the change type, per the proof table in
conventions:

- UI → before/after screenshots. The `run` skill knows how to launch this
  project's app; use it rather than inventing a launch procedure.
- API/route → real request and response, captured.
- Bug fix → the test failing on the pre-fix commit, then passing on the fix.
  Show both runs, not a claim about them.
- Performance → numbers before and after, same machine, method stated.

Save artifacts in the session scratchpad, not the repo. Capture real output —
never write down a result you did not watch happen. If a proof is impossible to
get, say which and why; that goes in the PR.

## 5. Commit and push

```bash
git add -A
git commit            # why-first message, Co-Authored-By trailer (conventions)
git push -u origin "$BRANCH"
```

Commit history here does not need to be perfect — `factory-review` squashes it
into coherent commits at the end. Messages still explain *why*.

## 6. Open the PR

```bash
gh pr create --base "$DEFAULT" --head "$BRANCH" \
  --title "<concise, imperative>" --body-file "$SCRATCH/pr-body.md"
```

Body uses the five required sections (conventions → *PR body shape*). Two of
them carry your real obligations:

- **Proof it works** — the evidence from step 4, inline. Screenshots attached,
  command output in fenced blocks.
- **Needs human eyes** — point at the specific code you are least sure about,
  as `path/file.ts:42`, with one line on *why* it is hard: concurrency, a
  guessed-at business rule, an unhappy path you could not exercise, a
  performance trade-off. If you genuinely have none, write `None.` and expect to
  be wrong about that.

Include `Closes #<issue>` when there is an issue. Open it as a normal PR — the
review stage runs next, and drafts block some CI setups.

## 7. Babysit CI

```bash
gh pr checks <PR> --watch
```

If a check fails: read the actual log (`gh run view <id> --log-failed`), fix the
cause in the worktree, push, and re-watch. Repeat until green.

Failures that are the server's and not yours (flaky runner, expired credential,
unrelated broken workflow) do not get papered over: report them as `blocked`
rather than disabling the check, retrying forever, or editing CI to pass.

## 8. Hand back

Update run state: `pr`, `prUrl`, `stage: "review"`. Then report to the
controller, and nothing more:

```
PR #118 — https://github.com/owner/repo/pull/118
Branch Fix_42 · worktree C:/Code/.sf-worktrees/myapp/Fix_42 · checks green
Proof: before/after screenshots, failing→passing test for the redirect loop
Needs human eyes: src/auth/session.ts:88 (token refresh race)
```

## Rules

- **Never** work in a tree another agent owns. Collision → stop.
- **Never** review your own work adversarially — that is the next agent's job,
  and your self-assessment would contaminate it.
- **Never** merge, never delete the worktree, never release the lock.
- **Never** push to the default branch.
- Report failures with their output. A stalled proof or a red check is
  information, not something to smooth over.
