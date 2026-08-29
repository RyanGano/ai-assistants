# Modernization conventions (shared contract)

Every `modernize-*` skill follows these rules. `modernize-this` orchestrates them;
each sub-skill must also work standalone.

## Branch protocol

The branch name is `modernize/<topic>` for a standalone run (e.g. `modernize/dotnet`)
or `modernize/<yyyy-MM-dd>` when `modernize-this` drives several sub-skills together.

**How a sub-skill decides what to do** — check the current branch:

```
git rev-parse --abbrev-ref HEAD
```

- Branch already starts with `modernize/` → you are running **orchestrated**.
  Commit onto the current branch. Do **not** create a branch, push, or open a PR;
  the orchestrator does that once at the end.
- Otherwise → you are running **standalone**. Do the full flow yourself: verify a
  clean tree, sync the default branch, create `modernize/<topic>`, commit, push,
  open a Draft PR.

Detect the default branch with
`git symbolic-ref --quiet --short refs/remotes/origin/HEAD` (strip the `origin/`
prefix), falling back to `main`, then `master`. Never hardcode it.

Never start on a dirty tree. Run `git status` first; if there are changes, stash
(`git stash -u`) or ask the user — don't silently include their work.

## Commit granularity — the core rule

**One commit per distinct modernization task.** The whole point is that a reviewer
can read the PR commit-by-commit and accept or drop individual changes. A single
"modernize everything" commit is a failed run.

Split by *kind of change*, not by file. Good commit boundaries:

- `Modernize: retarget CatandomizerService to net10.0`
- `Modernize: adopt file-scoped namespaces`
- `Modernize: replace string.Format with interpolation`
- `Modernize: bump actions/checkout to v5`

Rules:

- Each commit must build on its own. Verify before committing (see below).
- Never mix a mechanical refactor with a behavior change in one commit. If a
  modernization changes runtime behavior, isolate it and call that out in the
  commit body.
- Prefix subjects with `Modernize: ` so the history reads cleanly.
- If a change is large but purely mechanical (e.g. file-scoped namespaces across
  60 files), it is still one commit — mechanical uniformity is what makes it
  reviewable.
- End every commit message with:
  ```
  Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
  ```

## Verify before each commit

Discover the project's real commands (`CLAUDE.md`, `README`, `package.json`
scripts, `Makefile`, `*.sln`/`*.csproj`) rather than guessing. Before **each**
commit: build, and run tests if the repo has any. If it fails, fix it or revert
that task — never commit a broken tree and never "fix it in the next commit".

If the repo has no tests, say so explicitly in your report and in the PR body.
Modernization without tests is higher risk and the user should know.

## Scope discipline

- Modernize only. No new features, no bug fixes, no opportunistic redesigns.
- Don't touch generated files, vendored code, or lockfile-only artifacts unless
  the task is specifically about them.
- If a modernization would require a breaking API change or a product decision,
  **stop and surface it** rather than forcing it through. Record it as a "deferred"
  item in your report and in the PR body.
- Prefer the smallest change that achieves the modernization. Don't reformat
  untouched code — a formatter run that rewrites the whole repo drowns the diff.
  If the repo needs a format pass, make it its own commit.

## The Draft PR

Always `--draft`. Never merge. Title:

```
Modernize: <stack summary>
```

Body structure:

```markdown
## What changed

<one line per commit, grouped by sub-skill>

## Verification

<build/test commands run and their results; state plainly if there are no tests>

## Deferred / needs a decision

<anything skipped, and why — breaking changes, ambiguous upgrades, missing coverage>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Reporting

Report honestly. If a build failed, show the output. If you skipped a task, say
which and why. Never describe a modernization as done when it was only attempted.
