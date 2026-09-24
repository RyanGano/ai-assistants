# poteto-skills

A selection of skills from [pstack](https://github.com/cursor/plugins/tree/main/pstack/skills),
Lauren Tan's (poteto) skill pack for Cursor, ported to run in Claude Code. MIT
licensed; see [LICENSE](LICENSE).

## How they load

Claude Code only discovers skills one level under a `skills/` directory, so these
folders are not found where they sit. Each one has a directory junction in
`../skills/<name>` pointing back here, and `~/.claude/skills` is itself a junction
to `../skills`. The junctions are gitignored. After a fresh clone, recreate them:

```powershell
./poteto-skills/link-skills.ps1
```

## Skills

| Skill | Invoked | What it does |
| --- | --- | --- |
| [`create-verification-skill`](create-verification-skill) | `/create-verification-skill` | Generates a project `verify-<app>` skill that launches the app, drives it like a user, and captures evidence. |
| [`principle-prove-it-works`](principle-prove-it-works) | auto | Verify against the real artifact before declaring done, not a proxy or "it compiles." |
| [`principle-attack-the-premise`](principle-attack-the-premise) | auto | After two failed fixes on one premise, question the premise instead of writing a third fix. |
| [`no-comments`](no-comments) | `/no-comments` | Spawns the Comment Sicko reviewer to strip narration, dead code, and workaround comments from a diff. |
| [`blast-radius`](blast-radius) | `/blast-radius` | Finds what a change breaks outside the diff and proves the one fact it's safe because of. |
| [`reflect`](reflect) | `/reflect` | Three parallel reviewers mine the session transcript and route learnings into skill edits. |
| [`automate-me`](automate-me) | `/automate-me` | Mines transcripts and interviews you to write a personal `<handle>-mode` skill. |
| [`principle-laziness-protocol`](principle-laziness-protocol) | auto | Smallest change that solves the problem; prefer deletion over new layers. |
| [`principle-test-behavior-not-implementation`](principle-test-behavior-not-implementation) | auto | Tests call code the way users do and assert literal results, or get deleted. |
| [`typescript-best-practices`](typescript-best-practices) | auto (`.ts`/`.tsx`) | Discriminated unions, branded types, no `as`, parse at boundaries. |
| [`unslop`](unslop) | auto | Cuts AI tells from prose meant for people. |
| [`principle-never-block-on-the-human`](principle-never-block-on-the-human) | auto | Proceed on reversible work and present the result; confirm only irreversible actions. |
| [`how`](how) | auto | Explains how a subsystem works, using parallel explorer subagents for big questions. |
| [`why`](why) | auto | Reconstructs why code is shaped the way it is from git, PRs, and any connected MCPs. |
| [`teach`](teach) | auto | Runs `how` and `why` and turns them into one plain explanation. |

`why` is here because `teach` depends on it.

## Changes from upstream

- **Subagents:** Cursor's `Task` tool, `generalPurpose` type, `readonly` flag, and
  per-role model routing (`pstack-models.mdc`) became Claude Code's `Agent` tool with
  `Explore` or `general-purpose` and the session's model.
- **Comment Sicko:** the custom Cursor agent is now a prompt file,
  [`no-comments/references/comment-sicko.md`](no-comments/references/comment-sicko.md),
  run on a `general-purpose` subagent.
- **Paths and tools:** `.cursor/skills` became `.claude/skills`, Cursor's
  `agent-transcripts/` became `~/.claude/projects/<project>/*.jsonl`, `AskQuestion`
  became `AskUserQuestion`, `create-skill` became `skill-creator`, and MCP discovery
  uses Claude Code's `mcp__<server>__<tool>` names.
- **Missing dependencies:** references to pstack skills not included here (`arena`,
  `architect`, the other principles, `maintain-verification-skill`, `poteto-mode`)
  are replaced with an inline one-line version of the idea or a link upstream.
- **Invocation:** upstream marks every skill `disable-model-invocation: true`. The
  principles, `typescript-best-practices`, `how`, `why`, `teach`, and `unslop` are
  now auto-invocable so Claude applies them without a slash command. `unslop` and
  `why` got narrower descriptions so they don't fire on every turn.
- **teach:** Claude Code has no image generator, so spatial diagrams use an inline
  visual or ASCII sketch instead.
