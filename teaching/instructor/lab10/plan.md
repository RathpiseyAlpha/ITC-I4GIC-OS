# Instructor plan — OS Lab 10 - Backups, Archiving, Scheduling & cron Automation (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Create/list/restore a project archive and distinguish archiving from compression.
2. Implement bounded retention for only the lab-owned completed archives.
3. Run the script with a restricted environment and verify/clean up a personal practice cron job when available.

Original Levels 0–2 automation/archive/backup are core, followed by Level 5 environment diagnosis and scoped practice scheduling. Expired dated graded jobs are replaced with observable in-class jobs. Log rotation/health/design-your-own remain extensions.

Read the [student instruction](../../../labs/lab10/lab10-instruction.md), [report template](../../../labs/lab10/README.md) and [optional extensions](../../../labs/lab10/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `bash`, `tar`, `gzip`, `mktemp`, GNU `date`; Python 3 for the helper, personal cron if available. No student sudo or privileged execution of student code.
- Check tar/gzip/GNU date, personal crontab permission, daemon and timezone. No administrator cron edits in class. Keep fake-crontab test separate from real daemon validation.
- In an ordinary test account run `oslab doctor`, `oslab start lab10`, then `cd "$OSLAB_WORKSPACE/lab10"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Restore bytes match; after at least four sequential runs three recognized completed archives remain and keep-me.txt survives. Restricted-environment execution still finds project. Heartbeat scheduling is distinct from backup scheduling and unavailable cron must be labeled.

Public complete model: [backup_solution.sh](backup_solution.sh). Copy it to `backup.sh` next to a fresh owned `project/` and invoke from another directory. It retains three recognized regular archives and preserves unrelated names. Sequential execution is the core assumption; the optional cron wrapper adds a nonblocking overlap lock.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: A cron entry finds `/bin/bash` but runs a script containing `tar -czf backup.tar.gz project` without changing directory. Explain the likely path fault and one robust correction. Why does a five-field date entry not by itself mean “one time”?

Key: An unspecified cron working directory may not contain project. Derive work from the script and tar -C it, or explicitly cd to a known absolute directory. A five-field date rule has no year and recurs; one-time intent needs a full-date guard/removal and verified timezone.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students count an archive as proof of restore, delete every backup directory file, paste expired date rules, or say crontab install proves execution. Ask for cmp, preserved unrelated file and observed timestamp.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

If you installed the practice entry, run `lab10-cron remove`, then `lab10-cron status` and inspect `crontab -l`. Remove only the managed practice line, never the whole crontab. Save evidence before `oslab clean lab10`; retain only three completed lab-owned archives. A missing cron capability is reported, not silently claimed as tested.

After evidence is saved, `oslab clean lab10` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Restorable archive and scoped keep-three retention (objectives 1–3) | 3 |
| Restore/retention/unrelated-file/restricted-environment evidence | 2 |
| Explain archive versus compression, paths and scheduling limits; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
