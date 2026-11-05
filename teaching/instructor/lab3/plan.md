# Instructor plan — OS Lab 3 - Wildcards, Hard Links and Symbolic Links (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format. Read the [student instruction](../../../labs/lab3/lab3-instruction.md) and the [report template](../../../labs/lab3/README.md) first.

## Objectives

1. Explain which filenames a Bash wildcard selects and what quoting changes.
2. Use inode numbers to distinguish a hard link from a separate copy.
3. Explain and repair a symbolic link after its target is renamed.

GRUB and shared libraries stay in the [optional extensions](../../../labs/lab3/extensions.md), with a longer chain of links. The core uses only ordinary-user files and needs no `sudo`, compiler or VM.

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md), and the website source with it. Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab3.checkpoint` does **not** exist.
- As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab3`; `oslab values lab3` prints a name, a tag and two version numbers; `ls -a notes` shows five files with that name; `ls links` shows one file; `oslab check lab3` must say `0/5`.
- A student who started Lab 3 before this update has `links/source.txt` and `links/target-name.txt`. `oslab start lab3` removes both while they are unchanged, adds the student's own report and the `notes/` folder. A student who already renamed or edited `source.txt` keeps their files; `oslab reset lab3` saves the old attempt and starts clean.
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- Ask students to run `oslab prelab lab3` the evening before. Look at the `prelab` column.

## Guide

The slide guide (`labs/lab3/guides/slides.html`, 68 slides) was rebuilt on 2026-11-06 in the pilot format: personal values, the guided part, `oslab predict`, Core 1 to 3, Plus and Challenge, the live checkpoint and `oslab debrief`. If the guide and the Markdown instruction ever differ, the instruction governs. Slides 1 to 3 are the cover and opening question, 4 to 16 the concepts, 17 to 26 the lab overview and setup, 27 to 30 the guided part, 31 and 32 the prediction, 33 to 36 Core 1, 37 to 41 Core 2, 42 to 45 Core 3, 46 and 47 Plus and Challenge, 48 to 51 the checkpoint, 52 to 58 debrief, submission, grading and mistakes, 59 to 66 GRUB and shared libraries, and 67 and 68 the takeaways.

## Timetable and What You Do

Keep `sudo oslab-teach board lab3 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–5 | Setup | Check the `started` column. The most common first error is a space around `=` in `name=maple` |
| 5–20 | Guided: names, inodes and links | First five minutes: Concepts First with the guide (the shell expands patterns, inode and names, hard against symbolic link). Then type along. Ask who can say why `report.log` is never in the list, and what `ls -li` shows for the two names of one file |
| 20–30 | Prediction, then class discussion | At minute 25 read the **prediction spread** aloud without names. The `soft` question (what does the symbolic link print after a new file takes the old name?) is the one to discuss: most students answer with their first version |
| 30–40 | Core 1: wildcards on your own files | Short. The most common TRY is a middle command that also prints `<name>12.txt` (a `*` instead of `?`) |
| 40–60 | Core 2: rename, break, and reuse the old name | Make the class read the `No such file or directory` error aloud. At step 3 ask who is surprised that the dangling link works again |
| 60–75 | Core 3: repair and prove it | Nobody is given the repair. Sort your visits by the board: stuck at 2/5 or 3/5 is normal. Ask "from which folder is the stored target read?" |
| 75–90 | Plus and Challenge (or finish Core) | Work only with students below 5/5 |
| 90–105 | Live checkpoint | At minute 90 say "close AI tools" and run `sudo oslab-teach release lab3` |
| 105–115 | Debrief | Students run `oslab debrief lab3` first (two minutes), then use the script below |
| 115–120 | Submit | Run `sudo oslab-teach export lab3 --roster FILE > lab3.csv` |

## Expected Results

Every student has other names and numbers; the shape is the same. For a student whose `oslab values lab3` says `name = maple`, `tag = old`, `v1 = 417`, `v2 = 463`:

- **Core 1:** `notes/*.txt` prints `notes/maple1.txt`, `notes/maple12.txt` and `notes/maple2.txt` (the order depends on the locale; the check ignores it), and not the hidden `notes/.maple.txt`. The student's own middle command is `notes/"$name"?.txt`: it prints `maple1.txt` and `maple2.txt`. The quoted pattern prints `notes/*.txt`.
- **Core 2:** `maple-hard.txt` and `maple-old.txt` share an inode and print `version 417`. `maple-soft.txt` stores `maple.txt`: after the rename `cat` fails. After a new `maple.txt` with `version 463`, the symbolic link prints `version 463` (the wrong file), the hard link still prints `version 417`, and the inode of the new file differs.
- **Core 3** (public model, only after the student has tried): `rm -- maple-soft.txt`, then `ln -s maple-old.txt maple-soft.txt`. Never repair by replacing the hard link or by renaming the report back. `oslab check` accepts any relative target that reaches the renamed report, and refuses an absolute one.
- **Plus:** `notes/"$name"[12].txt` prints `maple1.txt` and `maple2.txt`; `notes/"$name"[!1]*` prints `maple.log` and `maple2.txt` (the hidden file never matches, and `maple1` and `maple12` are excluded).
- **Challenge:** after the second `rm` the link count of the remaining name is 2, then 1; the data is gone only when the last name is removed.

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab3 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. Each student gets a new folder `cp-WORD/`, a data file, and a new tag for the renamed file.

The checkpoint is a chain: `links/hard.txt` is a hard link to the data file, `links/first.txt` stores `../DATA.txt`, `links/second.txt` stores `first.txt`, and the data file is renamed. The five questions: does the hard link still read (yes), does `second.txt` read (no), the relative target `first.txt` must store (`../RENAMED.txt`), whether `second.txt` works after only `first.txt` is repaired (yes), and one sentence on which folder the stored target is read from (the folder that holds the link, `links/`). Then the student builds the case with the printed commands, repairs `first.txt`, and saves the output in `evidence/checkpoint.txt`.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The four marked answers: hard link, chain, target, second link (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points` in the export |
| The file task: `first.txt` repaired with a relative target, `second.txt` unchanged, `hard.txt` intact, output saved | 1 | milestone 6 of `oslab check` |
| The sentence: the stored target is read from the folder that holds the link | 1 | you read it in the export |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread for `soft`. Ask a student who answered with `v1`: "What does a symbolic link store? Then what does `cat` do after a new file takes that name?"
2. Ask: "Which of the two links would you trust to keep reading your original report, and why?" Lead to: the hard link follows the inode; the symbolic link follows a name.
3. Ask who stored an absolute target in the repair, and what happens when the folder is moved.
4. Name the limit: a hard link cannot cross filesystems and cannot point to a folder; a symbolic link can do both.

## Misconceptions

- A symbolic link is a copy, or knows which file it was made for (it stores a path and repeats it).
- A hard link breaks when the original is renamed or deleted (both names are equal).
- A file with the same content is the same file (only the inode shows it).
- A relative target is read from where I am (it is read from the folder that holds the link).
- `*` is understood by the command (Bash expands it first; quotes switch that off).

Use the hints in order (`oslab hint lab3 1` to `3`).

## Caveats Moved Out of the Student Text

- `oslab check lab3` looks at the student's files only. It does not prove the rename happened in that order; `evidence/links.txt` carries the labelled states, and milestone 5 checks that the failure and the repair are written there with the student's own names and numbers.
- The helper permits links that resolve inside the managed lab and never follows them during cleanup. Links that escape the lab folder are refused.
- `oslab reset lab3` saves the current attempt and creates a fresh fixture. Do not suggest it for one wrong link: `rm --` and `ln -s` repair it.
- The evidence is copied to the repository with `cp`; the prediction, check, checkpoint and debrief reach you through the inbox.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do the whole lab in WSL or a local Linux with the [local setup](../../../labs/SETUP.md).

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Correct files: `oslab check lab3` passes Core milestones 1 to 4 | 2 |
| Tests: the failure after the rename and the repaired link in `links.txt` (milestone 5) | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab3` | 2 |
| Live checkpoint: the four answers, the repaired chain and the saved output, and the sentence | 3 |
| Complete submission: the required files in the repository, on time | 1 |

Every row is suggested on the marking screen: rows 1 and 2 from the best `oslab check` record (milestone 5 gives 1 point for the failure recorded and 1 for the repair recorded), row 3 from the prediction (1) and the last debrief (1 when all its answers are right, 0.5 when at least half are), row 4 from the checkpoint, and row 5 from the website's file check of the repository. Press "fill the empty boxes with the suggested points", look only at rows whose note shows a problem, then save. Read the `Decision:` line in `links.txt` and the report if a row looks wrong; the report itself is not marked.
