---
name: modernize-react
description: Upgrade a React app's major version and component patterns — createRoot, removed legacy APIs (string refs, defaultProps on functions, findDOMNode, ReactDOM.render), ref-as-prop, class components to hooks, React Router major migrations, and the official codemods — committing each task separately. Use when the user asks to "modernize React", "upgrade to React 19", "get off React 17/18", "replace class components with hooks", "run the React codemods", or when `modernize-this` dispatches to it. Owns React library and component patterns; the build tool and package manager belong to modernize-node-tooling.
---

# Modernize React (version, APIs, component patterns)

Own the React library upgrade and the component/API patterns that come with it.
The bundler, dev server, test runner, and package manager are **not** yours —
those belong to `modernize-node-tooling`. TypeScript compiler options and type
strictness belong to `modernize-typescript`.

**Read `~/.claude/skills/modernize-this/references/conventions.md` first** — it
defines branch handling (orchestrated vs standalone), the one-commit-per-task
rule, per-commit verification, and the Draft PR format. Standalone topic branch
name: `modernize/react`.

## 1. Survey

Never assume what "latest" is — your training data is stale. Query it:

```
npm view react version
npm view react-dom version
npm view @types/react version
npm view react-router-dom version
npm ls react react-dom            # what's actually installed, and duplicates
npm outdated                       # or yarn/pnpm equivalent
```

Read `package.json` for the current `react`/`react-dom` range and every
React-ecosystem peer (`react-router`, `react-bootstrap`, `styled-components`,
`@testing-library/react`, `@mui/*`, `redux`, …).

**Read the declared range, not just the installed version.** A lockfile can hold
a compatible version while `package.json` still declares a floor from before the
React major — `"react-bootstrap": "^2.7.2"` resolves to 2.10.x today, but the
range is a lie about what the app supports, and the next resolution, a fresh
`npm install`, or a peer-driven downgrade can land under the floor. Raise the
declared range to the version you actually verified.

Then grep the source for the legacy shapes you'll have to fix:

```
grep -rn "ReactDOM.render\|ReactDOM.hydrate\|unmountComponentAtNode" src
grep -rn "findDOMNode\|createFactory\|react-dom/test-utils" src
grep -rn "defaultProps\|propTypes\|contextTypes\|getChildContext" src
grep -rn "ref=[\"']" src                    # string refs
grep -rn "componentWillMount\|componentWillReceiveProps\|componentWillUpdate" src
grep -rn "extends React.Component\|extends Component" src
```

Record what you found. If none of it appears, say so — a version bump may be the
entire job, and that's a fine outcome.

## 2. Pick the target version

Take the latest stable major from `npm view react version` unless a peer
dependency blocks it. **Check peers before committing to the jump**: run
`npm info <peer> peerDependencies` for each React-ecosystem package and confirm
it accepts the new major. A peer that doesn't support it yet is a deferred item,
not a `--legacy-peer-deps` override.

**UI component libraries need a version that supports the new major, not merely
one that installs.** They reach into React internals — refs, portals, transitions,
`findDOMNode` — far more than application code does, so a stale-but-installable
version fails at runtime rather than at build time. Known floors:

| Library | React 19 floor |
| --- | --- |
| react-bootstrap | **2.10.7** (2.x is the stable line; 3.0.0 is still beta) |
| @mui/material | 6.x, or a 5.x release with the React 19 patches |
| react-router-dom | 6.28 / 7.x |
| styled-components | 6.x |

Verify rather than trust the table — it ages. For each UI library run
`npm view <pkg> version` for the latest stable and
`npm info <pkg> peerDependencies` for what it claims to accept, and check
whether the newest line is a prerelease. **Never move a deployed app onto a
beta or release-candidate UI library to fix a React compatibility problem**;
that is the user's call, not the skill's.

Read the official upgrade guide for the target major before editing anything —
fetch `https://react.dev/blog` and find the current "React <N> Upgrade Guide".
The deprecations and codemod names below are the React 19 set; re-verify them
against the guide for whatever major you are actually targeting.

If you are two or more majors behind, land the intermediate major first
(React's own advice: go to the last minor of the previous major, fix the
deprecation warnings it logs, then jump). Each major is its own commit.

## 3. Do the tasks — one commit each

Skip any that don't apply. Build after each, then commit.

### Task: clear deprecation warnings on the current major
Bump to the latest minor of the *current* major, run the app and the tests, and
fix every React deprecation warning it logs. This is the cheapest way to find
what the major bump will break.
→ `Modernize: clear React deprecation warnings before major upgrade`

### Task: switch to the createRoot API
Replace `ReactDOM.render` / `ReactDOM.hydrate` with `createRoot` /
`hydrateRoot` from `react-dom/client`, and `unmountComponentAtNode` with
`root.unmount()`.
```
npx codemod@latest react/19/replace-reactdom-render
```
→ `Modernize: switch to the createRoot API`

### Task: raise UI library ranges to versions that support the new major
Bump each UI component library to the newest stable release that accepts the
target React major, and update the declared range in `package.json` — not only
the lockfile. Do this **before** bumping React, so the libraries are already on
compatible code when React changes underneath them.
→ `Modernize: raise <library> to a React <N> compatible version`

### Task: bump React and its type packages
Update `react`, `react-dom`, `@types/react`, `@types/react-dom` together — a
mismatched `@types/react` major produces hundreds of phantom errors. Bump
React-ecosystem peers in the same commit only when the new React major requires
it; otherwise leave them.
→ `Modernize: upgrade React to v<N>`

### Task: run the official migration codemods
```
npx codemod@latest react/19/migration-recipe        # aggregate recipe
npx types-react-codemod@latest preset-19 ./src      # TS-specific
```
Review the diff — codemods are mechanical and occasionally wrong. Individual
codemods (`react/19/replace-string-ref`, `react/19/replace-act-import`,
`react/prop-types-typescript`) exist if you want them one at a time; each
individual codemod you run separately gets its own commit.
→ `Modernize: apply React <N> migration codemods`

### Task: remove APIs deleted in the new major
The React 19 set — re-verify against the guide for your target:
- `propTypes` / `defaultProps` on **function** components → TS prop types and ES6
  default parameters. (Class `defaultProps` still works.)
- String refs (`ref="input"`) → callback refs. Note callback refs may no longer
  implicitly return a value: write `ref={el => { this.x = el }}`, not
  `ref={el => (this.x = el)}`.
- Legacy context (`contextTypes`, `getChildContext`) → `createContext`.
- `findDOMNode` → a real ref on the element.
- `createFactory` and module-pattern factories → plain functions returning JSX.
- `react-dom/test-utils` `act` → `import { act } from 'react'`.
- `react-test-renderer/shallow` → the `react-shallow-renderer` package, or better,
  delete the shallow test.
→ one commit per API family, e.g. `Modernize: replace string refs with callback refs`

### Task: adopt ref-as-prop (function components)
Where a function component wraps `forwardRef` solely to pass a ref through,
accept `ref` as an ordinary prop and drop the `forwardRef` wrapper. Do not touch
`forwardRef` uses that also use `useImperativeHandle` — those still need review.
→ `Modernize: accept ref as a prop instead of forwardRef`

### Task: convert class components to function components — **behavior-adjacent**
Only for components you can verify. Map:
- `componentDidMount` / `componentWillUnmount` → `useEffect` with a cleanup return
- `componentDidUpdate` → `useEffect` with a dependency array
- `componentWillMount` / `componentWillReceiveProps` / `componentWillUpdate` →
  `useEffect`, derived state during render, or `useMemo`
- `this.state` / `setState` → `useState` (note: `setState` merges partial state,
  `useState` replaces — split into separate `useState` calls or merge explicitly)
- `this.props.x` → destructured props

Error boundaries **cannot** be converted — they still require a class. Leave them.

**One component per commit.** This changes runtime behavior (effect timing,
state batching, closure capture) and is the single most likely task in this skill
to introduce a bug. If the component has no test, say so in the commit body and
in the PR.
→ `Modernize: convert <ComponentName> to a function component`

### Task: adopt error-handling options on the root — **behavior-adjacent**
React 19 no longer re-throws caught errors to `window.onerror`. If the app relied
on that for telemetry, wire `onUncaughtError` / `onCaughtError` on `createRoot`.
Isolated commit; verify an error actually reaches the reporter.
→ `Modernize: wire root error handlers for React <N> error semantics`

### Task: React Router major upgrade — **behavior-adjacent**
Only if `react-router` is actually imported (a dependency nobody imports is a
`modernize-node-tooling` cleanup, not yours). Follow the official upgrade guide
at `https://reactrouter.com/upgrading` for the major you're on; v6→v7 and the v7
framework/data modes each change routing semantics. Isolated commit, and verify
every route renders.
→ `Modernize: upgrade React Router to v<N>`

## 4. Verify

Discover the real commands from `package.json` scripts / `CLAUDE.md` rather than
guessing. Typically:

```
<pm> install
<pm> run build
<pm> test --watchAll=false      # or vitest run
<pm> start                       # then actually load the page
```

Honest limits: a green build proves nothing about hooks. **Load the app and
exercise every screen you touched**, watching the browser console for warnings —
React logs most of the interesting failures at runtime, not compile time. If the
repo has no tests, say so loudly in your report and in the PR body; a class→hooks
conversion without tests is the riskiest thing in this skill.

**Exercise the UI library's overlay components by hand.** Tooltips, popovers,
dropdowns, modals and anything else that portals or positions itself is where a
React major breaks a component library, and it breaks silently: the element
renders, so the build and the tests pass, but it lands unpositioned in a corner
or behind the rest of the page. Open one of each and watch where it actually
appears. A jsdom test can confirm such a component mounts and portals, but it
cannot confirm it is positioned or visible — its rects are all zero. Say so in
the report rather than implying coverage you do not have.

## 5. Finish

Orchestrated (branch already `modernize/*`): stop here and report the commits.
Standalone: push `modernize/react` and open the Draft PR per the conventions file.

## Rules

- Never bump React and convert components in the same commit.
- Never use `--force` / `--legacy-peer-deps` to paper over a peer that doesn't
  support the new major. Defer the upgrade and say why.
- Raise a dependency's declared range whenever you verify a newer version of it;
  leaving the range below what the app needs is the bug that bites later.
- Never reach for a beta or release-candidate UI library to solve a compatibility
  problem. Report the option and let the user decide.
- `react` and `react-dom` versions must always match exactly.
- Don't convert error boundaries to functions. They can't be.
- Don't restyle, rename, or "improve" a component while converting it — the diff
  must show the conversion and nothing else.
- Codemod output is a draft, not a result. Read every hunk before committing.
