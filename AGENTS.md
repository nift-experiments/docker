# Agent instructions

Read HANDOVER.md before substantial work. It contains project checkpoints and the retained Nift initialization guidance. Read investigation/BASELINE.md and machine-readable inventories before assuming routes or page counts.

- Maintain upstream authored Markdown wherever practical, preserving editorial structure and human-maintainable front matter. Render Markdown through Nift shared layouts.
- Report the different authoring models and transformation costs explicitly in the final comparison.
- This checkpoint authorizes setup and investigation only. Await the next migration instruction before migrating the corpus.
- Do not modify Nift, its libraries, or its installation. Confirm and document a real blocker, stop that line of work, and report it.
- Do not alter upstream source to simplify migration. Preserve ../docker-upstream and ../docker-baseline and all baseline artifacts.
- Never delete/replace .git, rewrite history, destructively clean repositories, or tag releases.
- Commit bounded checkpoints, verify tracked changes, push normal checkpoints, and leave a clean working tree.
- Run nift build after configuration edits and meaningful source changes; finish with nift build and nift status.
- Track every generated route and ancillary output. Validate the full corpus; representative screenshots alone cannot establish completion.
- Benchmark equal output obligations, including assets, search, Markdown, metadata, redirects and feeds. Separate renderer-only measurements from complete publication pipelines.
- Preserve Docker's Apache-2.0 license and attribution when copying reference material.
- Do not send feedback, analytics events, or chat prompts to Docker services during automated validation. Use deterministic fixtures for remote behavior and report the limitation.
