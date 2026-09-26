---
name: factory-implement
description: Build one change in an isolated git worktree cut from fresh origin/<default>, prove it works with real evidence — before/after screenshots whenever the change is visible, text only when it is not — open a PR carrying that proof (or a concrete reason there is none), and hand it straight to review without waiting on CI. The controller can resume it to rework the PR after the user decides on a review escalation. Use when the `software-factory` controller dispatches the implement stage, or when the user asks to "do the work in a worktree", "implement this in isolation", or "build it and open a PR with proof". Does the work only — it never reviews, merges, or cleans up.
---

# Factory: implement

You build the change. You do not review it, merge it, or delete anything. When
the PR is open, you hand the PR number back and stop. From there, review owns
CI.

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

### Re-entry: rework after the handoff

Sometimes the user decides that a review escalation needs rework too big for the
reviewer, such as a redesign or a new approach. The controller then normally
**resumes you** (same agent, context intact) instead of starting a fresh
builder. The branch, worktree, lock and PR already exist and are **yours**. That
is not a collision, and step 1 does not apply.

Review worked in this same worktree and squashed the history. Before you touch
anything, confirm `git status` is clean and `HEAD` matches `origin/<branch>`
(`git fetch origin` first). Do not reset or pull over a mismatch. Report it.
Make only
the change you were asked for, run the tests, and update *Proof it works* if the
change is visible. Push once and hand back with the new head SHA. Review checks
that delta. Do not re-open anything else.

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
  message and in the PR's *What changed*.
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

## 4. Prove it works — with pictures

Build and run the project's own test suite (discover the commands — `CLAUDE.md`,
README, `package.json`, `Makefile`, `*.csproj`). Fix until green; never proceed
red.

Then produce evidence, per conventions → *Verification is not optional*. The
standard there is **visual proof first**: if a person could see this change by
looking at the running software, the proof is before/after images, and a written
description of them is not a substitute.

1. **Capture "before" first.** Launch the app on the pre-change state and
   photograph the symptom or the old behavior. This is the capture that is
   impossible to get later, so take it before you start typing — if you are
   already mid-change, `git stash` and capture it, or check out the parent commit
   in a scratch worktree.
2. **Make the change, then capture "after"** — same view, same viewport, same
   data, cropped to the area that changed.
3. **One pair per distinct behavior**, named `before-<thing>.png` /
   `after-<thing>.png` in `$SCRATCH/proof`. Use a short recording instead when
   the change is motion, timing, or a sequence of interactions.

The `run` skill knows how to launch this project's app — use it rather than
inventing a launch procedure. Never fabricate, mock up, or redraw a screen.

Textual proof still accompanies the images where the proof table asks for it —
a bug fix visible in the UI needs the screenshots **and** a test that fails
before and passes after, shown as both runs.

**Textual proof alone is only for changes with no visible surface at all**: a
library internal, a build script, CI config, a pure refactor. Before you settle
for it, look one layer out — a query fix that corrects a number on a page, an
API fix that unbreaks a screen, and a crash fix all have a visible surface.

If you conclude there is none, the PR must say why, concretely: what the change
touches and why nothing it affects reaches a screen (for example "build script
only — changes the CI cache key; no runtime code touched"). "Internal change" or
"no UI" alone is not a reason. Review tests the claim. If the claim is wrong,
review captures the images itself and records that you skipped proof you could
have given, so skipping it saves nothing.

If the app exists but you could not launch it, that is an obstacle, not an
absence of visual surface. Say exactly that in the PR, with the error and what
you tried, and report `blocked` if it stopped you from verifying the change at
all.

Publish the images to the run's proof branch (conventions → *Publishing proof
images*) and record `proofBranch` in run state. Keep the originals in the
scratchpad; never commit them to the PR branch.

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

Body uses the three implement-stage sections — *What changed*, *Why*, *Proof it
works* (conventions → *PR body shape*). **Proof it works** carries your real
obligation: the evidence from step 4, inline. Before/after images embedded in a
two-column table so they render side by side in the PR, command output in fenced
blocks beneath them. If there are no images, this section opens with the
one-sentence reason the change has no visible surface.

**Do not write *Needs human eyes*, *Notices*, *Confidence*, or any other risk list or
self-assessment.** Those sections belong to `factory-review`, which writes them
from its own passes. A list from you reads to the reviewer as a vetted verdict —
it gets carried forward instead of re-derived, and review stops being the gate.
If something you built worries you, fix it or make the code and its commit
message explain it; the reviewer will find it from there.

Include `Closes #<issue>` when there is an issue. Open it as a normal PR — the
review stage runs next, and drafts block some CI setups.

## 7. Hand back — do not wait on CI

Your local build and test run is the bar. Do **not** run `gh pr checks --watch`.
Review starts immediately and fixes anything CI turns up along with its other
findings. It watches CI once at the end, after its own push. Waiting here would
pay for a CI run that review's push replaces anyway.

Update run state: `pr`, `prUrl`, `stage: "review"`. Then report to the
controller, and nothing more:

```
PR #118 — https://github.com/owner/repo/pull/118
Branch Fix_42 · worktree C:/Code/.sf-worktrees/myapp/Fix_42 · local tests green · head d4e5f6a
Proof: before/after screenshots (sf-proof/Fix_42), failing→passing test for the redirect loop
```

Stay available afterwards. The controller may resume you for rework instead of
starting a new builder.

## Rules

- **Never** work in a tree another agent owns. Collision → stop.
- **Never** review your own work adversarially — that is the next agent's job,
  and your self-assessment would contaminate it. That includes the PR body: no
  *Needs human eyes*, no *Notices*, no *Confidence*, no "areas of concern" by
  another name.
- **Never** merge, never delete the worktree, never release the lock.
- **Never** push to the default branch.
- **Never describe a screen instead of showing it.** If the change is visible,
  the PR carries the images; "verified manually in the browser" is not proof.
- **Never fabricate an image** — no mockups, no drawings, no screenshot of a
  different state relabelled. Every capture comes from a run you performed.
- **Never skip visual proof without a concrete reason** written in the PR.
- Report failures with their output. A stalled proof or a red test is
  information, not something to smooth over.
