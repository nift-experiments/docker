# Objective
Establish two faithful Nift recreations of Docker Docs from the complete built upstream production output. This initial checkpoint covers setup and investigation only; do not begin corpus migration without the next user instruction.

# Repository purpose
Human + agent maintainable Docker Docs recreation.

# Upstream Docker Docs source
- Repository: https://github.com/docker/docs
- Pinned commit: `6cf1b1c167f032e8a6629da211602300b623b20e`.
- Preserved local checkout: `../docker-upstream`.
- Baseline artifacts and tools: `../docker-baseline`.
- Official release: `HUGO_ENV=production DOCS_URL=https://docs.docker.com docker buildx bake release` (deployment workflow plus Dockerfile).
- Required toolchain: Hugo extended 0.163.0, Node 24, Pagefind 1.5.2, Go 1.26 / Alpine 3.23 in Dockerfile. Vendored modules avoid re-vendoring; go.mod declares Go 1.26.8.
- Native reproduction and measured versions: see investigation/BASELINE.md and scripts/build-upstream.sh. No Docker executable is installed on this host.

# Migration philosophy
Preserve useful authored Markdown, semantic content organization and structured data. Recover shared templates and keep the project plausible for a conventional engineering/docs team to inherit. Do not flatten sources solely for benchmark speed.

# Source of truth
The complete pinned production build is primary. Use upstream authored content, templates and data to recover useful semantics. Use https://docs.docker.com only for behavior the local build cannot explain; production may change after the pin. Never overwrite the baseline with a later build.

# Non-goals
No redesign, arbitrary content changes, changes to Nift without explicit approval, benchmark cheating, production deployment, history rewriting, release tags, or upstream modifications.

# Required parity
Every route and file, including hidden pages, 404, aliases/redirects, Markdown downloads, JSON metadata, RSS, sitemap, robots, llms.txt and llms-full.txt. Preserve titles, descriptions, canonical/Open Graph/schema metadata, anchors, content, assets, responsive layout, navigation state, keyboard controls, focus behavior and practical accessibility. Record inherited upstream defects separately from migration regressions.

# Project-specific architecture
Proposed: authored content organized by Docker source sections, explicit published route/data map, family templates and shared partials, structured CLI/API data with deterministic generation.
The starter currently tracks only `/` through templates/template.html. It is a setup smoke test, not migrated output. No final architecture has been benchmarked.

# Page families
- Home, get-started and guides landing pages.
- Standard documentation/section pages sharing the sidebar/article/right-rail shell.
- Guide articles, learning series and modules.
- Docker CLI and sbx CLI reference generated from YAML content adapters.
- API catalog, API overview, operation/tag and schema pages from structured API reference data; legacy Engine API rendering uses remote Redoc.
- Samples, glossary, wide pages and 404.
- Non-HTML output families: Markdown, discovery/search metadata, redirects, feeds and LLM outputs.
Validate actual family assignment against the built inventory before final template design.

# Shared templates/layouts
Upstream baseof provides head, header/search/theme, Gordon panel, recursive sidebar, main article, right rail, footer and conditional YouTube/Mermaid/interactive-diagram loading. Preserve page-specific sidebar state, headings/TOC and Git metadata. Families override the main/left/right/article slots. The source contains 118 layout files; this is not the proposed Nift template count.

# Data/content strategy
Maintain Docker's authored Markdown wherever practical. Markdown remains the editorial source; Nift composes/renders it through shared layouts. Preserve front matter or convert it into equally human-maintainable metadata. Keep source organization familiar for contributors and meaningful diffs. Translate shortcode semantics into clear Nift partials or a small explicit conversion layer only where needed. Retain CLI YAML/API data and upstream attribution; keep conversion reproducible. Rendering parity problems require a bounded proof of concept and documented decisions, not wholesale flattening for speed.
Model the published route map explicitly: `/manuals` is removed from output URLs while source references retain it. Preserve vendored content and provenance. Content adapters generate CLI/API pages beyond the authored Markdown count. Preserve hidden-page rules (sitemap:false plus cascade), sidebar visibility on the active path, weights/groups/badges and navigation overrides. Avoid guessing frontmatter or tracked.json fields. Nift evaluates syntax before markup conversion: escape literal sigils in Docker examples and test round-trip text fidelity.

# JavaScript strategy
Prefer vanilla implementations for small interactions. Retain an existing dependency where rewriting increases parity risk; document and measure the dependency footprint.
Inventory Alpine persistence/collapse/focus, mobile sidebar, search modal and keyboard shortcut, themes, tabs, accordions, copy code/Markdown, heading/TOC behavior, tooltip positioning, Mermaid, interactive diagrams, YouTube and API reference controls. Gordon uses Docker's remote AI endpoint; analytics and consent involve remote services. Test local UI and mocked response flows without submitting prompts or telemetry to Docker. Keep necessary specialized libraries unless equivalent behavior is demonstrated. External service availability is a documented boundary, not a reason to remove UI.

# Validation strategy
1. Freeze complete built-file manifest with SHA-256, size, extension and route mapping. Distinguish documents from assets and redirects; authored page counts are not route counts.
2. Store per-page titles/meta/link declarations, anchor IDs and asset references. Compare every route, generated feed and metadata artifact. Resolve internal links and fragments; establish upstream defect baseline.
3. Choose fixtures spanning every page family and behavior: home, deep docs, hidden navigation, CLI options, API operation/schema, guide series, samples, long tables, Mermaid and interactive diagrams, 404 and redirects.
4. Capture desktop (1440x900) and mobile (390x844), light/dark themes, deterministic fonts and network mocks. Add keyboard/focus/search/tab/sidebar/copy checks. Inventory capture coverage; representative images supplement full-corpus checks.
5. Run clean-checkout full builds, then edit dependencies and compare incremental output against full rebuild output. Test deletion/addition/rename and navigation data fan-out. Keep validation outside timing windows.

# Benchmark methodology
The authoring models intentionally differ: Hugo renders Markdown plus Hugo templates; docker renders maintained Markdown plus Nift templates; docker-agent composes maintained HTML with Nift. Report this explicitly. Measure Markdown conversion, composition, asset/publication work and indexing separately where possible. A faster HTML architecture demonstrates a different maintenance/work tradeoff; do not present it as equivalent Markdown authoring. Compare docker against Hugo for conventional documentation adoption, and compare docker-agent for the cost and benefits of agent-primary HTML maintenance.
Do not compare the Nift starter with the Docker corpus. Measure renderer-only and complete publication pipeline separately. Include asset handling, metadata, Markdown and search obligations in both pipelines. Preserve exact commands, versions, machine/CPU/thread settings, output manifest, logs, wall time and GNU time peak RSS. Record child-process RSS limits: phase maxima are not a combined pipeline peak.
Use isolated fresh checkouts and fresh output/cache directories for application-cold runs; do not claim OS-cold unless caches are controlled. Warm full runs still regenerate all pages (`nift build --all`); Hugo is a full invocation. Include at least five uncontended repetitions and median/range. Separate dependency installation and downloads from build time.
Changed-input scenarios: deterministic edits to 1/10/100 authored pages, shared layout and navigation/data, matching semantic edits across projects. Restore from separate disposable benchmark copies without destructively cleaning references. Include any preprocessing and regenerated search/index data; assert incremental outputs match full rebuild. Hugo server incremental behavior is a separate workflow measurement, not conflated with CLI full builds. Choose and record Nift modified/hash mode and state restoration policy.
Compare source/template counts, shared abstractions, direct/transitive dependencies, JS bytes, full and changed build time/RSS, output size, migration effort, ease of human/agent editing and compromises. Neither architecture is required to win.

# Current checkpoint
C0 setup/investigation complete: final production pipeline succeeded; complete website/source archives, full Git history, logs, dependency/tool provenance and full 8,622-file inventory preserved. See investigation/BASELINE.md for measured evidence and execution status. Browser fixtures and full link audits are pending C1. Migration has not begun.

# Completed checkpoints
Repositories created/cloned; Nift initialized; generated handover v0.0.8 inspected and preserved below plus investigation/generated-HANDOVER-v0.0.8.md. Nift 4.7.2 does not generate AGENTS.md here; project rules added manually. Upstream pinned and source architecture inspected. Production build procedure traced through deployment workflow, bake file, Dockerfile and releaser environment.

# Remaining checkpoints
- C1: freeze complete baseline, route/assets/metadata/redirect inventory and desktop/mobile/behavior fixtures; complete any gaps recorded in BASELINE.md.
- C2: reconstruct shared chrome and representative page families; verify route/path/sigil handling and dependency fan-out.
- C3: migrate full standard docs and guide corpus, preserving metadata and semantic authoring choices.
- C4: CLI/API adapters, samples, glossary, special layouts and all ancillary outputs.
- C5: interactions, search and responsive/accessibility parity; full route/asset/link audits.
- C6: clean-checkout and changed-input correctness, reproducible full/changed benchmarks.
- C7: architecture comparison and final evidence report, known compromises and maintainers' resume guide.
Commit, validate, update handover and push at each bounded checkpoint. Do not proceed merely because representative pages look right.

# Known deviations
No migration exists yet. Native baseline execution differs from the official Alpine/BuildKit environment; record this honestly. Browser fixtures and full route link validation belong to C1 and must be completed before claiming parity.

# Blockers
No active setup blocker. Native production pipeline passed. Docker/BuildKit container reproduction remains unmeasured because Docker is not installed; native execution differences are recorded in investigation/BASELINE.md. No confirmed Nift blocker so far.

# Nift limitations encountered
Initialization emitted `Failed to create stream fd: Operation not permitted` under the restricted shell but returned success and built the starter. Verify builds outside the restricted shell if it interferes; do not change Nift. Hugo-specific Goldmark/shortcode rendering is a migration translation risk, not demonstrated evidence that Nift needs changes.

# Decisions and rationale
The user explicitly required Markdown as maintained source in docker and pre-rendered HTML as maintained source in docker-agent on 7 October 2026. This is an experiment variable, not an incidental optimization. No migration has begun.
Keep upstream and built reference material outside both migration working trees to prevent accidental source edits and benchmark contamination. Preserve generated Nift guidance; project-specific sections extend it. Keep a single pinned baseline for both architecture experiments. Build production with full Git history because enableGitInfo influences output metadata. Freeze complete output before choosing extraction strategy.

# Exact commands to resume work
```sh
nift build
nift status
cat investigation/BASELINE.md
# Use a fresh output/evidence path for each reproduction:
bash scripts/build-upstream.sh ../docker-upstream ../docker-baseline/site-next ../docker-baseline/run-next ../docker-baseline/tools
python3 scripts/inventory.py ../docker-baseline/site-next ../docker-baseline/inventory-next
```
Read build prerequisites and provenance in BASELINE.md before running reproduction. Never migrate against partial failed output.

# Completion criteria
All pinned routes and publication artifacts accounted for; full-corpus content/meta/assets/navigation validation passes with only explicitly documented inherited/external deviations; desktop/mobile and keyboard fixtures pass across every family; clean-checkout builds work; changed-input outputs equal full rebuild; benchmarks reproduce with equal workload; comparison and handovers explain architecture, compromises and continuation. Nift remains unmodified. Setup is complete only when its baseline build and investigation evidence are recorded and checkpoint pushed.

# Retained generated Nift guidance
The following is the original initialization guidance, preserved rather than replaced. Project-specific requirements above govern this experiment.

# HANDOVER.md
v0.0.8

This is a living handover for working effectively in a Nift project.

Canonical version:

https://nift.dev/HANDOVER.md

Check the version at the top of this file against the canonical copy when the
project is old, unfamiliar, or behaving differently from the current Nift
documentation.

To replace this file with the latest canonical version:

```sh
curl -fsSL https://nift.dev/HANDOVER.md -o HANDOVER.md
```

If this project has project-specific additions, preserve or reapply them when
updating the canonical handover.

This project uses Nift as part of its website build process.

Nift is the project's build-time templating and dependency layer. It does not determine what the website is about or what other technologies the project should use.

Keep the existing project architecture and use the project's normal HTML, CSS, JavaScript, frameworks, backend, and other tooling where appropriate.

Do not introduce Nift-specific machinery where ordinary web tooling is the clearer solution.

## Start here

Before making substantial changes:

1. Inspect `.nift/config.json` and `.nift/tracked.json`.
2. Inspect the existing `content/`, `templates/`, and output structure.
3. Read this project's `README.md` and other project-specific documentation.
4. Run:

```sh
nift status
```

During normal development, build frequently:

```sh
nift build
```

Use this throughout a task, not only at the end. Rebuild after meaningful
changes so Nift can surface template, path, dependency, configuration, and
tracking errors while the cause is still obvious.

In particular, run `nift build` immediately after editing
`.nift/config.json` or `.nift/tracked.json`.

Use:

```sh
nift status
```

when you want to inspect what Nift considers stale and why.

Successful `nift build` output may include indented `↳ ...` lines explaining
why a page was considered stale and rebuilt, such as a missing generated output
or a changed dependency. These are rebuild reasons, not errors. Actual build
failures are reported as errors and cause the build to fail.

Do not delete or recreate `.nift/`.

## Nift's core template model

Most Nift websites need very little Nift-specific syntax.

The three primitives you will use most often are:

```text
@content
@input(...)
@path(...)
```

`@content` inserts the tracked page's content into its template.

```html
<main>
    @content
</main>
```

`@content` should execute exactly once across the rendered template/input graph
for a tracked page. It is normally placed in the page's template; the tracked
content file supplies the content inserted there.

Content files may still use other Nift syntax when needed. If page text needs
to display Nift syntax literally, prefix the active sigil with `\` rather than
leaving it as template syntax:

```html
<code>\@content</code>
<code>\@path('about')</code>
<code>\$[title]</code>
```

This applies whenever `@...`, `$[...]`, or other Nift syntax is intended as
literal output rather than something Nift should execute or resolve.

`@input(...)` inserts a reusable file and automatically makes it a dependency of the output using it.

```html
@input('templates/header.html')

<main>
    @content
</main>

@input('templates/footer.html')
```

### Structured JSON and markup sources

Use name-first `@json` when a template needs immutable structured data:

```text
@json(name, path)
@json(name, schema-path, path)
@json(name, schema-name, path)
@json(name){...}
@json(name, schema-path){...}
@json(name, schema-name){...}
```

Inline bodies are evaluated as Nift templates before JSON parsing. A schema
name refers to an earlier JSON binding. Data and schema files are automatic
dependencies and paths must stay inside the project.

Use `@markup(format){...}` or `@markup(format, path)` for Markdown (`md`),
AsciiDoc (`adoc`) or reStructuredText (`rst`). Nift evaluates template syntax in
the source first, Markup++ converts it once, and the resulting HTML is appended
without being parsed as Nift syntax again. File sources and host-resolved
AsciiDoc/RST includes are automatic dependencies.

`@path(...)` creates project-aware links to tracked pages and local assets.

Nift has additional features including metadata, JSON data, loops, conditionals, pagination, contracts, and explicit dependencies. Use them when the project actually needs them; do not use advanced features merely because they exist.

When writing expressions inside constructs such as `@if(...)`, refer to values directly rather than wrapping them in `$[...]`. For example:

```html
@if(name == 'about'){...}
```

Use `$[...]` when resolving or rendering a value into output, for example `$[title]`. Consult the expressions and control-flow documentation when using more advanced expression syntax.

## Internal links: use `@path`

Use `@path(...)` for internal links.

This applies to:

- links between pages;
- stylesheets;
- JavaScript;
- images and other local assets where Nift should know the relationship.

For pages, link to the **tracked page name**, not its generated file.

```html
<nav>
    <a href="@path('/')">Home</a>
    <a href="@path('about')">About</a>
    <a href="@path('docs')">Docs</a>
    <a href="@path('contact')">Contact</a>
</nav>
```

Do this:

```html
<a href="@path('about')">About</a>
```

Do not do this:

```html
<a href="@path('about.html')">About</a>
```

and do not hard-code the generated output path:

```html
<a href="about.html">About</a>
```

The tracked page name is the stable project identity. Its output filename or location may change independently.

CSS and JavaScript includes should also use `@path(...)`:

```html
<link rel="stylesheet" href="@path('public/assets/style.css')">
<script src="@path('public/assets/app.js')"></script>
```

Do not calculate relative paths such as:

```html
<link rel="stylesheet" href="../../assets/style.css">
```

Using `@path` lets Nift resolve the correct output-relative path and check the project relationship during the build.

## Project configuration

`.nift/config.json` contains project-level Nift configuration.

`.nift/tracked.json` describes tracked pages and their metadata, including things such as their content, template, and output relationships.

By default, ordinary CSS, JavaScript, images, fonts and other static assets live
directly in the configured output tree (normally `public/`) and do not have
entries in `.nift/tracked.json`. Edit those files in place. This keeps Nift's
tracked graph focused on content that Nift actually renders and avoids duplicate
source/output copies for files that need no build-time transformation.

Track an asset only when Nift genuinely needs to generate it from content,
templates or build-time data. Template-less tracked entries remain available for
that advanced case; they are not the default asset workflow.

These files are part of the project and should evolve with its structure.

If you add, remove, or reorganise pages, templates, outputs, deployment settings, or other Nift-managed structure, inspect the relevant `.nift` configuration and update it where necessary.

Do not treat `.nift/` as disposable generated state.

Do not invent `.nift/tracked.json` fields or assume arbitrary fields become
`$[...]` metadata. When you need tracking behaviour or metadata that is not
already demonstrated by the project, consult the tracked-files and metadata
documentation rather than guessing.

## Output directory

Do not assume the generated website always lives in `public/`.

A normal Nift project may use `public/`, but deployment targets can use a different output structure appropriate to the platform.

Inspect `.nift/config.json` before making assumptions about output paths.

Edit Nift-managed page sources rather than their generated output. Edit untracked
static assets directly in the configured output tree, unless the project
documents another tool or source directory as their owner.

## Pagination

Pagination has several related pieces across `.nift/tracked.json`, page
content, pagination templates, and generated page links. Do not infer its full
behaviour from this handover.

If working with pagination, read the dedicated documentation first:

https://nift.dev/docs/pagination.html

Preserve the project's existing pagination structure unless the task actually
requires changing it, and run `nift build` frequently while doing so.

## Other stacks and tools

Nift does not need to own the whole application.

A project may use Nift alongside tools such as Vite, React, Vue, Svelte, TypeScript, Go, Node, Python, PHP, serverless functions, or other systems.

Keep responsibilities separated:

- use Nift for build-time composition, tracked relationships, and dependencies;
- use the neighbouring tool for the job it is designed to do.

Do not replace an existing stack with Nift-specific code simply to make more of the project use Nift.

## Before finishing

Run:

```sh
nift build
nift status
```

The build should succeed and `nift status` should report the project up to date.
Spot-check generated output when changes affect paths, templates, tracked
relationships, or deployment structure.

## Documentation

Nift documentation:

https://nift.dev/docs.html

When unfamiliar with the project, prioritise:

1. Getting started — https://nift.dev/docs/getting-started.html
2. the three-primitives/template-language material;
3. paths and tracked files, especially `@path`;
4. project structure;
5. `.nift/config.json` and `.nift/tracked.json`;
6. incremental builds and CLI commands.

Then read feature documentation only when the task requires it, for example:

- JSON and control flow;
- pagination;
- contracts;
- minification;
- deployment targets;
- integration with other application stacks.

Prefer documented Nift behaviour and the existing project structure over guessing based on another website generator or framework.
