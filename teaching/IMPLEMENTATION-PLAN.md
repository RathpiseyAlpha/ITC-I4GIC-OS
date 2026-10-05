# Second revision implementation record

1. Compared the current instructions with the source lab titles, objectives and task sequences, and the local revision brief. Documented the core/extension mapping in [the audit](REVISION-AUDIT.md).
2. Rewrote all 11 student instructions with explicit objectives, numbered starting examples, observations, workspace/submission trees, topic-specific tests, hints and completion criteria. Lab 11 remains optional bonus work.
3. Expanded all 11 optional guides into procedures that preserve original breadth, with capability requirements and cleanup. Rewrote the report templates and public instructor plans to match the new routes. Added complete public models for CSV reporting, joined workers, safe argument handling and bounded backup retention.
4. Added [environment setup](../labs/SETUP.md) and [the complete index](../labs/INDEX.md). Replaced the prose-overwriting generator with an index-only tool. Teaching prose is edited directly from now on.
5. Updated workspace inspection to support internal/dangling symbolic links, reject escaping links and detected mountpoints, and archive symlink entries without following them. Extended lifecycle checks accordingly. Bounded Lab 8 model inputs to match the student exercise.
6. Ran structural/link gates, Linux lifecycle/isolation tests and executable walkthrough/model checks. Results and outstanding teaching-server checks are in [validation](VALIDATION.md).

The source remote is `source` (`RathpiseyAlpha/ITC-OS-2026`), and the push destination is `origin` (`RathpiseyAlpha/ITC-I4GIC-OS`). The first revision was pushed as `1e72b5f`. This second revision targets `origin/main`; the server deployment runbook remains a separate administrator procedure.
