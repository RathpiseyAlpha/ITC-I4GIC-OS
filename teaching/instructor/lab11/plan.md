# Instructor plan — OS Extra Lab 11 (Bonus) — Linux Disk Management Utilities (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Read filesystem capacity and per-file allocation without confusing `df`, `du` and apparent size.
2. Create a bounded sparse regular image and explain the difference between length and allocation.
3. Format/inspect only an owned regular image when tools exist, or interpret a supplied metadata trace with a stated limitation.

The whole lab remains optional bonus. Original Levels 0–3 inventory/usage/image/metadata form its two-hour route. Levels 4–7 mount/utility/maintenance/capstone remain optional extensions, with cleanup always required.

Read the [student instruction](../../../labs/lab11/lab11-instruction.md), [report template](../../../labs/lab11/README.md) and [optional extensions](../../../labs/lab11/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `truncate`, `stat`, `du`, `df`; `mkfs.ext4`, `dumpe2fs` for formatting; FUSE optional. No student sudo or privileged execution of student code.
- Check quota and mkfs/dumpe2fs. Core needs no FUSE/root. Bonus status must remain clear; any optional mount requires pretested unmount and cleanup verification.
- In an ordinary test account run `oslab doctor`, `oslab start lab11`, then `cd "$OSLAB_WORKSPACE/lab11"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
- Provide the actual server host, individual usernames, submission repository paths and any prepared optional directory. Installation takes place before the 120-minute class.
- Prepare one normal and one edge/failure observation below. Prepare a fresh private checkpoint of comparable scope; retain its key privately and collect answers before debrief.

## Exact 120-minute Timetable

| Minutes | Teacher action and evidence |
|---|---|
| 0–10 | State objectives, scenario and required artifacts; verify login, helper and working directory |
| 10–25 | Demonstrate the numbered guided commands; pause for the embedded observation questions |
| 25–35 | Capture original prediction before execution; optional peer comparison at most five minutes |
| 35–70 | Individual numbered investigation; circulate using topic hints; AI optional |
| 70–85 | Require normal and edge/failure cases; check claim, contradiction and test limits |
| 85–100 | Collect individual changed-case answer; no AI or peer help |
| 100–110 | Discuss key and anonymized misconceptions; students preserve and correct prediction |
| 110–120 | Confirm cleanup; copy selected artifacts and two records to personal course repository |

## Expected Results and Public Model

Both guided files have 8 MiB apparent length. Sparse allocation is normally smaller. Formatting the 32 MiB regular image adds metadata; block count×block size describes filesystem size. Supplied illustrative header analysis is valid only when labeled, not as a local format/mount test.

Use the student core command sequence on a fresh bounded regular image, recording stat before/after mkfs. If tools are missing, use the labeled illustrative header in the instruction. Its 32768 blocks × 1024 bytes = 32 MiB; 25830 free blocks is illustrative, not an expected universal value.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: Two files have equal apparent length. One was created sparsely with `truncate`; the other was fully written with zero bytes. Predict how their allocated blocks may differ and identify a command/field that checks your claim. Why is `df` insufficient to attribute usage to either file?

Key: Equal lengths need not imply equal allocation. Sparse holes can reduce allocated blocks; check stat blocks×block-unit or du. A fully written file may still be compressed/deduplicated by its host. df describes containing-filesystem capacity, not attribution to one file.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students equate df/du/ls, treat -F as a path safeguard, or format a device. Require the owned regular-file path, type and bounded size before formatting.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

The core creates no mount. If you completed a FUSE extension, unmount it and verify it is unmounted before cleanup; never recursively clean a mounted directory. Save evidence, then remove only your own demo/image files if reclaiming quota. No real devices or loop mounts are used.

After evidence is saved, `oslab clean lab11` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct bounded regular-image measurements and metadata interpretation (objectives 1–3) | 3 |
| Sparse/written and fresh/formatted comparisons, with capability limits | 2 |
| Explain df versus du versus length and filesystem metadata; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit. The entire lab is bonus and skipping it carries no penalty.
