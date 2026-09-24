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

### Software factory

`software-factory` is the entry point: it drives one task through four stages,
each run by a skill that can do only its own job — so the agent that writes the
code is never the agent that judges it.

| Skill | Stage |
| --- | --- |
| [`software-factory`](skills/software-factory) | Controller — frames the run, spawns each stage, owns the handoff between them. Runs manual by default; `/software-factory 42 auto` opts that run into auto-merge. |
| [`factory-implement`](skills/factory-implement) | Builds the change in an isolated worktree cut from fresh `origin/<default>`, proves it works, opens a PR, and watches CI to green. |
| [`factory-review`](skills/factory-review) | Reviews the PR adversarially with no context outside it, fixes every finding, loops to 90% confidence or declares it unresolvable, then squashes and rewrites the description. |
| [`factory-handoff`](skills/factory-handoff) | Checks the PR against what was actually asked for, verifies the proof is real, and gives a link, a status and a merge recommendation. |
| [`factory-land`](skills/factory-land) | Merges an approved, green PR, confirms the issue closed, and tears down the worktree, branch and lock. |

Auto-merge is opt-in per run and gated: it lands unattended only at a review
confidence of 9/10 or better, with *Needs human eyes* empty, checks green, and
the handoff audit confirming the PR matches what was actually asked for. Any gate unmet and
the PR comes to you as usual.

Shared rules — worktree isolation and locking, run state, the auto-merge gate,
proof standards, PR shape — live in
[`software-factory/references/conventions.md`](skills/software-factory/references/conventions.md).

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

### Skills from other people

| Skill | What it does |
| --- | --- |
| [`upgrade-my-skills`](skills/upgrade-my-skills) | `/upgrade-my-skills from <github-url>` audits my Claude Code and VS Code history against another repo's skills, recommends a ranked batch, then imports my picks into a `<author>-skills/` folder, ports them to Claude Code, and junctions them into `skills/`. Re-run it on the same repo to pull upstream updates. |
| [`poteto-skills/`](poteto-skills) | 15 skills from poteto's [pstack](https://github.com/cursor/plugins/tree/main/pstack/skills), imported this way. |
| [`mattpocock-skills/`](mattpocock-skills) | 8 skills from Matt Pocock's [skills](https://github.com/mattpocock/skills/tree/main/skills), imported this way: bug diagnosis, TDD, plan grilling, setup wizards, and writing for agents. |

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
