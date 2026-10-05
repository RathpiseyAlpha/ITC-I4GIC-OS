# Second revision audit

The first revision shortened the labs into generic investigation summaries. That lost useful teaching structure from the original source: objectives, an executable starting example, file trees, familiar task progression and concrete submission guidance. This revision rebuilds those structures in all 11 Markdown instructions and supplies procedural extension guides for the wider original scope.

The core remains an individual 120-minute route. The table maps the original tasks to the current core/extensions; it does not claim that every original task is required within two hours. The original instructions remain in Git history at `source/main` (`b7cc507f93759d2db65af2dff5a23a86c7d19eb0`). Existing lecture notes, visual guides and challenges remain references and may describe the older broader route.

| Lab | Original structure retained in core | Wider scope with optional procedures | Concrete evidence and correction |
|---|---|---|---|
| 1 | OS identification, file-command warm-up, program/process and multitasking tasks | APT inspection; install/remove only in disposable VM; virtualization and top/ps | Kernel/distribution record; two live/finished PID observations; late samples are not proof of no process |
| 2 | TechCorp navigation, company tree, absolute/relative paths, move/copy and directory audit | Read-only system directories, expanded company folders, hidden files and listing orders | Quoted quarterly filenames, Finance/archive layout, cmp and changed-directory diagnosis |
| 3 | Wildcards, hard/symbolic links, rename/repair and changed target name | Complete user-local shared-library build/load; VM GRUB configuration, transient fault and snapshot recovery | Inode/target-path records; internal and dangling links supported by lifecycle helper, escaping links refused |
| 4 | Redirection, pipeline stages and CSV data analysis | Redirection order, bounded owned signals, orphan/zombie observation | Totals 8/0/15, missing-input status; simple CSV scope explicit |
| 5 | Guided pthread example, two-worker investigation and shared-update trace | fork versus thread memory, LWP/kernel-worker inspection, safe signal-handler design | Check create/join return codes; join both before result reads; delay and join do not provide mutual exclusion |
| 6 | File/directory rwx and octal modes, private-record/notice policy | Account/group inspection, narrow prepared ACL/group test, VM special-bit exercise | Owner access and directory-search denial/restoration; private parent prevents an empirical public-notice claim |
| 7 | Bash argument guide, direct execution/shebang, reusable personal command | Session PATH, login preview, owned outbox/harvester, prepared peer delivery | Spaces, actual leading-dash operand and aggregate missing-input status; no privileged shell helper |
| 8 | Quantum Widget engine, naive race, full critical-section repair and tests | Quantity conservation, invalid-state test, narrow drop box and owned log handling | At most two buyers; stock plus sold units checked; nonnegative stock alone is insufficient |
| 9 | Quantum Vault locks, naive/local deadlock, ordering, timeout and cleanup levels | Resource graph, isolated missing participant, optional prepared partner vault | Coordinated first holdings; at least one second-lock timeout; ordered mode excludes the barrier |
| 10 | Archive/compress/restore, backup/retention and environment trap | Actual backup cron entry, health report and restore capstone | Keep three recognized archives, preserve unrelated names, restricted environment; heartbeat versus backup scheduling explicit |
| 11 bonus | Storage inventory, sparse/full images and metadata | Capability-dependent FUSE, unmounted owned-image check/grow, diagnostic utility | Owned regular destinations, bounded sizes; illustrative header labeled when tools are unavailable; bonus status retained |

Every route now includes three observable core objectives, prerequisites/tool checks, explicit `start` then `cd`, numbered guided commands, a starting tree, prediction before investigation, constrained implementation tasks, progressive hints, normal/edge tests, an independent checkpoint, a submission tree and a topic rubric. Reports name the actual artifacts. Instructor plans align with the new questions, observations, misconceptions and keys, with public complete model files where useful.

The ambiguous account wording has been replaced throughout the teaching routes with **shared Ubuntu server with an individual account for each student**. The shared server is the machine; accounts, workspaces and submissions are individual.

`tools/build_lab_revision.py` now maintains only `labs/INDEX.md`. It cannot overwrite teaching prose. Static checks and executable walkthrough checks are separate; see [validation](VALIDATION.md) for their limits. The revision targets `origin/main`; no server deployment was performed.
