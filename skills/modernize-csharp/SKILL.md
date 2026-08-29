---
name: modernize-csharp
description: Modernize C# source syntax and idioms — file-scoped namespaces, primary constructors, collection expressions, pattern matching, records, `is null`, raw string literals — committing each transformation separately. Use when the user asks to "modernize C#", "use modern C# syntax", "clean up old C# idioms", "adopt file-scoped namespaces", or when `modernize-this` dispatches to it. Run after modernize-dotnet, since newer syntax needs a newer LangVersion.
---

# Modernize C# syntax

Mechanical, behavior-preserving syntax upgrades across the C# source. Platform
and package upgrades belong to `modernize-dotnet` — run that first, because the
language version available here depends on the target framework it sets.

**Read `~/.claude/skills/modernize-this/references/conventions.md` first** for
branch handling, the one-commit-per-task rule, per-commit verification, and PR
format. Standalone topic branch: `modernize/csharp`.

## Ground rule

**Every change in this skill must be behavior-preserving.** If a transformation
could change semantics (nullability, evaluation order, equality, disposal timing),
it doesn't belong in a "syntax" commit — isolate it, verify it, and call it out.

## 1. Establish the available language version

Check the target framework set by `modernize-dotnet`. C# version maps to the
target framework by default (net8 → C# 12, net9 → C# 13, net10 → C# 14, and so
on — verify rather than assume). Only apply features the target actually supports;
a compile error is the fast feedback, but prefer knowing up front.

Do **not** set `<LangVersion>latest</LangVersion>` to unlock features beyond the
target framework's default. It's a footgun for future upgrades.

## 2. Do the tasks — one commit each

Apply repo-wide, one transformation at a time. Each is mechanical and uniform,
which is exactly what makes a big diff reviewable. **Build after each, then
commit.** Skip anything the codebase already does.

| Task | Transformation | Commit subject |
| --- | --- | --- |
| File-scoped namespaces | `namespace X { … }` → `namespace X;` | `Modernize: adopt file-scoped namespaces` |
| Implicit usings | remove `using System;` etc. now covered by `ImplicitUsings` | `Modernize: remove usings covered by ImplicitUsings` |
| Global usings | move repo-wide usings into `GlobalUsings.cs` | `Modernize: consolidate common usings into global usings` |
| Primary constructors | ctor that only assigns fields → primary constructor | `Modernize: use primary constructors` |
| Collection expressions | `new List<T> { … }` / `new T[] { … }` → `[…]` | `Modernize: use collection expressions` |
| Target-typed `new` | `Foo x = new Foo()` → `Foo x = new()` | `Modernize: use target-typed new expressions` |
| Pattern matching | `x is Foo && ((Foo)x).Y` → `x is Foo { Y: … }`; `if/else` chains → `switch` expressions where it reads better | `Modernize: use pattern matching and switch expressions` |
| Null checks | `x == null` → `x is null`; manual guards → `ArgumentNullException.ThrowIfNull` | `Modernize: use modern null checks and argument guards` |
| String handling | `string.Format`/concat → interpolation; escaped multiline strings → raw string literals (`"""`) | `Modernize: use string interpolation and raw string literals` |
| Records | immutable data-only classes → `record` / `record struct` | `Modernize: convert data-only types to records` |
| `using` declarations | `using (…) { … }` → `using var …` where scope allows | `Modernize: use using declarations` |
| Async | `Task.Result`/`.Wait()` → `await`; add missing `ConfigureAwait` per repo convention; `async void` → `async Task` | `Modernize: fix blocking and async-void call sites` |
| Nullable annotations | replace `!` suppressions with real checks; annotate `?` correctly | `Modernize: replace null-forgiving operators with real checks` |

### Two of those need extra care

- **Records.** Converting a class to a record changes equality from reference to
  value, and adds `ToString`/`with`. That is a behavior change. Only convert types
  where value equality is correct, and only if nothing relies on reference
  identity (dictionary keys, caches, `ReferenceEquals`). Its own commit, with the
  reasoning in the body.
- **Async fixes.** Removing `.Result`/`.Wait()` changes threading and can surface
  deadlocks or change ordering. Its own commit; run the tests and the app.

## 3. Let the tooling do the boring parts

If the repo has (or you add) an `.editorconfig` with the relevant
`csharp_style_*` / `dotnet_style_*` rules, `dotnet format` can apply many of these
mechanically and consistently:

```
dotnet format --diagnostic-id IDE0161   # file-scoped namespaces, e.g.
dotnet format style --verify-no-changes # check-only
```

Run one diagnostic ID per commit so the diff stays scoped. **Never** run a bare
repo-wide `dotnet format` mixed into another task — a whitespace reflow of every
file makes the real changes invisible. If the repo genuinely needs a formatting
pass, it gets its own final commit, clearly labeled.

Adding an `.editorconfig` where none exists is itself a good first commit
(`Modernize: add .editorconfig with current C# style rules`) — it makes the
conventions durable rather than one-time.

## 4. Verify

```
dotnet build
dotnet test
```

After each commit, not just at the end. If a transformation breaks the build and
the fix isn't obvious, revert that task and record it as deferred.

## 5. Finish

Orchestrated (branch already `modernize/*`): stop and report the commits.
Standalone: push `modernize/csharp` and open the Draft PR per the conventions file.

## Rules

- Behavior-preserving by default; anything else gets isolated and flagged.
- Don't restructure code. This skill changes *how* code is written, never *what
  it does* or how it's organized.
- Match the repo's existing conventions where they conflict with your defaults —
  if the codebase deliberately avoids a feature, leave it alone and ask.
- Don't apply a transformation to generated files (`*.g.cs`, `*.Designer.cs`,
  `obj/`).
