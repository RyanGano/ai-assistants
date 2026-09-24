---
name: modernize-blazor
description: Modernize a Blazor app's component patterns, routing, rendering, and project layout — render modes, `@rendermode`, `PersistentComponentState`, typed `HttpClient`, `IHttpClientFactory`, `NavigationManager` APIs, `.razor.css` isolation, and current Blazor WASM/Server/Web App structure — committing each task separately. Use when the user asks to "modernize Blazor", "update Blazor components", "move to the Blazor Web App model", or when `modernize-this` dispatches to it. Run after modernize-dotnet.
---

# Modernize Blazor

Update Blazor component and app-model patterns to what the current framework
version supports. Target framework and package upgrades belong to
`modernize-dotnet` — run that first; the render-model features here only exist
on newer targets.

**Read `~/.claude/skills/modernize-this/references/conventions.md` first** for
branch handling, one-commit-per-task, per-commit verification, and PR format.
Standalone topic branch: `modernize/blazor`.

## 1. Identify the hosting model

Read the `.csproj` SDK and `Program.cs`:

- `Microsoft.NET.Sdk.BlazorWebAssembly` → standalone WASM (client-only; often
  calls a separate API).
- `Microsoft.NET.Sdk.Web` with `AddServerSideBlazor`/`AddInteractiveServerComponents`
  → Blazor Server, or the unified **Blazor Web App** model.
- A `.Client` project alongside a server project → Web App with WASM interactivity.

**Do not convert between hosting models as part of a modernization pass.** Moving
a standalone WASM app to the Blazor Web App model is an architectural decision
with real deployment consequences (static hosting vs. a running server, prerendering,
auth flow). If it looks worthwhile, surface it as a recommendation in the PR body
and let the user decide. Everything below works within the existing model.

## 2. Do the tasks — one commit each

Skip anything already current. **Build after each, then commit.**

### Task: current component lifecycle and parameters
- `OnInitializedAsync`/`OnParametersSetAsync` used correctly; no `async void`
  handlers; no blocking calls in lifecycle methods.
- `[Parameter]` properties on components should be `public` with setters;
  `[EditorRequired]` on parameters the component can't work without.
- Replace manual `StateHasChanged()` calls that the framework already triggers.
- Use `EventCallback<T>` rather than raw `Action<T>` for component callbacks (it
  handles the re-render for you).
→ `Modernize: tighten component parameters and lifecycle usage`

### Task: HTTP access
Replace ad-hoc `new HttpClient(...)` and hardcoded URLs:
- Register via `builder.Services.AddHttpClient(...)` / typed clients, and inject.
- In standalone WASM, keep `BaseAddress` configured from
  `builder.HostEnvironment.BaseAddress` or configuration — **not** a URL literal
  in a component. A URL that differs between local and deployed belongs in
  `appsettings.json` / `wwwroot/appsettings.json`, not commented-out code.
- Use `GetFromJsonAsync<T>`/`PostAsJsonAsync` over manual serialization.
- Consider a source-generated `JsonSerializerContext` for WASM — it trims better
  and avoids reflection.
→ `Modernize: use typed HttpClient with configured base address`

### Task: render modes (only on frameworks that have them)
If the app is a Blazor Web App, set interactivity explicitly with `@rendermode`
(`InteractiveServer`, `InteractiveWebAssembly`, `InteractiveAuto`) per component
rather than globally, and use `PersistentComponentState` so prerendered data
isn't fetched twice. Skip entirely for standalone WASM.
→ `Modernize: declare explicit render modes`

### Task: routing and navigation
- `NavigationManager.NavigateTo` with the current overloads; use
  `GetUriWithQueryParameter` instead of hand-built query strings.
- `[SupplyParameterFromQuery]` for query-string state instead of manual parsing.
- Route constraints (`@page "/item/{Id:int}"`) instead of parsing strings.
- `NavigationManager.LocationChanged` unsubscribed in `Dispose`.
→ `Modernize: use current navigation and routing APIs`

### Task: CSS isolation
Move component-specific rules out of the global `wwwroot/css/app.css` into
`Component.razor.css` scoped files. Leave genuinely global styles (layout, resets,
theme variables) where they are.
→ `Modernize: move component styles to CSS isolation`

⚠️ If the app positions elements with absolute pixel offsets that depend on the
global stylesheet, verify visually after this change — scoping can quietly break
layout. If you can't verify, skip it and say so.

### Task: JS interop
- `IJSRuntime` calls wrapped in a typed service rather than scattered in
  components; `IJSObjectReference` with ES modules
  (`import`) instead of globals on `window`; `await using` for disposal.
→ `Modernize: use module-based JS interop`

### Task: forms and validation
`EditForm` + `DataAnnotationsValidator` + `ValidationMessage` instead of manual
validation; bind with `@bind-Value` and `:after` where appropriate.
→ `Modernize: use EditForm with data-annotations validation`

### Task: publish/trimming settings (WASM)
Enable the current WASM publish optimizations if not already on and if the app
tolerates them: `<PublishTrimmed>`, `<InvariantGlobalization>` (only if no
culture-specific formatting), `<BlazorWebAssemblyLoadAllGlobalizationData>false`.
Trimming can break reflection-based serialization — verify a published build
actually runs, not just that it compiles.
→ `Modernize: enable WASM publish optimizations`

## 3. Verify

```
dotnet build
dotnet test          # if any
dotnet run           # then actually load the app
```

Blazor breaks at runtime far more often than at compile time. **Load the app in a
browser and exercise the changed components.** If you can't, state that plainly
in your report and the PR body — an unverified Blazor refactor is a risk the
reviewer needs to know about.

## 4. Finish

Orchestrated (branch already `modernize/*`): stop and report the commits.
Standalone: push `modernize/blazor` and open the Draft PR per the conventions file.

## Rules

- Never change the hosting model as a drive-by. Recommend it instead.
- Never change rendered output. If markup must move, the resulting DOM should be
  equivalent; verify visually.
- Keep client/server DTO shapes in sync. If the app mirrors the service's wire
  format by hand, changing one side without the other silently breaks
  deserialization — check both.
- Don't add a component library or CSS framework. That's a redesign, not a
  modernization.
