# poteto-skills

A selection of skills from [pstack](https://github.com/cursor/plugins/tree/main/pstack/skills),
Lauren Tan's (poteto) skill pack for Cursor, ported to run in Claude Code. MIT
licensed; see [LICENSE](LICENSE).

## Origin

| | |
| --- | --- |
| Author | Lauren Tan ([@poteto](https://github.com/poteto)) |
| Source | [`cursor/plugins`](https://github.com/cursor/plugins), `pstack/skills/` |
| Upstream commit | [`12d587d`](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills) (2026-09-23) |
| License | MIT, copyright 2026 Lauren Tan ([LICENSE](LICENSE)) |

Each folder here is a copy of the upstream folder with the same name, plus the
Claude Code changes listed under [Changes from upstream](#changes-from-upstream).
The Comment Sicko prompt in `no-comments/references/` comes from upstream's
[`pstack/agents/comment-sicko.md`](https://github.com/cursor/plugins/blob/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/agents/comment-sicko.md).

| Skill | Upstream |
| --- | --- |
| `automate-me` | [pstack/skills/automate-me](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/automate-me) |
| `blast-radius` | [pstack/skills/blast-radius](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/blast-radius) |
| `create-verification-skill` | [pstack/skills/create-verification-skill](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/create-verification-skill) |
| `how` | [pstack/skills/how](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/how) |
| `no-comments` | [pstack/skills/no-comments](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/no-comments) |
| `principle-attack-the-premise` | [pstack/skills/principle-attack-the-premise](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/principle-attack-the-premise) |
| `principle-laziness-protocol` | [pstack/skills/principle-laziness-protocol](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/principle-laziness-protocol) |
| `principle-never-block-on-the-human` | [pstack/skills/principle-never-block-on-the-human](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/principle-never-block-on-the-human) |
| `principle-prove-it-works` | [pstack/skills/principle-prove-it-works](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/principle-prove-it-works) |
| `principle-test-behavior-not-implementation` | [pstack/skills/principle-test-behavior-not-implementation](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/principle-test-behavior-not-implementation) |
| `reflect` | [pstack/skills/reflect](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/reflect) |
| `teach` | [pstack/skills/teach](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/teach) |
| `typescript-best-practices` | [pstack/skills/typescript-best-practices](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/typescript-best-practices) |
| `unslop` | [pstack/skills/unslop](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/unslop) |
| `why` | [pstack/skills/why](https://github.com/cursor/plugins/tree/12d587dfb20741cafc376c42c696c5f6e2a64487/pstack/skills/why) |

To pull in upstream changes later, diff these folders against a newer pstack
commit and re-apply the Claude Code changes below.

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
