# Instructor plan — OS Lab 9 - Vault Deadlock, Resource Ordering & Recovery (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format. Read the [student instruction](../../../labs/lab9/lab9-instruction.md) and the [report template](../../../labs/lab9/README.md) first.

## Objectives

1. Draw holdings and requests that form a circular wait.
2. Reproduce a coordinated two-worker conflict with bounded waits and interpret timeout recovery.
3. Apply one global lock order and explain why it removes the cycle.

The original wait-trace inspection and the partner exercise stay in the [optional extensions](../../../labs/lab9/extensions.md). The partner exercise needs a narrow prepared directory and the other student's consent; it never runs on the shared server by default.

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md). Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab9.checkpoint` does **not** exist.
- `flock` (package `util-linux`) and `timeout` must exist for ordinary users. As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab9`; `oslab values lab9` prints two lock names and `a_first`; `oslab check lab9` takes about 7 seconds and must say `1/4` (the unmodified worker already reproduces the conflict).
- A student who started Lab 9 before this update has `vault/alpha.txt`, `vault/beta.txt` and a one-line `vault/worker.sh`. `oslab start lab9` removes the first two and replaces the third while they are unchanged, and adds the student's own files. A student who already pasted a worker keeps it; milestone 3 then asks for the two `res1=` and `res2=` lines. `oslab reset lab9` saves the old attempt and starts clean.
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- Ask students to run `oslab prelab lab9` the evening before. Look at the `prelab` column.

## Guide

The slide guide (`labs/lab9/guides/slides.html`, 53 slides) was rebuilt on 2026-11-05 in the pilot format: two personal lock names and the lock worker A takes first, the worker in three listings, `oslab predict`, Core 1 and Core 2, Plus and Challenge, the live checkpoint and `oslab debrief`. If the guide and the Markdown instruction ever differ, the instruction governs. Slides 1 to 3 are the cover and opening question, 4 to 8 the concepts, 9 to 17 the lab overview and setup, 18 to 20 the guided part, 21 and 22 the prediction, 23 to 28 Core 1, 29 to 35 Core 2, 36 and 37 Plus and Challenge, 38 to 41 the checkpoint, 42 to 48 debrief, submission, grading and mistakes, 49 to 51 wait traces and site-to-site synchronization, and 52 and 53 the takeaways.

## Timetable and What You Do

Keep `sudo oslab-teach board lab9 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–10 | Setup | Check the `started` column. Ask students to read their lock names aloud to a neighbour: they differ |
| 10–25 | Guided: locks and bounded waiting | Type along. Ask what is held while the contender waits, and why the status is not 0 |
| 25–35 | Prediction | At minute 30 read the **prediction spread** aloud without names. The `timeout` question (does the timeout prevent the deadlock?) is the one to discuss |
| 35–55 | Core 1: reproduce the deadlock | Students run the opposite mode once. Ask who got status 5 for A, for B, or for both. Draw the circle on the board with the names of one student |
| 55–70 | Core 2: repair it with a global order | Nobody is given the rule. The most common TRY is a rule that breaks the opposite mode too (milestone 1 then shows no conflict). The second is a rule that depends on the lock names: milestone 3 catches it |
| 70–85 | Instructor demonstration, Plus and Challenge | Run the opposite mode on the projector with `HOLD=1`; show the two statuses. Draw the three-worker circle |
| 85–100 | Live checkpoint | At minute 85 say "close AI tools" and run `sudo oslab-teach release lab9` |
| 100–110 | Debrief | Students run `oslab debrief lab9` first (two minutes), then use the script below |
| 110–120 | Submit | Run `sudo oslab-teach export lab9 --roster FILE > lab9.csv` |

## Expected Results

Every student has other lock names; the shape is the same. For a student whose `oslab values lab9` says `res1 = haze`, `res2 = ember`, `a_first = haze`:

- **Opposite mode:** A holds `haze` and asks for `ember`; B holds `ember` and asks for `haze`. At the barrier both wait. After 2 seconds at least one worker prints `second lock timeout` and exits with status 5; its first lock is released, so the other worker may finish with status 0. Both timing out (5 and 5) is also possible.
- **Ordered mode:** both workers take `haze` first, then `ember`. B waits for `haze` while A holds it. Both finish with status 0 and print `holds both`.
- **The repair** (public model): change the swap line to `if [[ "$role" = B && "$mode" = opposite ]]; then tmp=$first; first=$second; second=$tmp; fi`. Accept any rule that makes both workers use the same order in ordered mode and leaves the opposite orders in opposite mode, if it uses `$first`/`$second` or `$res1`/`$res2`.
- **Milestone 3** replaces the two lines `res1=...` and `res2=...` by two other names and runs the ordered mode again. A rule that depends on the student's own names (for example `[[ "$first" = haze ]]`) fails here and says so; a rule that never mentions a name passes.
- **Plus:** with `HOLD=1`, B waits about one second for the first lock and the total run takes about 2.5 seconds; both still finish with status 0 because 1 second is less than the 2-second timeout of the first lock.
- **Challenge:** the circle A→B→C→A; with the global order x, y, z, worker C (which lists z first and then x) must take x before z.

[worker_solution.sh](worker_solution.sh) is the older public worker for the previous (fixed-name) version of the lab. It still runs, but the lab now uses `vault/worker.sh` from `oslab start lab9`.

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab9 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. Each student gets three new lock names `x`, `y`, `z` from a random release value.

The checkpoint asks four things: can all three workers be stuck at once (yes), which worker lists its locks in the wrong order for the global order x, y, z (C), how many workers can wait forever once all follow that order (0), and one sentence on whether the rule still works with a third worker. Then the student copies their worker to `vault/third.sh`, changes only the two top lines to the names `x` and `y`, runs both workers in ordered mode and saves the logs in `checkpoint.txt`.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The three marked answers: cycle, wrong worker, how many wait (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points` in the export |
| The file task: `third.sh` has the new names, both workers finish, `checkpoint.txt` shows them | 1 | milestone 5 of `oslab check` |
| The sentence: any total order of the locks works for any number of workers, because a worker that waits holds only locks that come earlier in the order | 1 | you read it in the export |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread for `timeout`. Ask a student who answered "yes" what the timeout did to the circle.
2. Ask: "Worker A exited with status 5. Why did B finish?" Lead to: the exit released A's first lock.
3. Ask who wrote the rule with a name in it, and what happened at milestone 3.
4. Name the limit: a total order fixes this class of circular wait; it does not give fairness, and locks taken in code you do not control still need care.

## Misconceptions

- A timeout prevents the deadlock (it ends the waiting; the circle formed first).
- Both workers must always fail in the opposite run (one timeout can free the other).
- Removing the second lock repairs it (the data would then need another protection).
- The lock files are the data (the `.txt` files are data; the `.lock` files only coordinate).

Use the hints in order (`oslab hint lab9 1` to `3`).

## Caveats Moved Out of the Student Text

- `oslab check lab9` runs only the caller's own `worker.sh`, in disposable folders inside the lab folder, with `bash`, no input, and a limit of 8 seconds for each pair. It never runs another student's script and never touches the student's own `vault/` lock files.
- The environment variable `HOLD` (default 0) is set by the check to 0.6 seconds, so that the unmodified order fails every time instead of by luck. Students may set it too (Plus).
- `oslab reset lab9` saves the current attempt and creates a fresh worker. Do not suggest it for one wrong line.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do the whole lab in WSL or a local Linux with the [local setup](../../../labs/SETUP.md). `flock` is part of `util-linux`, which WSL has.

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Worker: `oslab check lab9` passes the four Core milestones | 2 |
| Tests: `opposite.txt` and `ordered.txt` show the conflict and the repair, and the README explains the recovery by timeout | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab9` | 2 |
| Live checkpoint: the answers and the worker running with the new names | 3 |
| Complete submission: the required files in the repository, on time | 1 |

Every row is suggested on the marking screen: row 1 from the best `oslab check` record, row 3 from the prediction (1) and the last debrief (1 when all its answers are right, 0.5 when at least half are), row 4 from the checkpoint, and row 5 from the website's file check of the repository. Row 2 needs your reading of the README.
