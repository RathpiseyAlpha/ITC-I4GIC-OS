# Instructor plan — OS Lab 3 — Wildcards, Links, GRUB & Shared Libraries (Hands-on)

**Public repository notice:** this plan and its answers are public. The `instructor` folder does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository; do not use the public checkpoint verbatim for secure assessment.

## Objectives and Original-task Mapping

1. Select files with a wildcard and explain shell expansion versus a literal name.
2. Create and inspect hard links and symbolic links using inode and target-path evidence.
3. Predict and diagnose the effects of renaming or replacing a link target.

Original Task 1 wildcards introduces selection; Task 2 links is the central investigation. Original Tasks 3–5 GRUB/shared-library work are optional and keep their specific environment requirements.

Read the [student instruction](../../../labs/lab3/lab3-instruction.md), [report template](../../../labs/lab3/README.md) and [optional extensions](../../../labs/lab3/extensions.md). Sources/tests should demonstrate these objectives, not merely a helper PASS message.

## Before Class

- Environment: Shared Ubuntu server with an individual account for each student. Required tools: `ln`, `ls`, `readlink`, `stat`, `mv`; compiler only for library extension. No student sudo or privileged execution of student code.
- Verify ln/readlink and internal/broken-link lifecycle behavior. Compiler only for the optional library; GRUB needs a pretested disposable VM snapshot/console.
- In an ordinary test account run `oslab doctor`, `oslab start lab3`, then `cd "$OSLAB_WORKSPACE/lab3"` (export the configured workspace first). Inspect fixture tree, ownership and quota. Verify a second start preserves edits.
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

Before rename source and hard have equal inode numbers. Renaming source leaves hard usable but soft, pointing at the old name, dangling. Retarget soft to moved.txt. A newly created source name has a distinct inode/bytes; the hard link still names the old inode.

```bash
cd "$OSLAB_WORKSPACE/lab3/links"
ln source.txt hard.txt
ln -s source.txt soft.txt
mv source.txt moved.txt
cat hard.txt
cat soft.txt   # intentional missing target
ln -sfn moved.txt soft.txt
printf 'version 2\n' > source.txt
ls -li source.txt moved.txt hard.txt soft.txt
cat hard.txt source.txt soft.txt
```
The model rewrites only the known owned symlink entry.

Accept equivalent correct commands/programs. Different observations caused by scheduling/capabilities require an evidence-based explanation, not fabricated expected output. Do not grade an exact filename unless execution depends on it.

## Checkpoint Key and Quick Marking

Practice question: A symbolic link inside `lab3/links/` stores `../source.txt`. Only `lab3/links/source.txt` exists. Resolve the stored path and explain why the link fails; give a suitable target for the existing file.

Key: The stored ../source.txt resolves relative to links/, therefore to lab3/source.txt, which is absent. For links/source.txt use source.txt (or its actual absolute path). Symbolic paths are not relative to the invoking shell.

Of the checkpoint's two points, award one for the defensible result/diagnosis and one for the mechanism plus a suitable verification observation. Relevant but incomplete reasoning earns partial credit. Students with an unfinished earlier artifact can still earn both checkpoint points. Use a private changed example for a graded session.

## Misconceptions and Progressive Support

Students confuse equal content with equal inode, or interpret a symlink relative to pwd. Draw directory entries and stored target strings. Do not treat one inode number as globally unique across filesystems.

Use the student task's progressive hints in order: mechanism → diagnostic observation → narrow implementation clue. Do not distribute the full model during the investigation. For a student behind pace, supply a clean *separate* fixture or restrict to one case, preserving their original work and the independent checkpoint.

Prediction accuracy is lightly weighted: a reasoned attempt, preserved answer, relevant test and correction matter. No random public oral examination is required. A solo student can use the guided example instead of the optional peer exchange.

## Capability Fallback and Cleanup

Use local Linux/WSL for unprivileged work if the server is unavailable; source/printed trace analysis can support mechanism assessment but does not establish executable behavior. VM/peer/cron/FUSE work needs the actual capability checks described in extensions. A teacher demonstration alone does not establish each student's practical recovery competence.

Save evidence before optional cleanup. If you later run `oslab clean lab3`, only the managed directory is removed; internal links are removed as entries and external links are refused. No boot configuration changes occur in the core.

After evidence is saved, `oslab clean lab3` is optional. It removes only the marked managed workspace; escaping links and detected mountpoints are refused. Internal symbolic links are supported. Confirm any optional jobs/processes/mounts are stopped before cleanup.

## Topic Rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct wildcard explanation and working hard/symbolic links (objectives 1–3) | 3 |
| Rename failure, repair and recreated-name evidence | 2 |
| Explain inode identity and relative symbolic-target resolution; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Review only the required artifacts and two selected records, plus prediction/correction and the collected checkpoint. AI use is optional; ask for one verified suggestion if used, not full chat history, paid tools or an AI detector. Optional extension completion is not required for full core credit.
