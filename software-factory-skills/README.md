# Software factory skills

`software-factory` is the entry point: it drives one task through five stages,
each run by a skill that can do only its own job — so the agent that writes the
code is never the agent that judges it.

| Skill | Stage |
| --- | --- |
| [`software-factory`](software-factory) | Controller — frames the run, spawns each stage, owns the handoff between them. Runs manual by default; `/software-factory 42 auto` opts that run into auto-merge. |
| [`factory-implement`](factory-implement) | Builds the change in an isolated worktree cut from fresh `origin/<default>`, proves it works, opens a PR, and watches CI to green. |
| [`factory-review`](factory-review) | Reviews the PR adversarially with no context outside it, fixes every finding, loops to 90% confidence or declares it unresolvable, then squashes and rewrites the description. |
| [`factory-handoff`](factory-handoff) | Checks the PR against what was actually asked for, verifies the proof is real, and gives a link, a status and a merge recommendation. |
| [`factory-land`](factory-land) | Merges an approved, green PR, confirms the issue closed, and tears down the worktree, branch and lock. |
| [`factory-spin-off`](factory-spin-off) | Files everything review left out of the merged PR as GitHub issues linked back to it, splitting anything too big for one run with `split-into-issues`. |

Review sorts what it does not fix into **escalations** (the PR needs a decision
before it merges) and **spin-offs** (the PR is complete without them). Spin-offs
never block a merge; they become issues once the PR lands. If you spin off
something the PR depends on, the issue is filed at once and the PR is parked
behind it.

Auto-merge is opt-in per run and gated: it lands unattended only at a review
confidence of 9/10 or better, with *Needs human eyes* empty, checks green, and
the handoff audit confirming the PR matches what was actually asked for. Any gate unmet and
the PR comes to you as usual.

Shared rules — worktree isolation and locking, run state, the auto-merge gate,
proof standards, PR shape — live in
[`software-factory/references/conventions.md`](software-factory/references/conventions.md).

## How these are installed

Claude Code does not discover nested skill folders, so each skill here is linked
into `../skills/<name>` by a gitignored directory junction. The stage skills read
the shared conventions at `~/.claude/skills/software-factory/references/`, which
resolves through that junction. Recreate the junctions with
[`link-skills.ps1`](../skills/upgrade-my-skills/scripts/link-skills.ps1).
