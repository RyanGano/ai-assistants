# Software factory conventions

Shared rules for `software-factory` and its stage skills (`factory-implement`,
`factory-review`, `factory-handoff`, `factory-land`). Every stage obeys these.
Where a stage skill and this file disagree, this file wins.

## Vocabulary

| Term | Meaning |
| --- | --- |
| **Controller** | The session running `software-factory`. Owns the run, talks to the user, spawns stage agents. |
| **Run** | One task moving through implement → review → handoff → land. |
| **Slug** | Short kebab-case id for the run, derived from the issue number or task title (e.g. `42-login-redirect`, `add-csv-export`). |
| **Home repo** | The user's normal clone — where the controller runs. Never the place code is written. |
| **Worktree** | The isolated checkout a run's code is written in. |

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
  "stage": "implement | review | handoff | land | done | blocked",
  "reviewPasses": 2,
  "confidence": 8,
  "autoMerge": false,
  "autoMergeDecision": null,
  "blockedReason": null
}
```

Every stage reads this file on entry and writes it on exit. It is the handoff
contract — stage agents return a summary to the controller, but the file is the
source of truth.

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
| Review finished **within** five passes, not unresolvable | `factory-review` | run state |
| *Needs human eyes* is `None.` | `factory-handoff` | PR body |
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

## Verification is not optional

"It builds" is not proof. Each run must carry evidence appropriate to the change:

| Change type | Acceptable proof |
| --- | --- |
| UI | Before/after screenshots (the `run` skill can drive the app) |
| API / route | Actual request + response captured (`curl`, `Invoke-RestMethod`) |
| Bug fix | A test that fails before the fix and passes after — show both runs |
| Performance | Timing numbers before and after, same machine, stated method |
| Refactor | Full test suite output, plus what proves behavior is unchanged |

Paste real command output. **Never** describe a result you did not observe. If
proof could not be obtained, say so explicitly and say why — that is a finding,
not a failure to hide.

## Commits

- Explain **why**, not what. The diff shows what.
- End every commit message with:
  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  ```
- Never `git push --force` to the default branch; never push to it at all.
- Never run `git clean -fdx`.

## PR body shape

Markdown, and always these sections:

```markdown
## What changed
## Why
## Proof it works
## Needs human eyes
## Confidence
```

- **Proof it works** — the evidence from the table above, inline.
- **Needs human eyes** — specific `file.ts:42` links to subtle or risky code, or
  `None.` Never leave it empty.
- **Confidence** — `x/10` plus one sentence on what caps it.
- End the body with:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)
  ```

## Stage boundaries — what each stage may not do

| Stage | Must not |
| --- | --- |
| `factory-implement` | Review its own work adversarially, merge, delete worktrees, or touch another run's branch |
| `factory-review` | Know anything about the run beyond the PR itself; merge; open new PRs |
| `factory-handoff` | Change code, push, or merge |
| `factory-land` | Merge anything unapproved or red; land a PR it also reviewed |

A stage that hits work belonging to another stage stops and reports, rather than
reaching across the boundary.
