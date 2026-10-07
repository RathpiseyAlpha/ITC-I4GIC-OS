# Instructor plan — OS Lab 2 — Linux Navigation & File Management (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format. Read the [student instruction](../../../labs/lab2/lab2-instruction.md) and the [report template](../../../labs/lab2/README.md) first.

## Objectives

1. Move around with absolute and relative paths, and explain `.` and `..`.
2. Build a folder tree, then move and copy files without changing their contents.
3. Find the cause of a path error and prove that a copy is identical.

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md). Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab2.checkpoint` does **not** exist.
- As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab2`; `ls incoming` must show two file names with spaces that match `oslab values lab2`; `oslab check lab2` (expect 0/4).
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- Read the Lab 1 retrospective in the [roadmap](../../ROADMAP.md) and adjust the first five minutes if the `oslab` commands were unclear last week.

## Timetable and What You Do

Keep `sudo oslab-teach board lab2 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–5 | Setup | Check the `started` column. The most common first error is losing the quotes when typing `file1='…'` |
| 5–20 | Guided: where am I? | Type along on the projector. At step 4, let the unquoted `ls` fail and ask the class to read the error aloud: it names two files that do not exist |
| 20–30 | Prediction, then class discussion | At minute 25 read the **prediction spread** aloud without names. The `same` question (does `../reports` still work from the lab folder?) is the one to discuss |
| 30–40 | Core 1: build the company folders | Short. Move on at minute 40 even if some are slow; Core 2 does not depend on the reader and third folders |
| 40–65 | Core 2: move and copy with your own paths | Nobody is given commands here. Sort your visits by the board: no check yet, then stuck at 1/4. Answer with "run `pwd`; now draw where the file must go" |
| 65–75 | Core 3: prove it | Check that students compare with `cmp`, not with `ls` |
| 75–90 | Plus and Challenge (or finish Core) | Work only with students below 4/4 |
| 90–105 | Live checkpoint | At minute 90 say "close AI tools" and run `sudo oslab-teach release lab2` |
| 105–115 | Debrief | Use the script below |
| 115–120 | Submit | Run `sudo oslab-teach export lab2 --roster FILE > lab2.csv` |

## Expected Results

Every student has different names; the shape is the same. For a student with `file1='budget 2026.txt'`, `file2='audit notes.txt'`, `owner=Finance`, `reader=HR`:

```bash
cd "$OSLAB_WORKSPACE/lab2/incoming"
mv -- 'budget 2026.txt' ../reports/
cd "$OSLAB_WORKSPACE/lab2"
mv -- "$OSLAB_WORKSPACE/lab2/incoming/audit notes.txt" "$OSLAB_WORKSPACE/lab2/reports/"
cp -- 'reports/budget 2026.txt' 'reports/audit notes.txt' TechCorp/Finance/
cp -- 'reports/budget 2026.txt' TechCorp/Finance/archive/first-original.txt
cd TechCorp/HR
cat '../Finance/budget 2026.txt'
cat "$OSLAB_WORKSPACE/lab2/TechCorp/Finance/budget 2026.txt"
```

Use this only on a fresh instructor fixture with those values; it is an illustration, not a reset command.

- **Deliberate error (Core 3):** from the reader department, `cat 'reports/budget 2026.txt'` gives "No such file or directory" although the name is right, because `reports` is not a child of the current folder.
- **Plus:** from `mess/c`, `mv -- '../a/b/lost file.txt' found.txt`. From `mess/a/b`, the copy needs three `..` to reach the lab folder.
- **Challenge:** a quoted `'*.txt'` is not expanded by the shell, so `cp` looks for a file literally named `*.txt`. An unquoted `*` does not match names that start with a dot.

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab2 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. Each student gets one of four start-folder and target pairs. Any relative path that reaches the target is accepted, not only the shortest one. An unquoted name with one space gives `cat` two arguments.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The three marked answers (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points_of_2` in the export |
| `evidence/checkpoint.txt` holds the content of the target file | 1 | same column |
| The sentence says each `..` goes up one folder from the current one | 1 | read `checkpoint_sentence` in the export |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread for `same`. Ask a student who answered "yes" what happened when they tried it.
2. Ask: "The file name was correct. Why did the system say no such file?" Lead to: a relative path is read from the current folder.
3. Ask who used `ls` and who used `cmp` to prove the copy. What can `ls` not show?
4. Read two checkpoint sentences without names and let the class improve the weaker one.

## Misconceptions

- Adding quotes fixes a path error that is really about the current folder.
- `mv` leaves the original in place.
- A matching name in `ls` proves matching contents.
- `..` means "the home folder" or "the lab folder", not "one level up from here".

Use the hints in order (`oslab hint lab2 1` to `3`). For a student far behind at minute 65, let them finish steps 1–3 of Core 2 only; the checkpoint does not depend on the rest.

## Caveats Moved Out of the Student Text

- `--` stops option parsing; it matters for names that start with a dash and is good habit in scripts.
- `oslab reset lab2` saves the current attempt and creates a fresh fixture. Do not suggest it for one wrong `mv`; the student can move the file back.
- `oslab check lab2` compares bytes of the student's files. It reads `evidence/paths.txt` only for the presence of a relative and an absolute path, not for correctness.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do the whole lab in WSL or a local Linux with the [local setup](../../../labs/SETUP.md).

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Correct folders and files: `oslab check lab2` passes the four Core milestones | 2 |
| Tests: identical copies with `cmp`, and one path error explained | 2 |
| Prediction saved in time, and an honest confirmed/corrected explanation | 2 |
| Live checkpoint: answers, the saved output, and the sentence | 3 |
| Clear, complete evidence files and report | 1 |

The export gives you the first and fourth rows almost directly. Read only `paths.txt` and the report's explanation for the rest.
