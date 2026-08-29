---
name: backup-private-data
description: Move a local folder that must never be published into the private app-private-data repo, junction it back to its original path so everything that reads it keeps working, fix both .gitignore files, and commit and push. Use when the user says "backup private data", "back up this folder privately", "move this into app-private-data", "this folder can't be public but needs versioning", or names a folder holding .env files, deploy procedures, or infrastructure names that a public repo currently ignores.
---

# Back up a folder into app-private-data

`C:\Code\app-private-data` is a **private** GitHub repo that versions files public
repos need at runtime but must never publish. Folders live there for real and are
mounted back into their original locations as Windows directory junctions, so every
path that read them before still reads them.

Take one argument: the folder to move (a path, or a name you can resolve to one).
If the user did not name a folder, ask which one — never guess.

## Before touching anything

1. Resolve the source to an absolute path and confirm it exists and is a real
   directory, **not already a junction**:
   `cmd /c dir /AL "<parent>"` — if the name is listed there, it is already
   junctioned. Stop and tell the user; re-moving it would follow the link.
2. Read `C:\Code\app-private-data\CLAUDE.md` and `README.md`. They carry the rules
   this skill has to keep true, and the tables you will update.
3. Pick the destination name. Match what is already there: a whole project's data
   goes in a top-level folder (`find-me-local/`); a Claude skill goes in
   `private-skills/<skill-name>/`. Confirm the destination does **not** exist.
4. Check whether the source repo is a git repo and whether the folder is tracked
   in it (`git ls-files <path>`). If it *is* tracked, its contents are already in
   that repo's history — say so plainly. Moving it stops future commits but does
   not erase the past; if that repo is public, the user needs to decide about the
   existing history before this is actually private.

## Move and junction

```
Move-Item -Path '<source>' -Destination '<dest>'
New-Item -ItemType Junction -Path '<source>' -Target '<dest>'
```

Junctions need no admin rights. `Move-Item` must be a plain move — never copy and
then delete the original, and never delete anything with a recursive command
anywhere near a junction (`rm -rf`, `rmdir /s`, `Remove-Item -Recurse` all follow
junctions and destroy the only live copy).

Verify the junction reads through before going further: `cat` a known file via the
**original** path and check it returns the real content.

## .gitignore, both sides

**Source repo** — add the folder's repo-relative path (with a trailing `/`) to its
`.gitignore`, under a comment saying why. Git on Windows walks straight through a
junction like an ordinary directory, so this line — not the junction — is the only
thing keeping the files out of that repo. If a matching entry is already there
(often it is; that is usually why the folder was unversioned), leave it and say so.

**app-private-data** — normally needs no change; `node_modules/`, `.azure/` and
`*.log` are already covered. Add an entry only for genuinely rebuildable build
output you just moved in. **Never** add `.env`, `*.local`, or `secrets*`: storing
those is the entire purpose of the repo, and a stock Node `.gitignore` would
silently un-track the data it exists for.

## Docs

Add a row for the new folder to the junction table in **both**
`app-private-data/README.md` (Folder | Mounted at | Public repo) and
`app-private-data/CLAUDE.md` (Real path | Junction), and add the `mklink /J` line
to the README's new-machine setup block. Match the existing formatting exactly.

## Check what you are about to publish

`git status --short` in app-private-data, then actually look at what is new. Private
on GitHub is not secret: everything committed is plaintext to GitHub and to any
future collaborator. Endpoint, database, and container *names* are fine. Account
keys, connection strings, tokens, and passwords are not — they belong in the app's
own settings or a secret store. If you find one, stop and tell the user before
committing.

## Commit and push

Commit in app-private-data only — one commit, with a message saying what moved,
where it is junctioned, and why it could not stay where it was. Then `git push`.

If the source repo's `.gitignore` needed a new line, that is a separate commit in
that repo. Show the user the change and ask before committing there; that repo may
be public and is not this skill's to push.

## Report

Tell the user: what moved, the junction that now stands in its place, which
`.gitignore` files changed, the pushed commit, and anything left for them to decide
(untracked-to-tracked history, a source-repo commit not yet made).
