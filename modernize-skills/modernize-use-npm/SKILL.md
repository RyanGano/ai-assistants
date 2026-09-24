---
name: modernize-use-npm
description: Migrate a JavaScript/TypeScript repo from yarn (or pnpm/bun) to npm — replace the lockfile, rewrite package.json scripts and CI, and install a guard that fails with an explanation when someone runs the old package manager. Use when the user asks to "switch from yarn to npm", "move to npm", "get rid of yarn", "use npm instead", "block yarn", "stop people using yarn", or when yarn's deprecation noise (DEP0169 url.parse, DEP0040 punycode, "Workspaces can only be enabled in private projects") shows up in build logs. Owns the package-manager choice only; bundler, test runner and linter belong to modernize-node-tooling.
---

# Migrate to npm

Move a repo onto npm as its single package manager, and make the switch stick by
failing loudly when someone reaches for the old one.

**Read `~/.claude/skills/modernize-this/references/conventions.md` first** — it
defines branch handling (orchestrated vs standalone), the one-commit-per-task
rule, per-commit verification, and the Draft PR format. Standalone topic branch:
`modernize/use-npm`.

## When this is the right call

npm is not automatically better than yarn or pnpm. Have a reason, and put it in
the PR. Good reasons:

- **yarn classic (1.x) is unmaintained.** Last release 1.22.22; maintenance-only
  since 2020. On Node 22+ it prints `DEP0169` (`url.parse()`) and `DEP0040`
  (`punycode`) from its *own* bundled `cli.js` on every install, and there will
  be no fix.
- **yarn 1 emits spurious warnings you cannot act on.** `Workspaces can only be
  enabled in private projects.` fires for any *dependency* whose published
  manifest carries a `workspaces` key without `private: true` — nothing to do
  with your repo. It also fails to credit transitive dependencies toward peer
  ranges, producing "unmet peer dependency" for peers that are in fact installed.
- **The deploy platform dictates it.** Azure Static Web Apps (Oryx), some
  Netlify/Vercel and Docker base images ship their own package manager and pick
  it from the lockfile. If the platform runs npm well and yarn badly, match it.
- **`packageManager` is being ignored.** Corepack is not enabled everywhere. If
  the build log shows a different version than the field pins, that pin is
  decorative.

Bad reasons: preference, or "npm is the default". If the repo is on **Yarn Berry
(2+) or pnpm** and working, migrating to npm is usually a *downgrade* — both have
faster installs and stricter dependency resolution. Say so and stop rather than
grinding through it.

**Confirm the diagnosis before migrating.** Do not take a warning's word for
where it comes from:

```
# Is the warning really the package manager's own code?
grep -c "url\.parse(\|punycode" "$(dirname "$(which yarn)")/../lib/cli.js"

# Which dependency triggers a per-package warning? Isolate it.
mkdir /tmp/pmtest && cd /tmp/pmtest
echo '{"name":"t","version":"1.0.0","private":true}' > package.json
yarn add -D <suspect-package>     # does the warning appear alone?

# Does npm actually produce a clean install of this same package.json?
cd /tmp/pmtest && cp <repo>/package.json . && npm install --no-audit --no-fund
```

## 1. Survey

```
ls yarn.lock package-lock.json pnpm-lock.yaml bun.lockb   # more than one is a finding
cat package.json                     # scripts, packageManager, engines
node --version && npm --version
grep -rn "yarn\|pnpm" .github/workflows/ Dockerfile* *.md 2>/dev/null
grep -rn "yarn\|pnpm" .husky/ .config/ 2>/dev/null
```

Find **every** invocation, not just the obvious ones: CI workflows, Dockerfiles,
git hooks (husky/lefthook), `Makefile`, `netlify.toml` / `vercel.json` /
`staticwebapp.config.json`, README and CLAUDE.md, VS Code tasks, and any script
that shells out to `yarn`.

Also check for yarn features with no npm equivalent — these decide whether the
migration is even clean:

- `resolutions` → npm's `overrides` (different syntax, mostly translatable)
- `.yarnrc.yml` with `nodeLinker`, `plugins`, patch protocol → **stop and ask**
- Yarn workspaces → npm workspaces (supported, but verify each package resolves)
- `yarn patch` / `patch:` protocol → needs `patch-package` under npm

## 2. Do the tasks — one commit each

### Task: replace the lockfile
Delete the old lockfile, generate `package-lock.json`, set
`"packageManager": "npm@<version>"`. Never leave two lockfiles committed — that
is the ambiguity the whole migration exists to remove.

```
git rm yarn.lock
rm -rf node_modules
npm install
```

Diff the resulting tree against the old one for anything that moved major
version. `npm install` resolves fresh; it does **not** read `yarn.lock`. If you
need to preserve exact versions, note that `yarn.lock` → `package-lock.json`
conversion is not lossless and say so in the commit body.
→ `Modernize: switch package manager from yarn to npm`

### Task: rewrite package.json scripts
Translate every script that shells out to the old manager:

| yarn | npm |
| --- | --- |
| `yarn <script>` | `npm run <script>` |
| `yarn <bin>` inside a script | just `<bin>` — `node_modules/.bin` is already on PATH |
| `yarn install --frozen-lockfile` | `npm ci` |
| `yarn add X` / `yarn add -D X` | `npm install X` / `npm install -D X` |
| `yarn remove X` | `npm uninstall X` |
| `yarn version --major` | `npm version major` |
| `yarn dlx X` | `npx X` |

Two npm behaviors that bite:

- **Flags need `--`.** `yarn test -t foo` becomes `npm run test -- -t foo`.
  Update docs, and verify one such command actually filters rather than
  assuming.
- **`npm version` has a `version` lifecycle hook** that runs after the bump and
  before the commit. If the repo regenerated a version file *after* `yarn
  version` (leaving it in a separate commit), move it here so it lands in the
  same commit: `"version": "npm run store-version && git add src/version.ts"`.
→ `Modernize: rewrite package.json scripts for npm`

### Task: install the guard — the part that makes it stick
Muscle memory outlives the migration, and so do AI agents that were trained on
`yarn install`. Without a guard the repo silently grows a second lockfile and a
divergent tree.

Write `scripts/ensure-npm.cjs`. It must have **no imports** (it runs from
`preinstall`, before `node_modules` exists) and be `.cjs` if package.json sets
`"type": "module"`:

```js
const agent = process.env.npm_config_user_agent ?? "";
const manager = agent.split("/")[0] || "yarn";  // yarn-path sets no agent

if (manager !== "npm") {
  process.stderr.write(`✖ This project uses npm. Detected: ${manager}\n...`);
  process.exit(1);
}
```

Wire it to **two** entry points — neither alone is sufficient:

1. `package.json`: `"preinstall"` and `"prebuild"`. Reads
   `npm_config_user_agent`, so pnpm and bun are caught too.
2. `.yarnrc` (classic) with `yarn-path "./scripts/ensure-npm.cjs"`. Yarn
   delegates every command to that script **before** it parses `package.json`.
   This matters: without it, yarn classic stops earlier on its own corepack
   check and prints a genuinely confusing message — it concatenates its own name
   onto the field and reports `"packageManager": "yarn@npm@10.9.4"`, which reads
   like a malformed config rather than "wrong package manager". Yarn invokes
   `yarn-path` with no user agent set, which is why an empty agent must be
   treated as *not npm*.

Make the message **useful**, not just a refusal: the npm equivalent of what they
tried, why the repo enforces it, and which files to change if they are switching
deliberately.

Verify every entry point: `yarn install`, `yarn add X`, `yarn <script>` must each
exit 1; `npm ci`, `npm install`, `npm run build` must be unaffected.
→ `Modernize: fail with an explanation when yarn or pnpm is used`

### Task: update CI and deploy config
`yarn install --frozen-lockfile` → `npm ci`; `setup-node`'s `cache: yarn` →
`cache: npm`. If the repo has a `.nvmrc`, keep reading it via
`node-version-file`.

For platforms that auto-detect (Azure SWA/Oryx, Netlify, Vercel, Cloudflare
Pages), the **lockfile is the switch** — there is usually nothing to configure,
but confirm it in the build log after the first run rather than assuming.
→ `Modernize: run CI on npm`

### Task: update the docs
README, CLAUDE.md, CONTRIBUTING. Every command a human or agent copies. Include a
short note on *why* yarn is blocked, so whoever hits the guard finds the
reasoning and not just a wall.
→ `Modernize: update documentation for npm`

## 3. Verify

```
rm -rf node_modules && npm ci     # must succeed from a clean tree
npm run build
npm test
npm audit
yarn install                      # must exit 1 with the explanation
yarn build                        # must exit 1 with the explanation
```

Compare the build output against the pre-migration build — same files, same
approximate sizes. A different dependency tree can change the bundle, and that is
worth catching here rather than in production.

Honest limits: a clean local `npm ci` does not prove the deploy platform switched
package managers. That is only confirmed by reading the **first build log after
merge** for the manager and version it reports. Say so.

## 4. Finish

Orchestrated (branch already `modernize/*`): stop here and report the commits.
Standalone: push `modernize/use-npm` and open the Draft PR per the conventions
file.

## Rules

- Exactly one lockfile in the repo when you are done. Never commit two.
- Never run the old package manager after the switch to "just get it working" —
  that regenerates the lockfile you deleted.
- Never use `--force` or `--legacy-peer-deps` to make `npm install` complete.
  npm enforces peer ranges that yarn 1 ignored, so a *new* conflict here is real
  information about a dependency mismatch — surface it, don't suppress it.
- Don't migrate a working Yarn Berry or pnpm repo to npm without a stated reason
  the user has agreed to.
- Don't silently upgrade dependencies during the lockfile swap. If regenerating
  moved majors, that is its own commit and its own risk statement.
- If the repo uses yarn workspaces, `resolutions`, or patch protocols, verify
  each translated construct individually — these are where the migration
  actually breaks.
