# Instructor plan — OS Lab 6: Permissions and access decisions

**Public repository notice:** this file and its answers are public. A folder called `instructor` does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository. Do not use this public checkpoint verbatim for secure assessment.

## Preparation and environment

- Confirm 25–30 individual accounts, Python 3.8+, the `oslab` installation, quota, and shared Ubuntu account.
- Run `oslab doctor`, `oslab start lab6`, and `oslab check lab6` as an ordinary test account. Verify no symlink or ownership surprises.
- Review prerequisites: octal permissions, Lab 2 paths. Prepare paper prediction and checkpoint slips; collect the checkpoint before showing the key.
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

Guided example: `mkdir -p "$HOME/oslab-work/lab6/demo"; printf 'x\n' > "$HOME/oslab-work/lab6/demo/a"; chmod 700 "$HOME/oslab-work/lab6/demo"; stat -c '%A %n' "$HOME/oslab-work/lab6/demo"`. Ask: Which permission controls entering a directory?

Investigation goal: Inspect `private/record.txt` and `shared/notice.txt`; set and justify modes for owner-only record edits and read-only notice in your owned tree. Use `namei -l` if available to explain traversal.

**Model solution or acceptable alternative:** A private file can use 600 inside a searchable owner-only directory 700. A notice can use 644 only if every parent allows intended readers to traverse; avoid widening home permissions on the shared server.

The model sketch is public preparation material. Use a fresh private variant if this checkpoint is graded.

Expected core evidence: an owned artifact or transcript; two tests including one edge case; a preserved prediction and evidence-based correction; a 3–5 sentence mechanism explanation. Accept equivalent commands and programs if they meet the invariant. Do not grade exact filenames unless a tool genuinely depends on them.

## Checkpoint key and quick marking

Question: Directory is 711 and file 600. A peer knows the filename. Can they read it? Which mode is decisive?

Key: They can traverse directory but cannot read file. Credit distinction between directory search and file read.

Of the checkpoint's two points, give one for a defensible result or diagnosis and one for mechanism plus a suitable verification observation. Partial credit applies if the result is wrong but the reasoning identifies a relevant mechanism. A student with unfinished earlier implementation can still earn both points.

## Misconceptions, hints, support

- Common mistake: treating one successful run as universal proof or confusing a displayed output with the underlying OS mechanism. Use anonymized errors during debrief.
- Progressive hints: Check every parent directory; use `stat`/`namei`; change only one permission at a time.
- For students behind pace: provide a clean fixture copy, narrow the investigation to one test, and preserve the independent checkpoint. Do not complete their artifact for them.
- Peer exchange is five minutes maximum and optional; an individual can compare with the guided example. No public random questioning or one-by-one oral examination is required.

## Extensions, outage fallback, cleanup

Extension: ACLs, groups, sticky bit, and narrowly prepared two-account testing on a disposable VM or administrator-approved directory.

If the server is unavailable, use local Linux/WSL for unprivileged work and a printed trace for the checkpoint. For machine-specific tasks, use a disposable VM only; a teacher-only VM demonstration does not establish each student's recovery competence. At finish, confirm bounded processes have exited, any lab-owned cron marker is removed, and only owned workspace artifacts remain. `oslab clean lab6` is optional after submission and must never target unrelated files.

## Rubric (10 points)

| Evidence | Points |
|---|---:|
| Working behaviour against stated constraints | 3 |
| Tests and diagnosis, including a failure or edge case | 2 |
| Concept explanation and evidence-based correction | 2 |
| Independent changed-case checkpoint | 2 |
| Concise, attributable evidence | 1 |
