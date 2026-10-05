# Instructor plan — OS Lab 6 — Linux Security, Users, Groups & File Permissions (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Interpret owner/group/other mode bits and symbolic versus octal notation.
2. Set least-privilege modes on owned files/directories and explain directory traversal.
3. Diagnose an access failure using path/mode evidence, distinguishing observed access from a hypothetical peer decision.

Original Task 3 file/directory permissions is the required investigation. Tasks 1–2 account/group administration and Tasks 4–5 special bits/ACLs are optional with prepared permissions.

Read the [student instruction](../../../labs/lab6/lab6-instruction.md), [report template](../../../labs/lab6/README.md) and [optional extensions](../../../labs/lab6/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `id`, `stat`, `chmod`, `ls`; `namei` recommended, ACL tools optional. No student sudo or privileged execution of student code.
- Test as an ordinary account: root bypasses many denials. If ACL/group extension is used, prepare only a narrow directory and designated identities, never broad home access.
- In an ordinary test account run `oslab doctor`, `oslab start lab6`, then `cd "$OSLAB_WORKSPACE/lab6"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Typical policy: private directory 700, private file 600, notice directory 755 and file 644, while the managed workspace remains private. The notice is therefore not empirically public here. In demo/sealed mode 600, plain names may list but opening the child fails; restoring 700 permits read.

```bash
cd "$OSLAB_WORKSPACE/lab6"
chmod 700 private
chmod 600 private/record.txt
chmod 755 shared
chmod 644 shared/notice.txt
namei -l "$PWD/shared/notice.txt"
```
The private workspace/home parents still limit peer traversal. Do not widen them for this model.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: A prepared shared directory is 711 and its file is 600, owned by another student. You know the filename. Explain whether you can traverse the directory, list names, and read the file.

Key: For a peer with no overriding ACL/capability: directory 711 allows known-name traversal but denies name listing; file 600 owned by another student denies file read. All earlier parent components must also be searchable.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students conflate file execute with directory search, use chmod -R broadly, or claim a 644 notice overrides a 700 parent. Ask for full-path namei and separate observed/hypothetical claims.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

Restore the demo directory to 700 and keep private files at your stated policy. No new accounts/groups or jobs were created. Do not change home access or another student’s files.

After evidence is saved, `oslab clean lab6` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Modes match the owned-file policy and full-path reasoning (objectives 1–3) | 3 |
| Owner-access and directory-search failure/repair tests | 2 |
| Explain rwx/octal interpretation and the limits of peer-access claims; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
