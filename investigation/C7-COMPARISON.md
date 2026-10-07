# C7: Docker migration comparison

Both faithful migrations are complete, with separate maintained-source architectures and no Nift modifications. For a conventional Docker documentation team, **recommend `docker`**: familiar Markdown/frontmatter and structured CLI/API sources remain maintainable, while the optimized complete publication pipeline is competitive with the measured upstream production workflow. Choose `docker-agent` when maintained rendered HTML is an intentional editorial decision. Its lower transformation cost is a real advantage of that source model, not an apples-to-apples authoring comparison.

## Architecture

```text
docker:
maintained Markdown
  → Docker compatibility renderer
  → transient HTML
  → Nift composition
  → publication/search

docker-agent:
maintained HTML
  → Nift composition
  → publication/search
```

Human compatibility uses standalone Goldmark/Chroma plus the pinned corpus's shortcode/include/render-hook behavior and typed CLI/API/special-page ports. It is bounded to the actual corpus; it does not interpret Hugo generally. Seven hook categories are covered: headings, links, images, code fences, Mermaid fences, blockquotes and tables. Mount/published-path normalization, includes, tabs/tab children, Chroma tokens, heading anchors, tables and literal template/Nift syntax have real-source fixtures.

Both pipelines use Nift's proven raw HTML composition with explicit dependencies; returned HTML is not interpreted as template syntax. Joint HTML analysis supplies headings and Markdown downloads. Human output also passes the separately timed pinned HTML minifier. Agent maintains already-rendered bodies and intentionally has no routine Markdown renderer or HTML minification stage. Shared templates, typed route/metadata/navigation models, full auxiliary publication and fresh Pagefind remain. Use `python3 scripts/build.py` as the publication entry point; direct Nift invocation only composes prepared inputs. Human timings are **not native `@markup` performance**.

## Whole-pipeline comparison

Seconds: five serialized repetitions per row, medians and full ranges. Initial faithful migration and optimized faithful migration are retained independently.

| Pipeline | Warm full median (range) | Fresh committed checkout median (range) | Warm measured process/phase RSS median, MiB | Fresh measured process/phase RSS median, MiB |
|---|---:|---:|---:|---:|
| Hugo production CLI | 29.12 (27.74–30.55) | 34.46 (31.28–38.19) | 1532.8 | 1477.8 |
| docker initial | 61.52 (60.25–61.62) | 66.66 (64.71–87.12) | 1058.3 | 1052.1 |
| docker optimized | 21.83 (21.61–22.47) | 23.75 (23.46–23.99) | 441.6 | 432.0 |
| docker-agent initial | 30.27 (28.26–35.75) | 30.03 (29.46–30.25) | 992.2 | 980.7 |
| docker-agent optimized | 14.65 (13.56–14.91) | 15.20 (14.87–15.67) | 391.7 | 391.9 |

[The complete optimization report](C6-OPTIMIZATION.md) gives initial/optimized component medians, changed-input whole/project/search medians and ranges, exact changes and correctness results. Raw samples retain renderer parse/render/hooks/Chroma counters, typed CLI/API generation, shared shell, body analysis, Nift composition, minification, assets, downloads, ancillary output and search preparation/indexing. Diagnostic before/after wall hierarchies add source/frontmatter/YAML preparation, metadata binding, filesystem/hash work and nested timings; these instrumented profiles are not benchmark results. Nested counters and parallel worker wall sums must not be added twice. Hugo exposes generation/minification together; no unsupported Markdown-only Hugo timer is invented.

Warm `--all` rebuilds force all content generation, all 3,901 Nift compositions, all 2,170 body analyses/downloads, human minification and fresh search. Fresh runs clone the committed implementation with empty application state/output and prepared binaries/Node dependencies. Clone, dependency installation/Go compilation, validation and changed-input restoration are excluded. Every optimized fresh checkout reproduces every accepted publication-file hash. These are application-cold builds; operating-system caches are uncontrolled.

Changed-input cases cover one/ten/100 maintained bodies, shared footer, navigation and title metadata, with five repetitions each in both projects. First edits in all 12 cases equal forced-full output; all 60 successful edits restore all original output hashes. Addition, rename and deletion also pass full equality, navigation/canonical/SEO/TOC/literal/download/sitemap/search checks and retirement of previous outputs. Human metadata edits compile zero unrelated bodies; body edits compile/analyze only their changed pages. Conservative shared implementation/data dependencies can still invalidate multiple pages when they genuinely may affect rendering.

One- and ten-page edit medians are slightly higher after optimization in both projects. Full and shared-input builds improved substantially; this pass does not claim every edit became faster. Retained fresh-search costs are higher in these later desktop samples, and the complete ranges remain in the evidence.

Search is a material fixed cost. Both workflows retain fresh Pagefind indexing for every publication, timed separately; the project/search/whole table exposes it. A narrower search update needs a proven projection of all Pagefind-visible text, metadata, anchors, filters and ignored selectors. This experiment retains the correct full index instead of inventing incremental Pagefind behavior or omitting search from changed-input timings.

The retained Hugo changed-input results are complete production CLI publications, not Hugo development-server hot reload. No claim is made that Hugo lacks development caching. The upstream native reproduction includes Hugo generation/minification, flatten tests/processing, API output verification and Pagefind. Docker was unavailable, so this is not an Alpine/BuildKit deployment measurement. Upstream declares Go 1.26.8; tested native standalone renderer/minifier toolchain is Go 1.26.0. See BASELINE.md and immutable C6 environment evidence.

## Source, templates and output

Counts below distinguish maintained sources from generated publication. Tracked-file totals are the optimized C6 commit snapshot and include evidence/docs; physical authored Markdown includes includes/vendor/unpublished inputs and is not a route count. Page-source directory counts include auxiliary/setup files; active publication route counts are reported separately.

| Measurement | docker | docker-agent |
|---|---:|---:|
| Tracked files | 3,087 | 4,717 |
| Tracked bytes | 127,515,734 | 141,753,499 |
| Authored source files | 2,096 | 0 |
| Authored source bytes | 31,631,946 | 0 |
| Physical authored Markdown files | 1,263 | 0 |
| Maintained HTML page files | 2 | 3,902 |
| Maintained HTML page bytes | 106 | 48,877,784 |
| Shared chrome HTML templates | 323 | 323 |
| Shared chrome template bytes | 4,554,740 | 4,554,740 |
| All layout HTML files | 326 | 326 |
| Typed data files | 13 | 9 |
| Typed data bytes | 35,900,225 | 33,274,963 |
| Runtime/validation Python lines | 2,646 | 971 |
| Publication files | 8,622 | 8,622 |
| Publication bytes | 963,301,734 | 988,353,510 |
| Published JavaScript files | 10 | 10 |
| Published JavaScript bytes | 4,266,240 | 4,266,240 |

The source registry has 1,187 Markdown entries (eight render-never), 539 generated CLI pages and 452 generated API pages, yielding 2,170 content pages. Publication includes 1,728 alias HTML documents, 404 and two verification documents: 3,901 HTML documents in total. Redirect JSON retains 2,510 entries. Search indexes 2,142 routes and 31,268 distinct words. Typed API JSON preserves the upstream 2,193,471-byte source. Shared chrome uses 323 HTML templates rather than opaque per-page frames; additional special-page templates are maintained separately.

Both preserve the compiled upstream frontend, including the same published JavaScript bytes and specialized interactions/libraries. Asset compilation/dependency installation is outside routine builds; changing the upstream frontend toolchain remains a separate maintenance task. Human runtime dependencies add safe PyYAML, standalone Goldmark 1.8.2, Chroma 2.24.1, GoAT 0.5.0 and the pinned minify/parse libraries (go.mod/go.sum record exact direct/transitive dependencies). Agent routine builds require Python standard library, Nift and Pagefind, with no Go/Markdown renderer. Both retain the upstream manifest's 14 production dependencies (plus four development dependencies for upstream tooling) rather than claiming a new smaller JavaScript implementation. The human standalone Go tools have six distinct module dependencies across their two pinned module manifests.

## Acceptance and remaining boundaries

Both projects pass all 3,901 HTML route contracts and all 2,170 content-page comparisons, required assets/feeds/metadata/redirects/downloads and search semantic checks. The optimized output is SHA-256 identical to the accepted initial migration for all 8,622 publication files per project. All 192 browser states per project have zero DOM/behavior differences and pixel-identical required screenshots. Supplementary keyboard/theme/search/tab/accordion/copy/Gordon/API controls match accepted behavior. Real-source fixtures and full CLI/API/special/navigation fixture sets pass. Concurrent minification is checked with Go's race detector on real Docker pages, matching the production minifier's output hashes.

The accepted migration differs from upstream in HTML-derived Markdown formatting, XML container whitespace where semantic equality is used, RSS generator attribution, and 144 human Pagefind sentence-boundary punctuation cases. Search routes, words/counts, metadata, filters, anchors and locations match; agent fragments match exactly. The optimization introduces no new differences. Upstream inherited observations remain identical: 576 missing descriptions, 2,154 duplicate-ID observations, 80 missing fragments, four missing local targets, 54 empty metadata URLs and 38 absent redirect targets. See C5-PARITY.md for evidence and boundaries.

Remote requests are intercepted during browser tests. Local UI/markup/reference behavior is covered; actual Docker AI, telemetry, consent and remote Redoc/backend availability is not claimed. No prompts, feedback or telemetry were sent. Browser version/capture details and the untouched-baseline 404 capture workaround are preserved in C5.

These runs are serialized on an active i7-12700H desktop (20 logical CPUs, approximately 61 GiB RAM); existing user applications continue running. They are not CPU-isolated dedicated-host samples. GNU time RSS is the largest individual measured process/phase maximum, not aggregate memory across analysis workers. HTML analysis uses four workers; human minification uses eight; Nift retains its original build-threads=-1 setting. Diagnostic profiles and earlier tuning trials are separate from the five-run headline results; no fastest-trial substitution was made.

## Maintenance recommendation

`docker` preserves contributor-friendly Markdown/frontmatter/source organization, structured CLI/API data and readable diffs. The price is a Docker-specific compatibility layer and explicit maintained route/family/metadata/navigation bindings. New upstream behavior requires a corpus-backed fixture and a bounded port; unsupported features fail rather than silently emulating Hugo incompletely. The pin's conditional assets, provenance/Git dates and publication policies are explicit maintenance responsibilities. This architecture is reasonable for the demonstrated production corpus but is not a drop-in general Hugo replacement.

`docker-agent` is smaller operationally because rendered HTML is maintained directly. An agent must update associated title/schema/export/navigation metadata coherently and maintain rendered specialized references itself; it does not regenerate them from Markdown/YAML/API source during normal builds. This shifts editorial responsibilities and removes transformations. Do not normalize the two projects merely to equalize timings.

Migration effort included corpus inventory, seven render-hook ports, bounded shortcode/include compatibility, typed CLI/API/special generation, shared shell recovery, publication/dependency ownership and whole-corpus/browser acceptance, followed by profiling and optimized invalidation. No wall-clock labor hours were recorded, so none are invented. The checkpoint reports and maintained code expose the implementation effort and ongoing maintenance surface. Performance supports the conventional Markdown migration on this corpus; it alone does not establish universal superiority or justify an unqualified platform switch.

## Reproduction and checkpoint evidence

Use README.md for setup and complete publication commands. Human benchmark harnesses can run both sibling projects. Run measurements sequentially against committed sources with a new output directory:

```sh
python3 benchmarks/run.py --projects docker,docker-agent --repetitions 5 --output ../docker-rerun/warm
python3 benchmarks/changed.py --repetitions 5 --output ../docker-rerun/changed
python3 benchmarks/fresh.py --projects docker,docker-agent --repetitions 5 --output ../docker-rerun/fresh
python3 benchmarks/routes.py --output ../docker-rerun/routes
```

Do not overwrite immutable initial C6 or optimized accepted evidence. `DOCKER_EVIDENCE_ROOT` redirects validation evidence; browser capture uses the documented pinned Playwright/Chromium environment. The real-source fixtures, full publication tests and accepted-hash verification accompany the harnesses. Initial C6 raw evidence remains in `docker-baseline/c6`; optimized raw timings/logs/profiles/captures remain in `docker-optimization`; compact committed samples/proofs are under `investigation/c6-optimized` and `investigation/c7`. C2–C5, initial C6, optimized C6 and C7 are independent commits in each repository. Nift and the pinned upstream checkout remain unchanged.
