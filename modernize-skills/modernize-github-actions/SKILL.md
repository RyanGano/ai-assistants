---
name: modernize-github-actions
description: Update GitHub Actions workflows — action versions, runner images, toolchain versions, caching, permissions, concurrency, and deprecated commands — committing each task separately. Use when the user asks to "modernize CI", "update GitHub Actions", "bump action versions", "fix deprecated workflow syntax", or when `modernize-this` dispatches to it. Run last, so CI reflects the final toolchain versions.
---

# Modernize GitHub Actions workflows

Bring `.github/workflows/*.yml` up to current action versions, runner images, and
security defaults. Run this **after** the language/framework sub-skills, so the
CI toolchain versions match what the repo now targets.

**Read `~/.claude/skills/modernize-this/references/conventions.md` first** for
branch handling, one-commit-per-task, verification, and PR format. Standalone
topic branch: `modernize/github-actions`.

## 1. Survey

Read every file in `.github/workflows/` plus any `.github/actions/*/action.yml`.
Record: action `uses:` versions, `runs-on:` images, toolchain version inputs
(`dotnet-version`, `node-version`, `python-version`), triggers, and secrets used.

Check what's actually current rather than trusting memory — action major versions
move, and a wrong pin is a broken workflow:

```
gh api repos/actions/checkout/releases/latest --jq .tag_name
gh api repos/actions/setup-dotnet/releases/latest --jq .tag_name
gh api repos/actions/setup-node/releases/latest --jq .tag_name
```

Also check the repo's own Actions tab for deprecation warnings on recent runs:

```
gh run list --limit 5
gh run view <id> --log | grep -i -E "deprecat|warning"
```

Those warnings are the highest-value signal here — they tell you exactly what
GitHub is about to break.

## 2. Do the tasks — one commit each

Skip what's already current. **Validate after each, then commit.**

### Task: bump action versions
Move every `uses:` to the current major (`actions/checkout@v5`,
`actions/setup-dotnet@v5`, `actions/setup-node@v5`, `actions/upload-artifact@v5`,
… — verify each, don't assume the numbers). Read the release notes for any major
bump: `upload-artifact` v4 changed artifact semantics, `setup-*` actions have
changed caching defaults. Replace archived/deprecated actions with maintained
equivalents.
→ `Modernize: bump GitHub Actions to current major versions`

### Task: align toolchain versions with the repo
The `dotnet-version` / `node-version` in CI must match the target framework or
engines the repo now uses. If `modernize-dotnet` retargeted to net10.0, CI
building with `7.0.x` will fail — this is the most common post-upgrade break.
Prefer reading the version from the repo (`global.json`, `.nvmrc`,
`package.json` `engines`) via `global-json-file:` / `node-version-file:` so the
two can't drift again.
→ `Modernize: align CI toolchain versions with the repo target`

### Task: update runner images
`ubuntu-latest` / `windows-latest` are fine and self-updating. Replace **pinned
deprecated images** (`ubuntu-20.04`, `windows-2019`, any `macos-11/12`) with
current ones. Only pin a specific image if the workflow genuinely needs it.
→ `Modernize: update deprecated runner images`

### Task: least-privilege permissions
Add an explicit top-level `permissions:` block. Default to:
```yaml
permissions:
  contents: read
```
and grant more only per-job where actually needed (`packages: write`,
`id-token: write` for OIDC, `pull-requests: write` for commenting). An absent
block means the workflow inherits whatever the repo default is — usually more than
it needs.
→ `Modernize: apply least-privilege workflow permissions`

### Task: concurrency control
Cancel superseded runs on the same ref:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```
**Do not** set `cancel-in-progress: true` on deployment workflows — cancelling a
deploy mid-flight can leave the target in a broken state. Use `false` there.
→ `Modernize: add concurrency groups`

### Task: dependency caching
Enable the built-in cache inputs rather than hand-rolled `actions/cache` steps:
`setup-node` `cache: 'npm'|'yarn'|'pnpm'`, `setup-dotnet` `cache: true` with
`cache-dependency-path`, `setup-python` `cache: 'pip'`.
→ `Modernize: enable built-in dependency caching`

### Task: remove deprecated syntax
- `::set-output` / `::save-state` → `$GITHUB_OUTPUT` / `$GITHUB_STATE`
- `::add-path` / `::set-env` → `$GITHUB_PATH` / `$GITHUB_ENV`
- `actions/create-release`, `actions/upload-release-asset` (archived) → `gh release`
- `set-safe-directory` workarounds no longer needed
→ `Modernize: replace deprecated workflow commands`

### Task: secrets and auth hygiene
Report — don't silently change — anything worth flagging: long-lived publish
profiles or cloud credentials that could move to OIDC federated auth, secrets
referenced but not documented, `pull_request_target` usage with checkout of
untrusted refs (a real injection risk). Migrating auth to OIDC touches cloud-side
configuration you can't see, so **recommend it in the PR body** rather than
breaking the deploy.
→ (usually no commit; a PR-body recommendation)

### Task: add missing CI (only if the repo has none)
If there is deploy automation but no build/test workflow, adding one is a genuine
modernization — a workflow that runs build + test on PRs against the default
branch. Keep it minimal and matched to the repo's real commands.
→ `Modernize: add build and test workflow for pull requests`

## 3. Verify

You cannot fully test a workflow without pushing it, so verify what you can:

```
gh workflow list                       # workflows still parse
```

Lint the YAML (`actionlint` if available — it catches bad expressions, invalid
`uses:` refs, and shell issues that only surface at runtime otherwise). Re-read
each changed file end to end: indentation errors in YAML are silent until the run
fails.

State clearly in your report that workflow changes are verified only on the next
push — that's the honest limit here.

## 4. Finish

Orchestrated (branch already `modernize/*`): stop and report the commits.
Standalone: push `modernize/github-actions` and open the Draft PR.

## Rules

- Never change what a workflow *deploys to* — app names, resource groups, and
  secret names stay as they are. Modernize the mechanics only.
- Never remove or rename a secret reference. If one looks wrong, report it.
- Preserve path filters and triggers exactly; a workflow that starts firing on
  every push because you "simplified" the trigger is a regression.
- Verify current action major versions from the API — don't write a version
  number from memory.
