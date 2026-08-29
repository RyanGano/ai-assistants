# ai-assistants

My personal [Claude Code](https://claude.com/claude-code) skills, kept in version
control so they are reviewable, portable, and shareable.

A *skill* is a folder containing a `SKILL.md`: frontmatter describing what the
skill does and when to use it, followed by instructions Claude Code follows when
the task matches. Skills are loaded on demand — the description is what decides
whether one gets pulled in.

## Skills

### Git & GitHub workflow

| Skill | What it does |
| --- | --- |
| [`fix-github-issue`](skills/fix-github-issue) | Picks an open GitHub issue, fixes it end to end, opens a Draft PR, then moves to the next. Language- and stack-agnostic. |
| [`handle-pr-comments`](skills/handle-pr-comments) | Finds unhandled reviewer comments on open PRs and resolves each — answering questions, making changes, and replying with the commit that addressed it. |
| [`clean-pr-commits`](skills/clean-pr-commits) | Rewrites a PR branch's history into a small set of coherent commits grouped by intent, without changing the resulting tree. |
| [`delete-unused-branches`](skills/delete-unused-branches) | Deletes local branches already merged into the default branch, including squash- and rebase-merges that `git branch --merged` misses. |

### Modernization

`modernize-this` is the entry point: it detects the technologies in a repo, runs
the matching sub-skills, and opens a single Draft PR with commits split
task-by-task for easy review.

| Skill | Scope |
| --- | --- |
| [`modernize-this`](skills/modernize-this) | Orchestrator — detects the stack and dispatches to the skills below. |
| [`modernize-dotnet`](skills/modernize-dotnet) | Target frameworks, SDK pins, NuGet packages, project-file style. |
| [`modernize-csharp`](skills/modernize-csharp) | C# syntax and idioms — file-scoped namespaces, primary constructors, collection expressions, pattern matching. |
| [`modernize-blazor`](skills/modernize-blazor) | Render modes, `PersistentComponentState`, typed `HttpClient`, CSS isolation, current project layout. |
| [`modernize-react`](skills/modernize-react) | React major upgrades, removed legacy APIs, class components to hooks, React Router migrations. |
| [`modernize-typescript`](skills/modernize-typescript) | Compiler upgrades, `tsconfig` modernization, incremental strictness, type-only imports. |
| [`modernize-node-tooling`](skills/modernize-node-tooling) | Build and dev tooling — CRA/webpack to Vite, Jest to Vitest, ESLint flat config, package manager pinning. |
| [`modernize-use-npm`](skills/modernize-use-npm) | Migrates a repo from yarn/pnpm/bun to npm, including CI and a guard against the old package manager. |
| [`modernize-github-actions`](skills/modernize-github-actions) | Action versions, runner images, caching, permissions, concurrency, deprecated syntax. |
| [`add-modernization-skills`](skills/add-modernization-skills) | Finds technologies with no matching `modernize-*` skill and writes the missing ones. |

## Installing

Clone the repo, then point Claude Code's user skills directory at it. On Windows:

```powershell
git clone https://github.com/RyanGano/ai-assistants.git C:\Code\ai-assistants
cmd /c mklink /J "$env:USERPROFILE\.claude\skills" "C:\Code\ai-assistants\skills"
```

On macOS or Linux:

```bash
git clone https://github.com/RyanGano/ai-assistants.git ~/Code/ai-assistants
ln -s ~/Code/ai-assistants/skills ~/.claude/skills
```

Editing a file under `skills/` then takes effect immediately — there is no
separate install step.

## Note

Some skills I use are machine-specific and stay out of this repository by way of
`.gitignore`. If a skill referenced locally isn't listed above, that's why.
