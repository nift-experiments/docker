# C5: whole-corpus and browser acceptance

Both projects pass the full 3,901-document comparison for title, metadata attributes, links, asset references, IDs, hrefs and parsed structured data. All 2,170 content pages retain the reference text, headings, links and images. Every non-Pagefind publication path and owned asset hash matches the pin; regenerated downloads, JSON, discovery files and XML pass the C4 publication checks.

Both projects pass 192 browser states: 24 families × desktop/mobile × light/dark/system-light/system-dark. All initial DOM observations match (heading text is compared after normal browser whitespace normalization). **All 192 initial viewport JPEGs in each project are pixel identical to the C1 reference.** The human CLI badge's final whitespace correction eliminated the last four small visual differences.

Corrected C1 behavior fixtures pass for keyboard search, selected tab panels, accordions, code copying, diagram keyboard behavior and Markdown copying. Theme cycling/system changes, Gordon open/Escape/focus, Markdown viewing, API filtering, API request copying and example/media controls pass in both viewports. Pagefind's generated input/hint IDs are intentionally randomized and are compared by role/attributes rather than their random suffixes. Download copy/view controls must return the current generated download's exact bytes/hash; the HTML-derived downloads have formatting differences from Hugo's Markdown exports. Every reference download code fence is preserved, with the documented XML container-whitespace equivalence, and required raw API contract fields are retained. The real Dockerfile footnotes are emitted as Markdown footnote references/definitions.

Fresh Pagefind indexes contain the same 2,142 routes and 31,268 distinct words. Every indexed page's words, word count, filters, metadata, anchors and anchor locations match. Agent fragments are identical; human fragments differ in 144 sentence separators inserted by Pagefind at HTML block boundaries. These punctuation differences are retained in evidence, not described as byte-identical indexes. Browser keyboard search returns the reference result count and behaves correctly.

The entire inherited audit issue data is identical, not merely its counts: 576 missing descriptions, 2,154 duplicate-ID observations, 80 missing fragments, four missing local targets, 54 empty metadata URLs and 38 absent redirect targets. These are upstream observations; the migration does not silently repair them.

## Boundaries and capture reproducibility

Remote scripts are inert fixtures and remote non-script requests are blocked before transmission. No feedback, telemetry or AI request is sent to Docker services. Remote Redoc completion, actual consent behavior and backend responses are not claimed as live end-to-end validation; their markup, references and local controls are preserved.

Chromium 151.0.7922.34 intermittently failed to commit a screenshot surface on the **untouched baseline** 404 page. A one-pixel viewport resize and immediate restoration before capture produced all eight baseline and migrated 404 states with the original viewport, HTTP 404 status, zero script errors and pixel-identical images. It changes no page content. Browser restarts per theme bound retained resources. Source edits/builds are excluded from accepted capture runs.

C5 corrected the auxiliary Gordon title placeholder, empty metadata attribute serialization, accordion ID trimming, CLI badge whitespace and retrieval footnotes. The compatibility layer remains corpus-driven; there is no general Hugo interpreter and no Nift modification.

Run `scripts/capture-reference.mjs` with the documented Playwright/Chromium environment, then `python3 scripts/test-browser.py`. Run `scripts/inventory.py`, `scripts/audit-baseline.py` and `scripts/test-site.py` for whole-site checks. Local evidence is under the sibling `docker-baseline/c5`; compact results and observation hashes are retained here. C6 measurements must run serially after closing browser work.
