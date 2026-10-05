# Instructor plan — OS Lab 2 — Linux Navigation & File Management (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Navigate with absolute and relative paths and explain `.` and `..`.
2. Build a company directory tree and move/copy reports while preserving their contents.
3. Diagnose a path mistake and verify the final organization with directory listings.

Core retains the original sequence: navigation warm-up → company directory structure → absolute/relative paths → organization. Read-only system exploration and advanced listing remain optional.

Read the [student instruction](../../../labs/lab2/lab2-instruction.md), [report template](../../../labs/lab2/README.md) and [optional extensions](../../../labs/lab2/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `pwd`, `ls`, `mkdir`, `cp`, `mv`, `find`, `cmp`. No student sudo or privileged execution of student code.
- Confirm the two incoming fixtures and a writable workspace. Inspect saved submissions before choosing a reset; the helper preserves existing work.
- In an ordinary test account run `oslab doctor`, `oslab start lab2`, then `cd "$OSLAB_WORKSPACE/lab2"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Both original report contents remain revenue,120 and revenue,130 after moving into reports and copying into Finance/archive. Moving removes the source name; copying retains it. Accept equivalent hierarchy organization that preserves the specified destinations.

```bash
cd "$OSLAB_WORKSPACE/lab2"
mv -- 'incoming/quarter 1.txt' reports/
mv -- 'incoming/quarter 2.txt' reports/
mkdir -p TechCorp/Finance/archive TechCorp/Engineering TechCorp/HR
cp -- reports/'quarter 1.txt' reports/'quarter 2.txt' TechCorp/Finance/
cp -- TechCorp/Finance/'quarter 1.txt' TechCorp/Finance/archive/
cmp -- reports/'quarter 1.txt' TechCorp/Finance/'quarter 1.txt'
cd TechCorp/HR
cat '../Finance/quarter 1.txt'
```
Use this only on a fresh instructor fixture; it is not a resume/reset command.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: A report is now at `TechCorp/Finance/quarter 1.txt` and your current directory is `TechCorp/HR`. A command tries `cat "Finance/quarter 1.txt"`. Identify the fault and give a working relative path.

Key: From TechCorp/HR, Finance is not a child. Use ../Finance/quarter 1.txt with the entire path quoted. Diagnose current directory separately from the space in the name.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students add quotes but fail to change the parent path, or check only filenames. Ask for pwd, a component-by-component path and cmp.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

No background process or cron job is created. Leave the owned tree for review; do not remove reports before saving evidence.

After evidence is saved, `oslab clean lab2` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct directory/report organization and preserved contents (objectives 1–3) | 3 |
| Content comparison and changed-current-directory test | 2 |
| Explain absolute/relative paths and copy versus move; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
