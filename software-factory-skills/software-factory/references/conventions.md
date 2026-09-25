# Software factory conventions

Shared rules for `software-factory` and its stage skills (`factory-implement`,
`factory-review`, `factory-handoff`, `factory-land`, `factory-spin-off`). Every stage obeys these.
Where a stage skill and this file disagree, this file wins.

## Vocabulary

| Term | Meaning |
| --- | --- |
| **Controller** | The session running `software-factory`. Owns the run, talks to the user, spawns stage agents. |
| **Run** | One task moving through implement → review → handoff → land → spin-off. |
| **Slug** | Short kebab-case id for the run, derived from the issue number or task title (e.g. `42-login-redirect`, `add-csv-export`). |
| **Home repo** | The user's normal clone — where the controller runs. Never the place code is written. |
| **Worktree** | The isolated checkout a run's code is written in. |
| **Escalation** | A review finding the reviewer did not fix, handed to the human with why and a recommendation. |
| **Spin-off** | An escalation the run deliberately leaves out of this PR because the PR is correct and complete without it. Filed as a GitHub issue after the merge. Not to be confused with a *follow-up*. |
| **Follow-up** | A scoped re-review of only what changed after handoff: user comments, an escalation decision, or new commits. |

## Default branch

Never hardcode `main`:

```bash
DEFAULT=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')
DEFAULT=${DEFAULT:-main}
```

Fall back to `main`, then `master`, and say which you used.

## Branch naming

- Tied to a GitHub issue: `Fix_<issueNum>` (matches this user's existing convention).
- No issue: `sf_<slug>`.

One run = one branch = one worktree = one PR. Never bundle unrelated work.

## Blocked issues

An issue with an open blocker is not ready to build. Before starting a run on an
issue, list its open blockers:

```bash
gh api "repos/{owner}/{repo}/issues/<n>/dependencies/blocked_by" --jq '.[] | select(.state == "open") | .number'
```

and read its body for a `Blocked by #<n>` line naming an issue that is still
open. Any open blocker → do not start. Name the blockers, and walk the chain to
the first unblocked issue so the user knows where to begin.

## Worktree isolation

All code work happens in a dedicated worktree cut from **freshly fetched**
`origin/<default>` — never from a stale local branch, never in the home repo's
working tree.

```bash
git -C "$HOME_REPO" fetch origin --prune
REPO=$(basename "$(git -C "$HOME_REPO" rev-parse --show-toplevel)")
WT="$(dirname "$(git -C "$HOME_REPO" rev-parse --show-toplevel)")/.sf-worktrees/$REPO/$BRANCH"
git -C "$HOME_REPO" worktree add -b "$BRANCH" "$WT" "origin/$DEFAULT"
```

Worktrees live in a `.sf-worktrees/<repo>/` sibling directory so they never
pollute the repo and are never matched by its `.gitignore`.

### Claiming — never work where another agent is working

Before creating a worktree, prove nothing else owns this work:

```bash
git -C "$HOME_REPO" worktree list --porcelain          # existing worktrees + their branches
git -C "$HOME_REPO" branch --list "$BRANCH"            # local branch already exists?
git ls-remote --heads origin "$BRANCH"                 # remote branch already exists?
gh pr list --state open --json number,headRefName      # open PR on this branch?
ls "$HOME_REPO/.git/software-factory/locks/"           # active run locks
```

If **any** of these already exist for this branch, **stop**. Do not reuse,
reset, or force the worktree — report the collision to the controller and let a
human decide. Two agents in one tree is the one failure mode this design exists
to prevent.

Once clear, claim it atomically (`set -o noclobber` fails if the lock exists):

```bash
mkdir -p "$HOME_REPO/.git/software-factory/locks"
( set -o noclobber; printf '%s\n' "$SLUG $(date -Is) $$" \
  > "$HOME_REPO/.git/software-factory/locks/$BRANCH.lock" ) || { echo "LOCKED"; exit 1; }
```

The lock is released only by `factory-land` (or by an explicit user-approved
abort). Everything under `.git/` is invisible to Git itself, so none of this can
ever be committed or published.

## Run state

Each run records its state in a JSON file in the **home repo**, so it survives
the worktree being deleted:

`<home repo>/.git/software-factory/runs/<slug>.json`

```json
{
  "slug": "42-login-redirect",
  "task": "Verbatim text of what the user asked for",
  "issue": 42,
  "branch": "Fix_42",
  "worktree": "C:/Code/.sf-worktrees/myapp/Fix_42",
  "homeRepo": "C:/Code/myapp",
  "baseBranch": "main",
  "pr": 118,
  "prUrl": "https://github.com/owner/repo/pull/118",
  "proofBranch": "sf-proof/Fix_42",
  "stage": "implement | review | handoff | land | spin-off | done | parked | blocked",
  "fullPasses": 1,
  "deltaChecks": 2,
  "reviewRecommendation": "merge | do not merge: <reason>",
  "reviewedSha": "a1b2c3d",
  "implementAgentId": "agent-…",
  "reviewAgentId": "agent-…",
  "confidence": 8,
  "autoMerge": false,
  "autoMergeDecision": null,
  "spinOffs": [],
  "blockedReason": null
}
```

Every stage reads this file on entry and writes it on exit. It is the handoff
contract — stage agents return a summary to the controller, but the file is the
source of truth. `factory-review` is the exception: it never reads run state,
and the controller records its results for it.

`implementAgentId` and `reviewAgentId` let the controller **resume** those
agents with their context intact (`SendMessage`) instead of paying for a cold
start every time a stage has to run again. `reviewedSha` is the head the
reviewer last signed off on. A follow-up review starts its delta there.

## Auto-merge gate

A run is **manual by default**: the user sees the PR and approves it before
anything lands. `autoMerge: true` is set only when the user asked for it on that
specific run (see `software-factory` → *Frame the run*). It is per-run, never
sticky — the next run starts manual again.

Auto-merge fires **only when every one of these is true**:

| Gate | Checked by | Source |
| --- | --- | --- |
| `autoMerge: true` for this run | all | the user's words on this run |
| Confidence is **9/10 or better** | `factory-review` | review's own score |
| Review recommends **Merge** | `factory-review` | run state |
| *Needs human eyes* is `None.` | `factory-handoff` | PR body |
| *Spin-offs* holds nothing the PR depends on | `factory-handoff` | the audit |
| PR does what the task statement asked, nothing more | `factory-handoff` | the audit |
| Proof is present and spot-checks out | `factory-handoff` | the audit |
| All checks green, mergeable, no unresolved threads | `factory-land` | GitHub |

**Any single gate unmet → fall back to the normal human handoff.** That is not a
failure and is not reported as one; it is the mechanism working. Never relax a
gate, re-run review hoping for a better number, or ask the reviewer to
reconsider its score to unblock a merge.

Record the outcome in run state as `autoMergeDecision`: `"merged"`, or
`"deferred: <the gate that stopped it>"`.

Two deliberate properties of this design:

- **A high score is meant to be hard.** `factory-review` is told that 10/10 is
  almost never honest, so 9 is the realistic ceiling for clean work and 9/10 is
  the threshold. Plenty of auto runs will still land in front of the user — that
  is the intended bias, not a bug to tune out. The threshold is a property of
  this file; do not let a run argue it down further.
- **The reviewer does not merge its own verdict.** Review produces the score,
  but `factory-handoff` still audits independently against the original task
  statement — which review never sees — and can veto. Auto-merge removes the
  human, not the second opinion.
- **The reviewer is never told the run is auto.** `factory-review` works from
  the PR alone and never reads run state, so it cannot know its score is load-
  bearing. Keep it that way: a reviewer aware that a 9 merges unattended is a
  reviewer under pressure to score something other than the truth — and the
  pressure is sharper at 9 than at 10, because 9 is a score it might plausibly
  reach. Do not mention the mode to it, in the spawn prompt or anywhere else.

## Review economy

Review is where runs used to burn 30 to 40 minutes: fix one small thing, run a
full review again, find one more small thing, and repeat. These rules exist to
stop that loop. `factory-review` has the details.

- **Fix in place.** A reviewer that can see the right fix makes it. Nothing
  fixable goes back to the builder.
- **Escalate with a recommendation.** Whatever the reviewer will not fix goes to
  the human as a list. Each item gives the location, the problem, *why it was
  not fixed*, *what the reviewer would do*, and a severity.
- **One full pass, then deltas.** After each round of fixes, the reviewer
  checks only `git diff <last check>..HEAD`. Several small delta checks are
  fine. A full pass is repeated only when what changed was large, changed the
  design, or touched high-risk logic (money, auth, security, concurrency,
  persistence, data loss), never for a trivial fix. There is no fixed pass
  count. Every re-review has to be justified by what changed, and churn in one
  area is escalated instead of looped on.
- **Always finish.** Even a PR that should not merge comes back with coherent
  commits, a rewritten description, a green build, and a clear **Merge** or
  **Do not merge** recommendation.
- **Size the review to the change.** A copy fix gets a glance. A billing rewrite
  gets depth.
- **Push once.** The builder hands off without waiting on CI. The reviewer
  commits locally, squashes, pushes once, and watches CI once.
- **Follow-ups are scoped.** User comments, escalation decisions and later
  commits get a review of that change only, by the same agent, resumed.
- **Spin off what the PR does not need.** Work the PR is correct and complete
  without — out of scope, pre-existing, a redesign bigger than the PR — goes
  under *Spin-offs*, not *Needs human eyes*. It does not block a merge, and
  `factory-spin-off` files it as an issue once the PR lands.

## Verification is not optional

"It builds" is not proof. Every run carries evidence appropriate to the change,
and **visual evidence is the default**.

### Visual proof first

If a person could see the change by looking at the running software, the proof
is **before/after images** — not a sentence describing them.

The test is simple: *could someone watch this change happen on a screen?* If
yes, visual proof is available, and it is mandatory. That covers more than
"UI work":

- any UI change — layout, styling, copy, a new control, a rendering bug;
- a backend, query or data fix whose effect surfaces in the UI (a wrong total, a
  missing row, a stale cache) — capture the screen showing it wrong, then right;
- an error, empty, loading or offline state; a responsive breakpoint;
- rendered output that is not a web page — a generated PDF, chart, image, email
  template, or a CLI whose *appearance* changed;
- a crash or a broken page: the failure screen is half the proof.

Rules for the images:

- **Before and after, same view, same viewport, same data.** A pair that differs
  in two things at once proves nothing.
- **Crop to the area that changed**, tightly enough that the difference is
  obvious without being told where to look. Annotate only if it is still not.
- **One pair per distinct behavior.** Three fixed states means three pairs.
- **A short recording** (GIF or MP4) replaces the pair when the change is
  motion, timing, or a sequence of interactions.
- **Real captures of the real app**, taken from a run you actually performed —
  never a mockup, a drawing, or a picture of what it is supposed to look like.
- The `run` skill knows how to launch this project's app; use it rather than
  inventing a launch procedure.

**Textual proof is the fallback, not the default.** Command output, captured
requests and responses, and test runs stand alone as proof only when the change
has no visible surface at all. Where the table below asks for both, they
accompany the images rather than replacing them.

| Change type | Proof required |
| --- | --- |
| UI, or anything rendered to a screen | Before/after screenshots; a recording when the change is motion or an interaction sequence |
| Bug fix with a visible symptom | Before/after screenshots of the symptom **and** a test failing before, passing after |
| Bug fix with no visible symptom | A test that fails before the fix and passes after — show both runs |
| API / route | Actual request + response captured (`curl`, `Invoke-RestMethod`), **plus** screenshots of any client screen whose behavior changes |
| Performance | Timing numbers before and after, same machine, stated method; add a capture of the profiler or timing view when the tooling has one |
| Refactor, no behavior change | Full test suite output, plus what proves behavior is unchanged |
| Build, CI, infrastructure, docs | Whatever the change actually affects — a passing workflow run, the rendered docs page, the build log |

"No visual proof was available" is a claim the review stage tests, so only make
it when it is true. It holds when nothing a person can look at changed. It does
**not** hold because the app was awkward to launch, because the change felt
internal, or because a test run seemed like enough. If the app genuinely could
not be started, that is a stated obstacle with a reason — not an absence of
visual surface — and it belongs in the PR in those words.

Paste real command output. **Never** describe a result you did not observe, and
never embed an image you did not capture from a run you performed.

### Publishing proof images

Images must be visible **inside the PR**, so a reader sees them without
downloading anything. They never go on the PR branch — proof is evidence about
the change, not part of it.

Push them to an orphan proof branch in the same repo, built with plumbing so no
working tree is ever switched:

```bash
PROOF_BRANCH="sf-proof/$BRANCH"
GITDIR=$(git -C "$WT" rev-parse --absolute-git-dir)
export GIT_INDEX_FILE="$SCRATCH/proof.index"; rm -f "$GIT_INDEX_FILE"
git --git-dir="$GITDIR" --work-tree="$SCRATCH/proof" add -A .
TREE=$(git --git-dir="$GITDIR" write-tree)
COMMIT=$(git --git-dir="$GITDIR" commit-tree "$TREE" -m "Proof images for $BRANCH")
git --git-dir="$GITDIR" push --force origin "$COMMIT:refs/heads/$PROOF_BRANCH"
unset GIT_INDEX_FILE
```

`$SCRATCH/proof` holds only the images (`before-<thing>.png`,
`after-<thing>.png`). The branch has no parent and no source files; `--force` is
safe on it and only on it, because each push replaces the run's own proof.

Embed them in the PR body:

```markdown
| Before | After |
| --- | --- |
| ![before](https://raw.githubusercontent.com/<owner>/<repo>/sf-proof/<branch>/before-cart-total.png) | ![after](https://raw.githubusercontent.com/<owner>/<repo>/sf-proof/<branch>/after-cart-total.png) |
```

In a **private** repo `raw.githubusercontent.com` will not render; use
`https://github.com/<owner>/<repo>/blob/sf-proof/<branch>/<file>.png?raw=true`,
which resolves for signed-in users with access. Either way, open the PR
afterwards and confirm the images actually render — a broken image is no proof.

The proof branch outlives the merge, so the PR keeps rendering forever;
`factory-land` deletes the run's feature branch and leaves the proof branch
alone.

### Missing visual proof: review supplies it

The builder owes visual proof whenever the change is visible. If it skips the
proof, it owes a **concrete reason** in the PR. A PR without proof is never sent back
to the builder for pictures. That round trip cost a cold builder plus a
from-scratch review, just to add images.

Instead, `factory-review` judges proof against the final code, after its own
fixes:

- If images are missing and the change is visible, the reviewer captures them
  itself, publishes them to the proof branch, and marks them
  `Captured by review` in the PR. The builder's omission, and whether its reason
  held up, goes under *Review findings*.
- If the reviewer's fixes changed what the screen shows, it recaptures the
  "after" image itself.
- If nobody can capture them (the app will not start), *Proof it works* says so
  with the error. *Needs human eyes* then tells the human exactly what to look
  at.
- Images are evidence, not a gate. The reviewer decides whether the change works
  from everything it has, with or without them.

Because reviewer-captured images are labelled, `factory-handoff` and the user
always know who produced the evidence they are looking at.

## Commits

- Explain **why**, not what. The diff shows what.
- End every commit message with:
  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  ```
- Never `git push --force` to the default branch; never push to it at all.
- Never run `git clean -fdx`.

## PR body shape

Markdown. The sections are split by stage:

```markdown
## What changed        <- factory-implement
## Why                 <- factory-implement
## Proof it works      <- factory-implement (review keeps it current)
## Review findings     <- factory-review
## Needs human eyes    <- factory-review
## Spin-offs           <- factory-review
## Confidence          <- factory-review
```

- **Proof it works** — the evidence from the table above, inline.
- **Review findings** — what review found and fixed, one line each.
- **Needs human eyes** — first the escalations (issues review did not fix: the
  location, the problem, *Not fixed because*, *Recommendation*, and a severity
  of blocking, should-fix or minor), then specific `file.ts:42` pointers to
  fixed-but-subtle code. Or `None.` Never leave it empty. An escalation the PR
  depends on stays here even when the fix is "spin it off first".
- **Spin-offs** — unfixed work the PR is correct and complete without, each
  with the location, the problem, *Not fixed here because*, *Recommendation*,
  and a **Size** of `one issue` or `needs splitting`. Or `None.`
- **Confidence** — `x/10`, one sentence on what caps it, and
  `Reviewed through <sha>`. Ends with review's bold **Merge** or **Do not
  merge** recommendation and its reason.

The implementer never writes the last four. Review is the gate on whether a PR
is complete and mergeable, and a risk list handed to it by the author gets
inherited rather than judged. Review writes those sections from its own passes
alone.
- End the body with:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  ```

## Stage boundaries — what each stage may not do

| Stage | Must not |
| --- | --- |
| `factory-implement` | Review its own work adversarially, merge, delete worktrees, or touch another run's branch |
| `factory-review` | Know anything about the run beyond the PR itself; merge; open new PRs; send fixable work back to the builder; re-review untouched code on a follow-up |
| `factory-handoff` | Change code, push, or merge |
| `factory-land` | Merge anything unapproved or red; land a PR it also reviewed |
| `factory-spin-off` | Change code, push, or merge; file anything for a PR that did not merge, except a park the user chose |

A stage that hits work belonging to another stage stops and reports, rather than
reaching across the boundary.
