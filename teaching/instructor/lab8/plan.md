# Instructor plan — OS Lab 8 - Secure Bash Scripting, Race Conditions & File Locking (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Validate bounded purchase quantities and test rejection without changing stock.
2. Reproduce and explain a read-check-write race using stock plus logged sale quantities.
3. Protect the complete transaction with a bounded file lock and test the invariant.

Original Levels 0–2 warm-up/validation/logging introduce the store. Levels 3–4 exploit and lock repair are the required investigation. Cross-user permission/drop-zone/log-management levels are optional.

Read the [student instruction](../../../labs/lab8/lab8-instruction.md), [report template](../../../labs/lab8/README.md) and [optional extensions](../../../labs/lab8/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `bash`, `flock` (util-linux), `timeout`, `awk`. No student sudo or privileged execution of student code.
- Pretest flock semantics on the real filesystem (some network filesystems differ). Run only two buyers with owned files and timeout. The shell example does not offer crash-atomic stock-plus-log transactions.
- In an ordinary test account run `oslab doctor`, `oslab start lab8`, then `cd "$OSLAB_WORKSPACE/lab8"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Flawed two buyers of 4 against stock 5 can both log sold 4 while final stock is 1. Locked case accepts exactly one, rejects the other and leaves 1. Invalid quantity fails without a sale; held lock gives bounded timeout. Models use STORE QTY rather than the student QTY-only wrapper.

Public [flawed model](buy_flawed.sh) and [full-lock model](buy_solution.sh) take `STORE QTY`. Use a fresh owned store, reset test stock to 5 between cases, and run at most two buyers under `timeout 5`; wait for both saved PIDs. Expect the full-lock section to cover stock validation/read/check/write and log append, not just the last writes.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: Stock is 3 and two buyers request 2 each. Under correct transaction locking, predict how many purchases are accepted, final stock, and total logged units. Explain why nonnegative stock alone is an insufficient test.

Key: Exactly one purchase of 2 is accepted from stock 3, leaving 1 and logging 2 sold units. Check initial stock = final stock + accepted sold units, not log line count or nonnegativity alone. Locking only the write leaves a stale read/check outside the critical section; all cooperating writers must lock before read through log append.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students count transactions as units, lock only printf, delete lock files, or claim a single good run proves correctness. Draw the full read-check-write-log critical section and check conservation.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

Wait for only the two captured buyer jobs to finish. Save both test records, then leave lock/data files for review. Never delete an active lock file or kill unrelated processes.

After evidence is saved, `oslab clean lab8` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Validated purchase behavior and full transaction lock (objectives 1–3) | 3 |
| Flawed/locked concurrency and invalid-input evidence | 2 |
| Explain stale reads, lock scope and the units-sold inventory invariant; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
