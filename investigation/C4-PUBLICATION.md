# C4: complete route composition and publication

The human project maintains the pinned Markdown/frontmatter/organization. Its bounded standalone Goldmark/Chroma stage renders transient bodies; Nift composes those bodies with maintained shared HTML layouts through literal raw returns and explicit dependencies. The agent project maintains rendered bodies in `pages/`; its routine build contains no Markdown parser, renderer, Hugo evaluator, or Go compiler. HTML-to-Markdown downloads are a separate publication transformation in both projects.

All 3,901 HTML routes are tracked by Nift: 2,170 content pages, 1,728 aliases, the 404 page, and two verification files. The ordinary corpus is joined by 539 typed YAML CLI pages, 452 typed API adapter pages, and the real landing/glossary/sample/series/legacy families. The API model and YAML mounts are upstream maintained inputs in the human project. Their generated HTML is maintained directly in the agent project.

The old per-page shell copies were replaced by 323 maintained shared templates (about 4.6 MB of payload). `data/chrome.json` holds explicit per-route bindings and slot associations. Navigation uses 1,688 typed nodes, with a small API navigation model. This is Docker presentation data, not a general template interpreter. HEAD, breadcrumbs, page titles, TOCs, navigation, and API navigation have bounded typed update paths. Preserved scalar metadata includes pinned Git dates and inherited upstream defects; it does not promise generic Hugo semantics for future frontmatter fields.

`data/composition.json` is the explicit route/family manifest. `publication/ownership.py` reconciles it with Nift tracking and retires previously owned HTML/wrappers after route removal. Maintained source bodies/layouts are never deleted by a build. Page additions/renames must update the manifest, route metadata and shell bindings together; these are intentionally explicit migration data, rather than a general Hugo page-discovery implementation.

Publication regenerates 2,170 Markdown downloads, metadata, redirects, sitemap, security RSS, robots, `llms.txt`, `llms-full.txt`, and Pagefind. All 294 owned asset paths/hashes match the pinned output. Search uses pinned Pagefind 1.5.2 and the original exclusion configuration. Search is rebuilt into a fresh owned directory; stale chunks are retired. The RSS generator identifies this migration, while the remaining XML structure preserves the pin.

Download generation protects fenced payloads against list/quote whitespace transformations. Export-only HTML attributes retain source alert markers, ASCII diagrams and whitespace absent from rendered copy payloads. API operation templates retain the normalized contract fields required by Docker's Markdown download template in an inert HTML template attribute. Agents maintain these alongside the visible HTML/raw operation contract. No maintained Markdown source or Markdown parsing is introduced into agent builds. One XML fence is validated by its full XML tree/scalar values because Markdown container indentation expands preserved tabs differently.

Standalone HTML/CSS/JS/SVG minification uses the versions pinned by the upstream Hugo binary; it is measured separately, not treated as Markdown or Nift work. Agent bodies are already rendered/minified and avoid this normal publication transformation.

## Validation

- All 2,170 full-page content comparisons pass for text, headings, links and images.
- All 539 CLI and 452 API typed-family fixtures pass; all 46 special fixtures pass.
- All 1,604 ordinary navigation comparisons pass.
- Whole-publication path, JSON, discovery text, XML and asset checks pass, including every reference download fence (with the documented XML whitespace comparison).
- Changed-source and shared-layout tests compare every output hash after incremental versus forced-full publication, then verify exact restoration.
- Browser validation is C5. A browser-only 404 shell placeholder and file-browser wrapper mismatch were caught during preparation and corrected before acceptance.

## Reproduce

Run `python3 scripts/build.py --setup` once, separately from measured production work. Run `python3 scripts/build.py --all` for forced full publication or omit `--all` for changed-input publication. Human setup compiles its pinned standalone binaries; agent setup installs only pinned Pagefind. Routine builds run offline.

Run `python3 scripts/test-publication.py`, `python3 scripts/test-content.py` (human utility accepts the agent root), and `python3 scripts/test-dependencies.py`. Fixture migration/bootstrap scripts are one-time provenance tools, not normal build stages. Complete component metrics are written to `.generated/build-report.json`; final repeated measurements are C6. None of these timings is native `@markup` performance.

Nift core, libraries and installation are unchanged. No corpus feature outside the observed requirements was implemented for completeness.
