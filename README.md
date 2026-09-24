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

### Software factory — [`software-factory-skills/`](software-factory-skills)

`software-factory` runs one task through an isolated build, an adversarial
review, a human handoff and a merge, with a separate skill for each stage so the
agent that writes the code never judges it. Auto-merge is opt-in per run and
gated. The set's README covers each stage.

### Modernization — [`modernize-skills/`](modernize-skills)

`modernize-this` detects the technologies in a repo, runs the matching
`modernize-*` sub-skills (.NET, C#, Blazor, React, TypeScript, Node tooling, npm,
GitHub Actions), and opens a single Draft PR with commits split task by task.
`add-modernization-skills` writes sub-skills for stacks it can't handle yet.

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

Skills kept in set folders (`*-skills/`) are linked into `skills/` by junctions,
which a clone doesn't carry. Create them once on Windows:

```powershell
C:\Code\ai-assistants\skills\upgrade-my-skills\scripts\link-skills.ps1
```

On macOS or Linux, symlink each `<set>/<skill>` folder to `skills/<skill>`.

Editing a skill's files then takes effect immediately — there is no separate
install step.

## Note

Some skills I use are machine-specific and stay out of this repository by way of
`.gitignore`. If a skill referenced locally isn't listed above, that's why.
