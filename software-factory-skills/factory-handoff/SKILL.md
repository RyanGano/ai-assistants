---
name: factory-handoff
description: Audit a reviewed PR against what was actually asked for, confirm it carries real proof and an honest risk list, then present the user a link, a status, and a merge recommendation — and watch for their approval or comments. In an opt-in auto-merge run it makes the merge call itself, but only at 9/10-or-better confidence with no human-eyes items and a clean match to the original ask. Use when the `software-factory` controller reaches the surface-to-human stage, or when the user asks to "show me the PR", "is this PR ready for me", or "check this PR against what I asked for". Read-only: it never changes code, pushes, or merges.
---

# Factory: surface the PR to the human

The user's attention is the scarcest thing in this pipeline. Your job is to spend
it well: verify the PR is genuinely ready to be looked at, then hand it over with
a recommendation you would stand behind.

You run **in the controller's session**, because you talk to the user. You are
read-only — no code changes, no pushes, no merges.

**Read `~/.claude/skills/software-factory/references/conventions.md`** for the
run-state file and PR-body shape.

## 1. Does it match what was asked for?

Load the run-state file and re-read the original task statement verbatim. Then
read the PR as it now stands (`gh pr view <N>`, `gh pr diff <N>`). Note the
run's merge mode while you are there — it changes what you do at step 5, but
nothing about how hard you look.

Answer plainly:

- Does the change do what was asked? Point at the code that does it.
- Is anything asked for **missing**? Name it.
- Is anything there that was **not** asked for? Scope creep gets called out, even
  when it is an improvement.
- Did review reinterpret the problem? Sometimes correctly — but the user decides
  whether the reinterpretation is the one they wanted.

A mismatch does not stop the handoff. It becomes the headline.

## 2. Is the proof real?

The PR must contain evidence, not assertions — and where the change is visible,
that evidence is images (conventions → *Visual proof first*).

- **Look at the images.** Open the PR and confirm they render, that the pair
  shows the screen the change actually affects, and that "before" and "after"
  differ in the way the PR claims. An image that does not load is not proof.
- **Images marked `Captured by review`?** The reviewer supplied proof the
  builder skipped. Treat them like any other capture and check that they show
  what the diff changes. Mention in the verdict that review produced them.
- **No images?** Then the PR must say concretely why the change has no visible
  surface, or why nobody could capture it (with the error). That claim has to
  survive a glance at the diff. If it does not, say so in the headline.
- Textual evidence alongside: a test run quoted should exist, a route exercised
  should exist. Quoted output that corresponds to nothing in the diff is a
  finding.
- CI green now: `gh pr checks <N>`.

"Proof it works: builds cleanly" is not proof, and neither is "verified manually
in the browser". Say so rather than passing it along.

## 3. Is the risk list honest?

*Needs human eyes* and *Notices* must both exist, and every item in them must be
specific — `path/file.ts:42` plus why. If both are empty on a non-trivial change,
that is itself a risk: it usually means the review looked for typos rather than
for trouble.

Each escalation (an issue review chose not to fix) must say why it was not
fixed and what review recommends. If one is missing either part, point that out
in your report. Also flag an escalation that review obviously could have fixed
itself, because that is work pushed onto the user.

Cross-check it against the diff: anything you would want a human to look at that
the PR does not mention gets added to your report (not to the PR — you do not
edit it).

Read *Notices* with one question per item: *does the user have to decide
anything here?* A notice asks only to be seen: a subtle fix, a path nobody could
exercise, a check to run after deploy. An inferred business rule, a trade-off
with another reasonable answer, or a risk the user would want to rule on before
it lands is a decision. A decision filed as a notice is mis-sorted, because it
would pass the auto-merge gate unanswered. Report it under **Decide**, say review
put it in the wrong section, and treat *Needs human eyes* as non-empty from here
on.

Then read *Spin-offs* with one question per item: *is this PR correct and
complete without it?* A spin-off the PR actually depends on is mis-sorted — it
would slip past the auto-merge gate and ship a broken change. Report it under
**Decide** as an escalation, say review put it in the wrong section, and treat
*Needs human eyes* as non-empty from here on.

## 4. Give the user the verdict

One compact block, no preamble:

```
**#118 — Fix login redirect loop** · https://github.com/owner/repo/pull/118

Status      Green · 1 full pass + 2 delta checks · confidence <n>/10 · review says merge
Matches ask Yes — redirect loop fixed at the session layer
Proof       Before/after screenshots (render OK), failing→passing test (session.concurrent)
Scope       +1 unrelated fix (stale import cleanup) in its own commit

Decide
  1. [should-fix] src/auth/session.ts:120 — 30s refresh window is a guess.
     Not fixed: no stated token lifetime. Review recommends: 60s, matching the IdP default.
Notices (for your eyes; they do not block)
  - src/auth/session.ts:88 — token-refresh race, fixed but subtle
  - After deploy: watch for 401 spikes on /auth/refresh for a day
Spin off (filed as issues after merge)
  S1. src/auth/logout.ts:30 — logout has the same redirect bug. One issue.

**Recommendation: merge after deciding item 1.**
```

List the escalations under **Decide** and number them, so the user can answer
in a word ("take 1", "leave 1", "spin off 1"). Each one shows review's
recommendation. List spin-offs under **Spin off**, numbered `S1`, `S2`, so the
user can pull one into this PR ("take S1"); saying nothing lets them be filed
after the merge.

The recommendation is one of:

- **Merge** — matches the ask, proof is real, risks are minor and listed.
- **Merge after checking X** — ready, but one specific thing needs the user's eye.
- **Do not merge yet** — a mismatch with the ask, missing or fake proof, red CI,
  or a risk the user has to rule on before it lands.

Say which, in bold, on its own line. Never pad the verdict to be agreeable.

## 5. Auto mode — decide instead of waiting

If the run state has `autoMerge: true`, everything above still happened — the
audit is not skipped, and in auto mode it is the last independent judgment before
code lands. Then work the gate table in conventions → *Auto-merge gate*. Yours to
check are the three the audit covers:

- *Needs human eyes* is exactly `None.`
- *Notices* holds no decision in disguise (step 3). Notices themselves never
  block: an auto-merge with five genuine notices still merges.
- The PR does what the task statement asked, and nothing more.
- The proof is present and spot-checks out — including the images, where the
  change has a visible surface.

- *Spin-offs* holds nothing the PR depends on (step 3).

Plus the two carried in run state: confidence **9/10 or better**, and review's
recommendation is **Merge**.

**All gates hold** → record `autoMergeDecision: "merged"`, tell the controller to
run `factory-land` in auto mode, and state plainly that it is going in unreviewed:

```
Auto-merge gates met — 9/10, no human-eyes items, green, matches the ask.
Merging without your review. Diff: <url>/files
Notices for you (not blocking):
  - After deploy: watch for 404s on the removed /v1/export route
```

List every notice from the PR in full, or `Notices: none.` Merging past a
notice is fine; merging past one silently is not. The user reads it here
instead of in the PR they did not open.

**Any gate fails** → record `autoMergeDecision: "deferred: <gate>"`, say which
gate in one line, and continue to step 6 as a normal manual handoff.

Your verdict from step 4 overrides the score. A 9/10 PR that does not match the
ask, or whose proof you could not reproduce, does **not** auto-merge — you are the
only stage that has seen the original request, and that is exactly the failure a
reviewer scoring its own work cannot catch. Never soften a finding, and never
round an 8 up, to let a gate pass.

At 9/10 the reviewer has said out loud that something caps its confidence. Read
what that something is, in the PR's *Confidence* line. If it names a risk a human
would want to weigh in on, that belongs in *Needs human eyes* — and a populated
*Needs human eyes* means no auto-merge. If it only names something to watch or
look at, it belongs in *Notices*, and you list it in the auto-merge report if
review did not. A 9 whose caveat has quietly gone unrecorded is the gap this
threshold opens; closing it is your job.

## 6. Watch for the user's response

Then wait for the user. Offer the two ways to wait and use whichever they pick:

- **Poll** — check every few minutes with
  `gh pr view <N> --json reviewDecision,state,comments,reviews`, up to a stated
  limit, then report. The `loop` skill does this properly if they want it left
  running.
- **Park it** — stop here. The run state holds everything; the user resumes with
  `/factory-handoff <PR>` or by approving in GitHub and saying so.

Do not sit in a tight polling loop, and do not treat silence as approval.

Outcomes:

- **Approved** (GitHub approval, or the user saying so here) → set run state
  `stage: "land"` and tell the controller to run `factory-land`. Approval also
  covers filing the listed spin-offs after the merge.
- **"Spin off N" on an escalation the PR depends on** → the PR cannot merge
  ahead of that work. Tell the controller to **park** the run: `factory-spin-off`
  files the item now, then the cleanup-only half of `factory-land` runs. Any
  other "spin off N" or "take SN" is a decision like the rest, routed below.
- **Comments, change requests, or decisions on the Decide items**: collect
  every unresolved thread (`gh pr view <N> --comments`, plus review threads)
  and the user's decisions. Hand them to the controller as a **scoped
  follow-up**. The controller resumes the existing review agent (or the builder,
  for rework too big for review), and only the resulting change is reviewed.
  Pass the comments and decisions, and nothing else. When it comes back,
  re-audit only what changed and whether it moves the verdict.
- **Rejected / abandoned** → tell the controller to run the cleanup half of
  `factory-land`, so no worktree, branch or lock is left behind.

## Rules

- **Never change code, push, or merge.** If something is wrong, report it and let
  the review stage fix it.
- **Never approve on the user's behalf**, and never infer approval from silence,
  a thumbs-up on an unrelated message, or a green build. Auto mode is the single
  exception, it is opt-in for that one run, and it still requires every gate.
- **Never waive or reinterpret a gate to reach an auto-merge.** A deferred
  auto-merge is the mechanism working.
- **Never soften the verdict.** A "do not merge yet" that reads like a "merge" is
  the one failure this stage cannot recover from.
- Do not answer the user's review comments yourself — route them to the reviewer,
  who has the code in hand.
