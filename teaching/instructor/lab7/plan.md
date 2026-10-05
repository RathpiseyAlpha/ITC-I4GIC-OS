# Instructor plan — OS Lab 7 — Bash Scripting, Permissions & Server Automation (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Create and invoke a Bash script with understood arguments and execution permissions.
2. Handle spaces, leading-dash filenames and missing input without unintended word splitting.
3. Test a reusable command and explain its exit status and safe filename handling.

Original Task 1 script basics and Task 2 command lookup introduce a safe personal automation command. Original Tasks 3–8 login/outbox/mailbox tasks remain extensions; SUID work is a prepared-VM concept activity.

Read the [student instruction](../../../labs/lab7/lab7-instruction.md), [report template](../../../labs/lab7/README.md) and [optional extensions](../../../labs/lab7/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `bash`, `wc`, `printf`, `chmod`, `cmp`. No student sudo or privileged execution of student code.
- Check both unusual fixture filenames and wc. Do not enable SUID or change startup files; optional delivery needs a prepared narrow drop box.
- In an ordinary test account run `oslab doctor`, `oslab start lab7`, then `cd "$OSLAB_WORKSPACE/lab7"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Normal counts are 2 and 1. Zero arguments gives usage/nonzero. Missing input reports an error, continues any valid remaining arguments, and ends nonzero. Preserve each quoted argument and label; equivalent formatting is acceptable.

Public complete model: [count_words_solution.sh](count_words_solution.sh). Invoke with the exact quoted fixture paths, then missing plus valid input, then from `input/` with `-dash.txt`. An error remains reflected in the final exit status.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: Current directory contains a file literally named `-dash.txt`. Explain why `wc -w -dash.txt` may be misinterpreted and give a safe command. Then explain why quoting alone does not end option parsing.

Key: Use wc -w -- "-dash.txt" or wc -w -- ./-dash.txt from the input directory. Quoting preserves one operand; -- terminates option parsing. An input/-dash.txt operand already has a non-dash prefix.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students fix spaces but overlook leading dashes, use for x in $@, or let the last successful count erase an earlier failure. Ask what each utility receives and inspect final aggregate status.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

No cron jobs or background processes are created. Leave personal PATH or shell startup changes to the optional extension; do not copy entire shell configuration into the submission.

After evidence is saved, `oslab clean lab7` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Safe arguments, correct counts and aggregate failure status (objectives 1–3) | 3 |
| Space/leading-dash/missing/empty input tests | 2 |
| Explain quoting, option boundaries, execution mode and status; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
