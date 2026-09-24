# Porting skills to Claude Code

Read this when an imported skill has harness hints, mentions skills that were not
imported, or when deciding how it should be invoked.

## Rule zero: port, don't improve

Change only what stops the skill working in Claude Code. Keep upstream wording
everywhere else, even where you would write it differently. Your own ideas about
what the skill should also do are not part of a port. Every change you make gets a
line in the set's README under "Changes from upstream".

## Harness mapping

| Upstream (Cursor and similar) | Claude Code |
| --- | --- |
| `Task` tool, `subagent_type: generalPurpose` | `Agent` tool, `subagent_type: general-purpose` |
| Read-only explorer subagent (`readonly: true`) | `subagent_type: Explore` (read-only by design); for `general-purpose`, say "do not modify files" in its prompt |
| `readonly: false` "so MCPs stay available" | Drop it. Claude Code subagents inherit the session's MCP tools |
| Per-role model rules (`*-models.mdc`, model slugs like `grok-…`, `gpt-…`, `…-max`) | Leave `model` unset so subagents inherit the session model. Only set `sonnet`/`opus`/`haiku` when the upstream intent is clearly "cheap and fast" or "strongest" |
| Named custom agent (`subagent_type: "Some Persona"`) defined in the repo's `agents/` | Copy the agent file into the skill's `references/`, strip its frontmatter, and spawn `general-purpose` with that file verbatim as the prompt |
| `.cursor/skills/<name>/` (project) | `.claude/skills/<name>/` |
| `~/.cursor/skills/` (user) | `~/.claude/skills/` |
| Cursor `agent-transcripts/` directory | `~/.claude/projects/<project>/<session>.jsonl`, where `<project>` is the starting directory with non-alphanumerics replaced by `-` (case-insensitive). Subagents live in `<session>/subagents/*.jsonl` |
| `AskQuestion` (4-6 options, `allow_multiple`) | `AskUserQuestion` (up to 4 questions, 2-4 options each, `multiSelect`) |
| Cursor `create-skill` skill | `skill-creator` skill |
| MCP discovery through Cursor's `mcps/` folder | MCP tools are named `mcp__<server>__<tool>`; check loaded tools and the deferred tools listed in system reminders (load schemas with `ToolSearch`) |
| "Cursor location", "open files" | Files open in the IDE, the current selection |
| Image-generation tool | No equivalent. Use an inline visual tool if the session has one, else a mermaid or ASCII diagram, or a screenshot of the real UI |
| Rules files (`.mdc`, always-applied rules) | User-level `~/.claude/CLAUDE.md` or project `CLAUDE.md` |
| `/slash` references to other skills | Keep them if the named skill is imported; otherwise see below |

Files that configure the skill for another agent (`agents/openai.yaml`, `.cursor/`,
`.codex/`) are inert in Claude Code. Delete them from the imported copy and note it
under changes, unless the skill's own text reads them.

Skills already written for Claude Code (the repo ships `.claude-plugin/`, or the
text uses `Agent`, `Skill`, `.claude/`) usually need no port. Still check the
dependencies and the invocation policy.

## Skills that mention skills you did not import

For each mention, pick one:

1. **Import it too** when the skill calls it as a step and breaks without it (like
   `teach` running `why`). Tell the user it came along as a dependency.
2. **Inline the idea** in one clause when the mention is a pointer to a principle,
   such as "per the Fix Root Causes skill" becoming "trace the symptom to its cause
   and fix it there". Drop the link.
3. **Link upstream** at the pinned commit when the mention is an example to read,
   not a step to run.

Setup and configuration skills that exist only to wire the upstream pack into its
own harness (model pickers, plugin installers) are never dependencies. Drop the
reference.

## Invocation policy

Upstream packs often mark every skill `disable-model-invocation: true` because a
parent "mode" skill or rules file pulls them in. Without that parent, a manual-only
principle never fires. Decide per skill:

- **Auto-invocable** (remove the flag): principles, language or framework
  conventions (add `paths:` globs when the skill is file-type specific), and
  explainers that answer a question.
- **Manual only** (keep the flag): multi-agent workflows, anything that edits
  many files or runs for minutes, and anything that mines transcripts.

When making a skill auto-invocable, read its description as a trigger. A
description like "Must always apply" or one that matches common phrasing the user
means differently (for example "why did you change X" triggering a code-history
investigation) will fire on every turn. Narrow it to the situations it is for and
record the change.

## Name collisions

A skill name must be unique across `~/.claude/skills`. When an imported skill's
name is already taken:

- Same skill from the same upstream: it is an update, not a collision.
- Different skill: ask the user whether to skip it, or import it under a prefixed
  name (`<handle>-<name>`). When renaming, update the folder name, the frontmatter
  `name`, and every reference to it inside the imported set.

## Checks before handing back

- Every `SKILL.md` has YAML frontmatter that parses, and `name` matches its folder.
- `grep -rniE "cursor|\.mdc|generalPurpose|readonly:|AskQuestion|agent-transcripts|create-skill"`
  over the set returns only lines you meant to keep.
- Every relative link inside the set resolves.
