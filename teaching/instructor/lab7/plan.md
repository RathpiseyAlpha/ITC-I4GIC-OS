# Instructor plan — OS Lab 7 — Bash Scripting, Permissions & Server Automation (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format. Read the [student instruction](../../../labs/lab7/lab7-instruction.md) and the [report template](../../../labs/lab7/README.md) first.

## Objectives

1. Create and invoke a Bash script with understood arguments and execution permissions.
2. Handle spaces, leading-dash filenames and missing input without unintended word splitting.
3. Test a reusable command and explain its exit status and safe filename handling.

The original PATH, login-message and outbox tasks stay in the [optional extensions](../../../labs/lab7/extensions.md). Cross-user mailbox work needs a prepared shared directory and never runs on the shared server by default.

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md). Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab7.checkpoint` does **not** exist.
- As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab7`; `ls input` must show two files, one with spaces and one starting with `-`; `oslab check lab7` must say `0/4`.
- A student who started Lab 7 before this update has two old files, `input/one file.txt` and `input/-dash.txt`. `oslab start lab7` removes them while they are unchanged and adds the student's own two files. Tell such students to run it once.
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- Ask students to run `oslab prelab lab7` the evening before. Look at the `prelab` column.

## Guide

The slide guide (`labs/lab7/guides/slides.html`, 53 slides) was rebuilt on 2026-11-05 in the pilot format: two personal file names (a name with spaces and a name with a leading dash), `oslab predict`, Core 1 and Core 2, Plus and Challenge, the live checkpoint and `oslab debrief`. If the guide and the Markdown instruction ever differ, the instruction governs. Slides 1 to 3 are the cover and opening question, 4 to 9 the concepts, 10 to 18 the lab overview and setup, 19 to 23 the guided part, 24 and 25 the prediction, 26 to 30 Core 1, 31 to 35 Core 2, 36 and 37 Plus and Challenge, 38 to 41 the checkpoint, 42 to 48 debrief, submission, grading and mistakes, 49 to 51 PATH, login messages and the outbox, and 52 and 53 the takeaways.

## Timetable and What You Do

Keep `sudo oslab-teach board lab7 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–10 | Setup | Check the `started` column. Ask students to read their two file names aloud to a neighbour: they differ |
| 10–25 | Guided: script basics | Type along. At step 3 let the unquoted name fail and ask how many arguments the script saw |
| 25–35 | Prediction | At minute 30 read the **prediction spread** aloud without names. The `dash` question (does `wc -w -name` count the words?) is the one to discuss |
| 35–55 | Core 1: build count_words.sh | Nobody is given the loop. Sort your visits by the board: no check yet, then stuck at 1/4. Say "print what the script receives with show_args.sh" |
| 55–70 | Core 2: test it | The most common TRY is milestone 3: a `wc` without `--`. The second is the status: the last command succeeded, so the script ended with 0 |
| 70–85 | Instructor demonstration, Plus and Challenge | Run the script on a name with a space, quoted and unquoted. Show `*` against `./*` with a dash name |
| 85–100 | Live checkpoint | At minute 85 say "close AI tools" and run `sudo oslab-teach release lab7` |
| 100–110 | Debrief | Students run `oslab debrief lab7` first (two minutes), then use the script below |
| 110–120 | Submit | Run `sudo oslab-teach export lab7 --roster FILE > lab7.csv` |

## Expected Results

Every student has two other file names and other word counts; the shape is the same. For a student whose `oslab values lab7` says `file1 = bridge candle.txt` and `file2 = -silver.txt`:

- `file1` has two or three words in its name, so an unquoted `$@` loop sees that many pieces. `file2` starts with a dash.
- `wc -w -silver.txt` (no `--`) fails with `invalid option`; `wc -w -- -silver.txt` counts the words.
- `bash count_words.sh missing.txt 'input/bridge candle.txt'` prints a message on stderr, still counts the second file, and ends with a status other than 0.

Public model: [count_words_solution.sh](count_words_solution.sh). It works for any file names; its label is `NAME: N words`. The check accepts any label as long as the line holds the file name (intact) and the word count.

- **Milestone 1** runs `./count_words.sh` directly in a disposable copy, so it needs the execute bit and a shebang.
- **Milestone 3** runs the script from inside `input/` with the dash name as its argument.
- **Milestone 4** gives no argument, then a missing file followed by a valid file.
- **Plus:** a folder is not a regular file; `[[ -f "$file" ]]` rejects it with the same message as a missing file.
- **Challenge:** `*` gives the script the bare name `-silver.txt`, which any command can read as an option; `./*` gives `./-silver.txt`, which cannot.

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab7 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. Each student gets a new awkward name (two spaces, a leading dash plus a space, or three words) and a word count made from a random release value.

The checkpoint asks four things: how many arguments the unquoted name makes (2 or 3), how many words the script should report, whether the final status may be 0 when the first file is missing (no), and one sentence on why `"$file"` has double quotes. Then the student creates the file, runs their own script and saves the output in `checkpoint.txt`.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The three marked answers: arguments, words, status (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points` in the export |
| The file task: the new file exists, the script counts it, `checkpoint.txt` holds the line | 1 | milestone 5 of `oslab check` |
| The sentence: double quotes keep the name in one piece, so spaces are not split | 1 | you read it in the export |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread for `dash`. Ask a student who answered "yes" what `wc` printed.
2. Ask: "The file exists and you typed its name. Why did `wc` refuse it?" Lead to: a leading dash is read as an option; `--` ends options.
3. Ask who used `$?` after the loop and what it showed. A variable (`status`) records any failure.
4. Name the limit: the script handles spaces and dashes; a name that contains a newline would still print on two lines.

## Misconceptions

- `$@` and `"$@"` are the same (the unquoted form splits at spaces).
- Quoting a name on the command line is enough (the script must quote it again where it uses it).
- A script ends with the status of the first error (it ends with the status of its last command, unless you set your own).
- `-silver.txt` is a bad name that cannot be used (it is a valid name; commands must be told it is a file).

Use the hints in order (`oslab hint lab7 1` to `3`).

## Caveats Moved Out of the Student Text

- `oslab check lab7` runs only the caller's own script, in a disposable folder inside the lab folder, with a 10-second limit and no input. The test files are made from the student's personal values; the student's own `input/` files are not changed.
- The script is copied with its mode bits. A script that is not executable by its owner fails milestone 1 with a message that names `chmod u+x`.
- `oslab reset lab7` saves the current attempt and creates a fresh skeleton. Do not suggest it for one wrong quote.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do the whole lab in WSL or a local Linux with the [local setup](../../../labs/SETUP.md).

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Script: `oslab check lab7` passes the four Core milestones | 2 |
| Tests: `normal.txt` and `edge.txt` show the runs, and the README says what each test contradicts | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab7` | 2 |
| Live checkpoint: the answers and the script counting the new file | 3 |
| Complete submission: the required files in the repository, on time | 1 |

Every row is suggested on the marking screen: row 1 from the best `oslab check` record, row 3 from the prediction (1) and the last debrief (1 when all its answers are right, 0.5 when at least half are), row 4 from the checkpoint, and row 5 from the website's file check of the repository. Row 2 needs your reading of the README.
