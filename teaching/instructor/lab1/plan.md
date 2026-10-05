# Instructor plan — OS Lab 1 — Introduction to Operating Systems (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Identify the distribution and running kernel using command output, explaining the difference.
2. Create and inspect files in an owned directory using basic Linux commands.
3. Start two instances of one program and distinguish their PIDs, parent PID, state and lifetime.

Core: Task 1 OS identification, a short Task 2 file warm-up, and Tasks 4–5 program/process investigation. Original Task 3 package changes and Task 6 virtualization work are extensions.

Read the [student instruction](../../../labs/lab1/lab1-instruction.md), [report template](../../../labs/lab1/README.md) and [optional extensions](../../../labs/lab1/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `bash`, `uname`, `cat`, `ps`, `sleep`, `find`. No student sudo or privileged execution of student code.
- Check login, ps and sleep. No compiler or package install is needed. Prepare one live/finished transcript for an outage.
- In an ordinary test account run `oslab doctor`, `oslab start lab1`, then `cd "$OSLAB_WORKSPACE/lab1"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Distribution comes from /etc/os-release; uname describes the running kernel. Live sleep processes have different PIDs, normally the same shell PPID, and disappear after wait. Accept output differences due to WSL/container kernels.

```bash
sleep 10 & a=$!
sleep 10 & b=$!
ps -o pid,ppid,stat,comm -p "$a,$b"
wait "$a"; wait "$b"
ps -o pid,stat,comm -p "$a,$b"
```
The final `ps` can return nonzero because neither process exists.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: A shell starts two `sleep 1` commands in the background and captures both `$!` values. It waits two seconds before running `ps`. Predict the captured PID values relative to one another and whether `ps` must still show the processes.

Key: Two distinct PIDs are captured for the two live instances (barring PID reuse after an already exited process). After the delay ps may show neither: the jobs are only one second long. The captured IDs establish creation; a late sample does not reconstruct lifetime.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students mistake a program name for identity or an empty ps result for never having run. Ask them to compare $! immediately with a delayed sample.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

Confirm both captured jobs finished with `wait`. Keep the workspace until your evidence is saved. If you stop a demonstration early, signal only the PID you captured in this shell, immediately verify its identity, and wait for it; otherwise let the bounded sleep end normally.

After evidence is saved, `oslab clean lab1` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| OS/kernel identification and two owned-process observations (objectives 1–3) | 3 |
| Live/finished and short-duration tests, with timing diagnosis | 2 |
| Explain executable versus instance, PID/PPID and sampled state; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
