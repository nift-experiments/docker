# C2 architecture proof

The user approved the standalone Goldmark/Chroma architecture on 7 October 2026. The historical native Markdown investigation remains in C2-MARKDOWN-GATE.md; it does not require a further approval pause.

`docker`: maintained Markdown/frontmatter → bounded Docker compatibility renderer → transient HTML → Nift raw composition. Goldmark 1.8.2 and Chroma 2.24.1 match the pinned Hugo binary's dependencies. The renderer has seven Docker hook categories and only currently proven shortcode behavior: param, include, tabs/tab. Other corpus features fail explicitly until backed by a real fixture. It contains no Hugo template interpreter. Heading normalization adapts the pinned Apache-licensed Hugo GitHub-ID routine; third-party licenses are retained in compatibility/licenses.

`docker-agent`: maintained HTML → Nift raw composition. Its normal build uses Python's standard library and Nift, with no Markdown renderer, Go worker or conversion stage.

Both projects compose eight prototype routes from 47 exact shared shell subtrees. Extraction admits only shell subtrees of at least 1,024 characters shared by at least two distinct documents. Bodies are excluded from shared-shell candidates. Raw HTML is emitted by a scoped template helper with explicit @dep dependencies. It preserves literal Nift/template syntax and highlighted spans without reparsing.

Five real Docker source fixtures pass heading IDs/text, tables, code clipboard payloads, exact Chroma leaf-token streams, tabs, images, Mermaid, alerts and normalized content references. Ubuntu exercises tabs, four include uses and seven params; the device-mapper fixture exercises mounted content references and literal $[ syntax. Detailed results and dependency evidence are in c2/*.json.gz.

Browser proof covers home, Ubuntu, CLI run, API createPolicy and Mermaid MCP: 40 states per project, desktop/mobile and light/dark/system themes. All recorded initial DOM properties match the frozen C1 states, including body size, heading/navigation state, tabs and diagrams. No JavaScript errors. Remote services are inert/blocked as in C1. Full browser captures remain under ../docker-baseline/c2/browser-*-final. Earlier captures exposed omitted stylesheet publication; final evidence includes root and API stylesheets. This is partial-site evidence, not whole-site acceptance.

Reversible page and shared-partial edits changed their expected output sets, and incremental output hashes equalled forced-full hashes in both projects. Source/output bytes were restored. Asset publication compares bytes, including same-size replacements.

## Reproduce

For docker, install the Python PyYAML/lxml migration/test dependencies and run `python3 scripts/build.py --setup` once; Go module downloads/compiler setup are excluded from routine timings. Run `python3 scripts/build.py --all`, then `python3 scripts/test-compatibility.py OUT .cache/docker-renderer`. The test reads the preserved pinned sibling source/site. The agent normal build is `python3 scripts/build.py --all`. `nift status` verifies the resulting tracked outputs. Generated wrappers, renderer bodies, caches and public output are ignored; maintained source/assets are committed.

## Outstanding obligations

Home/CLI/API bodies in docker remain explicitly labelled generated-family prototypes; C4 must replace this scaffold with maintainable data/layout generation. Search and Markdown exports are frozen C2 fixtures, not regenerated output. C3 must cover all ordinary content/shortcodes; C4 must recover special families, ancillary outputs and publication; C5 must establish whole-site parity. Conditional assets, metadata, routes, search and synchronized exports need changed-input coverage before C6. Diagnostic component counters are not final benchmarks or native @markup measurements.

No Nift source, libraries or installation were modified. No confirmed core blocker.
