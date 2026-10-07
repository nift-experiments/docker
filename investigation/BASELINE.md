# Docker Docs setup and investigation baseline

Checkpoint date: 7 October 2026 (Australia/Melbourne). Setup and investigation succeeded. Migration has not started.

## Provenance and preservation

Upstream: https://github.com/docker/docs at **6cf1b1c167f032e8a6629da211602300b623b20e**. Full history fetched; HEAD stayed pinned. Tracked upstream working tree is clean, and no authored source was modified. Generated Hugo resources/statistics and installed node_modules are ignored upstream build artifacts.

Local references under `/home/nick/Repositories/nift/nift-experiments/`:

- `docker-upstream/`: complete source checkout and Git history.
- `docker-baseline/site/`: complete final production build, including Pagefind.
- `docker-baseline/site.tar.gz`: preserved complete website archive.
- `docker-baseline/upstream-source.tar.gz`: pinned tracked-source archive.
- `docker-baseline/run/`: final commands, logs, timings and versions.
- `docker-baseline/tools/`: SHA-256-verified Hugo and Node downloads and executables.
- `docker-baseline/inventory-final/`: complete file/hash manifest and per-document inventory.

Archive hashes are copied to `archive-sha256.json`; file hashes to `inventory/files.json`. Archives remain local, outside migration repositories, and can be reproduced from pinned source. They have not been uploaded as release assets. Earlier probe outputs/logs remain preserved but are not the parity reference.

## Build procedure

Official production deployment checks out full Git history, sets `HUGO_ENV=production` and `DOCS_URL=https://docs.docker.com`, and builds the bake `release` target. The generic Dockerfile defaults to development, so a bare `docker buildx bake` without production environment is not the production baseline.

```sh
HUGO_ENV=production DOCS_URL=https://docs.docker.com docker buildx bake release
```

Docker is not installed on this host. The successful native reproduction follows Dockerfile build/pagefind/release stages:

```sh
bash scripts/build-upstream.sh ../docker-upstream ../docker-baseline/site-next ../docker-baseline/run-next ../docker-baseline/tools
python3 scripts/inventory.py ../docker-baseline/site-next ../docker-baseline/inventory-next
```

The script requires the pinned SHA, full history, installed upstream production dependencies, the recorded tool directory and a new output path. It runs:

```sh
hugo --gc --minify --panicOnWarning --printPathWarnings --printUnusedTemplates -b https://docs.docker.com -e production --destination OUTPUT
node --test hack/test/flatten-and-resolve.mjs
node hack/flatten-and-resolve.js OUTPUT
node hack/api-docs/verify-output.mjs OUTPUT
npx --yes pagefind@1.5.2 --site OUTPUT --output-path OUTPUT/pagefind
```

The destination override preserves the reference outside the upstream checkout. Pagefind reads upstream pagefind.yml with the explicit destination override; table and md-dropdown exclusions remain active.

## Toolchain and dependencies

- Hugo **0.163.0 extended**, build `4a9485336a3ff2cea07ab88e2a17ec34d5baaa6e`, official Linux amd64 release.
- Node **24.21.0**, npm **11.19.0** for build steps.
- Pagefind **1.5.2 (Extended)**.
- Host Go **1.26.0**, Linux amd64. Upstream go.mod requests 1.26.8; the build consumes committed `_vendor` and does not re-vendor modules. A version-reporting probe triggered an unnecessary Go toolchain download and was stopped; the native build reports local Go explicitly.
- Nift **4.7.2**, initialization/handover **v0.0.8**.
- Production dependencies installed with `npm ci --omit=dev`, preserving package-lock.json, using existing Node 22.22.1/npm 9.2.0 for installation; rendering/postprocessing used Node 24.21.0. No lockfile changes occurred. This installer difference is recorded rather than represented as an exact Alpine container run.
- Dockerfile declares Alpine 3.23, Go 1.26, Node 24; no container-runtime baseline was measured here.

Upstream has 14 direct production npm dependencies: Alpine 3.15.8 plus collapse/focus/persist, Tailwind/CLI 4.2.1, typography 0.5.19, heroicons 2.2.0, Floating UI 1.7.6, highlight.js 11.11.1, marked 17.0.4, Mermaid 11.15.0, micromark 4.0.2 and Marlin SDK 0.6.0. Exact resolved dependency tree and lockfile are preserved. Vendored module versions are preserved in go.mod, go.sum and the source archive.

## Successful output inventory

| Measure | Count |
| --- | ---: |
| Complete publication files | 8,622 |
| Total bytes | 963,162,827 |
| HTML documents | 3,901 |
| HTML redirect documents | 1,728 |
| Non-redirect HTML documents | 2,173 |
| Markdown exports | 2,170 |
| redirects.json rules | 2,510 |
| Pagefind searchable pages | 2,142 |
| Search words | 31,268 |

Non-redirect HTML includes the 404 and two Google verification files; the remaining 2,170 are site pages. Redirect rules and HTML redirect files are separate parity obligations and must not be added as if they were unique content pages. Hidden pages are excluded from site search/discovery but can still be directly available. Hugo reports 4,348 Pages across output formats, 269 non-page files, 20 static files and 1,728 aliases; that build summary is not a unique HTML route count.

`inventory/pages.json.gz` records every HTML route, title, metadata, link declarations, JSON-LD, anchor IDs, asset references, hrefs and behavior attributes. It is compressed because shared navigation and page shells repeat heavily. This inventory is evidence, not an assertion that all baseline links or behaviors are correct. Full link/asset and browser audits belong to C1.

Source inventory: 1,116 authored content Markdown files, 266 vendored Markdown files, three content adapters, 510 data files, 118 layout files, 67 asset source files and 20 static files. Generated adapters and module mounts explain why authored Markdown count is smaller than the published corpus.

## Initial measurements

Hardware: Intel Core i7-12700H, 20 logical CPUs, 14 cores. GNU time logs preserve the full process measurements.

| Phase | Wall seconds | Peak RSS KiB |
| --- | ---: | ---: |
| Hugo, full history / fresh output and Hugo cache | 26.56 | 1,399,200 |
| Upstream flattening tests | 0.31 | 66,364 |
| Markdown flattening/link resolution | 9.14 | 512,900 |
| API output verification | 1.06 | 140,476 |
| Cached Pagefind invocation | 5.88 | 401,824 |

The cached indexing invocation writes to `docker-baseline/pagefind-cached`, leaving the final site unchanged. Pagefind's own indexing report is 5.087 seconds. The initial final-build Pagefind wrapper took 92.62 seconds because npm metadata/cache preparation was involved; it is not steady-state indexing time. Do not substitute it into a fair renderer benchmark without separating bootstrap.

These are diagnostic single runs, not a completed benchmark campaign. The filesystem had been warmed by the probe, so the fresh Hugo cache/output run is not OS-cold. An inventory process ran during part of the publication pipeline, so these timings are not an uncontended aggregate pipeline measurement. Phase RSS maxima are not a measured aggregate peak. Do not claim Hugo/Nift performance comparisons until both equal-workload migrations are complete and repeated uncontended runs pass output checks.

## Architecture and behaviors

Families: home/get-started/guide landings; standard documentation and section pages; guides/learning series; data-adapted Docker/sbx CLI reference; API catalog/overview/operation/schema pages; legacy Engine API/Redoc; samples; glossary; wide pages; 404 and ancillary outputs.

Shared shell: head/meta/JSON-LD, header/search/theme, Gordon chat panel, recursive sidebar with active/hidden-path state, breadcrumbs, article, TOC/right rail, footer, and conditional scripts. Manuals source paths lose `/manuals` in published URLs. Sidebar weights, grouping, badges, reverse order and overrides matter.

Interactions: mobile navigation, persisted light/dark/system theme, Pagefind modal/search/shortcut/focus, tabs, accordions, code/Markdown copying and downloads, tooltip positioning, TOC tracking, Mermaid and interactive diagrams, YouTube, API controls, Gordon chat/feedback, analytics and consent. Remote endpoints and CDN assets require deterministic validation fixtures; do not send telemetry or prompts as part of tests. Browser parity has not been verified at this checkpoint.

## Content strategy and expected difficulties

The user explicitly selected maintained Markdown for `docker` and maintained rendered HTML for `docker-agent`. `docker` retains authored structure/front matter where practical and renders through Nift; `docker-agent` converts once during migration and avoids Markdown rendering in routine builds. The authoring-model difference must be explicit in final performance and maintainability comparisons.

Difficulties include Goldmark/shortcode output fidelity (282 tabs blocks, 565 tab shortcodes, 86 includes in authored source), literal template sigils inside Docker code examples, vendored mounts and generated adapters, URL/alias normalization, responsive navigation/focus, hidden pages, metadata/Git dates, and synchronized Markdown/LLM exports after agent edits to HTML. Search/index and navigation fan-out must be included in changed-input correctness and complete-pipeline timings. The output is large because shared shells and API/navigation markup repeat; do not remove observable output to win timings.

No confirmed Nift change is required. Native markup parity and dependency fan-out need proof-of-concept checks before deciding whether a limitation exists. Nift initialization emitted restricted-shell stream-fd warnings but built successfully; both starters report up to date. No Nift implementation or installation was changed.

## Checkpoints

C0 setup/investigation: complete after committing/pushing this evidence. C1 freeze browser/keyboard fixtures and complete baseline link/asset/metadata audits. C2 shared chrome and representative families. C3 full docs/guide corpus. C4 adapters/special families and ancillary outputs. C5 interactions and whole-site parity. C6 clean-checkout/changed-input correctness and repeated fair benchmarks. C7 architecture comparison and final handover/report.

Fixture candidates are in `fixture-candidates.json`; captures are pending. Do not begin migration until instructed. At each checkpoint update HANDOVER.md, validate, commit/push normal history and leave clean working trees.
