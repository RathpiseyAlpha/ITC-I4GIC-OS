# Instructor plan — OS Lab 9: Deadlock diagnosis and recovery

**Public repository notice:** this file and its answers are public. A folder called `instructor` does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository. Do not use this public checkpoint verbatim for secure assessment.

## Preparation and environment

- Confirm 25–30 individual accounts, Python 3.8+, the `oslab` installation, quota, and shared Ubuntu account; `flock`.
- Run `oslab doctor`, `oslab start lab9`, and `oslab check lab9` as an ordinary test account. Verify no symlink or ownership surprises.
- Review prerequisites: Lab 8 locking. Prepare paper prediction and checkpoint slips; collect the checkpoint before showing the key.
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

Guided example: `( flock -x -w 2 9 && printf 'Alpha acquired\n' ) 9>"$HOME/oslab-work/lab9/vault/alpha.lock"`. Ask: What happens if both workers hold one lock and request the other?

Investigation goal: Write two short scripts that acquire owned Alpha/Beta lock files in opposite order, with a coordination barrier or documented teaching delay. Use `flock -w 2` for every acquisition. Capture a wait trace, then change both scripts to Alpha-before-Beta and explain why the cycle disappears.

**Model solution or acceptable alternative:** A holds Alpha and waits for Beta while B holds Beta and waits for Alpha. Draw both edges. Timeouts bound the demonstration. In the repair, both workers acquire Alpha then Beta; no cycle can form.

See `worker_solution.sh` in this directory. Its barrier coordinates opposite-order acquisition; every wait is bounded. In ordered mode the barrier is skipped so both workers can complete.

Expected core evidence: an owned artifact or transcript; two tests including one edge case; a preserved prediction and evidence-based correction; a 3–5 sentence mechanism explanation. Accept equivalent commands and programs if they meet the invariant. Do not grade exact filenames unless a tool genuinely depends on them.

## Checkpoint key and quick marking

Question: A third worker needs Beta only. Does global Alpha-before-Beta require it to lock Alpha? Why?

Key: No: one-lock work has no order conflict. Credit explanation of cycle prevention.

Of the checkpoint's two points, give one for a defensible result or diagnosis and one for mechanism plus a suitable verification observation. Partial credit applies if the result is wrong but the reasoning identifies a relevant mechanism. A student with unfinished earlier implementation can still earn both points.

## Misconceptions, hints, support

- Common mistake: treating one successful run as universal proof or confusing a displayed output with the underlying OS mechanism. Use anonymized errors during debrief.
- Progressive hints: Draw holdings and requests; verify both processes reached the barrier; use consistent acquisition order.
- For students behind pace: provide a clean fixture copy, narrow the investigation to one test, and preserve the independent checkpoint. Do not complete their artifact for them.
- Peer exchange is five minutes maximum and optional; an individual can compare with the guided example. No public random questioning or one-by-one oral examination is required.

## Extensions, outage fallback, cleanup

Extension: Partner site-to-site scenario only in a narrowly prepared shared directory; timeout recovery policy.

If the server is unavailable, use local Linux/WSL for unprivileged work and a printed trace for the checkpoint. For machine-specific tasks, use a disposable VM only; a teacher-only VM demonstration does not establish each student's recovery competence. At finish, confirm bounded processes have exited, any lab-owned cron marker is removed, and only owned workspace artifacts remain. `oslab clean lab9` is optional after submission and must never target unrelated files.

## Rubric (10 points)

| Evidence | Points |
|---|---:|
| Working behaviour against stated constraints | 3 |
| Tests and diagnosis, including a failure or edge case | 2 |
| Concept explanation and evidence-based correction | 2 |
| Independent changed-case checkpoint | 2 |
| Concise, attributable evidence | 1 |
