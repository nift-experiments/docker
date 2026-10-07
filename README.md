# docker: Docker Docs migration experiment

Faithful reconstruction of Docker Docs pinned at `6cf1b1c167f032e8a6629da211602300b623b20e`. Nift itself is unchanged.

Source model: maintained Markdown/frontmatter and structured CLI/API data → bounded Docker compatibility renderer → transient HTML → Nift composition → minification/publication/search.

## Build

Prerequisites: Python (tested 3.14.4) with PyYAML (tested 6.0.3), Go (tested 1.26.0) for initial renderer/minifier setup, Nift 4.7.2, and Node/npm (tested 24.21.0/11.19.0). Parallel HTML analysis uses POSIX fork. Install tools/dependencies before measuring builds:

```sh
python3 scripts/build.py --setup
python3 scripts/build.py --all
python3 scripts/build.py
nift status
```

Use `scripts/build.py` as the publication entry point: it prepares explicit Nift dependencies, downloads, metadata, feeds, redirects and fresh Pagefind search. Direct `nift build` only composes already-prepared fragments. Output is `public/`; `.generated/` and `.cache/` are disposable application state, while `.nift/` is maintained tracking/configuration.

Edit original Markdown/frontmatter under `authored/`, keeping Docker source organization. The compatibility layer implements only behavior used by the pinned corpus; unfamiliar features need real source/page fixtures. CLI YAML and API JSON remain structured source. This is not a native `@markup` performance measurement.

Shared layouts live under `layouts/`; navigation and publication bindings live under `data/`. Route additions/renames/deletions require the corresponding maintained registry/metadata/navigation changes. The lifecycle harness demonstrates these operations, including retirement of old outputs. Compiled frontend assets are maintained upstream assets, preserving accepted interactions.

## Evidence

See [HANDOVER.md](HANDOVER.md), [baseline provenance](investigation/BASELINE.md), [initial C6 benchmarks](investigation/C6-BENCHMARKS.md), and [C6 optimization](investigation/C6-OPTIMIZATION.md). See [the final C7 comparison](investigation/C7-COMPARISON.md) for initial versus optimized timings, correctness and maintenance recommendations. Initial evidence is immutable; reruns must use a new evidence output directory.
