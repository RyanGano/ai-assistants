---
name: add-modernization-skills
description: Scan the current repo for technologies that have no matching `modernize-<tech>` skill yet, and author the missing skills into the user's `~/.claude/skills/` so they work in every repo. Use when the user asks to "add modernization skills", "write a modernize skill for X", "fill in missing modernize skills", or when `modernize-this` finds a detected technology it has no sub-skill for.
---

# Add missing modernization skills

Find the technologies in this repo that `modernize-this` can't yet handle, and
write the missing `modernize-<tech>` sub-skills. This authors *skills*, not code
changes — it should leave the repo untouched.

## 1. Detect the stack

Use the same detection table as `modernize-this` (see
`~/.claude/skills/modernize-this/SKILL.md`, step 2). Read the manifests, not just
the filenames — you need versions and framework flavors to write anything useful.

## 2. Diff against installed skills

```
ls ~/.claude/skills/
```

For each detected technology, does `~/.claude/skills/modernize-<tech>/SKILL.md`
exist? Build the gap list.

Two judgment calls before you write anything:

- **Granularity.** One skill per technology that has a genuinely distinct upgrade
  story. `modernize-react` and `modernize-typescript` are separate concerns;
  "modernize-jsx" is not a thing. Yarn/npm/pnpm are one `modernize-node-tooling`
  skill, not three.
- **Coverage.** Does an existing skill already cover it under another name? A Vite
  config belongs in `modernize-node-tooling`, not a new `modernize-vite`. Don't
  create near-duplicates — extend the existing skill instead, and say that's what
  you're doing.

Report the gap list and what you plan to create before writing. If the list is
long, confirm with the user rather than generating a dozen speculative skills.

## 3. Research before writing

**Do not write a modernization skill from memory.** Version numbers and
recommended patterns are exactly the thing your training data is stale about, and
a skill that confidently names the wrong "current" version is worse than no skill.

For each technology, check what's actually current:

```
npm view <pkg> version                      # npm ecosystem
gh api repos/<owner>/<repo>/releases/latest --jq .tag_name
```

plus `WebSearch`/`WebFetch` for the framework's current upgrade guide and
migration docs. Note the deprecations and the standard migration path — that's
the substance of the skill.

Better still: write the skill so it *re-checks at run time* (as
`modernize-dotnet` and `modernize-github-actions` do) rather than hardcoding a
version. A skill that says "query the release API, take the latest LTS" stays
correct; one that says "upgrade to v18" rots.

## 4. Write the skill

Put the new skill beside the existing sub-skills. `~/.claude/skills/modernize-this`
may be a junction into a skill set folder; resolve it, create
`<that folder's parent>/modernize-<tech>/SKILL.md`, and if that parent is not the
skills folder itself, junction it back in with `link-skills.ps1 -ImportDir <parent>`
from the `upgrade-my-skills` skill's `scripts/`. Otherwise create
`~/.claude/skills/modernize-<tech>/SKILL.md` directly. Match the structure of the
existing sub-skills — read `~/.claude/skills/modernize-dotnet/SKILL.md` as the
reference implementation. Required elements:

**Frontmatter.** `name` in kebab-case matching the directory; `description` in
third person naming the technology, the concrete transformations, several trigger
phrases the user might actually type, and "or when `modernize-this` dispatches to
it". The description is the only thing loaded until the skill fires — it must be
enough to decide relevance.

**Body**, in this order:

1. One-line statement of what the skill owns and what it explicitly does *not*
   (name the neighboring skill that owns the rest).
2. A pointer to read `~/.claude/skills/modernize-this/references/conventions.md`
   first, and the standalone topic branch name (`modernize/<tech>`).
3. **Survey** — the exact commands to learn current versions and configuration.
4. **Tasks, one commit each** — the heart of the skill. Each task gets a concrete
   transformation and a `Modernize: <subject>` commit subject. Order them
   lowest-risk-first. Explicitly mark the ones that can change behavior, and
   require those to be isolated commits.
5. **Verify** — the real build/test/run commands, and an honest note about what
   can't be verified locally.
6. **Finish** — orchestrated vs standalone branching, per the conventions file.
7. **Rules** — the guardrails, especially what *not* to touch.

Write in the imperative, addressed to the agent that will run it. Be specific:
"replace `componentWillMount` with `useEffect`" beats "modernize lifecycle
methods". Vague skills produce vague changes.

Keep it under roughly 200 lines. If a technology needs more, put the depth in a
`references/` file next to the SKILL.md and link it.

## 5. Sanity-check what you wrote

- Frontmatter parses; `name` matches the directory name exactly.
- Every task has a distinct commit subject — no task that says "and also".
- No hardcoded version number that will be wrong in six months, unless the skill
  also says how to re-check it.
- The skill would work in a repo other than this one. It's a user-level skill;
  nothing repo-specific belongs in it.

Then update `~/.claude/skills/modernize-this/SKILL.md` — its step 3 lists the
known sub-skills. Add the new names so the orchestrator knows they exist.

## 6. Report

List each skill created (with its path) and each technology you deliberately
skipped, with the reason. Confirm the repo working tree is unchanged
(`git status`) — this skill writes to `~/.claude/skills/`, never to the repo.

## Rules

- Skills go in `~/.claude/skills/` (user area) so they work across repos. Never
  write a modernization skill into a project's `.claude/skills/`.
- Never modify repo code here. Authoring only.
- Don't create a skill for a technology the repo merely mentions — require real
  evidence (a manifest, a config, source files).
- If a skill for the technology already exists, improve it rather than adding a
  parallel one, and tell the user that's what you did.
