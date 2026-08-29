---
name: modernize-typescript
description: Upgrade the TypeScript compiler and modernize tsconfig and type-level source idioms — raising `target`/`lib`, moving to bundler module resolution, enabling strict family flags incrementally, `verbatimModuleSyntax` and type-only imports, replacing namespaces and enums, removing needless `any` and non-null assertions — committing each task separately. Use when the user asks to "modernize TypeScript", "upgrade TypeScript", "turn on strict mode", "fix the tsconfig", "get off target es5", or when `modernize-this` dispatches to it. Owns tsconfig and type-level syntax; framework APIs and the build tool belong to their own skills.
---

# Modernize TypeScript (compiler version, tsconfig, type idioms)

Own the TypeScript compiler version, `tsconfig.json`, and type-level source
idioms. The bundler and test runner belong to `modernize-node-tooling`; React
component patterns belong to `modernize-react`. Run this **after** the runtime and
package upgrades, since newer compiler options are what enable the newer syntax.

**Read `~/.claude/skills/modernize-this/references/conventions.md` first** — it
defines branch handling (orchestrated vs standalone), the one-commit-per-task
rule, per-commit verification, and the Draft PR format. Standalone topic branch
name: `modernize/typescript`.

## 1. Survey

Check what's actually current rather than trusting memory — TypeScript's major
cadence has moved faster than most people expect:

```
npm view typescript version
npx tsc --version                  # what the repo is on now
npm view typescript versions --json | tail -20   # is a major in between?
```

Read every `tsconfig*.json` (including `references` in a solution-style setup)
and record: `target`, `lib`, `module`, `moduleResolution`, `strict` and each
strict-family flag, `jsx`, `isolatedModules`, `verbatimModuleSyntax`, `noEmit`,
`skipLibCheck`, `paths`. Then survey the source:

```
grep -rn "namespace \|module [A-Za-z]" src --include=*.ts --include=*.tsx
grep -rn "\benum \b" src
grep -rn ": any\b\|as any\b\|<any>" src
grep -rn "!\." src                 # non-null assertions
grep -rn "@ts-ignore" src
grep -rn "/// <reference" src
```

Baseline the error count before you change anything:
`npx tsc --noEmit 2>&1 | tail -5`. Every task below is judged against it.

## 2. Pick the target version

Take the latest stable from `npm view typescript version`. **Majors are not
skippable**: if the repo is more than one major behind, land each intermediate
major as its own commit and fix its deprecation warnings before moving on — the
intermediate release is what tells you what the next one will break.

Before upgrading, check the release notes for the target major
(`https://www.typescriptlang.org/docs/handbook/release-notes/` — read the
"breaking changes" section, and `https://github.com/microsoft/TypeScript/wiki`
for the announcement post). Also confirm the ecosystem accepts it: the ESLint TS
plugin, the build tool's TS integration, and any `ts-node`/`tsx` all pin
supported compiler ranges, and a compiler ahead of its tooling is a broken repo.

## 3. Do the tasks — one commit each

Lowest-risk first. Skip what doesn't apply. `npx tsc --noEmit` **plus a real
build** after each, then commit.

### Task: upgrade the compiler
Bump `typescript` (and `@types/node` to a major matching the Node runtime). Land
one major per commit. Take zero new type errors as the bar — if the new compiler
finds real errors, fix them in this commit if there are a handful, otherwise
revert and make the fixes their own commit first.
→ `Modernize: upgrade TypeScript to <N>.x`

### Task: raise `target` and `lib`
`target: "es5"` is the classic CRA-era leftover and costs bundle size on every
downleveled class, generator, and `async`. Raise it to a level your browserslist
or Node `engines` actually supports — `ES2022` is the common safe modern floor —
and set `lib` to match (drop hand-listed polyfill libs the target now includes).
This changes emitted output; verify the app runs, not just that it compiles.
→ `Modernize: raise TypeScript target to ES2022`

### Task: modernize module resolution
For a bundled app (Vite/webpack/esbuild): `"module": "ESNext"` +
`"moduleResolution": "bundler"`. For a Node package: `"module": "NodeNext"` +
`"moduleResolution": "NodeNext"`, and add the `exports` map to `package.json` if
it's missing. `"moduleResolution": "node"` (node10) is legacy and cannot resolve
`exports` maps — that's the bug behind most "types not found" reports.
→ `Modernize: switch to bundler module resolution`

### Task: enable the strict family incrementally
If `strict` is already on, move to the flags it does *not* include:
`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`,
`noImplicitOverride`, `noPropertyAccessFromIndexSignature`,
`useUnknownInCatchVariables` (on under `strict` since 4.4 — verify).

If `strict` is off, do **not** flip it in one commit. Enable one flag at a time,
in this order, each its own commit: `noImplicitThis` → `strictBindCallApply` →
`strictFunctionTypes` → `noImplicitAny` → `strictNullChecks` (by far the
largest). Fix the errors it produces in that same commit.

If a flag produces more errors than you can honestly fix, **leave it off and
record it as deferred**. A wall of `@ts-ignore` or `as any` to make a flag pass is
worse than not enabling the flag, and you must not do it.
→ `Modernize: enable strictNullChecks` (one commit per flag)

### Task: adopt `verbatimModuleSyntax` and type-only imports
Set `"verbatimModuleSyntax": true` and mark type-only imports as
`import type { Foo } from './foo'`. This removes a whole class of bundler
side-effect surprises and is required by some build setups. `isolatedModules`
should be on too (bundlers require it).
→ `Modernize: adopt verbatimModuleSyntax and type-only imports`

### Task: replace namespaces with ES modules
`namespace Foo { }` and `/// <reference path=…>` predate ES modules and don't
tree-shake. Convert each to a module with named exports. Ambient
`declare module` blocks for untyped packages are fine — leave those.
→ `Modernize: replace namespaces with ES modules`

### Task: replace enums — **behavior-adjacent**
Numeric `enum` has runtime cost and reverse-mapping surprises; `const enum`
breaks under `isolatedModules`. Prefer a `const` object plus a derived union:
```ts
const Status = { Active: 'active', Done: 'done' } as const;
type Status = (typeof Status)[keyof typeof Status];
```
Only do this where the enum is internal. An enum in a published API is a
breaking change — defer it and say so. Isolated commit.
→ `Modernize: replace enums with const object unions`

### Task: modern type syntax
Mechanical, low risk, one commit for all of it:
- `Array<T>` ↔ `T[]` — pick whichever the codebase already prefers, consistently
- `satisfies` where a value is annotated only to check its shape
- `?.` / `??` in place of hand-written null guards and `||` defaults
- `unknown` instead of `any` in `catch` clauses and untyped boundaries
- drop `React.FC` in favor of a plain typed props parameter
→ `Modernize: adopt current TypeScript syntax idioms`

### Task: remove suppressions
Replace `@ts-ignore` with `@ts-expect-error` (it errors when the suppression
becomes unnecessary, so it self-cleans), and delete the ones that are already
unnecessary. Where the underlying type is genuinely wrong, fix the type.
→ `Modernize: replace @ts-ignore with @ts-expect-error`

## 4. Verify

```
npx tsc --noEmit              # must be no worse than the baseline you recorded
<pm> run build
<pm> test
```

Honest limits: `tsc --noEmit` is erasure-only — it proves nothing about runtime.
Raising `target`, replacing enums, and `verbatimModuleSyntax` all change emitted
JavaScript, so **run the app** after those. And a type change that silences an
error by widening a type has made things worse while looking green; re-read those
diffs yourself.

## 5. Finish

Orchestrated (branch already `modernize/*`): stop here and report the commits.
Standalone: push `modernize/typescript` and open the Draft PR per the conventions
file.

## Rules

- Never add `any`, `as`, `@ts-ignore`, or `skipLibCheck` to make a task pass.
  Fix, revert, or defer — those three only.
- Never enable `strict` wholesale in one commit on a non-strict codebase.
- One compiler major per commit; never skip a major.
- Don't touch `.d.ts` files in `node_modules` or generated types.
- If a stricter flag reveals a genuine latent bug, that's a **finding to report**,
  not a fix to sneak into a modernization commit.
