# C1 frozen parity contract

The pinned native production output remains the primary reference. `parity/contract.json` defines acceptance, counts, browser fixtures and remote boundaries. All 8,622 files retain their complete hashes in the C0 inventory. No migrated output exists yet.

## Browser evidence

24 representative families × two viewport sizes × four explicit/system theme states = 192 initial-view screenshots. All returned expected HTTP status (404 for the missing-route fixture) and zero JavaScript page errors. Chromium 151.0.7922.34; Playwright 1.62.1. Screenshots were inspected for representative desktop API/diagram and mobile dark documentation layouts. Full images are preserved in the checksum-recorded local archive; all image hashes and DOM observations are committed. This is a reference capture, not a claim of migrated visual parity.

`parity/behavior.json.gz` supersedes the main capture's premature search-result wait. It records 12 focused runs: search shortcut/input/results/Escape/focus; mobile sidebar Menu/Back; synchronized tabs; accordion visibility; exact Markdown and code clipboard hashes; interactive-diagram keyboard step changes. Search successfully loads matching links. Link counts while lazy results load are not a stable search-result equality assertion. Inherited search Escape restores an element with no ID; preserve/test actual focus semantics rather than asserting a fabricated trigger ID.

`parity/controls.json` records theme light→dark→automatic and OS theme response, Gordon drawer/input focus/Escape, desktop Markdown popup and export bytes, API filtering, clipboard requests and example/media selection on both viewport sizes. The Markdown toolbar is absent in the mobile layout, recorded as inapplicable rather than an error. Remote requests are intercepted before transmission, including blocked analytics POSTs. No chat questions or feedback were sent.

API schema and legacy Engine API fixtures supplement the main 22 families. Legacy Redoc is a remote rendering boundary: its CDN script is inert in these captures, so these images alone cannot prove the remote renderer's completed content. Keep its URLs/configuration and specification downloads; use a deterministic renderer/service fixture for later functional validation. Remote consent and media embeds have the same explicit boundary. Gordon local drawer behavior is measured; streamed service response parity remains a mocked C5 obligation.

## Whole-output audit

1,388,674 deduplicated per-page references, including 1,344,794 internal references, were examined. CSS URLs, XML sitemap/RSS, metadata records, redirect chains, Markdown/LLM/search publication entry points and page metadata were included. Counts remain separate: 2,170 content pages, one 404, two verification documents, 1,728 HTML aliases, 2,510 redirect rules, 2,170 Markdown exports, 2,142 searchable pages and 11 noindex documents.

Inherited observations: 576 missing descriptions; 2,154 documents with duplicate `gordon-tooltip` IDs; 80 statically missing fragments (some legacy API anchors are created at runtime); four missing internal targets; 38 redirects whose final targets are absent; 54 navigation metadata records with empty URLs. There are no detected missing titles/canonicals, redirect cycles, missing local CSS assets or invalid audited XML files. Empty metadata URLs are navigation-only records, not necessarily broken pages. The four missing local targets are two old Engine API version links and two Grafana image links. The complete issue records are committed, with no upstream edits or silent repairs.

## Reproduction and gates

Run `scripts/serve-reference.mjs SITE PORT`, then `scripts/capture-reference.mjs OUTPUT`, `scripts/capture-controls.mjs OUTPUT.json` and `scripts/audit-baseline.py SITE INVENTORY OUTPUT`. Browser scripts use `PLAYWRIGHT_MODULE_ROOT` and `CHROMIUM_PATH` to select an existing Playwright installation/browser; no package installation is hidden in the measurements. `REFERENCE_ORIGIN`, `FIXTURES` and `ONLY_BEHAVIORS` select a local server or focused recapture.

C2 must first demonstrate authored Markdown/table/anchor/code fidelity and safe literal template sigils, then shared shells across representative families. C3–C5 must satisfy complete-corpus acceptance as well as these browser fixtures. C6 must establish fresh-checkout and changed-input correctness before any final benchmark claims. These requirements cannot be reduced for speed. Native baseline/container and toolchain caveats remain in BASELINE.md.
