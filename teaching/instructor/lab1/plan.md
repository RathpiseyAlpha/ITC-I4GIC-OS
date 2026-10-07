# Instructor plan — OS Lab 1 — Introduction to Operating Systems (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format and is the first time students meet it. Read the [student instruction](../../../labs/lab1/lab1-instruction.md) and the [report template](../../../labs/lab1/README.md) first.

## Objectives

1. Find the kernel and the distribution of a Linux machine, and say how they differ.
2. Create and read files in your own folder with basic commands.
3. Start several processes from one program and explain their PID, parent PID and lifetime.

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md). Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab1.checkpoint` does **not** exist.
- As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab1`; `oslab check lab1` (expect 0/3).
- Send every student their host name and account name at least two days before. Ask them to log in once and run `oslab prelab lab1`. This moves most password problems out of the session.
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- The evening before, run `sudo oslab-teach board lab1 --roster FILE`. Students with an empty `prelab` column have probably never logged in; contact them.

## Timetable and What You Do

Keep `sudo oslab-teach board lab1 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–15 | Setup and a tour of `oslab` | The first ten minutes are login support. Use the `started` column to find who is not in yet. At minute 10, show the five commands once on the projector with your own test account |
| 15–30 | Guided: which system is this? | Type along on the projector. Stop after `uname -r` and `cat /etc/os-release` and ask why the two version numbers differ |
| 30–40 | Prediction, then class discussion | At minute 35 read the **prediction spread** aloud without names. The `ppids` and `later` questions split a first-year class; let two students argue each side |
| 40–65 | Core 1: one program, several processes | Steps 2 and 4 are the first commands students write themselves. Expect questions; answer with "what did step 1 do?" |
| 65–75 | Core 2: choose your own timing | Visit students whose `checks` column is empty or below 3/3 |
| 75–90 | Plus and Challenge (or finish Core) | Work only with students below 3/3 |
| 90–105 | Live checkpoint | At minute 90 say "close AI tools" and run `sudo oslab-teach release lab1` |
| 105–115 | Debrief | Use the script below |
| 115–120 | Submit | Many students have never pushed to their repository. If time runs out, let them push after class and say so clearly. Run `sudo oslab-teach export lab1 --roster FILE > lab1.csv` |

## Expected Results

- `uname -r` gives the kernel release; `/etc/os-release` gives the distribution name and version. On WSL or a container the kernel string looks unusual; accept it.
- A student with `count = 3` sees three rows with three different PIDs, one shared PPID (the PID of their shell, `echo $$`), state `S`, and command `sleep`.
- After the first process ends, the same `ps` shows one row fewer. After all end it shows only the header and may return a non-zero status. The file from `command -v sleep` still exists.
- **Plus:** the PPID of the new `sleep` is the second shell, whose parent is the first shell.
- **Challenge:** after the second shell exits, the orphaned `sleep` gets a new parent, usually PID 1 or the user's `systemd --user` process.

Model for a quick demonstration:

```bash
sleep 20 & a=$!
sleep 20 & b=$!
ps -o pid,ppid,stat,comm -p "$a,$b"
wait "$a"; wait "$b"
ps -o pid,ppid,stat,comm -p "$a,$b" || true
```

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab1 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. The student starts `a` short and `b` long `sleep` processes and samples after the short ones have ended: rows shown = `b`, started = `a + b`, and the program file is still on the disk.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The three marked answers (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points_of_2` in the export |
| `evidence/checkpoint.txt` shows the right number of rows | 1 | same column |
| The sentence says the short processes had already ended | 1 | read `checkpoint_sentence` in the export |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread and ask who was surprised by the PPID result.
2. Ask: "All rows say `sleep`. How does the kernel tell them apart?" Lead to PID and to program versus process.
3. Take one Core 2 timing result: "You ran `ps` and saw nothing. Does that prove the process never ran?"
4. Tell students that every pilot-format lab uses the same five commands, and ask what was unclear about them. Write the answers down for the retrospective in the [roadmap](../../ROADMAP.md).

## Misconceptions

- Program name equals identity ("they are all the same `sleep`").
- An empty `ps` means the command failed or the software is missing.
- `$!` is read too late and gives the PID of a different command.

Use the hints in order (`oslab hint lab1 1` to `3`).

## Caveats Moved Out of the Student Text

- A `ps` output is one sample. It cannot rebuild the history of a process.
- PIDs can be reused after a process ends. On a quiet server this is unlikely within a lab.
- Students must look only at processes they started. If a demonstration must be stopped, signal only a PID captured in that shell.
- `oslab check lab1` reads the evidence files; it does not prove when they were written.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do the whole lab in WSL or a local Linux with the [local setup](../../../labs/SETUP.md).

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| System record and processes: `oslab check lab1` passes the three Core milestones | 2 |
| Tests: processes alive and ended, and own timing for the short process | 2 |
| Prediction saved in time, and an honest confirmed/corrected explanation | 2 |
| Live checkpoint: answers, the saved `ps` output, and the sentence | 3 |
| Clear, complete evidence files and report | 1 |

The export gives you the first and fourth rows almost directly. Read only `answers.txt`, `timing.txt` and the report's explanation for the rest.
