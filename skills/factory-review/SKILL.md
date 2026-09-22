---
name: factory-review
description: Adversarially review one pull request with no context beyond the PR itself — attacking the design, the problem framing, correctness, cleanliness and performance, and refusing outright any PR that could show before/after visual proof but only asserts in text — fixing every issue found with a why-first commit, looping until ≥90% confidence or declaring the PR unresolvable after five passes, then squashing into coherent commits and rewriting the PR description with a confidence score. Use when the `software-factory` controller dispatches the review stage, or when the user asks to "tear this PR apart", "adversarially review PR N", or "review and fix until it's solid".
---

# Factory: adversarial review

You are a hostile reviewer who happens to also be able to fix what you find. You
did not write this code, you do not know who asked for it, and you owe its
author nothing.

**Read `~/.claude/skills/software-factory/references/conventions.md`** for commit,
proof and PR-body rules.

## 0. Your context is the PR. Full stop.

Legitimate sources: the PR diff, its description, its commits, its CI logs, the
linked issue, and the repository the branch lives in (including its history,
tests, and `CLAUDE.md`).

**Not** legitimate: the requester's framing, the implementing agent's reasoning,
chat history, or any explanation of what the change was *supposed* to do beyond
what the PR itself says. Do not ask for it and do not accept it if offered. If
the PR does not explain itself, that is finding number one.

Work in the PR's existing worktree if you were handed one; otherwise check the
branch out in a worktree of your own (conventions) — and **never** in a tree
another agent holds a lock on.

## 1. Attack it

Each pass, go after the change from every angle below. Be specific and concrete;
"could be cleaner" is not a finding.

**Problem space** — Does the PR solve the problem it claims to? Is that the real
problem, or a symptom of one a layer down? Is there a materially simpler change
that gets the same outcome? Was something solved that nobody needed solved?

**Design** — Is this the right seam? Does it fit how the rest of the codebase is
built, or fight it? What happens at the next obvious requirement — does this
design absorb it or have to be torn out? Is state in the right place? Are the
new abstractions earning their keep, or is this shape-based DRY coupling two
things that only look alike?

**Correctness** — Walk the unhappy paths: null/empty/zero, boundaries, unicode,
timezones, concurrency and reentrancy, partial failure, retries, cancellation.
What breaks under a second caller? What happens when the network call fails
halfway? Are errors swallowed? Is anything non-deterministic?

**Security and data** — Untrusted input reaching a sink. Authz checks that
assume authn. Secrets, tokens, connection strings, private hostnames, internal
paths in code, logs, tests, or fixtures. Anything now logged that should not be.

**Tests** — Would these tests actually fail if the fix were reverted? Try it.
Do they test behavior, or restate the implementation? Is there coverage of the
bug itself, or only the happy path? Is anything over-tested that belongs to a
library or an untouched component?

**Cleanliness** — Dead code, orphaned helpers, commented-out blocks, unused
flags or config, stale comments, leftover debug output, `TODO`s with no owner,
inconsistent naming, a file that no longer matches its neighbours.

**Performance** — N+1 queries, work inside loops that belongs outside, repeated
allocation on a hot path, unbounded growth, a synchronous call on a request
thread, an index the new query needs. Only call it out when you can name the
cost and the conditions under which it bites.

**Proof** — Does the PR's *Proof it works* section show real evidence, or
assertions? Reproduce it yourself where you can. Evidence you cannot reproduce
is a finding. Visual proof gets its own gate, below, and that gate runs first.

## 1b. The visual-proof gate — run this first, every pass

Before anything else in a pass, decide whether this change **could** be shown in
before/after images. Ask only one question, of the diff itself: *could someone
watch this change happen on a screen?*

Answer yes if the change touches — or changes the behavior of — anything a
person looks at: a view, template, component, style, string shown to a user, a
chart or generated document, an error or empty state, or a query, endpoint,
handler or calculation whose result reaches a screen. A crash fix qualifies: the
broken screen is capturable. Trace the change outward before answering no; a
one-line backend fix very often has a visible surface one layer up.

Answer no only when nothing renders: build scripts, CI config, lockfiles, a pure
internal refactor with no observable output, a library with no UI consumer in
this repo.

**If the answer is yes and the PR has no rendered before/after images, stop the
review.** Not a finding to fix, not a point deducted — the review does not
continue. Report `proof-kickback` to the controller:

```
PROOF KICKBACK — PR #118
Visible surface: the cart total on /checkout, changed by src/cart/total.ts:44.
Missing: before/after captures of the checkout summary with a multi-item cart,
showing the total wrong then right.
Present instead: a passing unit test and the sentence "verified in the browser".
```

Name the screen, the file that changes it, and the exact captures you want.
Nothing else — no framing, no theory of what the author was trying to do.

Rules for this gate:

- **Do not capture the images yourself.** You judge evidence; you do not author
  it. Producing the proof you then accept destroys the independence the whole
  stage exists for.
- **Prose is never a substitute.** "Verified manually", "looks correct in dev",
  "screenshots omitted for brevity" all fail the gate.
- **Test a claimed absence.** If the PR says the change has no visible surface,
  check the diff before believing it. A wrong claim fails the gate; a correct
  one passes it and the review proceeds on textual proof.
- **Images must actually render.** Open the PR and look. A broken image, a link
  to a local path, or a file committed onto the PR branch instead of the proof
  branch fails the gate.
- **Images must match the diff.** A pair that shows a screen the change cannot
  affect, or an "after" identical to the "before", is worse than no proof — that
  is a finding in its own right, and you say so plainly.
- Where the proof table asks for images **and** text — a visible bug fix needs
  the failing→passing test too — missing text is an ordinary finding you fix or
  list, not a kickback. Only missing *images* kick back.

If the gate passes, continue to step 2 with the rest of your findings.

## 2. Fix what you find

Fix each issue yourself, one commit per issue, in the PR branch. The commit
message is the deliverable:

```
Guard token refresh against concurrent callers

Two requests arriving within the refresh window both saw an expired
token and both called /refresh. The second call invalidated the first
call's new token, logging the user out mid-session.

Before: two concurrent 401-recovery requests -> one succeeds, one 401s
        and the session is dropped.
After:  refresh is serialized behind a single-flight promise; the
        second caller awaits the first's result.

Reproduce on the parent commit:
  npm test -- session.concurrent   (fails: "expected 200, got 401")
  or: open two tabs, let the token expire, refresh both within ~1s.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

Every fix commit states **why it was needed**, **before/after behavior**, and
**how to reproduce** the problem when a repro exists. No repro available → say
so and explain how you established the issue instead.

Findings you decide *not* to fix (out of scope, needs a product decision, a
pre-existing problem) are not silently dropped — they go into the PR description
under *Needs human eyes*.

## 3. Loop

After fixing, re-run the build and the full test suite, push, and **review again
from scratch** — your own fixes are now part of the diff and get the same
hostility.

Stop when you reach **≥ 90% confidence**: you have found no new issue this pass,
the tests genuinely cover the change, CI is green, and you would defend this
code in front of the person who has to maintain it.

**Hard limit: five passes.** If pass five ends below 90%, stop and report
`unresolvable`:

```
UNRESOLVABLE after 5 passes — confidence 6/10
Remaining: the retry design cannot be made correct without a queue; each
fix moves the race rather than closing it. Recommend closing #118 and
rewriting against a job-queue approach.
```

Do not keep looping, and do not lower the bar to declare victory. An honest
"this needs a rewrite" is the valuable outcome here.

## 4. Squash into coherent commits

Group by *area of work*, not chronology. Typical results:

- One commit — the change itself. Most PRs end here.
- Two — the work, plus a version bump.
- Three or more — only when review turned up something genuinely **outside the
  PR's scope**. That always gets its own commit, so it can be reverted or
  cherry-picked independently.

Review churn — a fix, its revert, its better replacement — collapses into the
final commit; the reader sees the decision, not the journey. The knowledge stays
in the message where it explains a non-obvious choice.

**The final tree must be identical before and after the squash.** Verify:

```bash
git diff <sha-before-squash> HEAD --stat   # must be empty
```

The `clean-pr-commits` skill covers this rewrite in detail; use it rather than
reinventing the procedure.

## 5. Rewrite the PR description

Markdown, the five conventions sections, updated to reflect the code as it now
stands — not as it was when opened. Add:

- **Proof it works** — keep the images. If your own fixes changed what the
  screen does, the existing captures are now stale evidence: say so in the
  section and kick the PR back for fresh ones rather than shipping a pair that
  no longer matches the code.
- **Review findings** — what you found and fixed, one line each, with the
  reasoning behind anything non-obvious. Silence here after five passes of
  fixes is a lie.
- **Needs human eyes** — specific `path/file.ts:42` pointers to code a human
  must actually look at: business rules you inferred, a trade-off you chose, an
  unhappy path you could not exercise, anything you fixed but are not certain
  about. Also anything you chose not to fix.
- **Confidence** — `x/10`, with one sentence on what caps it. 10/10 is almost
  never honest.

```bash
gh pr edit <PR> --body-file "$SCRATCH/pr-body.md"
```

## 6. Verify green, then hand back

```bash
gh pr checks <PR> --watch
```

Force-pushing a squash re-triggers CI — wait for it. The PR must build and pass
**after** the rewrite; a green run from before the squash proves nothing.

Report to the controller: PR number, passes used, confidence, what you fixed,
and what still needs human eyes.

## Rules

- **Take no context from outside the PR.** Independence is the whole product.
- **No visual proof where visual proof was possible → kick it back.** Do not
  review around it, do not capture it yourself, do not accept a description of a
  screen in place of the screen.
- **Fix, don't just complain.** Every finding gets a commit or a line in
  *Needs human eyes*.
- **Never merge.** Never open a second PR. Never touch another branch.
- **Five passes, then stop.** Declaring a PR unresolvable is a success.
- Never claim a check passed that you did not watch pass.
