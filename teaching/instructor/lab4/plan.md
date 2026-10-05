# Instructor plan — OS Lab 4 — Linux I/O Redirection, Pipelines & Process Management (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Use redirection and pipelines while distinguishing stdout, stderr and exit status.
2. Filter and aggregate a CSV fixture, checking intermediate stages.
3. Diagnose incorrect selection/aggregation using normal and changed-input tests.

Original Tasks 1–3 redirection/pipelines/data analysis form the core. Tasks 4–5 process tools and orphan/zombie observations are extensions with bounded owned processes.

Read the [student instruction](../../../labs/lab4/lab4-instruction.md), [report template](../../../labs/lab4/README.md) and [optional extensions](../../../labs/lab4/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `grep`, `cut`, `awk`, `wc`, `printf`, `ps`, `sleep`. No student sudo or privileged execution of student code.
- Check grep/cut/awk availability. Prepare normal, no-match and extra-record fixtures; do not install a data-science stack.
- In an ordinary test account run `oslab doctor`, `oslab start lab4`, then `cd "$OSLAB_WORKSPACE/lab4"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Normal total is 8; no-ok is 0; changed total is 15; missing input is nonzero on stderr. Use the public report model below. The fixture is simple CSV, not a general quoted-field parser.

Public complete model: [report_solution.sh](report_solution.sh). Invoke with `bash report_solution.sh /absolute/path/to/events.csv`; test normal 8, no-match 0, changed 15 and missing-input failure.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: The original fixture gains `ok,7` and `fail,20`. Predict the report total. A student uses `wc -l` after filtering; identify why their answer would measure a different quantity.

Key: New total is 15 (3+5+7); fail,20 is excluded. wc -l counts matching records (three), not the sum of their second fields. Accept a staged pipeline or an exact first-field awk filter.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students count rows, keep the first value, match not-ok as ok, or confuse stderr with pipeline input. Inspect the selected records and numeric field before aggregation.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

The core creates no background job. Finish any owned-process extension with its captured `wait` and keep selected evidence. Do not kill processes by name.

After evidence is saved, `oslab clean lab4` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct report selection/aggregation and clear stdout/stderr handling (objectives 1–3) | 3 |
| No-match, changed-count and missing-input diagnosis | 2 |
| Explain each pipeline stage and the claim each test supports; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
