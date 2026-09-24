# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repository is

A public, version-controlled home for Ryan Gano's personal Claude Code **skills**.
It is not an application — there is no build, no test suite, and no runtime. Every
tracked file is Markdown that Claude Code reads as instructions.

## Layout

```
poteto-skills/          # ported pstack skills, junctioned into skills/
skills/
  <skill-name>/
    SKILL.md            # required: frontmatter + instructions
    references/*.md     # optional: detail pulled in on demand
.gitignore
CLAUDE.md
README.md
```

## poteto-skills

`poteto-skills/` holds skills ported from poteto's pstack (MIT). Claude Code does
not discover nested skill folders, so each one is linked into `skills/` by a
gitignored directory junction. Edit them in `poteto-skills/`, never through the
junction path in a commit. After adding a skill there, or on a fresh clone, run
`poteto-skills/link-skills.ps1` and add the new `skills/<name>` line to
`.gitignore`. See `poteto-skills/README.md` for what changed from upstream.

## The junction — read this before moving files

`%USERPROFILE%\.claude\skills` is a **directory junction** pointing at
`C:\Code\ai-assistants\skills`. The repository is the single source of truth;
Claude Code discovers skills through the junction.

Consequences:

- Editing a file under `skills/` changes the live skill immediately. There is no
  install or sync step.
- Do not delete or replace the `skills/` directory wholesale — that breaks the
  junction. Edit files in place.
- Do not re-create the junction unless it is actually broken. To verify:
  `cmd /c dir /AL "%USERPROFILE%\.claude"`.

## Private skills

`skills/deploy-find-me-api/` is **gitignored on purpose**. It contains
deployment specifics for a personal Azure app — hostnames and operational detail
that should not be public. It still lives in the working tree so the skill keeps
working locally.

Rules:

- Never `git add -f` it, and never remove its `.gitignore` entry.
- Never run `git clean -fdx` in this repo — it would permanently delete the
  untracked private skill.
- Before any commit, confirm it is still ignored:
  `git check-ignore -v skills/deploy-find-me-api/SKILL.md`

## Adding or editing a skill

1. Create `skills/<kebab-case-name>/SKILL.md`.
2. Give it YAML frontmatter with `name` (matching the directory) and a
   `description` that states both what the skill does and *when* to use it —
   the description is the only thing Claude sees when deciding whether to load
   the skill, so include the phrases a user would actually say.
3. Keep `SKILL.md` focused. Push long reference material into
   `references/*.md` so it is loaded only when needed.
4. Skills here are user-level: they apply in every repository. Keep them
   generic, and keep machine-specific paths, hostnames, and account details out
   of anything tracked.

## Before committing

This repo is public. Every change is published. Check that new content contains
no credentials, tokens, connection strings, subscription or tenant IDs, private
hostnames, or local filesystem paths.
