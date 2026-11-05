# Instructor plan — OS Lab 4 — Linux I/O Redirection, Pipelines & Process Management (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format. Read the [student instruction](../../../labs/lab4/lab4-instruction.md) and the [report template](../../../labs/lab4/README.md) first.

## Objectives

1. Use redirection and pipelines while distinguishing stdout, stderr and exit status.
2. Filter and aggregate a CSV fixture, checking intermediate stages.
3. Diagnose incorrect selection/aggregation using normal and changed-input tests.

The original Tasks 4 and 5 (process tools, signals, orphan and zombie processes) stay in the [optional extensions](../../../labs/lab4/extensions.md). The core is the original Tasks 1 to 3.

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md). Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab4.checkpoint` does **not** exist.
- As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab4`; `cat data/events.csv` must show a header and six records, one of them a look-alike such as `ready-late`; `oslab check lab4` must say `0/4`.
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- Ask students to run `oslab prelab lab4` the evening before. Look at the `prelab` column.

## Guide

The slide guide (`labs/lab4/guides/slides.html`, 60 slides) was rebuilt on 2026-11-05 in the pilot format: personal values and the capital placeholders, `oslab predict`, Core 1 and Core 2, Plus and Challenge, the live checkpoint and `oslab debrief`. If the guide and the Markdown instruction ever differ, the instruction governs. Slides 1 to 3 are the cover and opening question, 4 to 13 the concepts, 14 to 22 the lab overview and setup, 23 to 27 the guided part, 28 and 29 the prediction, 30 to 40 Core 1 and Core 2, 41 and 42 Plus and Challenge, 43 to 46 the checkpoint, 47 to 53 debrief, submission, grading and mistakes, 54 to 58 processes, jobs and signals, and 59 and 60 the takeaways.

## Timetable and What You Do

Keep `sudo oslab-teach board lab4 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–10 | Setup | Check the `started` column. The most common first error is typing the capital words `STATUS` or `OTHER` instead of the personal value |
| 10–25 | Guided: redirection and pipelines | Type along. At step 2 ask which of the two files holds the error and why the screen alone could not tell |
| 25–35 | Prediction | At minute 30 read the **prediction spread** aloud without names. The `equal` question (is the first number the total?) is the one to discuss |
| 35–55 | Core 1: write report.sh | Nobody is given the script. Sort your visits by the board: no check yet, then stuck at 0/4. Say "run each stage of the pipeline alone" |
| 55–70 | Core 2: test your report | The most common TRY is the look-alike row counted (`ready-late`). Ask what the comma in `'^ready,'` does |
| 70–85 | Instructor demonstration, Plus and Challenge | Demonstrate a pipeline where the first stage fails and the pipe still ends with status 0 (`cat missing | wc -l`). Work only with students below 4/4 |
| 85–100 | Live checkpoint | At minute 85 say "close AI tools" and run `sudo oslab-teach release lab4` |
| 100–110 | Debrief | Students run `oslab debrief lab4` first (two minutes), then use the script below |
| 110–120 | Submit | Run `sudo oslab-teach export lab4 --roster FILE > lab4.csv` |

## Expected Results

Every student has a different status word and different numbers; the shape is the same. For a student whose `oslab values lab4` says `status = ready` and whose file holds the six records `ready-late,89`, `ready,4`, `done,4`, `ready,2`, `done,1`, `ready,2`:

- The expected report is `ready total: 8`.
- `grep '^ready,' data/events.csv | cut -d, -f2 | head -n 1` prints `4`, the first record only.
- `grep '^ready,' data/events.csv | wc -l` prints `3`, the number of records.
- A script that uses `grep '^ready'` (no comma) also counts `ready-late` and prints `ready total: 97`.

Public model for the simple two-field fixture, not general CSV parsing: [report_solution.sh](report_solution.sh) (set the student's word with `STATUS=ready bash report_solution.sh data/events.csv`; the default is `ok`).

```bash
awk -F, '$1 == "ready" { total += $2 } END { print "ready total: " total+0 }' data/events.csv
```

- **Missing input:** the script prints a message with `>&2` and ends with a status other than 0 (the public model uses 2). `bash report.sh data/missing.csv 2>/dev/null` prints nothing, which proves the message used stderr.
- **Plus:** `cut -d, -f1 data/events.csv | sort | uniq -c` counts one row per status and also counts the header line `status`.
- **Challenge:** `echo $(( $(grep '^ready,' data/events.csv | cut -d, -f2 | paste -sd+ -) ))` prints the same total. With no match, `paste` prints nothing and `$(( ))` evaluates to 0.

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab4 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. Each student gets a new file name (`data/WORD.csv`) and new numbers, made from a random release value, so nobody can prepare it.

The checkpoint asks four things: the total the student's script will print, the number `wc -l` would print (always 2: the two records of the student's status), the stream number of an error message (2), and one sentence on why the two numbers differ. Then the student creates the file, runs their own `report.sh` on it and saves the output in `checkpoint.txt`; `oslab check lab4` runs the script again on a fresh copy of the same records.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The three marked answers: total, `wc -l` number, stream number (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points` in the export |
| The file task: `report.sh` right on the new file and `checkpoint.txt` holding its output | 1 | milestone 5 of `oslab check` |
| The sentence: it must say that `wc -l` counts records while the total adds the numbers | 1 | you read it in the export |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread for `equal`. Ask a student who answered "yes" what the first number really was.
2. Ask: "Which of your tests would have caught a script that counts rows? Which would catch the look-alike?"
3. Ask who tried the missing file test first. What did the pipeline report as its status?
4. Name the limit: the report works for a two-field CSV without quoted commas. A quoted comma would break `cut` and `awk -F,`.

## Misconceptions

- `wc -l` after `grep` gives the sum of the numbers (it counts lines).
- `grep '^ok'` and `grep '^ok,'` are the same (the first also matches `ok-late`).
- An error message printed with plain `echo` is an error (it goes to stdout unless you add `>&2`).
- A pipeline fails when its first stage fails (only the last stage sets the status unless `pipefail` is set).

Use the hints in order (`oslab hint lab4 1` to `3`).

## Caveats Moved Out of the Student Text

- `oslab check lab4` runs the student's own `report.sh` on test files in a disposable folder inside the lab folder, with a 10-second limit and no input. It never runs another student's script.
- The check regenerates the records from the student's personal values. A student who edits `data/events.csv` is not penalised, but the report is tested on the original records.
- `oslab reset lab4` saves the current attempt and creates a fresh fixture. Do not suggest it for one wrong command.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do the whole lab in WSL or a local Linux with the [local setup](../../../labs/SETUP.md).

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Report: `oslab check lab4` passes the four Core milestones | 2 |
| Tests: `normal.txt` and `edge.txt` show the results, and the README says what each test contradicts | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab4` | 2 |
| Live checkpoint: the four answers and the report working on the new file | 3 |
| Complete submission: the required files in the repository, on time | 1 |

Every row is suggested on the marking screen: row 1 from the best `oslab check` record, row 3 from the prediction (1) and the last debrief (1 when all its answers are right, 0.5 when at least half are), row 4 from the checkpoint, and row 5 from the website's file check of the repository. Row 2 needs your reading of the README.
