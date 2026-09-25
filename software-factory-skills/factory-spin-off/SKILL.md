---
name: factory-spin-off
description: File every spin-off a factory run left out of its PR as a GitHub issue — one issue via `add-github-issue`, or an ordered, blocked chain via `split-into-issues` when the work is too big for one run — linked back to the PR that spun it off. Also files a single spin-off early when the user parks a PR behind it. Use when the `software-factory` controller reaches the spin-off stage after a merge, when the user parks a PR on a spin-off at handoff, or when the user asks to "file the spin-offs" or "turn the unfixed review items into issues" for a factory PR.
---

# Factory: file the spin-offs

A **spin-off** is work review left out of the PR because the PR is correct and
complete without it (conventions → *Vocabulary*). Unfiled, it disappears the
moment the PR merges. Your job is to turn each one into an issue an agent can
later pick up cold and finish without asking anyone anything.

You run **in the controller's session**. You never change code, push, or merge.

**Read `~/.claude/skills/software-factory/references/conventions.md`** for the
run-state file and the PR-body shape.

## 0. Which mode

- **After merge** (the normal path) — the controller runs you once
  `factory-land` has merged the PR. You file every item in the PR's
  `## Spin-offs` section.
- **Park** — at handoff the user chose to spin off an escalation the PR
  *depends on*. You file that one item now; the PR waits on it.

Permission to file comes from the run, not from asking again: the user's merge
approval covers the spin-offs they were shown at handoff, auto mode covers them
in an auto run, and the user's own "spin off N" covers a park.

## 1. Load the run and the items

Read the run-state file and the PR as it now stands:

```bash
gh pr view <PR> --json state,mergeCommit,body,url
```

- **After merge**: `state` must be `MERGED`. If it is not — the run was
  abandoned, rejected, or reviewed as do not merge — file nothing. List the
  spin-offs in your report and offer to file them; whether they still matter
  depends on what happens to the PR, and that is the user's call.
- The items are exactly those under `## Spin-offs` in the PR body. That section
  is the source of truth: the reviewer moves items in and out of it as the user
  decides at handoff. `None.` means there is nothing to do; record
  `spinOffs: []` and report that.
- **Park**: the item is the escalation the controller names, taken verbatim from
  *Needs human eyes*.

## 2. Ground in the merged code

Each issue names real files, so read them where they now live. After a merge
that is the home repo's default branch, which `factory-land` has already pulled;
confirm it contains the merge commit (`git -C "$HOME_REPO" merge-base
--is-ancestor <merge sha> HEAD`). In park mode, read the PR's worktree or
branch — the escalation describes code that has not landed.

## 3. Size each item

Review gave each item a **Size** hint from the PR alone. You decide, with the
code open, against one rule: an item that fits in **one factory run** — one
independently mergeable, reviewable PR — gets one issue. An item that crosses
more than one seam or subsystem, or needs staged steps (schema, then code, then
UI), gets split.

## 4. File each item

For every item, in the order the PR lists them:

1. **Duplicate check** — `gh issue list --state all --search "<keywords>"`. If an
   open issue already covers it, comment on that issue with the new evidence and
   `Seen again in #<PR> (<merge sha>)` instead of filing a second one. A closed
   duplicate is worth a new issue that links it.
2. **File it**:
   - one issue → the `add-github-issue` skill;
   - split → the `split-into-issues` skill, which files a parent and its
     ordered children.

   Hand either skill the item's location, problem, *Not fixed here because*,
   and *Recommendation*. The recommendation is where the implementation plan
   starts, not a plan to copy — check it against the code.
3. **Link it back.** The first line of the issue body (the parent's, for a
   split):
   - after merge: `Spun off from #<PR> (<merge sha>).`
   - park: `Spun off from #<PR>, which is blocked on this issue.`

## 5. Close the loop on the PR

**After merge** — one comment on the merged PR listing everything filed:

```bash
gh pr comment <PR> --body-file "$SCRATCH/spin-offs.md"
```

```markdown
Spin-offs filed from this PR:
- #131 Page the audit-log query (one issue)
- #132 Move invoice rounding to the total — parent of #133–#135
- `src/cache.ts:40` stale-entry TTL — already tracked in #97, evidence added
```

**Park** — add `Blocked by #<n>` as the first line of the PR body
(`gh pr edit <PR> --body-file`) and leave one comment saying why the PR waits.
The PR stays open with its branch; the controller runs the cleanup-only half of
`factory-land` next.

## 6. Record and report

Write the results into run state:

```json
"spinOffs": [
  { "item": "src/audit/log.ts:88 unpaged query", "issues": [131] },
  { "item": "src/billing/invoice.ts:88 rounding", "parent": 132, "issues": [133, 134, 135] },
  { "item": "src/cache.ts:40 stale-entry TTL", "existing": 97 }
]
```

After merge, set `stage: "done"`. In park mode, set `stage: "parked"` and
`blockedReason: "waiting on #<n>"`.

Report one line per item, the same list as the PR comment. Done when every item
under `## Spin-offs` has an issue, a parent, or a named existing issue — or, for
an unmerged run, is listed with the offer to file it.

## Rules

- **The PR body decides what is a spin-off.** File what is under
  `## Spin-offs`, nothing more. Moving an item in or out is the reviewer's job,
  on the user's decision.
- **File only for a merged PR, or a park the user chose.** Anything else is
  listed and offered.
- **Every issue links back to its PR**, and the PR lists every issue.
- Never change code, push, merge, or reopen a closed PR.
