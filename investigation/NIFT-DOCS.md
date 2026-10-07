# Nift documentation reviewed

Reviewed live documentation overview, initialization, paths and JSON via nift.dev; reviewed local website source for pages the web fetcher could not retrieve, with live HTML snapshots retained in ../docker-baseline when available.

- https://nift.dev/docs/getting-started.html — initialization and tracked content/template/output.
- https://nift.dev/docs/ai-agents.html — retain canonical handover and inspect project state.
- https://nift.dev/docs/templating.html — exactly one @content for templated pages, automatic @input dependencies, checked @path and literal sigil escaping.
- https://nift.dev/docs/paths.html — tracked identity and index routes; checked project-confined asset paths; URLs do not imply content dependencies.
- https://nift.dev/docs/project-structure.html — static assets directly in public by default.
- https://nift.dev/docs/tracked-json.html — documented metadata/extensions, optional template-less outputs.
- https://nift.dev/docs/frontmatter.html — inline/external YAML/JSON front matter, no merge precedence.
- https://nift.dev/docs/json.html — declaration/inject/validate forms and automatic source/schema dependencies. Generated guidance also documents @json; use the installed version's supported syntax.
- https://nift.dev/docs/dep.html and user-dependencies.html — explicit dependencies only for otherwise invisible inputs, with project-confined file/directory paths.
- https://nift.dev/docs/incremental-builds.html — modified/hash/hybrid, portable hash state, build --all versus updated build.
- https://nift.dev/docs/scripting.html — native scripting as an optional tool, not a reason to replace clear existing tools.

Project implications: preserve original authored semantic structure where useful, derive explicit route/content relationships, keep asset ownership clear, verify literal Docker examples, and test dependency correctness against full rebuilds before benchmarks. Do not invent schema fields or emulate all of Hugo.
