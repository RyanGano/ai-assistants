---
name: factory-land
description: Merge an approved, green PR, confirm its linked issue closed, then tear down everything the run created — worktree, local and remote branch, and the run lock — leaving no stragglers. Use when the `software-factory` controller reaches the merge stage, when the user says "merge it", "land the PR", "ship it", or when a run is abandoned and its worktree needs cleaning up. Refuses to merge anything red, or anything unapproved unless the run is in auto-merge mode and every gate re-verifies here.
---

# Factory: merge and clean up

The last stage. Two jobs: land the PR, and leave nothing behind.

**Read `~/.claude/skills/software-factory/references/conventions.md`** for the
run-state file, branch and worktree layout, and the lock.

## 1. Verify it is actually allowed to merge

Check all of it, and stop on the first failure:

```bash
gh pr view <N> --json state,isDraft,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup
```

Requirements:

- `state: OPEN`, not a draft.
- **Permission to merge**, which depends on the run's mode (below).
- **All checks green.** A pending check is not green — wait for it
  (`gh pr checks <N> --watch`). A failing check is a stop, not an override.
- `mergeable: MERGEABLE`. Conflicts are the review stage's problem: report and
  hand back, do not resolve them here.
- No unresolved review threads.

### Manual mode (the default)

**Explicitly approved** — a GitHub `APPROVED` review, or the user saying so in
this session in so many words. Not inferred from silence, from a green build, or
from "looks good" on a different topic.

### Auto mode

Only when the run state says `autoMerge: true`. Re-check the full gate table in
conventions → *Auto-merge gate* yourself from the run state and the PR — do not
take the controller's word for it. Every gate, including confidence of **9/10
or better**, `autoMergeDecision: "merged"` recorded by `factory-handoff`, and
*Needs human eyes* reading `None.`

If `autoMerge` is absent or false, this run is manual. A missing or unreadable
run-state file means manual — never infer auto mode from the absence of evidence.

If any gate fails, do not merge: report which one and leave the PR for the user.

### Either way

If any requirement fails, **stop and report** what blocked it. Never `--admin`,
never disable a check, never push a fixup to go green, and never merge because
the run "was supposed to" auto-merge.

## 2. Merge

Use the merge style the repo actually uses — check branch protection and recent
history (`gh api repos/{owner}/{repo} --jq .allow_squash_merge,.allow_merge_commit`
and `git log --merges -5 origin/<default>`) rather than assuming.

```bash
gh pr merge <N> --squash --delete-branch    # or --merge / --rebase, to match the repo
```

`factory-review` already grouped the commits deliberately. If the repo's style is
merge-commit or rebase, that grouping survives; if it is squash-merge, say so
when reporting — the deliberate grouping is collapsing by policy, not by mistake.

## 3. Close the issue

The PR body should carry `Closes #<issue>`, which closes it on merge. Verify
rather than assume:

```bash
gh issue view <issue> --json state,closedAt
```

Still open? Close it with a comment pointing at the merge commit:

```bash
gh issue close <issue> --comment "Fixed by #<N> (<merge sha>)."
```

## 4. Clean up — every time

Nothing from this run survives the stage:

```bash
# from the HOME repo, never from inside the worktree
git -C "$HOME_REPO" worktree remove "$WT"        # add --force only if it is dirty
git -C "$HOME_REPO" worktree prune
git -C "$HOME_REPO" branch -D "$BRANCH"          # local branch
git -C "$HOME_REPO" fetch origin --prune         # drop the deleted remote ref
rm -f "$HOME_REPO/.git/software-factory/locks/$BRANCH.lock"
```

**Leave the proof branch (`sf-proof/<branch>`) alone.** It holds the before/after
images the merged PR embeds; deleting it turns the PR's evidence into broken
image links forever. It is not a straggler.

Then update the home repo's default branch so the next run starts from the merge:

```bash
git -C "$HOME_REPO" switch "$DEFAULT" && git -C "$HOME_REPO" pull --ff-only
```

Before removing a dirty worktree, **look at what is uncommitted**
(`git -C "$WT" status --short`, `git -C "$WT" diff`). If it is real work that
never made it into the PR, stop and ask — `--force` there destroys it
permanently. Never run `git clean -fdx` anywhere.

Finally confirm the teardown actually happened:

```bash
git -C "$HOME_REPO" worktree list      # the run's worktree must be gone
ls "$HOME_REPO/.git/software-factory/locks/"
```

Mark the run `stage: "spin-off"` in its state file. The controller runs
`factory-spin-off` next, against the default branch you just pulled; that stage
marks the run done.

## 5. Report

```
#118 merged (squash) · issue #42 closed
Worktree removed, branch Fix_42 deleted local+remote, lock released
main now at a1b2c3d
```

After an **auto-merge**, say so in the first line and link the diff, so an
unattended merge is obvious in the transcript rather than buried:

```
#118 AUTO-MERGED unreviewed (squash) · <n>/10 · issue #42 closed
Diff: https://github.com/owner/repo/pull/118/files
Worktree removed, branch Fix_42 deleted local+remote, lock released
main now at a1b2c3d
```

## Cleanup-only mode

When a run is abandoned or rejected (including a "do not merge" PR the user
closes), or **parked** behind a spin-off it depends on, this skill is invoked
for step 4 alone. Then:

- Do **not** merge, and do not delete the remote branch or close the PR unless
  the user asked. A rejected PR's branch is the input to any rewrite.
- Do remove the worktree, prune, and release the lock, so the slug can be used
  again.
- Leave the run's stage as `factory-spin-off` set it (`parked`), or set
  `done` for an abandoned run.
- Say plainly what was kept and what was destroyed.

## Rules

- **Approved and green, or no merge.** The only alternative to human approval is
  a run the user put in auto mode whose every gate holds — re-verified here, not
  taken on trust. No admin override, ever.
- **When in doubt about the mode, it is manual.** Unreadable run state, a
  half-written file, a mode you inferred rather than read — all manual.
- **Never merge a PR you also reviewed or wrote.** Separate stages, separate
  agents.
- **Never leave a worktree, branch or lock behind** — a stale lock blocks every
  future run on that branch.
- Never destroy uncommitted work without asking first.
- Report the real outcome, including a merge that succeeded but left something
  unclean.
