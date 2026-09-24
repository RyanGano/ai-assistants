---
name: upgrade-my-skills
description: "Audit the user's Claude Code and VS Code history against the skills in another GitHub repo, recommend a ranked batch, then import the ones the user picks into a per-source folder, port them to Claude Code, and junction them into ~/.claude/skills. Also updates a set imported earlier. Use for /upgrade-my-skills, 'upgrade my skills from <repo>', 'which of these skills should I use', 'import skills from <github url>', or 'update my <author> skills'."
argument-hint: "from <github-url>"
disable-model-invocation: true
---

# Upgrade my skills

Recommend skills from someone else's repo based on how the user actually works,
then install the ones they choose.

Scripts live in `scripts/` next to this file. Run them with the scratchpad (or a
temp folder) as the working area, never inside the skills repo.

## 0. Find the places

- **Source:** the GitHub URL from the arguments (`from <url>`). A URL can point at
  the repo root or at a subfolder (`/tree/<ref>/<path>`). Ask for one if missing.
- **Skills folder:** `~/.claude/skills`, or the folder it is a junction or symlink
  to. Call its parent the **home repo**. If the home repo has a `CLAUDE.md`, read
  it and follow its conventions for everything below.
- **Existing set:** look for `*/.upstream.json` in the home repo whose `repo`
  matches the source (and whose `path` matches, when the source is a subfolder).
  If one exists, this run is an **update**: see step 6 first.

## 1. Read their skills

```bash
python scripts/remote-skills.py list <url> > <work>/remote.json
```

This pins the upstream commit and returns every skill's description, file list,
harness hints, and the other skills it mentions. Note the license. If there is no
license, or it forbids redistribution, tell the user: the imported set can still be
used locally, but it must be gitignored rather than committed to a public repo.

Read the full `SKILL.md` of any skill whose description is too thin to judge.

## 2. Read the user's usage

```bash
python scripts/mine-usage.py <work>/usage --days 365
```

`summary.json` has session and prompt counts, projects, the skills and tools the
user already invokes, and every skill installed in `~/.claude/skills`. `prompts.txt`
holds each prompt under a `##### <tool> <project> <date>` header. It can be
hundreds of kilobytes, so do not read it whole:

- For each candidate skill, grep `prompts.txt` for the situations the skill is
  for (its trigger phrases, and the symptoms it fixes, such as "still not working"
  for a verification skill). Count matches and pull a few short quotes as evidence.
- Sample prompts at random across projects to catch recurring friction no skill
  description names: repeated corrections, rework loops, the same instruction
  given many times.
- Check repo languages when a skill is stack-specific (for example, count `.ts`
  files in the user's active projects before recommending a TypeScript skill).

The user's own history is the only input here. Say how many sessions and prompts
the audit covered, and over which period.

## 3. Recommend a batch

Rank the upstream skills by how much they would help this user, judged by the
evidence from step 2. Drop anything that overlaps an installed skill unless it is
clearly better, and say which installed skill it overlaps.

Reply with:

1. **What the history shows.** Three or four bullets with counts.
2. **Ranked list.** For each recommended skill: its name, a one-line description
   of what it does, and a one-line benefit tied to specific evidence ("you asked
   for X 48 times"). Flag any that need porting, pull in a dependency, or collide
   with an installed skill name.
3. **Lower value.** One line per group: overlaps what they have, doesn't fit their
   work, or only useful later.

Then let the user pick. Use `AskUserQuestion` with `multiSelect: true`, up to four
questions of up to four skills each, in rank order, labelled by tier ("Top picks",
"Strong", ...). If more than 16 skills are worth offering, ask for a reply with
names instead. Wait for the choice. Do not install anything before it.

## 4. Import

1. **Folder.** New set: `<home repo>/<handle>-skills/`, where `<handle>` is the
   upstream author's GitHub handle or the pack's own name if it has one people
   know (ask if unsure). Update: the existing set's folder.
2. **Dependencies.** For each chosen skill, check its `mentions` in `remote.json`.
   A mentioned skill it runs as a step comes along. Tell the user which ones and
   why. Other mentions are handled while porting.
3. **Collisions.** A chosen name that already exists in the skills folder and is not
   from this set: ask whether to skip it or import it as `<handle>-<name>`.
4. **Download** into the scratchpad first, then copy into the set folder:

   ```bash
   python scripts/remote-skills.py download <url> <work>/import <skill> [<skill> ...] --commit <pinned sha>
   ```

5. **Port.** Follow [references/porting.md](references/porting.md) for every
   skill: harness mapping, missing dependencies, invocation policy, renames. Port,
   don't improve.
6. **Manifest.** Write `<set>/.upstream.json`:

   ```json
   {
     "source": "<url as given>",
     "repo": "<owner>/<repo>",
     "path": "<path in repo>",
     "commit": "<pinned sha>",
     "license": "<spdx id or null>",
     "imported": "<YYYY-MM-DD>",
     "skills": {
       "<local name>": { "upstream": "<path of the upstream folder>", "changes": ["<one line per porting change>"] }
     }
   }
   ```

7. **README.** Write or update `<set>/README.md`: origin table (author, source repo
   and path, pinned commit linked to its tree, license), a table of skills with how
   each is invoked and a link to its upstream folder at the pinned commit, how the
   junctions work, and "Changes from upstream" summarizing every porting change.
   Keep the upstream `LICENSE` file in the set folder.

## 5. Link and verify

```powershell
scripts/link-skills.ps1 -ImportDir <set folder>
```

It junctions each skill into the skills folder, adds the junctions to the home
repo's `.gitignore`, skips anything already taken, and is safe to re-run. With no
arguments it relinks every set folder beside the skills folder (imported sets and
the user's own), which is the fresh clone recovery step. Then check:

- Every imported `SKILL.md` has frontmatter that parses and a `name` matching its
  folder (parse it with a YAML library; don't eyeball it).
- The auto-invocable skills show up in this session's skill list after linking.
  Manual-only skills don't appear there; that is expected.
- `git status` shows the set folder and `.gitignore`, and no junction paths.

If the home repo documents its layout (a `CLAUDE.md` or README listing folders),
add the new set there in the same style. Do not commit unless the user asks.

## 6. Updating a set imported earlier

When step 0 found an existing set:

1. Compare the pinned commit with upstream head for each installed skill:
   `gh api repos/<repo>/compare/<pinned>...<head> --jq '.files[].filename'`, filtered
   to each skill's `upstream` path.
2. Check for local edits made after import:
   `git log --oneline -- <set>/<skill>` in the home repo. Anything after the
   import commit is the user's own change and must survive the update.
3. In the step 3 reply, add an **Updates** section: installed skills that changed
   upstream (one line on what changed), skills removed upstream, and any local
   edits that will need merging. New upstream skills go through the normal ranking.
4. For each update the user accepts: download the new upstream version, port it,
   and re-apply the user's local edits. Show the diff against the current local
   version before writing. Bump `commit` and `imported` in the manifest, and
   refresh the README's pinned links.
