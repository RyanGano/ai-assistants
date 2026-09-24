---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

The parent finds its own transcript file before fanning out. Claude Code writes transcripts to `~/.claude/projects/<project>/`, where `<project>` is the session's starting directory with every character that isn't a letter or digit replaced by `-` (for example `C:\Code\my-app` becomes `C--Code-my-app`; match case-insensitively). Use only that directory. Do not glob across `~/.claude/projects/*/`. That crosses project boundaries and reads private chats from unrelated projects.

```bash
ls -t ~/.claude/projects/<project>/*.jsonl | head -10
```

Two layouts: the session (`<session-id>.jsonl`) and its subagents (`<session-id>/subagents/*.jsonl`). The newest file is usually the active session.

Confirm the match: grep the candidate for a distinctive phrase from the conversation's opening user prompt (user turns are lines with `"type":"user"`; early lines can be metadata). Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

### 2. Spawn three reviewers in parallel

One message, three `Agent` calls, `subagent_type: general-purpose`, `run_in_background: false`, `model` unset (inherit the session model). Subagents inherit the session's MCP tools, so reviewers can look up tickets, chat threads, or traces the transcript references.

| Lens | Prompt template |
|---|---|
| Judgment | `references/judgment-reviewer.md` |
| Tooling | `references/tooling-reviewer.md` |
| Divergent | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the `Agent` result.

### 3. Synthesize

One `Agent` call, `subagent_type: general-purpose`, `run_in_background: false`, `model` unset. The synthesizer's quality check includes spot-verifying citations, which can require MCP access. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. A rule written twice as prose is a rule that belongs in structure.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent session. Do not auto-apply.

Offer to file Backlog items as GitHub issues in the repo that owns the affected skill (the `add-github-issue` skill, if present). Only file what the user approves.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to the `skill-creator` skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to `skill-creator` and run its description-optimization loop.
- `new skill via skill-creator: <kebab-name>`: hand creation to `skill-creator`. Do not invent the shape ad hoc.

If a touched skill lives in a repo with its own skill conventions (a `CLAUDE.md` describing layout or frontmatter rules), follow them.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog: `<issue title>`, filed or proposed. One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
