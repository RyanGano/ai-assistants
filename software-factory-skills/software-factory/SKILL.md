---
name: software-factory
description: Run a task end-to-end through an isolated build → adversarial review → human approval → merge pipeline, filing whatever review left out as GitHub issues, using a separate agent for each stage. Use when the user says "software factory", "run this through the factory", "build and review this", "fix issue N and review it", "take this from idea to merged PR", or asks for work done in a worktree with an independent code review before it reaches them. Supports an opt-in auto-merge mode (`/software-factory 42 auto`, "merge automatically") that lands the PR unattended only at 9/10-or-better review confidence with no human-eyes items and green checks. Orchestrates factory-implement, factory-review, factory-handoff, factory-land, and factory-spin-off.
---

# Software factory

You are the **controller**. You do not write the feature, you do not review it,
and you do not merge it. You move one run through five stages, each done by a
skill that can do only its own job:

```
factory-implement  →  factory-review  →  factory-handoff  →  factory-land  →  factory-spin-off
   (subagent)           (subagent)         (this session)     (this session)    (this session)
   isolated worktree    PR-only context    user decides       merge + cleanup   file left-out work
        ^                    ^                   |                                as issues
        |                    +-------------------+  user comments / small decisions:
        |                         resume reviewer,  review only that change
        +----------------------------------------+  rework too big for review:
                                                    resume builder, then reviewer checks the delta
```

Nothing flows backwards from review to the builder. Review fixes what it can
itself, captures missing proof itself, and hands everything else to the user
as a list with recommendations: escalations the PR needs decided, and
spin-offs it can merge without, which become issues once it lands.

**Read `references/conventions.md` (next to this file) before starting.** It
defines the slug, branch, worktree, lock, run-state, proof, and PR rules every
stage obeys.

Invoke as `/software-factory <task or issue number> [auto]`.

## 1. Frame the run

Settle these before spawning anything:

- **Task statement** — one paragraph, in the user's own terms, of what "done"
  means. If the input is an issue number, read it: `gh issue view <n> --comments`,
  and check it for open blockers (conventions → *Blocked issues*). A blocked
  issue does not start: name its blockers and the first unblocked issue in the
  chain, and stop.
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
an empty *Needs human eyes*. Review's *Notices* never block: they are listed in
the auto-merge report instead. Any gate unmet and the run falls back to a normal
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
Stages: implement → review → audit → merge → spin-offs
```

State the merge mode explicitly in that block every time, including when it is
manual. The user should never have to remember which mode a run is in.

## 2. Stage 1 — implement

Spawn a **fresh subagent** (`Agent`, `subagent_type: general-purpose`, run in the
background so the user can interject). Keep its agent ID (see *Reuse agents*
below). Its prompt must contain the task
statement, the run-state file path, and an instruction to invoke the
`factory-implement` skill — nothing about how you would have done it.

```
Invoke the `factory-implement` skill.
Run state: C:/Code/myapp/.git/software-factory/runs/42-login-redirect.json
Task: <verbatim task statement>
Do only what that skill describes. Report the PR number and URL when done.
```

The builder hands back as soon as the PR is open and local tests pass. It does
not wait on CI, because review watches CI once, after its own push.

Do not poll and do not start the next stage early — you are notified when it
finishes. While waiting, stay available to the user.

If it reports **blocked** (lock collision, ambiguous spec, scope much larger than
stated), surface that to the user and stop. Do not fix it yourself.

## 3. Stage 2 — adversarial review

Spawn a **second, separate** subagent, and keep its agent ID too. This one
gets **only the PR number, the repo, and the worktree path**. Never give it the
task statement, your framing, or the implement agent's reasoning. Its
independence is the entire point, and leaking context destroys it.

```
Invoke the `factory-review` skill.
Repo: owner/name
PR: 118
Worktree: C:/Code/.sf-worktrees/myapp/Fix_42
You have no other context, and must not seek any outside the PR itself.
```

The reviewer runs one full pass and fixes every clear issue itself. After that,
it checks only each round of its own fixes. It repeats a full pass only when
what changed is large or high-risk. It captures any missing visual proof
itself, pushes once, and watches CI once. You do not send anything back to the
builder from this stage.

Review always finishes. Whatever its verdict, you get back a green PR with
coherent commits, a rewritten description, and a **Merge** or **Do not merge**
recommendation with its reason. Record `fullPasses`, `deltaChecks`,
`reviewedSha`, `confidence` and `reviewRecommendation` from its report, then go
to stage 3 in every case:

- **Merge** (≥ 90% confidence): the normal path.
- **Merge, with escalations**: the escalations (issues it chose not to fix, each
  with a reason and a recommendation) go to the user at stage 3. Do **not**
  route them to the builder on your own. Deciding them is the user's job.
  Spin-offs ride along to stage 3 as well; they do not block anything.
- **Do not merge**: the review's reason becomes the handoff headline. Do not
  send it back in for another round on your own. Let the user choose between
  deciding the escalations, closing the PR and starting a fresh run with a
  revised task statement, or accepting it anyway. Auto mode never merges this
  one.

## 4. Stage 3 — audit and surface

Invoke `factory-handoff` **in this session** (not a subagent) — it has to talk to
the user and watch for their response. It checks the PR against the original task
statement, verifies proof and risk callouts are present, and gives a link, a
status, and a merge recommendation.

This stage runs in **both** modes. In auto mode its audit is the only independent
check left between the reviewer's own score and a merge, so it is never skipped
or abbreviated.

**Manual mode**: hand the verdict to the user and wait. What the user says next
is routed as a **scoped follow-up**, never a fresh full review:

- **Review comments, or a decision on an escalation that the reviewer can carry
  out** (for example "do your recommendation on item 1"): resume the review
  agent with `SendMessage`. Send the comments or the decision, and nothing else.

  ```
  Follow-up on PR #118 (you reviewed through a1b2c3d).
  <the user's PR comments, or: "Apply your recommendation on escalation 1.">
  Review only the resulting change, per factory-review → Follow-ups.
  ```

- **Rework too big for review** (a redesign, a different approach, new scope
  the user now wants): resume the **builder** with `SendMessage` and the user's
  decision. When it reports the new head SHA, resume the reviewer with
  `Review the new commits since <reviewedSha>, per factory-review → Follow-ups.`

- **Park** (the user spins off an escalation the PR depends on): invoke
  `factory-spin-off` in park mode for that item, then the cleanup-only half of
  `factory-land`. The PR stays open with `Blocked by #<n>` at the top of its
  body. Report the run as parked and stop.

  To resume once the blocker lands (the user asks, or `/software-factory` is
  given an issue whose run state reads `parked`): claim a worktree on the kept
  branch, have the builder rebase it onto fresh `origin/<default>`, then resume
  the reviewer on the new commits since `reviewedSha`, and hand off as usual.

Then return here. On the re-audit, look at what changed and whether it changes
the verdict. Do not redo the parts of the audit that nothing touched. Repeat
until the user approves or calls it off.

**Auto mode** — apply the auto-merge gate (conventions). If every gate holds,
say so and go straight to stage 4:

```
Auto-merge gates met (9/10, no human-eyes items, green) — merging.
```

If any gate fails, fall back to the manual path: report which gate stopped it,
in one line, and wait for the user as usual.

```
Auto-merge deferred — confidence <n>/10 and 2 human-eyes items. Over to you.
```

A deferred auto-merge is a normal outcome, not an error. Never re-run review to
chase a higher score, and never waive a gate because the run was marked auto.

## Reuse agents, don't respawn them

Every fresh subagent starts cold. It re-reads the conventions, the skill, the
diff and the surrounding code before doing anything useful, which is the same
cost paid twice in tokens and in time. So:

- Keep the agent ID of the builder and the reviewer for the whole run. Continue
  them with `SendMessage`, which keeps their context, whenever a stage has to
  run again on the same PR.
- Spawn a fresh agent only when the old one is gone (the session restarted, or
  the agent errored out). In that case, give the new one the same minimal prompt
  its stage always gets, plus the scoped follow-up. The PR body's `Reviewed
  through <sha>` line tells a fresh reviewer where the delta starts, so it still
  reviews only the change.
- Resuming the reviewer does not compromise its independence. Everything it is
  sent is PR-shaped: review comments, its own escalations, and new commits.
  Still never pass it the task statement or the builder's reasoning.

## 5. Stage 4 — land

Invoke `factory-land` in this session: verify the merge is permitted, merge,
close the issue, remove the worktree, delete the branch, release the lock, mark
the run `done`.

What counts as permission depends on the mode — explicit user approval in manual
mode, the full gate set in auto mode. `factory-land` re-checks this itself rather
than trusting the controller; pass it the run-state path so it can see the mode.

## 6. Stage 5 — spin-offs

Invoke `factory-spin-off` in this session once the merge lands. It files every
item under the PR's `## Spin-offs` as an issue (or an ordered chain of issues)
linked back to the PR, and marks the run `done`. The user's merge approval, or
the run's auto mode, is the permission — do not ask again.

A run that ends without a merge files nothing: list its spin-offs in the closing
report and offer to file them.

After an auto-merge, report what landed **and what the user did not see**, so an
unattended merge is never silently unattended:

```
#118 auto-merged · <n>/10 · 1 full pass + 2 delta checks · issue #42 closed
Notices (not blocking): after deploy, watch for 404s on the removed /v1/export route
Spin-offs filed: #131, #132 (parent of #133–#135)
You did not review this one. Diff: <url>/files
```

Always include the *Notices* line, or `Notices: none.` Review's notices never
hold up an auto-merge, and this report is where the user sees them.

## 7. Next run

Report one summary line (`#118 merged · 1 full pass + 2 delta checks · <n>/10 · spin-offs #131 #132`), then ask
whether to start another run. Runs are sequential by default — if the user wants
two at once, each gets its own slug, branch, worktree and lock, and you must
confirm they touch different code before starting the second.

## Rules

- **One job per agent.** The implementer never reviews its own work; the reviewer
  never knows what was asked for; neither merges.
- **Review never bounces work back to the builder.** It fixes what is clear,
  captures missing proof, and escalates the rest to the user.
- **Follow-ups are scoped.** A change after review gets a review of that change,
  by the agent that already has the context, never a new full review.
- **Never reach across a boundary.** If a stage agent stalls, re-spawn it or
  surface the problem — do not finish its work yourself.
- **Never merge without explicit user approval** — unless the user put this run
  in auto mode *and* every auto-merge gate holds. Auto mode is the only path
  around this rule, it is opt-in per run, and it never widens on its own.
- **Nothing left out goes unrecorded.** Every spin-off of a merged PR becomes
  an issue linked to it.
- **Never leave a worktree or lock behind.** If a run is abandoned, run the
  cleanup half of `factory-land` and say so.
- Report faithfully. A red build, a skipped proof, or a review that stalled gets
  said out loud with its output.
