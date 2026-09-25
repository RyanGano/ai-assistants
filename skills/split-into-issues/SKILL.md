---
name: split-into-issues
description: Break a problem too large for one PR into a parent GitHub issue and a chain of child issues — vertical slices, each one PR, wired with native sub-issue and blocked-by links so an agent can work the chain in order without stopping to ask. Use when the user says "break this into issues", "split this up into issues", "plan this as a series of issues", "this is too big for one PR", or when `factory-spin-off` hands over a spin-off sized `needs splitting`. Works in any Git repo with a GitHub remote and `gh` authenticated.
---

# Split a problem into ordered issues

The reader of every issue you file is an **agent picking it up cold**, one issue
per run, with nothing but the issue and the repo. The chain works when that
agent can take the first unblocked child, finish it in one PR, merge it, and
move to the next — never stalled on a question, never tripping over a half-built
neighbour.

Each issue is written with `add-github-issue`: its template, grounding, duplicate
check and public-repo rules all apply. This skill adds the slicing and the
wiring.

## 1. Understand the whole problem

Read what you were handed: the user's description, or the spin-off item (its
location, problem, and recommendation) plus the merged PR it came from. Read the
repo's `CLAUDE.md`, then the code the work will touch. Every file you later name
in an issue must exist.

Done when you can state the end state in one sentence and name the files, seams
and data the work crosses.

## 2. Slice it

Cut the work into **vertical slices**. A slice is one PR that:

- leaves the default branch green and shippable once merged, even if no later
  slice ever lands;
- can be built, reviewed and proven in one `software-factory` run;
- delivers something observable — a behavior, a passing check, a migrated table
  in use — rather than a layer nobody calls yet.

Order slices by what each one **needs to already exist**, not by the order you
thought of them. A slice with no prerequisite among its siblings is left
unblocked, so independent slices can run in parallel. Prefer the fewest slices
that satisfy the rules above; two to six is typical. When the plan needs more
than eight, the goal itself is too broad — split the goal and say so.

Write the plan as a graph before filing anything:

```
Parent: Let admins export any report as CSV
  1. Add paging to the report query            (unblocked)
  2. Stream CSV from the paged query           blocked by 1
  3. Export button on the report page          blocked by 2
  4. Document the export endpoint              blocked by 2
```

Done when every slice passes the three rules and every edge in the graph names
what the blocked slice needs from its blocker.

## 3. Confirm, or proceed

- **Invoked by the user** — show the graph, one line per slice with its
  blockers, and wait for a yes. Filing several issues is public and tedious to
  undo; adjust the plan to their answer first.
- **Invoked by `factory-spin-off`** — the user's merge approval (or the run's
  auto mode) already covers filing. Proceed without asking.

## 4. File in dependency order

File the **parent first**, then the children in the graph's order, so every
`Blocked by` reference points at an issue that already exists.

**Parent** — the `add-github-issue` template for the whole goal: what is missing,
why, and how we will know the whole thing worked. Its implementation plan is the
ordered child checklist, filled in after the children exist:

```markdown
## Implementation plan

Work these in order; each is one PR. Unblocked items can run in parallel.

- [ ] #121 Add paging to the report query
- [ ] #122 Stream CSV from the paged query (blocked by #121)
```

**Each child** — the `add-github-issue` template, scoped to its slice, with two
additions:

- The first line of the body: `Part of #<parent> · Blocked by #<a>, #<b>` (or
  `Part of #<parent> · Unblocked`). An agent reading `gh issue view` sees the
  order even where the native links do not render.
- A final **Not in this issue** step in the implementation plan naming the
  neighbouring slices' work, so the agent stops at the slice boundary.

*How we will know it worked* must be checkable by the agent that builds it: a
test that goes from failing to passing, an observable behavior, a command whose
output changes.

After the last child, rewrite the parent body with the real numbers:
`gh issue edit <parent> --body-file <file>`.

## 5. Wire the native links

GitHub's sub-issue and dependency endpoints take an issue's numeric **id**, not
its number:

```bash
id() { gh api "repos/{owner}/{repo}/issues/$1" --jq .id; }

# attach each child to the parent
gh api -X POST "repos/{owner}/{repo}/issues/<parent>/sub_issues" -F sub_issue_id=$(id <child>)

# record each edge: <child> is blocked by <blocker>
gh api -X POST "repos/{owner}/{repo}/issues/<child>/dependencies/blocked_by" -F issue_id=$(id <blocker>)
```

Then read the links back and compare them with the graph:

```bash
gh api "repos/{owner}/{repo}/issues/<parent>/sub_issues" --jq '.[].number'
gh api "repos/{owner}/{repo}/issues/<child>/dependencies/blocked_by" --jq '.[].number'
```

If an endpoint refuses (an older GitHub Enterprise, a missing permission), the
body lines from step 4 still carry the order. Report which links are missing
rather than retrying.

Done when every child is a sub-issue of the parent and every edge in the graph
reads back as a blocked-by link, or is reported as missing.

## 6. Report

```
Parent #120 — Let admins export any report as CSV
  #121 Add paging to the report query            unblocked
  #122 Stream CSV from the paged query           blocked by #121
  #123 Export button on the report page          blocked by #122
  #124 Document the export endpoint              blocked by #122
Start with: /software-factory 121
```

Name the first unblocked child as the place to start.
