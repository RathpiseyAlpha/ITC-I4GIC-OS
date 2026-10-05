# Instructor plan — OS Lab 3: Links and user-local libraries

**Public repository notice:** this file and its answers are public. A folder called `instructor` does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository. Do not use this public checkpoint verbatim for secure assessment.

## Preparation and environment

- Confirm 25–30 individual accounts, Python 3.8+, the `oslab` installation, quota, and shared Ubuntu account; disposable VM only for GRUB extension.
- Run `oslab doctor`, `oslab start lab3`, and `oslab check lab3` as an ordinary test account. Verify no symlink or ownership surprises.
- Review prerequisites: Lab 2, basic C compiler for library extension. Prepare paper prediction and checkpoint slips; collect the checkpoint before showing the key.
- Keep VM snapshots, compiler, FUSE and cron availability topic-specific. Do not add sudo to student accounts to make a task work.

## Exact timetable

| Minutes | Teacher action and evidence |
|---|---|
| 0–10 | Opening question and safety/setup; circulate and collect a sample of evidence |
| 10–25 | Guided example; circulate and collect a sample of evidence |
| 25–35 | Prediction on paper; five-minute optional peer comparison; circulate and collect a sample of evidence |
| 35–70 | Individual investigation or build; AI optional; circulate and collect a sample of evidence |
| 70–85 | Normal and edge tests; feedback pause; circulate and collect a sample of evidence |
| 85–100 | Individual changed case, supervised; no AI or peers; circulate and collect a sample of evidence |
| 100–110 | Evidence-based correction and concept explanation; circulate and collect a sample of evidence |
| 110–120 | Cleanup and concise submission; circulate and collect a sample of evidence |

## Expected observations and alternatives

Guided example: `cd "$HOME/oslab-work/lab3/links"; ln source.txt hard.txt; ln -s source.txt soft.txt; ls -li source.txt hard.txt soft.txt; readlink soft.txt`. Ask: Which links name the same inode, and which stores a path?

Investigation goal: Inspect `source.txt`, a hard link and a symlink in your own workspace. Rename the source, observe both links, then repair the symlink without replacing the hard link. Record inode and path evidence.

**Model solution or acceptable alternative:** `ln source.txt hard.txt` shares an inode; `ln -s source.txt soft.txt` stores a path. After rename, hard.txt still reads the old bytes. Recreate soft.txt with a target path that exists from the symlink's directory.

The model sketch is public preparation material. Use a fresh private variant if this checkpoint is graded.

Expected core evidence: an owned artifact or transcript; two tests including one edge case; a preserved prediction and evidence-based correction; a 3–5 sentence mechanism explanation. Accept equivalent commands and programs if they meet the invariant. Do not grade exact filenames unless a tool genuinely depends on them.

## Checkpoint key and quick marking

Question: A symlink points to `../source.txt` from inside `links/`. Predict where it resolves and explain whether it works.

Key: It resolves from the symlink's directory to the workspace root's `source.txt`, which is absent in the fixture. Credit correct relative resolution.

Of the checkpoint's two points, give one for a defensible result or diagnosis and one for mechanism plus a suitable verification observation. Partial credit applies if the result is wrong but the reasoning identifies a relevant mechanism. A student with unfinished earlier implementation can still earn both points.

## Misconceptions, hints, support

- Common mistake: treating one successful run as universal proof or confusing a displayed output with the underlying OS mechanism. Use anonymized errors during debrief.
- Progressive hints: Compare inodes; inspect `readlink`; draw the path relative to the symlink's directory.
- For students behind pace: provide a clean fixture copy, narrow the investigation to one test, and preserve the independent checkpoint. Do not complete their artifact for them.
- Peer exchange is five minutes maximum and optional; an individual can compare with the guided example. No public random questioning or one-by-one oral examination is required.

## Extensions, outage fallback, cleanup

Extension: Wildcard selection; build a shared object with `gcc -fPIC -shared` and use a user-local loader path; GRUB observation and recovery only in a snapshot-backed disposable VM with instructor supervision.

If the server is unavailable, use local Linux/WSL for unprivileged work and a printed trace for the checkpoint. For machine-specific tasks, use a disposable VM only; a teacher-only VM demonstration does not establish each student's recovery competence. At finish, confirm bounded processes have exited, any lab-owned cron marker is removed, and only owned workspace artifacts remain. `oslab clean lab3` is optional after submission and must never target unrelated files.

## Rubric (10 points)

| Evidence | Points |
|---|---:|
| Working behaviour against stated constraints | 3 |
| Tests and diagnosis, including a failure or edge case | 2 |
| Concept explanation and evidence-based correction | 2 |
| Independent changed-case checkpoint | 2 |
| Concise, attributable evidence | 1 |
