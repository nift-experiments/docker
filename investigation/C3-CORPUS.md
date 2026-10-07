# C3 ordinary corpus

The bounded renderer accepts all 1,187 mapped maintained Markdown sources. This includes ordinary pages plus landing/sample/glossary inputs and navigation-only stubs; it is not a count of completed publication pages. The C3 publication contains 1,012 ordinary Markdown pages and the three explicit C2 generated-family prototypes, for 1,015 Nift-tracked routes per project. Generated landing/sample/glossary families, CLI/API adapters, redirects, ancillary exports and fresh search remain C4 work.

All 1,012 ordinary pages pass heading IDs/text, visible table cells, exact decoded code clipboard payloads, Chroma leaf-token streams, tabs, zoom-image URLs/alt, Mermaid, alert titles and authored content links against the frozen production pages. Table comparison treats paragraph/line-break boundaries as visible spaces; byte-level text concatenation would incorrectly join words after production minification. The agent project's complete output bytes match the corresponding baseline on all 1,015 routes. Both full Nift builds and statuses pass.

Maintained human source preserves all 1,187 mapped files byte-for-byte, original frontmatter and the original content/vendor path organization. The original authored content tree and required pinned data are retained. The agent source remains HTML bodies; its routine builder has no Markdown imports/compiler. Shared chrome is extracted in two bounded-memory passes: 861 repeated-shell candidates, 294 maximal shared parts used. The retained C2 parts remain recoverable in history/source; publication uses the manifest's explicit paths. Body content is excluded from shared-shell extraction.

## Corpus-driven additions

Named Docker components are direct ports of pinned source templates, not a Go-template interpreter. Support now covers actual param/include/tabs, release dates, badges, inline images, grids/cards, accordions, experimental notices, buttons, labspace instructions, setting metadata, summary bars, section/recipe links, figures, interactive diagrams, Desktop download links, authentication selector, files/file browser and its Bash/PowerShell scaffold scripts, and the three specific inline definitions present in the corpus. The parameterless authentication component is maintained HTML with explicit Chroma slots.

Fence support is limited to observed title, collapse, highlighted lines and line-number options; GoAT permits the observed class attribute. GoAT 0.5.0 is the standalone library pinned by the Hugo binary and its diagram work belongs to compatibility cost, not Chroma. Unknown languages retain Docker's unhighlighted code behavior. Malformed attribute syntax is ignored as in the reference. Params under the frontmatter params map and whitespace after a YAML delimiter are handled without rewriting maintained source.

The indentation helper preserves spaces on blank lines inside tabbed code. Heading IDs use parsed visible text, excluding link destinations and decoding entities/escaped punctuation. Eight pre-existing shortcode-placeholder anchor IDs on the settings-reference page are retained as small explicit legacy-anchor metadata; newly authored heading names use normal IDs. This avoids inventing a general Hugo placeholder-ID system.

The guide's remote Dockerfile payload is pinned from the frozen clipboard output with URL/provenance. Routine builds do not refetch a mutable remote file. Ref resolution handles verified section/index aliases, globally unique basenames/titles, generated published-route aliases and normalized path traversal. It does not implement generic Hugo mounts or templates.

## Reproduce and limits

`python3 scripts/build.py --setup` prepares the human compiler separately from production timings. `python3 scripts/build.py --all` builds each project. `python3 scripts/test-corpus.py OUT .cache/docker-renderer` reads the preserved sibling baseline and validates the ordinary corpus. `scripts/bootstrap-c3.py` is one-time migration tooling and is never a build/benchmark stage.

C3 evidence is in c3/*.json.gz and build logs. Diagnostic counters exist for Markdown parse/render, Docker hooks, Chroma, compatibility preparation, Nift composition and asset publication. These are not final performance claims or native @markup timings. Search and existing Markdown exports remain frozen fixtures until C4. Metadata/navigation/TOC regeneration, family-specific pre/post-content controls and changed-input publication coverage must be completed before C5/C6. Semantic body checks do not establish whole-site browser parity.

No Nift modification or core blocker.
