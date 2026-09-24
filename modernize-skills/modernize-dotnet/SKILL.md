---
name: modernize-dotnet
description: Upgrade a .NET repo's target framework, SDK pin, NuGet packages, and project-file style to current supported versions, committing each task separately. Use when the user asks to "modernize .NET", "upgrade to the latest .NET", "update the target framework", "bump NuGet packages", "get off net6/net7/net8", or when `modernize-this` dispatches to it. Handles csproj/props/global.json; does not touch C# syntax (that's modernize-csharp).
---

# Modernize .NET (runtime, packages, project files)

Bring the project's *platform* up to date: target framework, SDK pin, NuGet
package versions, and project-file hygiene. Language-syntax modernization belongs
to `modernize-csharp`; run this one first, since newer syntax often needs the
newer target.

**Read `~/.claude/skills/modernize-this/references/conventions.md` first** — it
defines branch handling (orchestrated vs standalone), the one-commit-per-task
rule, per-commit build verification, and the Draft PR format. Standalone topic
branch name: `modernize/dotnet`.

## 1. Survey

```
dotnet --info
dotnet --list-sdks
```

Find every project and manifest: `**/*.csproj`, `**/*.fsproj`, `**/*.sln`,
`**/*.slnx`, `global.json`, `Directory.Build.props`, `Directory.Packages.props`,
`nuget.config`. Read each — record current `TargetFramework(s)`, SDK type,
`LangVersion`, `Nullable`, `ImplicitUsings`, and every `PackageReference` version.

## 2. Pick the target framework

Choose the **latest LTS** .NET that is actually installed (`dotnet --list-sdks`)
unless the user asked for STS/preview or a deployment target constrains you.
Verify what's current rather than trusting memory — your knowledge of the release
calendar may be stale:

```
curl -s https://raw.githubusercontent.com/dotnet/core/main/release-notes/releases-index.json
```

(`support-phase: active` + `release-type: lts` is the safe pick.) If the newest
LTS isn't installed locally you cannot build to verify — either have the user
install it or target the newest installed LTS and say so.

**Hosting constraint check:** if the app deploys somewhere with a pinned runtime
(Azure App Service, a Dockerfile base image, a CI `setup-dotnet` version), the
target framework and that runtime must move together. Note every such place now;
you'll update CI in `modernize-github-actions`, but a `Dockerfile` base image or
an Azure config in this repo is yours to fix in the same commit.

## 3. Do the tasks — one commit each

Work through these in order. Skip any that don't apply. **Build after each, then
commit.**

### Task: retarget the framework
Update `<TargetFramework>` in every project. If a `global.json` pins an SDK, bump
`sdk.version` to match and set `rollForward: latestMinor`. Update any Dockerfile
base images in the repo.
→ `Modernize: retarget <projects> to net<N>.0`

### Task: adopt current project-file defaults
For each project, ensure:
- `<Nullable>enable</Nullable>`
- `<ImplicitUsings>enable</ImplicitUsings>`
- SDK-style project format (if any legacy `.csproj` with `<Compile Include=…>`
  globs and `packages.config` remains, converting it is its own commit)

If enabling `Nullable` produces warnings, **do not** blanket-suppress them.
Either fix them in this commit (if few) or leave `Nullable` off and record it as
deferred — a wall of `#pragma warning disable` is worse than not enabling it.
→ `Modernize: enable nullable reference types and implicit usings`

### Task: update NuGet packages
```
dotnet list package --outdated
dotnet list package --deprecated
dotnet list package --vulnerable
```
Rules:
- Framework-tied packages (`Microsoft.AspNetCore.*`, `Microsoft.Extensions.*`,
  `System.Text.Json`) must match the new target framework's major version.
- Take patch and minor bumps freely. For **major** bumps, read the release notes
  for breaking changes before taking them; if a major bump needs code changes,
  that's its own commit.
- Replace deprecated/abandoned packages with their successors (e.g.
  `Newtonsoft.Json` → `System.Text.Json` only if the usage is simple; complex
  serialization customization is a deferred item, not a drive-by).
- Prioritize anything `--vulnerable` reports.
→ `Modernize: update NuGet packages to current versions` (one commit for the
routine bumps; a separate commit per major upgrade that required code changes)

### Task: central package management (multi-project repos only)
If there are 3+ projects with overlapping `PackageReference` versions, introduce
`Directory.Packages.props` with `<ManagePackageVersionsCentrally>true</…>` and
strip versions from the projects.
→ `Modernize: adopt central package management`

### Task: modern hosting/API patterns (ASP.NET Core only)
Only if the project still uses old shapes:
- `Startup.cs` + `WebHost.CreateDefaultBuilder` → minimal hosting
  (`WebApplication.CreateBuilder`) in `Program.cs`.
- `IHostingEnvironment` → `IWebHostEnvironment`; `System.Web`-era helpers →
  current equivalents.
- `Microsoft.AspNetCore.Mvc.NewtonsoftJson` → built-in JSON where feasible.
Each of these is a behavior-adjacent change — one commit each, and verify the app
actually starts, not just that it compiles.
→ `Modernize: convert to minimal hosting model`

### Task: build warnings introduced by the upgrade
New analyzers ship with new SDKs. Fix real warnings (obsolete APIs above all).
Don't chase style-only analyzer noise here — that's `modernize-csharp`.
→ `Modernize: fix obsolete API usage flagged by net<N> analyzers`

## 4. Verify

```
dotnet restore
dotnet build -warnaserror-  # see the warnings, don't hide them
dotnet test                 # if the repo has tests
```

Then run the app if it's runnable and the change touched hosting — a compiling
ASP.NET app can still fail at startup.

## 5. Finish

Orchestrated (branch already `modernize/*`): stop here and report the commits.
Standalone: push `modernize/dotnet` and open the Draft PR per the conventions file.

## Rules

- Never bump a major package version and refactor around it in the same commit as
  routine bumps.
- Never suppress warnings to make a build pass — fix, revert, or defer.
- If the newest LTS isn't installed, don't retarget blind. Say so.
- Behavior must not change. Any upgrade that alters runtime semantics gets its
  own commit and an explicit callout in the PR body.
