# Instructor plan — OS Lab 5 — Threads, Kernel Workers & Process Signals (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Create POSIX threads and check API return codes.
2. Join each worker before consuming its result and explain shared versus separate address spaces.
3. Use a bounded execution trace to diagnose missing completion synchronization.

Original Task 1 processes/threads introduces memory ownership; Task 2 thread interaction and joining is the core. Task 3 kernel mapping and Task 4 signals remain extensions.

Read the [student instruction](../../../labs/lab5/lab5-instruction.md), [report template](../../../labs/lab5/README.md) and [optional extensions](../../../labs/lab5/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `gcc` with pthread support, `timeout`, `ps`; instructor provides trace fallback if compiler is unavailable. No student sudo or privileged execution of student code.
- Confirm gcc -pthread and timeout before class. Without a compiler, supply the annotated source/trace for diagnosis and mark executable implementation as unverified.
- In an ordinary test account run `oslab doctor`, `oslab start lab5`, then `cd "$OSLAB_WORKSPACE/lab5"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Guided worker produces 42 after join. Joined A (id 2, three steps) gives 6; B (id 3, four steps) gives 12, then B with two steps gives 6. A zero-step worker produces 0 and still needs a join. Print order may vary; accept no deterministic ordering claim.

Public complete model: [two_workers_solution.c](two_workers_solution.c). Compile `gcc -Wall -Wextra -Werror -pthread two_workers_solution.c -o /tmp/YOUR_OWN_UNIQUE_OUTPUT` in an owned temporary directory; run with `timeout 5`. Edit B steps to 2 and then 0 for changed tests. The model joins any already-created threads even if a later create fails.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: Main joins worker A but not worker B, then reads B’s result. Explain what remains unestablished and identify the minimal synchronization change. Would that change alone protect a counter updated concurrently by both workers?

Key: Joining A does not establish B completion; join B before reading B.result. A quick observed finish cannot replace the synchronization guarantee. Workers owning separate result fields avoid a shared-counter race in this core.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students assume sleep or a successful run ensures completion, read B early, or report errno for pthread calls. Check their direct return codes and exactly which joins occur before reads.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

All core executions use a five-second timeout and joined workers; confirm the executable ended. Copy source, not binaries, into the submission. Kernel workers are observed only, never signalled.

After evidence is saved, `oslab clean lab5` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct worker creation, joins and result use (objectives 1–3) | 3 |
| Normal and changed-step/zero-step evidence with build diagnosis | 2 |
| Explain thread memory, completion and mutual-exclusion differences; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
