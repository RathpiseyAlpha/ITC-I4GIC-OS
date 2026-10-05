# Instructor plan — OS Lab 9 - Vault Deadlock, Resource Ordering & Recovery (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Draw holdings and requests that form a circular wait.
2. Reproduce a coordinated two-worker conflict with bounded waits and interpret timeout recovery.
3. Apply one global lock order and explain why it removes the cycle.

Original Levels 1–3 workspace/naive scripts/local deadlock form the core, followed by Levels 5–6 ordering/timeout. Partner Level 4 is optional; Level 7 cleanup stays required.

Read the [student instruction](../../../labs/lab9/lab9-instruction.md), [report template](../../../labs/lab9/README.md) and [optional extensions](../../../labs/lab9/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `bash`, `flock`, `timeout`, `ps`. No student sudo or privileged execution of student code.
- Pretest two bounded workers, fresh readiness markers and flock. Confirm all held resources are on the same filesystem path/inode. No mandatory partner.
- In an ordinary test account run `oslab doctor`, `oslab start lab9`, then `cd "$OSLAB_WORKSPACE/lab9"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Opposite case logs both first holdings then at least one second-lock timeout. One timeout releases its first lock so the other may finish. Ordered mode has no rendezvous barrier and both complete. Model interface is VAULT ROLE MODE; students derive vault from their script path.

Public [worker model](worker_solution.sh) takes `VAULT A|B opposite|ordered`. Remove only `coord/A.ready` and `coord/B.ready` after both workers exit, before a new opposite-mode case. Bound each worker with `timeout 6`. Ordered mode must omit the rendezvous barrier.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: A third worker needs only Beta. Must it also acquire Alpha to follow the global-order policy? Explain. Separately, identify whether timeout is prevention or recovery in the opposite-order example.

Key: A worker needing only Beta does not need Alpha; order applies among resources actually requested. Opposite-mode timeout breaks an existing hold-and-wait cycle (recovery), whereas consistent alpha-before-beta ordering prevents this modeled cycle.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students expect both to timeout, retain a barrier in ordered mode, or remove a lock pathname while held. Explain release after exit and why the ordered barrier would itself block progress.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

Wait for the two captured workers; all waits are bounded. After both exit, remove only their two readiness markers. Leave lock files in place and never kill by a broad name match.

After evidence is saved, `oslab clean lab9` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Bounded conflict reproduction and consistent global ordering (objectives 1–3) | 3 |
| Opposite/ordered and missing-participant diagnosis | 2 |
| Explain circular wait, barrier role and timeout recovery; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
