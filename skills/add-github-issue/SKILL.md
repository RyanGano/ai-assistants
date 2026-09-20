---
name: add-github-issue
description: Write and file a GitHub issue for a feature or change, in the house template — Overview, Why it's wanted, Implementation plan, How we will know it worked — grounded in the repo's real files and rules. Use when the user asks to "add a github issue", "file an issue", "open an issue for X", "write this up as an issue", "put these ideas in github", or hands over a list of ideas to turn into issues. Works in any Git repo with a GitHub remote and `gh` authenticated.
---

# Add a GitHub issue

File issues that someone could pick up cold and build from: they say what is missing,
why it matters, how to build it in *this* codebase, and how anyone will know it worked.
The template below is the standard. An issue that is only a title and a sentence is
not finished.

## Prerequisites

- `gh auth status` succeeds and the repo has a GitHub remote.
- Read the repo's `CLAUDE.md` (and any README sections it points at) before writing.
  Its rules apply to issue text too, because issues on a public repo are public: no
  secrets, endpoints, hosts or private paths, and nothing else the repo says must
  never be written down (in a game, for example, anything that spoils a puzzle).

## Steps

1. **Read the model issue.** If the repo already has issues, read one or two good ones
   (`gh issue view <n> --json title,body,labels`) and match their voice, depth and
   labels. The template below describes what those issues have in common. If an
   existing issue does it better, follow the issue.
2. **Ground it in the code.** Before writing an implementation plan, find the real
   files, types, functions and tests it will touch (Grep/Glob/Read). Name them in
   backticks. Check that each one exists. A plan that names a file that isn't there
   is worse than having no plan. Note what is already half-built: it is often the
   most useful sentence in the issue.
3. **Check it isn't a duplicate.** `gh issue list --state all --search "<keywords>"`.
   If a similar issue exists, tell the user instead of filing a second one.
4. **Draft the body** to a file in the scratchpad (not the repo), using the template.
5. **File it** with `gh issue create --title "<title>" --label <label> --body-file <file>`.
   Use only labels that already exist (`gh label list`); usually `enhancement` for a
   feature and `bug` for a defect. When filing several, file them **in the order the
   user gave**, one after another, so the issue numbers follow that order.
6. **Report** each issue's number and URL, with a one-line note on anything the user
   should know: a dependency between issues, a deferral, or a rule that shaped the plan.

## Title

A plain sentence saying what changes for the user, not the name of a component.
"Let a player give up, and show them where it was", not "Give-up button". Sentence
case, no trailing full stop, no ticket-style prefixes.

## Template

```markdown
## Overview

What exists today and what is missing, in two or three short paragraphs. Name the code
that is involved (`src/...`, the function, the type). End with one clear sentence (or
a small example block) saying what to add.

If the work is deliberately deferred, say so here in bold, with the condition it is
waiting on.

## Why it's wanted

The case for it. What the user or player experiences now and why that costs something.
Where it helps, cite how comparable products handle it (a short bulleted list, named
products). Include any second-order benefit specific to this repo, for example a new
signal for tuning, or a rule it makes easier to keep.

## Implementation plan

1. **Short bold label.** A step saying what to do and where, naming real files and
   functions. Include the decisions that need making, with a proposal, and flag any
   that want a second opinion before building.
2. ...
N. **Tests.** Which test files gain what, plus any repo-wide invariant check that must
   still pass (for example, a fingerprint diff that must stay empty).

Put the repo's own constraints in the steps where they apply (e.g. a checklist that
any change to reporting must meet), rather than in a separate caveats section.

## How we will know it worked

How it will be measured, using data the project already collects where possible, and
compared before and after:

- **Primary — <metric>.** The one reading that says whether it did its job.
- **Secondary / honesty check.** A reading that catches a false positive.
- **Watch for.** The specific way it could backfire, and what to do if it does.

If there is no way to measure it yet, say what would be needed and that adding it is
a separate piece of work.
```

## Style

- Write in the repo's voice: plain, specific sentences with reasons. Avoid marketing
  words, and use no emoji outside examples.
- Keep paragraphs short. Use lists for steps and measures, and prose for reasoning.
- Say what is already half-built, and link related issues with `#<n>`.
- Never paste secrets, private hosts, or anything from gitignored private folders into
  an issue, even to explain a plan. Describe the need ("a new read from the tally
  server") without saying where it lives.
