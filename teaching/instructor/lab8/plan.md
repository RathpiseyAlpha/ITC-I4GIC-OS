# Instructor plan — OS Lab 8: Stock race and complete critical section

**Public repository notice:** this file and its answers are public. A folder called `instructor` does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository. Do not use this public checkpoint verbatim for secure assessment.

## Preparation and environment

- Confirm 25–30 individual accounts, Python 3.8+, the `oslab` installation, quota, and shared Ubuntu account; `flock`.
- Run `oslab doctor`, `oslab start lab8`, and `oslab check lab8` as an ordinary test account. Verify no symlink or ownership surprises.
- Review prerequisites: Bash conditionals and bounded background jobs. Prepare paper prediction and checkpoint slips; collect the checkpoint before showing the key.
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

Guided example: `( flock -x -w 2 9 && printf 'lock acquired\n' ) 9>"$HOME/oslab-work/lab8/store/stock.lock"`. Ask: Does locking only the final write protect a preceding stock check?

Investigation goal: Create a purchase script in your lab8 workspace. It reads stock, rejects invalid or excessive quantities, updates stock and appends a sale log. Use a short teaching delay between read and write to observe a race, then protect the full read-check-write-log sequence with `flock -w 2`. Remove the delay for final version.

**Model solution or acceptable alternative:** Validate `^[1-9][0-9]*$`, open a dedicated lock descriptor, `flock -x -w 2` before reading stock, and keep read, sufficiency check, write and sale log inside the same scope. Compare two requests for four units from stock five: exactly one may succeed.

See `buy_flawed.sh` and `buy_solution.sh` in this directory. The first deliberately demonstrates a stale-read race with a one-second teaching delay; the second locks the entire update.

Expected core evidence: an owned artifact or transcript; two tests including one edge case; a preserved prediction and evidence-based correction; a 3–5 sentence mechanism explanation. Accept equivalent commands and programs if they meet the invariant. Do not grade exact filenames unless a tool genuinely depends on them.

## Checkpoint key and quick marking

Question: Stock becomes 3. Two buyers request 2. Predict number of accepted purchases under correct locking and final stock.

Key: One accepted, one rejected, final stock 1. Credit an invariant-based explanation.

Of the checkpoint's two points, give one for a defensible result or diagnosis and one for mechanism plus a suitable verification observation. Partial credit applies if the result is wrong but the reasoning identifies a relevant mechanism. A student with unfinished earlier implementation can still earn both points.

## Misconceptions, hints, support

- Common mistake: treating one successful run as universal proof or confusing a displayed output with the underlying OS mechanism. Use anonymized errors during debrief.
- Progressive hints: Write the invariant; place lock before read; keep validation and update inside one lock scope.
- For students behind pace: provide a clean fixture copy, narrow the investigation to one test, and preserve the independent checkpoint. Do not complete their artifact for them.
- Peer exchange is five minutes maximum and optional; an individual can compare with the guided example. No public random questioning or one-by-one oral examination is required.

## Extensions, outage fallback, cleanup

Extension: Audit log design; red-team review of a classmate's test only by consent; permission setup on prepared accounts.

If the server is unavailable, use local Linux/WSL for unprivileged work and a printed trace for the checkpoint. For machine-specific tasks, use a disposable VM only; a teacher-only VM demonstration does not establish each student's recovery competence. At finish, confirm bounded processes have exited, any lab-owned cron marker is removed, and only owned workspace artifacts remain. `oslab clean lab8` is optional after submission and must never target unrelated files.

## Rubric (10 points)

| Evidence | Points |
|---|---:|
| Working behaviour against stated constraints | 3 |
| Tests and diagnosis, including a failure or edge case | 2 |
| Concept explanation and evidence-based correction | 2 |
| Independent changed-case checkpoint | 2 |
| Concise, attributable evidence | 1 |
