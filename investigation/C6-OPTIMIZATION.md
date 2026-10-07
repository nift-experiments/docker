# C6: optimized faithful migration

Initial C6 evidence is preserved under `investigation/c6` and the sibling `docker-baseline/c6`. Optimized evidence uses `docker-optimization` and compact committed copies under `investigation/c6-optimized`. Nift 4.7.2 and the accepted publication remain unchanged.

## Exact changes

1. Prepare navigation values and ancestor adjacency once. Reuse invariant inactive branches while computing active branches per route. Cache shared template reads; stop retaining thousands of generated HTML strings.
2. Use per-route metadata/layout/body fingerprints and scope-specific navigation hashes, with explicit `.generated/chrome-inputs` dependencies. Ordinary Markdown body fingerprints include only frontmatter actually consumed by the bounded renderer; shortcode/include ASTs are reused. Title edits no longer compile unrelated bodies.
3. Parse each content body once for heading bindings and Markdown downloads, using four bounded workers and body/title/policy/implementation fingerprints. Forced full builds still analyze and export all 2,170 content pages.
4. Human-only: use the safe C-backed YAML loader and reuse CLI YAML; cache Chroma lexer lookup within the renderer process.
5. Human-only: batch all required HTML minification into one persistent process with eight workers, one minifier instance per worker, and a synchronized, exact-input SVG cache bounded to 32 MiB. Return output hashes from the minifier. All 3,901 pages are minified in forced full builds; incremental state includes the minifier implementation fingerprint.
6. Keep assets, redirects, metadata, feeds, Markdown downloads and fresh Pagefind output in the publication. Time search preparation and indexing separately. Search remains conservatively regenerated rather than claiming unsupported incremental indexing.

Profiles preceded these changes. Initial profiles found 4,391 HTML parses, 1,350,168 navigation-node visits and 2,350 YAML loads; Go CPU profiles identified expensive repeated Chroma lexer discovery and SVG shortening. Diagnostic profiles are instrumented and are not headline benchmark samples. The initial minifier already used a persistent process: this improvement is batching/parallelism and invariant SVG reuse, not removal of a fictional per-page process startup.

## Warm full publication

Five serialized forced-full runs per project; seconds. Setup, validation and restoration are outside timing. These are medians, not fastest trials.

| Project | Initial median (range) | Optimized median (range) | Initial → optimized process/phase RSS median, MiB |
|---|---:|---:|---:|
| docker | 61.52 (60.25–61.62) | 21.83 (21.61–22.47) | 1058.3 → 441.6 |
| docker-agent | 30.27 (28.26–35.75) | 14.65 (13.56–14.91) | 992.2 → 391.7 |

## Component medians

Outer stages are sequential. Nested renderer counters and parallel-worker wall sums must not be added again to the compatibility/body-analysis stage. Component medians need not sum to the median whole pipeline; external timing also includes startup and unlabelled orchestration.

### docker

| Component | Initial seconds | Optimized seconds |
|---|---:|---:|
| Compatibility | 10.5606 | 6.3505 |
| Shared shell | 16.1946 | 2.6825 |
| Shared body analysis | — | 2.4197 |
| Nift composition | 2.8140 | 2.8516 |
| HTML minification | 19.7808 | 1.8063 |
| Markdown export write / initial conversion | 7.3129 | 0.0719 |
| Ancillary publication | 0.0946 | 0.2642 |
| Assets | 0.0317 | 0.0356 |
| Search preparation | — | 0.0260 |
| Search indexing | — | 3.8047 |
| Whole search | 3.2965 | 3.8312 |
| Nested Markdown parse | 0.4168 | 0.3810 |
| Nested Markdown render | 0.1600 | 0.1555 |
| Nested render hooks | 1.0202 | 0.3302 |
| Nested Chroma | 1.6057 | 1.7025 |
| Nested shortcode expansion | 0.1994 | 0.1327 |
| Nested CLI generation | 3.5199 | 0.8756 |
| Nested API generation | 0.3044 | 0.3235 |

### docker-agent

| Component | Initial seconds | Optimized seconds |
|---|---:|---:|
| Agent preparation | 15.6193 | 3.5346 |
| Shared body analysis | — | 2.5268 |
| Nift composition | 3.0198 | 3.2288 |
| Markdown export write / initial conversion | 7.2679 | 0.0695 |
| Ancillary publication | 0.0968 | 0.1543 |
| Assets | 0.0334 | 0.0390 |
| Search preparation | — | 0.0289 |
| Search indexing | — | 4.0072 |
| Whole search | 3.5351 | 4.0360 |

The optimized shared-analysis stage includes both HTML parsing and download conversion; the much smaller export timer is writing prepared downloads, not disappearance of that work. Agent builds intentionally have no Markdown rendering or routine HTML minification, matching their accepted maintained-HTML architecture. Hook timing includes Chroma lexer discovery; Chroma timing measures tokenization/formatting.

## Changed inputs

Five edits per case, fresh search included. Project work is whole elapsed time minus search. First edited run per case is compared with forced full output outside timing; all edits restore original output hashes.

| Project / edit | Initial whole | Optimized whole (range) | Optimized project work | Optimized search |
|---|---:|---:|---:|---:|
| docker / 1-page | 8.55 | 9.23 (9.00–9.31) | 5.13 | 4.05 |
| docker / 10-pages | 8.10 | 9.64 (9.14–9.98) | 5.37 | 4.21 |
| docker / 100-pages | 12.53 | 11.26 (10.56–11.38) | 6.96 | 4.31 |
| docker / layout | 47.44 | 16.27 (15.59–17.92) | 12.49 | 3.95 |
| docker / navigation | 54.63 | 13.95 (12.80–16.45) | 9.62 | 4.25 |
| docker / metadata | 71.30 | 9.20 (8.58–10.01) | 4.80 | 4.28 |
| docker-agent / 1-page | 5.96 | 6.43 (6.34–6.66) | 2.59 | 3.92 |
| docker-agent / 10-pages | 6.31 | 7.10 (6.64–10.78) | 2.82 | 4.28 |
| docker-agent / 100-pages | 9.35 | 7.40 (6.99–7.75) | 3.29 | 3.87 |
| docker-agent / layout | 25.82 | 12.18 (12.01–12.78) | 8.33 | 3.85 |
| docker-agent / navigation | 26.79 | 10.55 (10.32–11.22) | 6.60 | 3.99 |
| docker-agent / metadata | 26.43 | 6.68 (6.47–6.79) | 2.57 | 3.98 |

## Correctness and boundaries

Every one of 8,622 publication files per project has the same SHA-256 as the accepted initial migration. Whole-site contracts cover 3,901 HTML routes, 2,170 content pages/downloads, 2,510 redirect entries and the 2,142-page Pagefind index. Real-source compatibility fixtures, 539 CLI pages, 452 generated API pages, 46 special pages and 1,604 navigation fixtures pass. Both projects pass all 192 browser states with zero DOM/behavior differences and pixel-identical screenshots. Supplementary controls retain the accepted behavior. Route addition, rename and deletion pass incremental/full equivalence and retire previous output paths.

Existing accepted deviations and inherited upstream defects remain documented in C5; output hashes prove this pass introduced none. Browser remote requests are intercepted: these tests establish local UI behavior rather than live Docker backend availability.

GNU time memory numbers are individual measured process/phase maxima, not aggregate simultaneous memory of the four-worker analysis pool. Builds are serialized but run on an active desktop with uncontrolled OS caches. No dedicated-host or OS-cold claim is made. Native upstream production reproduction is not an Alpine/BuildKit deployment measurement. Prepared tools/dependencies are excluded. Full runs force regeneration of bodies/composition/analysis/downloads/minification/search; unchanged assets may be copied conditionally as in the initial faithful pipeline.

Optimized fresh committed checkouts and the final authoring/architecture recommendation are recorded at C7. The human timing is standalone Goldmark/Chroma compatibility plus Nift composition, never native `@markup` performance.
