# Modernization skills

`modernize-this` is the entry point: it detects the technologies in a repo, runs
the matching sub-skills, and opens a single Draft PR with commits split
task-by-task for easy review.

| Skill | Scope |
| --- | --- |
| [`modernize-this`](modernize-this) | Orchestrator — detects the stack and dispatches to the skills below. |
| [`modernize-dotnet`](modernize-dotnet) | Target frameworks, SDK pins, NuGet packages, project-file style. |
| [`modernize-csharp`](modernize-csharp) | C# syntax and idioms — file-scoped namespaces, primary constructors, collection expressions, pattern matching. |
| [`modernize-blazor`](modernize-blazor) | Render modes, `PersistentComponentState`, typed `HttpClient`, CSS isolation, current project layout. |
| [`modernize-react`](modernize-react) | React major upgrades, removed legacy APIs, class components to hooks, React Router migrations. |
| [`modernize-typescript`](modernize-typescript) | Compiler upgrades, `tsconfig` modernization, incremental strictness, type-only imports. |
| [`modernize-node-tooling`](modernize-node-tooling) | Build and dev tooling — CRA/webpack to Vite, Jest to Vitest, ESLint flat config, package manager pinning. |
| [`modernize-use-npm`](modernize-use-npm) | Migrates a repo from yarn/pnpm/bun to npm, including CI and a guard against the old package manager. |
| [`modernize-github-actions`](modernize-github-actions) | Action versions, runner images, caching, permissions, concurrency, deprecated syntax. |
| [`add-modernization-skills`](add-modernization-skills) | Finds technologies with no matching `modernize-*` skill and writes the missing ones into this folder. |

Shared rules — branch protocol, one commit per task, verification, scope
discipline, the Draft PR — live in
[`modernize-this/references/conventions.md`](modernize-this/references/conventions.md).

## How these are installed

Claude Code does not discover nested skill folders, so each skill here is linked
into `../skills/<name>` by a gitignored directory junction. The sub-skills read
the shared conventions at `~/.claude/skills/modernize-this/references/`, which
resolves through that junction. Recreate the junctions with
[`link-skills.ps1`](../skills/upgrade-my-skills/scripts/link-skills.ps1).
