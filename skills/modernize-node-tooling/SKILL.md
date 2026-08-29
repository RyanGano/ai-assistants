---
name: modernize-node-tooling
description: Modernize a JavaScript/TypeScript project's build and dev tooling — migrate off Create React App or legacy webpack to Vite, move Jest to Vitest, adopt ESLint flat config, pin the package manager with corepack and an `engines` range, refresh lockfiles, and clear deprecated or vulnerable dependencies — committing each task separately. Use when the user asks to "modernize the build", "migrate off Create React App", "move to Vite", "switch to Vitest", "update ESLint config", "upgrade Node", "clean up package.json", or when `modernize-this` dispatches to it. Covers npm, yarn, and pnpm as one concern; framework and compiler upgrades belong to modernize-react and modernize-typescript.
---

# Modernize Node tooling (build, test runner, linter, package manager)

Own everything between the source and the artifact: bundler and dev server, test
runner, linter config, package manager, Node version, and `package.json` hygiene.
Framework APIs belong to `modernize-react`; `tsconfig.json` and type-level syntax
belong to `modernize-typescript`. Run this **first** — the others build on the
toolchain this skill lands.

**Read `~/.claude/skills/modernize-this/references/conventions.md` first** — it
defines branch handling (orchestrated vs standalone), the one-commit-per-task
rule, per-commit verification, and the Draft PR format. Standalone topic branch
name: `modernize/node-tooling`.

## 1. Survey

Identify the package manager from the lockfile — `package-lock.json` → npm,
`yarn.lock` → yarn, `pnpm-lock.yaml` → pnpm — and use **that one** throughout.
Multiple lockfiles is itself a finding. Then:

```
node --version && npm --version
cat package.json                    # scripts, deps, engines, packageManager
npm outdated                        # or `yarn outdated` / `pnpm outdated`
npm audit                           # vulnerabilities; note, don't auto-fix
npm ls --depth=0
```

Check current versions rather than trusting memory:

```
npm view vite version
npm view vitest version
npm view eslint version
npm view typescript-eslint version
curl -s https://nodejs.org/dist/index.json | head -c 2000   # find lts:"<name>"
```

Pick the **latest active LTS** from that Node index (entries with a non-false
`lts` field), not the newest release.

Look for the tooling files that tell you what era the repo is from:
`react-scripts` in deps (Create React App — unmaintained since 2023),
`webpack.config.js`, `.babelrc`, `.eslintrc*` (legacy eslintrc format),
`jest.config.*`, `.nvmrc`, `craco.config.js`, `config-overrides.js`.

## 2. Do the tasks — one commit each

Order is lowest-risk-first. Skip what doesn't apply. Run install + build + test
after each, then commit.

### Task: pin the toolchain
Add to `package.json`:
- `"engines": { "node": ">=<lts-major>" }`
- `"packageManager": "<pm>@<exact-version>"` (corepack reads this and makes every
  machine and CI agree on one package manager version)

Add `.nvmrc` with the LTS major if the repo or its CI already uses nvm/fnm.
→ `Modernize: pin Node and package manager versions`

### Task: refresh the lockfile and clear vulnerabilities
Delete `node_modules`, reinstall from a fresh lockfile, and take patch/minor
bumps. Review `npm audit` output but **do not run `npm audit fix --force`** — it
takes breaking majors silently. Fix real vulnerabilities deliberately; a
transitive advisory in a dev-only dependency is a note, not an emergency.
→ `Modernize: refresh lockfile and take patch/minor dependency updates`

### Task: drop dependencies nothing imports
Grep for each dependency's import specifier before removing it. A package in
`dependencies` with zero imports is dead weight; a build-time-only package in
`dependencies` instead of `devDependencies` is misfiled. Move or delete.
→ `Modernize: remove unused dependencies`

### Task: migrate off Create React App to Vite — **behavior-adjacent**
CRA is unmaintained and `react-scripts` pins an old webpack, Babel, and Jest.
The migration, in one commit:

1. Remove `react-scripts`; add `vite` and `@vitejs/plugin-react` to devDeps.
2. Move `public/index.html` → repo root. Replace `%PUBLIC_URL%/` with `/`, and
   add `<script type="module" src="/src/index.tsx"></script>` before `</body>`.
3. Add `vite.config.ts`:
   ```ts
   import { defineConfig } from 'vite';
   import react from '@vitejs/plugin-react';
   export default defineConfig({
     plugins: [react()],
     server: { port: 3000 },
     build: { outDir: 'build' },   // keep CRA's dir if CI/deploy expects it
   });
   ```
4. Scripts: `"start": "vite"`, `"build": "tsc --noEmit && vite build"`,
   `"preview": "vite preview"`. Drop `eject`.
5. Env vars: `REACT_APP_*` → `VITE_*`, and `process.env.X` →
   `import.meta.env.VITE_X`. Grep for both — a missed one is `undefined` at
   runtime, not a build error.
6. Ensure every file containing JSX has a `.jsx`/`.tsx` extension (esbuild, unlike
   Babel, will not parse JSX out of a `.js` file).
7. Add `vite-env.d.ts` with `/// <reference types="vite/client" />`.

**Check the deploy config before changing `outDir`** — a CI workflow or an Azure
Static Web Apps / Netlify / Vercel setting names the output directory, and it must
move with you. Update in-repo deploy config here; CI workflow files are
`modernize-github-actions`'s job, so flag them for it.
→ `Modernize: migrate build from Create React App to Vite`

### Task: migrate Jest to Vitest — **behavior-adjacent**
Only after the Vite migration. Add `vitest` and `jsdom`; put `test` config in
`vite.config.ts` with `globals: true`, `environment: 'jsdom'`, and a setup file
importing `@testing-library/jest-dom/vitest`. Replace `jest.fn`/`jest.mock` with
`vi.fn`/`vi.mock`, and `@types/jest` with Vitest's globals. Script becomes
`"test": "vitest"` and `"test:ci": "vitest run"`.

If the repo has no tests, this task is just wiring the runner so tests *can* be
added — say that plainly rather than claiming a test migration.
→ `Modernize: migrate test runner from Jest to Vitest`

### Task: adopt ESLint flat config
`.eslintrc*` is legacy; ESLint 9+ wants `eslint.config.js`. Migrate with:
```
npx @eslint/migrate-config .eslintrc.json
```
then review the result by hand — the migration tool is a starting point. For a
CRA repo the `eslintConfig` block in `package.json` (`extends: react-app`) has no
flat-config successor: replace it with `typescript-eslint` plus
`eslint-plugin-react-hooks` and `eslint-plugin-react-refresh`. Add a `lint`
script — CRA-era repos usually have none.

Land the config with the **existing** rule severity. If the new setup surfaces
real violations, fixing them is a separate commit; do not weaken rules to get a
clean run.
→ `Modernize: adopt ESLint flat config`

### Task: remove superseded tooling config
Once Vite owns the build, delete what only existed to work around CRA or old
webpack: `craco.config.js`, `config-overrides.js`, `.babelrc`/`babel.config.js`
(unless something other than the bundler reads it), `jest.config.*` after the
Vitest move, and `browserslist` if no consumer remains (Vite's `build.target`
supersedes it).
→ `Modernize: remove superseded build configuration`

### Task: major dependency upgrades — **behavior-adjacent**
For each remaining major bump in `npm outdated`: read its release notes and
changelog first, and give it **its own commit**. Never batch majors. If one needs
source changes, the source changes go in that same commit and the commit body
names the breaking change.
→ `Modernize: upgrade <package> to v<N>` (one per package)

## 3. Verify

Use the repo's real commands, discovered from `package.json` scripts and
`CLAUDE.md`:

```
<pm> install --frozen-lockfile     # --frozen-lockfile / ci / --immutable
<pm> run build
<pm> run lint
<pm> run test
<pm> start                          # and actually load the page
```

Honest limits: a Vite build succeeding proves the bundle emits, not that it runs.
Env-var renames, asset URLs (`%PUBLIC_URL%`, `process.env.PUBLIC_URL`), and
dynamic imports fail **only at runtime** — load the app and click through it,
watching the console and network tab. Compare the production build's output
directory and asset paths against what the deploy expects; that mismatch is the
most common way a green CRA→Vite migration still ships a blank page.

## 4. Finish

Orchestrated (branch already `modernize/*`): stop here and report the commits.
Standalone: push `modernize/node-tooling` and open the Draft PR per the
conventions file.

## Rules

- One package manager. Never generate a second lockfile, and never commit one
  from a different package manager than the repo already uses.
- Never `npm audit fix --force`, never `--legacy-peer-deps` / `--force` to get an
  install to complete. A peer conflict is information.
- Never batch major upgrades into one commit.
- Don't run a formatter across the repo as part of any of these tasks. If the repo
  needs a format pass, it's its own commit.
- Don't touch `.github/workflows/` — flag needed CI changes for
  `modernize-github-actions` instead.
- If the build output directory or asset base path changes, say so explicitly in
  the commit body and the PR — that's the change most likely to break a deploy.
