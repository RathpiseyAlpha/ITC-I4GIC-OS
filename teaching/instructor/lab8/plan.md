# Instructor plan — OS Lab 8 - Secure Bash Scripting, Race Conditions & File Locking (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format. Read the [student instruction](../../../labs/lab8/lab8-instruction.md) and the [report template](../../../labs/lab8/README.md) first.

## Objectives

1. Read a short script and find its critical section.
2. Reproduce a race condition and show which rule it breaks.
3. Protect the whole critical section with a file lock and test it.

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md). Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab8.checkpoint` does **not** exist.
- As an ordinary test account: `oslab doctor` must say `class inbox: connected`. Then `oslab start lab8`, `oslab check lab8` (expect 2/3), copy `teaching/instructor/lab8/buy_fixed.sh` over `store/buy.sh`, `oslab check lab8` (expect 3/3).
- Test `flock` on the real home filesystem; some network filesystems behave differently. If `flock` is missing, the lab cannot run as written.
- Prepare a roster file with one account name per line (the same allowlist as for installation). All `oslab-teach` commands below take `--roster FILE`.
- The evening before, run `sudo oslab-teach board lab8 --roster FILE` and remind students who have no pre-lab entry.

## Timetable and What You Do

Keep `sudo oslab-teach board lab8 --roster FILE --watch 20` open on your own screen for the whole session. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–5 | Setup | Check the `started` column fills. Walk to anyone still empty after three minutes |
| 5–20 | Read and trace the script | Do not explain the bug. Ask individuals: "Which line reads? Which lines write?" |
| 20–30 | Prediction, then class discussion | At minute 25 read the **prediction spread** aloud without names. Ask one student from each camp to argue. Do not give the answer; the experiment will |
| 30–50 | Core 1: break it | Visit students whose `checks` column is still empty at minute 45 |
| 50–75 | Core 2: fix it | Sort your visits by the board: no check yet, then many checks still at 2/3, then high hint level. Leave 3/3 students alone and point them to Plus |
| 75–90 | Plus and Challenge (or finish Core) | Work only with students below 3/3. Others are occupied |
| 90–105 | Live checkpoint | At minute 90 say "close AI tools" and run `sudo oslab-teach release lab8`. Watch the `checkpoint` and `task` columns |
| 105–115 | Debrief | Use the script below |
| 115–120 | Submit | Run `sudo oslab-teach export lab8 --roster FILE > lab8.csv` |

## Expected Results

- **Unsafe script, buyers A and B:** both are accepted. `sales.log` shows A + B units, more than the stock. `stock.txt` holds `stock - A` or `stock - B`, whichever buyer wrote last. It is not negative, which is why "stock is not negative" is a useless test.
- **Unsafe script, two small quantities (Core 1 step 4):** both sales are legitimate, but `stock.txt` is still wrong: one update is lost. This is the result that surprises students most; use it in the debrief.
- **Repaired script:** exactly one of A and B is accepted, and sold + left = start.
- **The three AI answers:** `a.sh` locks only the write, so both buyers have already read and decided. `b.sh` uses a lock file named after the process ID, so the two buyers lock different files. `c.sh` takes the lock in a subshell, so it is released before the transaction starts. All three fail the third milestone of `oslab check lab8`.
- **Challenge, killed buyer:** the kernel releases a `flock` lock when the descriptor is closed, and that happens when the process dies. The next buyer does not wait forever. The data can still be half-updated; a lock is not a transaction.

[`buy_fixed.sh`](buy_fixed.sh) is the public model in the student's form. [`buy_flawed.sh`](buy_flawed.sh) and [`buy_solution.sh`](buy_solution.sh) take `STORE QTY` and are used by `server/test_local.sh`.

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab8 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. Three buyers each want `q` units from stock `s`: accepted = `min(3, s // q)`, left = `s - accepted × q`, sold = `accepted × q`. The script change is a per-purchase limit that exits with status 4.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The three numeric answers (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points_of_2` in the export |
| The limit rule passes `oslab check lab8` | 1 | same column |
| The sentence names the lock line before the read | 1 | read `checkpoint_sentence` in the export; about 10 seconds each |

A student with an unfinished Core can still earn the first and third points. The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread again and ask: "Who changed their mind after Core 1, and what did you see?"
2. Take the small-quantities case: "Both sales were allowed. Why is the stock still wrong?" Draw read–check–write for two buyers on the board.
3. Read two checkpoint sentences without names: one that names the lock before the read, one that names only the write. Ask the class which is complete.
4. Close with the limit of the tool: `oslab check` ran one slow interleaving. Passing it does not prove every interleaving is safe.

## Misconceptions

- Counting log lines, not units.
- "The lock goes around the write." Ask what value the check used.
- Deleting the lock file to "reset" it. A waiting buyer then locks a different file.
- "It passed once, so it is correct."

Use the hints in order (`oslab hint lab8 1` to `3`). Hint 3 gives the syntax but not the place. Do not hand out `buy_fixed.sh` during the lab.

## Caveats Moved Out of the Student Text

- `BUY_DELAY` is a teaching aid that widens the window. It is not part of any fix, and without it the race still exists but is rarely seen.
- `flock` is advisory. A process that does not ask for the lock is not stopped.
- The repaired script is not crash-safe: a failure between the stock write and the log write leaves them inconsistent.
- `oslab check lab8` runs the student's own script as that student in a temporary copy of the store. It never runs with privileges.
- At most two or three buyers per run. No stress loops on the shared server.

## Fallback

Without the class inbox (`oslab doctor` says `not found`), everything still works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. Local Linux or WSL works the same way.

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Working script: `oslab check lab8` passes the three Core milestones | 2 |
| Tests: unsafe run, own quantities, and the run after repair | 2 |
| Prediction saved in time, and an honest confirmed/corrected explanation | 2 |
| Live checkpoint: answers, the change to the script, and the sentence | 3 |
| Clear, complete evidence files and report | 1 |

The export gives you the first and fourth rows almost directly. Read only `race.txt`, `locked.txt` and the report's explanation for the rest.
