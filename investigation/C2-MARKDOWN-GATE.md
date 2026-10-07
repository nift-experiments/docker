> Historical investigation: the user approved the external Goldmark/Chroma architecture on 7 October 2026. See C2-ARCHITECTURE.md for the implemented bounded proof; no approval pause remains.

# C2 native Markdown parity gate — incomplete checkpoint

C1 is completed and pushed. C2 has bounded renderer/composition evidence, but shared-chrome/page-family migration is not complete. C3–C7 have not started. There are no final performance results or migrated corpus claims.

## Demonstrated installed behavior

The fixture uses Docker's actual `Lifecycle stage` heading and table from `content/manuals/release-lifecycle.md`, pinned at `6cf1b1c167f032e8a6629da211602300b623b20e`. Installed Nift 4.7.2 successfully builds `@markup(md, "content/docker-table.md")`, but its output contains a paragraph of literal pipe-delimited rows and `<h2>Lifecycle stage</h2>` without `id="lifecycle-stage"`. This changes the visual/semantic table and breaks the heading-anchor contract. A third `extended` argument is rejected: `markup: file syntax is @markup(format, path)`. This is a demonstrated limitation of the direct native path, not a failed upstream build.

Separately, `@input` on minimal existing Chroma-style HTML turns `<span class="k">` inside `<pre><code>` into `&lt;span...`, displaying markup rather than highlighted code. A synthetic recognized `@input(...)` inside a Markdown code fence is evaluated and fails for a missing file. That synthetic case is a boundary test, not an assertion that Docker currently contains that exact example. Docker's real device-mapper `$[ $(...) ]` console sample **does pass** the native probe unchanged; do not claim all shell sigils are corrupted.

All fixtures, source provenance, exact Nift directives, exit codes, output hashes and logs are in `markdown-probe/`. Reproduce with `python3 scripts/probe-markdown.py OUTPUT_DIRECTORY`; it creates only a temporary Nift project. It neither alters the migration starter nor Nift.

## Workarounds assessed

A minimal standalone Goldmark 1.8.2 program (the version recorded in the preserved Hugo executable's build information) with GFM/footnotes, automatic heading IDs, attributes and raw HTML enabled renders the actual table as a table and adds the expected heading ID. It also preserves the code sample and treats the synthetic `@input` as code. This proves a plausible migration-side renderer exists; it does **not** prove complete Docker/Goldmark/Hugo fidelity. The source and Go module/checksum are committed. Reproduce using `bash scripts/probe-goldmark.sh OUTPUT_DIRECTORY`; its dependency/cache/bootstrap work is explicitly separate from benchmark phases. No Hugo invocation is needed by this narrow program.

Nift raw composition can preserve already-rendered HTML exactly without parsing the HTML as template syntax:

```nift
@dep("content/highlight.html")@script {
  f := file("content/highlight.html"); f.open();
  value := f.read_all(); f.close(); return value;
}
```

The probe preserved every byte, including spans and literal sigils. Editing the raw source invalidated the dependency; incremental output changed and equaled a full build. This is a reasonable solution for `docker-agent` and for transient renderer output in `docker`; it does not require a Nift change. Explicit dependencies are necessary for this emission path. Maintained sources can remain ordinary HTML, rather than JSON-encoded HTML or escaped copies of every code example.

## Proposed architecture requiring a decision

For `docker`: retain authored Markdown/frontmatter/source organization; parse Docker shortcode/include semantics in a bounded compatibility layer; render with standalone Goldmark plus Chroma and Docker's seven render hooks; compose transient HTML through Nift shared templates with explicit dependencies; generate synchronized Markdown/LLM/search/metadata/redirect outputs. Nift remains unmodified. Measure Markdown conversion, Nift composition and publication/search separately and together. Do not describe this as native `@markup` performance.

For `docker-agent`: maintain rendered HTML directly; use the demonstrated raw-composition/dependency path; no Markdown renderer in routine builds. Its authoring model stays distinct.

The additional compatibility renderer is substantial: the lexical source inventory finds 2,022 shortcode openings across 449 authored files, including 282 tabs, 565 tab children and 86 includes. 231 authored and 175 vendored files contain table candidates. These are lexical candidates, not validated semantic counts; examples/comments and inline shortcode definitions must be parsed correctly. Docker also has seven render hooks, Git-derived metadata, generated adapters, mount/ref resolution and context-dependent rendering. Simple replacements or a plain standalone Goldmark call cannot establish full parity. Retaining Hugo as the routine renderer would undermine the intended framework comparison; freezing generated HTML as `docker` source would violate its maintained-Markdown requirement.

## Why this line is stopped

The user instructed: “If a real blocker is encountered” prove it, assess a reasonable migration workaround, document it in HANDOVER, “stop that affected line of work,” and report before touching Nift. The user also requested immediate reporting for Nift-change questions and major architectural compromises. The direct native renderer has a reproducible parity blocker. Switching the conventional version to a dedicated Docker compatibility compiler is my interpretation of a substantial architecture decision that warrants that report, rather than an automatic authorization to enhance Nift.

The affected direct-native `docker` renderer line is stopped. The paired C2 campaign remains incomplete pending the choice of external compatibility compilation versus separately considering native capability work. Markdown maintenance has not been proven fundamentally impossible; overall Nift core modification has not been proven necessary. The narrow external workaround is viable, and raw HTML composition is proven. No Nift, library or installation changes were made. Both repositories retain the full C1 contract and the same decision evidence; neither has been normalized to the other's content model.
