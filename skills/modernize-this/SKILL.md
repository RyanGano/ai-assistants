---
name: modernize-this
description: Detect every technology in the current repo (C#/.NET, Blazor, React, GitHub Actions, yarn/npm, …), run the matching `modernize-*` sub-skills, and open a single Draft PR whose commits are split task-by-task for easy review. Use when the user says "modernize this", "modernize the repo", "bring this codebase up to date", "update to modern .NET/React/etc", or asks to upgrade a project's stack. Works in any Git repo.
---

# Modernize this repo

Survey the repo, decide which `modernize-*` sub-skills apply, run each one, and
land the whole thing as one **Draft** PR with one commit per modernization task.

**Read `references/conventions.md` (next to this file) first** — it defines the
branch, commit, verification, and PR rules that every sub-skill obeys. Everything
below assumes those rules.

## 1. Preflight

- Confirm a Git repo with a GitHub remote and `gh auth status` working. (No
  remote? Do the work locally and tell the user you can't open a PR.)
- `git status` — the tree must be clean. Stash or ask; never bulldoze.
- Sync the default branch:
  ```
  git fetch origin
  git switch <default> && git pull --ff-only
  ```

## 2. Detect the stack

Look for real evidence, not vibes. Cheap high-signal probes:

| Signal | Files to look for |
| --- | --- |
| .NET / C# | `*.csproj`, `*.sln`, `*.slnx`, `global.json`, `Directory.Build.props` |
| Blazor | `Microsoft.NET.Sdk.BlazorWebAssembly`, `*.razor`, `_Imports.razor` |
| React | `package.json` with `react` dep, `*.jsx`/`*.tsx` |
| TypeScript | `tsconfig.json` |
| Node package manager | `yarn.lock` / `package-lock.json` / `pnpm-lock.yaml` |
| Python | `pyproject.toml`, `requirements.txt`, `setup.py` |
| GitHub Actions | `.github/workflows/*.yml` |
| Docker | `Dockerfile`, `compose.yaml` |

Run them in parallel — e.g. `Glob` for `**/*.csproj`, `**/package.json`,
`.github/workflows/*`, plus `Read` on `CLAUDE.md` and the README. Then read the
key manifests to learn *versions*, since that's what decides whether a
modernization is even needed.

Report the detected stack to the user before doing work:

```
Detected: .NET 7 (2 projects), Blazor WebAssembly, GitHub Actions
Will run: modernize-dotnet, modernize-csharp, modernize-blazor, modernize-github-actions
```

## 3. Map technologies to sub-skills

For each detected technology, look for an installed skill named
`modernize-<tech>` (check `~/.claude/skills/`). Known sub-skills at time of
writing: `modernize-dotnet`, `modernize-csharp`, `modernize-blazor`,
`modernize-node-tooling`, `modernize-typescript`, `modernize-react`,
`modernize-github-actions`, `modernize-use-npm`.

Coverage notes so you don't invent overlapping skills: `modernize-node-tooling`
owns the bundler (webpack/Vite), test runner (Jest/Vitest), linter config,
package manager *version* pinning, and Node version — there is no separate
`modernize-vite`, `modernize-eslint`, or `modernize-yarn`.

`modernize-use-npm` owns *changing which* package manager a repo uses (yarn or
pnpm → npm, including the lockfile swap and a guard against the old one). It is
**not** part of the default pipeline — only run it when the user asks to switch,
or when yarn's own deprecation noise (`DEP0169`, `DEP0040`, "Workspaces can only
be enabled in private projects") is the problem being solved. Migrating a
working Yarn Berry or pnpm repo to npm is usually a downgrade; don't do it
unprompted.

**If a detected technology has no matching skill**, don't improvise a one-off
modernization. Tell the user and offer to run `add-modernization-skills`, which
writes the missing skill so it's reusable in every future repo. If they decline,
skip that technology and note it as deferred.

Skip sub-skills whose technology is already current (e.g. .NET already on the
latest LTS with current packages) — say so rather than manufacturing churn.

## 4. Create the shared branch

```
git switch -c modernize/<yyyy-MM-dd>
```

Sub-skills detect the `modernize/` prefix and know to commit onto this branch
without opening their own PR.

## 5. Run the sub-skills in dependency order

Order matters — run in this sequence, and generally lowest-layer first:

1. **Platform/runtime** (`modernize-dotnet`, `modernize-node-tooling`) — target
   framework, build tooling, and package versions. Everything else builds on this.
2. **Language** (`modernize-csharp`, `modernize-typescript`) — new syntax often
   requires the newer runtime landed in step 1.
3. **Framework** (`modernize-blazor`, `modernize-react`) — component/API patterns.
4. **Tooling/CI** (`modernize-github-actions`, Docker) — last, so CI reflects the
   final target framework and toolchain versions.

Invoke each with the `Skill` tool, one at a time, and let it finish (including its
own build verification and commits) before starting the next. If a sub-skill
fails to get a green build, **stop the pipeline** and report — don't stack more
changes on a broken tree.

## 6. Final verification

After the last sub-skill, build the whole solution and run the full test suite
once more from a clean state. Fix or revert anything red before proceeding.

## 7. Push and open the Draft PR

```
git push -u origin modernize/<yyyy-MM-dd>
gh pr create --draft --base <default> --head modernize/<yyyy-MM-dd> \
  --title "Modernize: <stack summary>" --body "<body>"
```

Use the body structure from `references/conventions.md`. List the commits grouped
by sub-skill so a reviewer can see which layer each change came from, and be
explicit in "Deferred / needs a decision" about anything you chose not to do.

Report the PR URL, the commit count, and the deferred list to the user.

## Rules

- Draft PR only. Never merge, never push to the default branch.
- One commit per task, always — see `references/conventions.md`.
- Modernization only: no features, no bug fixes riding along.
- If the repo has no tests, say so loudly. It changes how much the user should
  trust a mechanical upgrade.
- Prefer stopping and asking over guessing on anything that breaks a public API
  or changes runtime behavior.
