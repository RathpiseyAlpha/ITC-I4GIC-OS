# Instructor plan — OS Lab 5 — Threads, Kernel Workers & Process Signals (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format. Read the [student instruction](../../../labs/lab5/lab5-instruction.md) and the [report template](../../../labs/lab5/README.md) first.

## Objectives

1. Create POSIX threads and check API return codes.
2. Join each worker before consuming its result and explain shared versus separate address spaces.
3. Use a bounded execution trace to diagnose missing completion synchronization.

The original Tasks 3 and 4 (kernel mapping, signals) and the fork-versus-thread comparison stay in the [optional extensions](../../../labs/lab5/extensions.md).

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md). Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab5.checkpoint` does **not** exist.
- `gcc` with pthread support and `timeout` must exist for ordinary users. As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab5`; `oslab values lab5` prints four numbers; `oslab check lab5` must say `1/4` (the unmodified program builds without warning; the other three fail).
- If `gcc` is missing, `oslab check lab5` says so on every line. Use the trace fallback: students read `threads/two_workers.c` and `threads/trace.csv`, answer the prediction and the checkpoint, and report that executable behaviour was not tested.
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- Ask students to run `oslab prelab lab5` the evening before. Look at the `prelab` column.

## Guide

The slide guide (`labs/lab5/guides/slides.html`, 55 slides) was rebuilt on 2026-11-05 in the pilot format: personal worker ids and step counts, a program with two TODO gaps, `oslab predict`, Core 1 and Core 2, Plus and Challenge, the live checkpoint and `oslab debrief`. If the guide and the Markdown instruction ever differ, the instruction governs. Slides 1 to 3 are the cover and opening question, 4 to 8 the concepts, 9 to 17 the lab overview and setup, 18 to 21 the guided one-worker example, 22 and 23 the prediction, 24 to 31 Core 1, 32 to 36 Core 2, 37 and 38 Plus and Challenge, 39 to 42 the checkpoint, 43 to 49 debrief, submission, grading and mistakes, 50 to 53 fork, kernel workers and signals, and 54 and 55 the takeaways.

## Timetable and What You Do

Keep `sudo oslab-teach board lab5 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–10 | Setup | Check the `started` column. Ask each student to read their four numbers aloud to a neighbour: they differ |
| 10–25 | Guided: one worker | Type along. Ask which line makes main wait, and what `rc` holds on success |
| 25–35 | Prediction | At minute 30 read the **prediction spread** aloud without names. The `unjoined` question (must `worker A finished` always appear?) is the one to discuss |
| 35–55 | Core 1: finish the two-worker program | Nobody is given the lines. Sort your visits by the board: no check yet, then stuck at 1/4. Say "which variable is worker B's thread?" |
| 55–70 | Core 2: test and change | The most common TRY is milestone 4 (changed case): a student who joined only A passes the normal run by luck, because A takes longer. Use it for the demonstration |
| 70–85 | Instructor demonstration, Plus and Challenge | Remove the join of B and run the program ten times on the projector. Ask what this proves about "it worked three times" |
| 85–100 | Live checkpoint | At minute 85 say "close AI tools" and run `sudo oslab-teach release lab5` |
| 100–110 | Debrief | Students run `oslab debrief lab5` first (two minutes), then use the script below |
| 110–120 | Submit | Run `sudo oslab-teach export lab5 --roster FILE > lab5.csv` |

## Expected Results

Every student has other ids and step counts; the shape is the same. For a student whose `oslab values lab5` says `id_a = 3`, `id_b = 9`, `steps_a = 5`, `steps_b = 2`:

- The program prints `worker 9 finished` after about 40 ms, `worker 3 finished` after about 100 ms, then `A result=15 B result=18`, then `main finishing`.
- Before the joins are added, `main finishing` appears at once and the workers are cut off when the process ends, so the `finished` lines may be missing.
- The changed case (A 0 steps, B 1 step) must print `A result=0 B result=9`.

Public model: [two_workers_solution.c](two_workers_solution.c) is the student's file with both `TODO` lines filled in (it uses A = {2, 3} and B = {3, 4}, so it prints `A result=6 B result=12`; your students have other numbers).

- **Join mistakes the check finds:** one join only; a join with the wrong thread variable; the report line printed before the joins (results 0); a join that is not tested (milestone 3 counts `rc = pthread_join(...)` and `if (pthread_join(...))`).
- **Why a missing join can still pass milestone 2:** if B is not joined but A takes longer, B has finished by the time A is joined. Milestone 4 changes the steps, A takes 0, and the same program fails.
- **Plus:** with B's join removed, main prints B's number when B is quick, and a smaller number or 0 when B is slow. Nothing is guaranteed.
- **Challenge:** in the order of `trace.csv` (A read, B read, A write, B write) both workers read 0, so both write 1. The final value is 1, not 2: one update is lost. Joining does not prevent this; a lock does (Lab 8).

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab5 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. The checkpoint has two cases with numbers made from a random release value:

- Case 1 (questions): main joins A but not B and prints `b.result`. Not guaranteed (no), the smallest possible value is 0, the number of joins for K workers is K, and one sentence: main still does not know whether B has finished.
- Case 2 (file task): a copy `threads/WORD.c` with new step counts; `oslab check lab5` builds and runs it and expects `A result=ID_A*STEPS_A B result=ID_B*STEPS_B`, and `checkpoint.txt` must hold that line.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The three marked answers: guaranteed, smallest value, number of joins (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points` in the export |
| The file task: the copy builds, prints the right results, `checkpoint.txt` holds them | 1 | milestone 5 of `oslab check` |
| The sentence: main does not know whether B has finished (or: B may still be running) | 1 | you read it in the export |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread for `unjoined`. Ask a student who answered "yes" what happens to a worker when `main` returns.
2. Ask who got milestone 4 red while 2 was green, and why a passing run is not a proof.
3. Draw the trace: two workers read 0, both write 1. Ask what a join changes here (nothing) and what is needed (mutual exclusion, Lab 8).
4. Name the limit: the delay is for teaching, not for synchronization.

## Misconceptions

- A delay or `sleep` in main waits for the worker (it only hides the problem).
- One join waits for all threads (it waits for exactly one).
- A run that prints the right numbers proves there is no race.
- Joining the threads makes updates to a shared counter safe.

Use the hints in order (`oslab hint lab5 1` to `3`).

## Caveats Moved Out of the Student Text

- `oslab check lab5` compiles and runs only the caller's own file, in a disposable folder inside the lab folder, with a 60-second limit for the compiler and 5 seconds for each run. It never runs another student's program.
- Milestone 4 changes the `struct job a = ..., b = ...;` line of a copy. A student who moved that definition to several lines gets a message asking to keep it on one line.
- `oslab reset lab5` saves the current attempt and creates a fresh program. Do not suggest it for one missing join.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do the whole lab in WSL or a local Linux with the [local setup](../../../labs/SETUP.md).

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Program: `oslab check lab5` passes the four Core milestones | 2 |
| Tests: `normal.txt` and `changed.txt` show the runs, and the README explains thread memory, completion and mutual exclusion | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab5` | 2 |
| Live checkpoint: the four answers and the copy running with new step counts | 3 |
| Complete submission: the required files in the repository, on time | 1 |

Every row is suggested on the marking screen: row 1 from the best `oslab check` record, row 3 from the prediction (1) and the last debrief (1 when all its answers are right, 0.5 when at least half are), row 4 from the checkpoint, and row 5 from the website's file check of the repository. Row 2 needs your reading of the README.
