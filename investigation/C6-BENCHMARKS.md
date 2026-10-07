# C6: serialized publication benchmarks and correctness

All numbers are seconds. Five repetitions per project/mode/case; setup, clone, validation and restoration are outside timed intervals. The projects retain different maintained source models. No Nift implementation changes were made.

| Pipeline | Warm full median (range) | Fresh checkout median (range) | Largest measured process/phase RSS median, MiB |
|---|---:|---:|---:|
| hugo | 29.12 (27.74–30.55) | 34.46 (31.28–38.19) | 1532.8 |
| docker | 61.52 (60.25–61.62) | 66.66 (64.71–87.12) | 1058.3 |
| docker-agent | 30.27 (28.26–35.75) | 30.03 (29.46–30.25) | 992.2 |

## Warm full components

Component medians do not necessarily sum to the whole-pipeline median. Nested renderer timers diagnose the compatibility stage and must not be added to it again. Hugo exposes its complete generation/minification stage together; no synthetic Markdown-only Hugo timer is asserted.

### hugo

| Measured component | Median seconds |
|---|---:|
| hugo | 18.8445 |
| flatten-tests | 0.2573 |
| flatten | 5.8100 |
| api-verify | 0.8258 |
| pagefind | 3.3159 |

### docker

| Measured component | Median seconds |
|---|---:|
| nift_composition_s | 2.8140 |
| asset_publication_s | 0.0317 |
| total_s | 60.5459 |
| markdown_exports_s | 7.3129 |
| ancillary_s | 0.0946 |
| search_s | 3.2965 |
| compatibility_wall_s | 10.5606 |
| shell_prepare_s | 16.1946 |
| html_minification_s | 19.7808 |
| shortcode_expansion_s | 0.1994 |
| MarkdownParseNS | 0.4168 |
| MarkdownRenderNS | 0.1600 |
| HookNS | 1.0202 |
| ChromaNS | 1.6057 |

### docker-agent

| Measured component | Median seconds |
|---|---:|
| nift_composition_s | 3.0198 |
| asset_publication_s | 0.0334 |
| total_s | 29.5350 |
| markdown_exports_s | 7.2679 |
| ancillary_s | 0.0968 |
| search_s | 3.5351 |
| composition_prepare_s | 15.6193 |

## Changed inputs

| Edit | Hugo warm CLI full | docker incremental publication | docker-agent incremental publication |
|---|---:|---:|---:|
| 1-page | 46.60 | 8.55 | 5.96 |
| 10-pages | 46.42 | 8.10 | 6.31 |
| 100-pages | 49.90 | 12.53 | 9.35 |
| layout | 50.91 | 47.44 | 25.82 |
| navigation | 40.38 | 54.63 | 26.79 |
| metadata | 44.08 | 71.30 | 26.43 |

Body cases edit the same published routes with the same sentinel paragraph, using Markdown versus HTML. Layout edits append a sentinel to the shared footer. Navigation edits alter a maintained sidebar label; Hugo uses linkTitle frontmatter and the migrations use their explicit navigation tree. Metadata edits change the Ubuntu page title; the HTML project maintains the associated title meta/schema fields directly. These are comparable publication intentions, not identical authoring operations.

Hugo changed-input measurements invoke the full production CLI pipeline with warm application caches. They are **not Hugo server incremental measurements**. Nift pipelines use modified-mode dependencies and cached unchanged compiler/export work, followed by fresh search generation. Comparing these rows evaluates those workflows, not the best possible Hugo incremental server.

Every migration case has five measured edits; its first edit is compared against a forced full rebuild, outside timing. All five edits restore every original publication hash. Addition, rename and deletion pass incremental/full equivalence in both projects, including body/anchor/TOC/literal syntax, navigation, download, sitemap and search, plus retirement of previous outputs. Tracking history is left to pipeline reconciliation; a test-fixture restoration-order error was corrected before acceptance.

Fresh builds use full-history local committed checkouts, empty application state/output, prepared binaries/Node dependencies and the verified Python environment. All ten migration fresh publications are byte-identical to accepted output; all five native Hugo fresh publications verify route/download/search counts. OS caches are uncontrolled: **application-cold, not OS-cold**. Warm full migration runs force all compilation/composition/export stages; Hugo full runs use fresh destinations with warm resource/application caches.

Builds run serially with no parallel build or browser capture from this experiment. Existing user desktop processes/services remain; host load observations are recorded in environment.json, and ranges expose observed variability. These are not CPU-isolated dedicated-host samples. Nift configuration is build-threads=-1, incremental-mode=modified, native minify-exts=[]; human minification is its separately timed standalone pinned Hugo-equivalent minifier. RSS values are GNU time process/phase maxima, not aggregate concurrent memory.

The native Hugo reproduction is not an Alpine/BuildKit deployment measurement. Inputs/tool versions/provenance are in c6/environment.json and BASELINE.md. Maintained compiled frontend assets are copied by both migrations; changing the upstream asset toolchain is a separate maintenance task. Routine migration builds are offline. Dependency install/Go compilation/clone/hash validation are excluded from build timings.

Reproduce with benchmarks/run.py, benchmarks/fresh.py, benchmarks/routes.py, benchmarks/changed.py and benchmarks/hugo-changed.py, sequentially. One incomplete Hugo attempt is excluded after /tmp quota exhaustion in upstream flatten tests. The task-owned Go download cache was relocated and subsequent upstream test temporaries use .cache/benchmark-tmp; source inputs and production commands are unchanged. Four successful one-page samples precede that temporary-directory change, and the recovered fifth plus later cases use it. Raw time/log files stay in the sibling docker-baseline/c6 evidence directory; compact samples and summaries are committed under investigation/c6. Do not run these scripts concurrently or change renderer/publication inputs during measurements.
