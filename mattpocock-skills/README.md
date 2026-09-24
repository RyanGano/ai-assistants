# mattpocock-skills

A selection of skills from Matt Pocock's [skills](https://github.com/mattpocock/skills/tree/main/skills)
repo, set up to run in Claude Code. MIT licensed; see [LICENSE](LICENSE).

## Origin

| | |
| --- | --- |
| Author | Matt Pocock ([@mattpocock](https://github.com/mattpocock)) |
| Source | [`mattpocock/skills`](https://github.com/mattpocock/skills), `skills/` |
| Upstream commit | [`c55ee46`](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills) (2026-09-24) |
| License | MIT, copyright 2026 Matt Pocock ([LICENSE](LICENSE)) |

Upstream groups skills into category folders (`engineering/`, `productivity/`).
Here each skill sits at the top level, a copy of the upstream folder with the same
name, plus the changes listed under [Changes from upstream](#changes-from-upstream).

| Skill | Upstream |
| --- | --- |
| `codebase-design` | [skills/engineering/codebase-design](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/codebase-design) |
| `diagnosing-bugs` | [skills/engineering/diagnosing-bugs](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/diagnosing-bugs) |
| `domain-modeling` | [skills/engineering/domain-modeling](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/domain-modeling) |
| `grill-with-docs` | [skills/engineering/grill-with-docs](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/grill-with-docs) |
| `grilling` | [skills/productivity/grilling](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/productivity/grilling) |
| `tdd` | [skills/engineering/tdd](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/tdd) |
| `wizard` | [skills/engineering/wizard](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/wizard) |
| `writing-for-agents` | [skills/productivity/writing-for-agents](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/productivity/writing-for-agents) |

## How they load

Claude Code only discovers skills one level under a `skills/` directory, so these
folders are not found where they sit. Each one has a directory junction in
`../skills/<name>` pointing back here, and `~/.claude/skills` is itself a junction
to `../skills`. The junctions are gitignored. [`.upstream.json`](.upstream.json)
pins the upstream commit and lists each skill's porting changes, which is what
`/upgrade-my-skills` reads to update this set. After a fresh clone, recreate the
junctions for every imported set:

```powershell
./skills/upgrade-my-skills/scripts/link-skills.ps1
```

## Skills

| Skill | Invoked | What it does |
| --- | --- | --- |
| [`diagnosing-bugs`](diagnosing-bugs) | auto | Builds a tight pass/fail feedback loop for a bug before forming any theory, then reproduces, hypothesizes, instruments, fixes, and adds a regression test. |
| [`writing-for-agents`](writing-for-agents) | auto | How to write skills, `CLAUDE.md`, and other docs an agent reads: context pointers, steps vs. reference, invocation choice. |
| [`wizard`](wizard) | auto | Generates an interactive bash script that walks you through manual steps (dashboards, secrets, provisioning) and writes captured values to `.env` or GitHub secrets. |
| [`tdd`](tdd) | auto | Red-green loop at agreed seams, one vertical slice at a time, with the anti-patterns to avoid. |
| [`grilling`](grilling) | auto | Interviews you in rounds about a plan, asking every open decision with a recommended answer, until nothing is left assumed. |
| [`grill-with-docs`](grill-with-docs) | `/grill-with-docs` | Runs `grilling` and `domain-modeling` together, so the interview also writes the glossary and ADRs. |
| [`domain-modeling`](domain-modeling) | auto | Sharpens project terminology into a `CONTEXT.md` glossary and records hard-to-reverse decisions as ADRs. |
| [`codebase-design`](codebase-design) | auto | Deep-module vocabulary (module, interface, seam, adapter, depth) and how to deepen shallow modules. |

`domain-modeling` is here because `grill-with-docs` runs it, and `codebase-design`
because `tdd` calls it when a seam is in question.

## Changes from upstream

- **Other-agent config:** every skill's `agents/openai.yaml` (display metadata for
  another agent harness) is removed. Claude Code doesn't read it.
- **tdd:** the pointer to upstream's `code-review` skill, which isn't imported and
  whose name collides with Claude Code's built-in `/code-review`, is inlined as "a
  later review stage".

Nothing else needed porting. Upstream already refers to Claude Code's Skill tool and
sub-agents, and keeps its own invocation settings: `grill-with-docs` is manual-only,
the rest are auto-invocable.
