# Instructor plan — OS Lab 6 — Linux Security, Users, Groups & File Permissions (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format. Read the [student instruction](../../../labs/lab6/lab6-instruction.md) and the [report template](../../../labs/lab6/README.md) first.

## Objectives

1. Interpret owner/group/other mode bits and symbolic versus octal notation.
2. Set least-privilege modes on owned files/directories and explain directory traversal.
3. Diagnose an access failure using path/mode evidence, distinguishing observed access from a hypothetical peer decision.

The original account and group inspection, ACLs and special bits stay in the [optional extensions](../../../labs/lab6/extensions.md). No student receives `sudo`, a new account or a changed home folder.

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md). Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab6.checkpoint` does **not** exist.
- As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab6`; `oslab values lab6` prints a policy sentence and a `sealed-…` name; `oslab check lab6` must say `0/4`.
- `namei` (package `util-linux`) should exist. If it does not, students list each parent with `ls -ld`.
- Check that students' home folders are not world-writable and that a default ACL does not give new files extra bits (`getfacl "$HOME"`). A default ACL would change the modes students see.
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- Ask students to run `oslab prelab lab6` the evening before. Look at the `prelab` column.

## Guide

The slide guide (`labs/lab6/guides/slides.html`, 54 slides) was rebuilt on 2026-11-05 in the pilot format: a personal notice policy and demo folder name, `oslab predict`, Core 1 and Core 2, Plus and Challenge, the live checkpoint and `oslab debrief`. If the guide and the Markdown instruction ever differ, the instruction governs. Slides 1 to 3 are the cover and opening question, 4 to 10 the concepts, 11 to 19 the lab overview and setup, 20 to 23 the guided part, 24 and 25 the prediction, 26 to 29 Core 1, 30 to 36 Core 2, 37 and 38 Plus and Challenge, 39 to 42 the checkpoint, 43 to 49 debrief, submission, grading and mistakes, 50 to 52 accounts, ACLs and special bits, and 53 and 54 the takeaways.

## Timetable and What You Do

Keep `sudo oslab-teach board lab6 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–10 | Setup | Check the `started` column. Ask students to read their policy sentence aloud to a neighbour: the sentences differ |
| 10–25 | Guided: permission basics | Type along. Stop at `namei -l` and ask which line of its output would stop a stranger |
| 25–35 | Prediction | At minute 30 read the **prediction spread** aloud without names. The `list` and `open` questions (mode 600 folder: names yes, file no) are the ones to discuss |
| 35–55 | Core 1: set the modes | Nobody is given the numbers. Sort your visits by the board: no check yet, then stuck at 0/4. Say "write the policy as r, w, x for owner, group and others" |
| 55–70 | Core 2: prove it | The most common TRY is `policy.txt` written before the last `chmod`. Ask who ran the `stat` line last |
| 70–85 | Instructor demonstration, Plus and Challenge | Show two accounts on your prepared machine, not on the shared server: 644 file in a 711 folder, then 700 |
| 85–100 | Live checkpoint | At minute 85 say "close AI tools" and run `sudo oslab-teach release lab6` |
| 100–110 | Debrief | Students run `oslab debrief lab6` first (two minutes), then use the script below |
| 110–120 | Submit | Run `sudo oslab-teach export lab6 --roster FILE > lab6.csv` |

## Expected Results

The private policy is the same for everybody: `private/` is `700` and `private/record.txt` is `600`. The notice policy is one of three sentences, each with a fixed answer:

| Notice sentence (short) | `shared/notice.txt` | `shared/` | Group can list `shared/` |
|---|---|---|---|
| The owner may change the file. The owner's group may read it and list the folder. Others have no access. | `640` | `750` | yes |
| Everyone may read the file if they know its name, but only the owner may list the folder. Only the owner may change anything. | `644` | `711` | no |
| The owner and the owner's group may read and change the file and the folder. Others have no access. | `660` | `770` | yes |

The checkpoint adds a fourth policy (`600` and `700`: only the owner) and always gives a different policy from the student's notice policy.

- **Traversal (Core 2):** with `demo/BOX` at `600`, `ls demo/BOX` shows `item.txt` (the folder has `r`), and `cat demo/BOX/item.txt` says `Permission denied` (it has no `x`). After `chmod 700 demo/BOX` the read works and prints `inside`. The check wants `Permission denied` and `inside` in `evidence/traversal.txt`, and the folder back at `700`.
- **Hypothetical peer:** `namei -l` shows every parent. The notice file itself may be `644`, but `oslab-work` and the home folder decide whether a stranger can get there; a student must not widen them to find out.
- **Plus:** `u=rw,g=r,o=` equals `640`; the mode does not change if the numbers were already `640`.
- **Challenge:** with `umask 077` a new file is `600` (`rw-------`).

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab6 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. Each student gets a different policy for a new folder `checkpoint-WORD/`: the answers are two octal modes (three digits), whether the group can list the folder, and one sentence on why a folder needs `x`. The student then creates the folder and `data.txt`, sets the two modes, and saves the `stat` output in `checkpoint.txt`.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The three marked answers: file mode, folder mode, group list (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points` in the export |
| The file task: the folder and `data.txt` have the modes of the policy, and `checkpoint.txt` shows them | 1 | milestone 5 of `oslab check` |
| The sentence: the `x` bit of a folder is what lets you reach a file inside it by name | 1 | you read it in the export |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread for `open`. Ask a student who answered "yes" what `Permission denied` came from.
2. Ask: "The file was `644`. Why could you not read it?" Lead to: every folder on the path is checked, and the folder had no `x`.
3. Ask which of the three claims in the report table was only reasoning, and what you would need to test it (a second account).
4. Name the limit: a single account cannot show what another user sees. The lab never changes your home folder.

## Misconceptions

- A file mode of 644 makes the file readable by everyone, whatever its folder.
- `x` on a folder lets you run it (it lets you enter it).
- `r` on a folder lets you read the files in it (it lets you list their names).
- Mode `640` gives the group write permission (it gives read).

Use the hints in order (`oslab hint lab6 1` to `3`).

## Caveats Moved Out of the Student Text

- `oslab check lab6` only reads modes and file contents. It does not run anything the student wrote, and it never touches another account.
- Root ignores these permissions. Run every test as an ordinary user.
- A default ACL (`getfacl`) can change the mode a new file gets. A student who sees an unexpected mode should show `getfacl` output; do not remove ACLs from their folders for them.
- `oslab reset lab6` saves the current attempt and creates a fresh workspace. Do not suggest it for one wrong `chmod`.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do the whole lab in WSL or a local Linux with the [local setup](../../../labs/SETUP.md).

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Modes: `oslab check lab6` passes the four Core milestones | 2 |
| Tests: `policy.txt` and `traversal.txt` show the modes and the failure, and the README separates what was tested from what was reasoned | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab6` | 2 |
| Live checkpoint: the answers and the new folder with the right modes | 3 |
| Complete submission: the required files in the repository, on time | 1 |

Every row is suggested on the marking screen: row 1 from the best `oslab check` record, row 3 from the prediction (1) and the last debrief (1 when all its answers are right, 0.5 when at least half are), row 4 from the checkpoint, and row 5 from the website's file check of the repository. Row 2 needs your reading of the README.
