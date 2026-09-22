---
name: software-factory
description: Run a task end-to-end through an isolated build → adversarial review → human approval → merge pipeline, using a separate agent for each stage. Use when the user says "software factory", "run this through the factory", "build and review this", "fix issue N and review it", "take this from idea to merged PR", or asks for work done in a worktree with an independent code review before it reaches them. Supports an opt-in auto-merge mode (`/software-factory 42 auto`, "merge automatically") that lands the PR unattended only at 9/10-or-better review confidence with no human-eyes items and green checks. Orchestrates factory-implement, factory-review, factory-handoff, and factory-land.
---

# Software factory

You are the **controller**. You do not write the feature, you do not review it,
and you do not merge it. You move one run through four stages, each done by a
skill that can do only its own job:

```
factory-implement  →  factory-review  →  factory-handoff  →  factory-land
   (subagent)           (subagent)         (this session)     (this session)
   isolated worktree    PR-only context    user decides       merge + cleanup
        ^                    |
        +--------------------+
         proof kickback: visual proof was possible and is missing
```

**Read `references/conventions.md` (next to this file) before starting.** It
defines the slug, branch, worktree, lock, run-state, proof, and PR rules every
stage obeys.

Invoke as `/software-factory <task or issue number> [auto]`.

## 1. Frame the run

Settle these before spawning anything:

- **Task statement** — one paragraph, in the user's own terms, of what "done"
  means. If the input is an issue number, read it: `gh issue view <n> --comments`.
- **Slug** and **branch** (conventions).
- **Home repo** path and **base branch**.
- **Merge mode** — manual (default) or auto.

### Merge mode

Set `autoMerge: true` when the invocation says so, either as the bare word
`auto` after the target, or in the task text:

```
/software-factory 42 auto
/software-factory "fix the export timeout and merge automatically"
/software-factory 42            → manual (default)
```

Trigger phrases: `auto`, "auto-merge", "merge automatically", "merge it if it's
clean", "land it without me", "don't wait for me". Anything ambiguous is
**manual** — ask rather than assume, because the cost of guessing wrong is an
unreviewed merge.

Auto mode does not skip review or the handoff audit. It removes only the wait
for the user's approval, and only when every gate in conventions →
*Auto-merge gate* holds — chiefly a review confidence of **9/10 or better** and
an empty *Needs human eyes*. Any gate unmet and the run falls back to a normal
handoff.

`autoMerge` applies to this run only. It never carries to the next one.

Ask the user only about decisions that are genuinely theirs and that the issue
and code do not settle — a contradictory spec, or a real fork in the approach.
Investigate first; most ambiguity dissolves on reading the code.

Preflight: Git repo with a GitHub remote, `gh auth status` clean, home repo tree
clean (a dirty home tree is fine for the *worktree*, but you need `git fetch` to
work and you need the user to not be mid-surgery — ask if unsure).

Write the run-state file, then tell the user the plan in three lines:

```
Run 42-login-redirect · branch Fix_42 · base main
Worktree C:/Code/.sf-worktrees/myapp/Fix_42
Merge mode: auto (merges only at 9/10+ with no human-eyes items)
Stages: implement → review → audit → merge
```

State the merge mode explicitly in that block every time, including when it is
manual. The user should never have to remember which mode a run is in.

## 2. Stage 1 — implement

Spawn a **fresh subagent** (`Agent`, `subagent_type: general-purpose`, run in the
background so the user can interject). Its prompt must contain the task
statement, the run-state file path, and an instruction to invoke the
`factory-implement` skill — nothing about how you would have done it.

```
Invoke the `factory-implement` skill.
Run state: C:/Code/myapp/.git/software-factory/runs/42-login-redirect.json
Task: <verbatim task statement>
Do only what that skill describes. Report the PR number and URL when done.
```

Do not poll and do not start the next stage early — you are notified when it
finishes. While waiting, stay available to the user.

If it reports **blocked** (lock collision, ambiguous spec, scope much larger than
stated), surface that to the user and stop. Do not fix it yourself.

## 3. Stage 2 — adversarial review

Spawn a **second, separate** subagent. This one gets **only the PR number and
repo** — never the task statement, never your framing, never the implement
agent's reasoning. Its independence is the entire point, and leaking context
destroys it.

```
Invoke the `factory-review` skill.
Repo: owner/name
PR: 118
You have no other context, and must not seek any outside the PR itself.
```

Outcomes:

- **Passed** (≥ 90% confidence) — go to stage 3.
- **Proof kickback** — the PR could have carried before/after images and did
  not. Send it back to the builder, not on to the user (below).
- **Unresolvable** (5 passes without reaching confidence) — do **not** send it
  back in. Report to the user that the PR needs rewriting, recommend closing the
  PR and starting a fresh run with a revised task statement, and stop. Preserve
  the review agent's findings — they are the input to the rewrite.

### Proof kickback

Spawn a fresh `factory-implement` subagent on the **same branch and worktree**,
passing the reviewer's kickback message verbatim and nothing else you know:

```
Invoke the `factory-implement` skill. This is a proof-kickback re-entry —
the branch, worktree, lock and PR already exist and are yours.
Run state: C:/Code/myapp/.git/software-factory/runs/42-login-redirect.json
<the reviewer's kickback message, verbatim>
Capture the proof it asks for, publish it, update the PR, and report back.
```

Then run stage 2 again with a **new** review subagent, from scratch — the old
one saw a PR that no longer exists. Increment `kickbacks` in run state and reset
`reviewPasses`.

**Two kickbacks maximum** (conventions). If a third review still finds the proof
missing, stop looping and take the run to stage 3 with the missing proof as the
headline, so the user decides whether to accept it.

Never tell the review agent that a previous review kicked this PR back, and
never argue with a kickback on the builder's behalf. If the proof is genuinely
unobtainable, that surfaces to the user — it is not something the controller
waives.

## 4. Stage 3 — audit and surface

Invoke `factory-handoff` **in this session** (not a subagent) — it has to talk to
the user and watch for their response. It checks the PR against the original task
statement, verifies proof and risk callouts are present, and gives a link, a
status, and a merge recommendation.

This stage runs in **both** modes. In auto mode its audit is the only independent
check left between the reviewer's own score and a merge, so it is never skipped
or abbreviated.

**Manual mode** — hand the verdict to the user and wait. If they leave review
comments, pass them to a **new** `factory-review` subagent (comments + PR only),
then return here. Repeat until they approve or call it off.

**Auto mode** — apply the auto-merge gate (conventions). If every gate holds,
say so and go straight to stage 4:

```
Auto-merge gates met (9/10, no human-eyes items, green) — merging.
```

If any gate fails, fall back to the manual path: report which gate stopped it,
in one line, and wait for the user as usual.

```
Auto-merge deferred — confidence 8/10 and 2 human-eyes items. Over to you.
```

A deferred auto-merge is a normal outcome, not an error. Never re-run review to
chase a higher score, and never waive a gate because the run was marked auto.

## 5. Stage 4 — land

Invoke `factory-land` in this session: verify the merge is permitted, merge,
close the issue, remove the worktree, delete the branch, release the lock, mark
the run `done`.

What counts as permission depends on the mode — explicit user approval in manual
mode, the full gate set in auto mode. `factory-land` re-checks this itself rather
than trusting the controller; pass it the run-state path so it can see the mode.

After an auto-merge, report what landed **and what the user did not see**, so an
unattended merge is never silently unattended:

```
#118 auto-merged · 9/10 · 2 review passes · issue #42 closed
You did not review this one. Diff: <url>/files
```

## 6. Next run

Report one summary line (`#118 merged · 3 review passes · 9/10`), then ask
whether to start another run. Runs are sequential by default — if the user wants
two at once, each gets its own slug, branch, worktree and lock, and you must
confirm they touch different code before starting the second.

## Rules

- **One job per agent.** The implementer never reviews its own work; the reviewer
  never knows what was asked for; neither merges.
- **Never reach across a boundary.** If a stage agent stalls, re-spawn it or
  surface the problem — do not finish its work yourself.
- **Never merge without explicit user approval** — unless the user put this run
  in auto mode *and* every auto-merge gate holds. Auto mode is the only path
  around this rule, it is opt-in per run, and it never widens on its own.
- **Never leave a worktree or lock behind.** If a run is abandoned, run the
  cleanup half of `factory-land` and say so.
- Report faithfully. A red build, a skipped proof, or a review that stalled gets
  said out loud with its output.
