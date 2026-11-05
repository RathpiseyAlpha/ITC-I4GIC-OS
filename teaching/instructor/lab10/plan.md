# Instructor plan — OS Lab 10 - Backups, Archiving, Scheduling & cron Automation (Hands-on)

**Public repository notice:** this plan is public, and so is the code that computes every student's values and answers. Personal values stop neighbour copying and force each answer to use the student's own numbers; they are not secret. The live checkpoint is protected by its release time, not by secrecy. Keep anything that must stay private outside this repository.

This lab uses the pilot format. Read the [student instruction](../../../labs/lab10/lab10-instruction.md) and the [report template](../../../labs/lab10/README.md) first.

## Objectives

1. Create/list/restore a project archive and distinguish archiving from compression.
2. Implement bounded retention for only the lab-owned completed archives.
3. Run the script with a restricted environment and verify/clean up a personal practice cron job when available.

Scheduling the backup itself, rotating logs, the health snapshot and date-specific jobs stay in the [optional extensions](../../../labs/lab10/extensions.md).

## Before Class

- Install or update the helper as in the [runbook](../../../server/RUNBOOK.md), including `lab10_cron.py`. Check that `/var/lib/itc-oslab/inbox` exists with mode `1733` and that `/var/lib/itc-oslab/release/lab10.checkpoint` does **not** exist.
- `tar`, `gzip`, `mktemp`, GNU `date` and `env` must exist for ordinary users, with `/bin/bash`. As an ordinary test account: `oslab doctor` must say `class inbox: connected`; `oslab start lab10`; `oslab values lab10` prints a number to keep and an archive name; `oslab check lab10` must say `2/4` (the supplied script already makes a restorable archive and works under `env -i`; the retention is missing, and the test of files that are not the student's waits for it).
- Check personal cron: `crontab -l` must not fail with "not allowed", the cron daemon must run, and `date '+%F %T %Z'` shows the server timezone. If cron is not available, the Plus task is skipped and the fallback line in `automation.txt` is the evidence.
- A student who started Lab 10 before this update has a one-line `backup.sh`. `oslab start lab10` replaces it while it is unchanged. A student who already pasted the old script keeps it (it makes `backup-...` archives, so milestone 1 asks for the student's own name); `oslab reset lab10` saves the old attempt and starts clean.
- Prepare a roster file with one account name per line. All `oslab-teach` commands below take `--roster FILE`.
- Ask students to run `oslab prelab lab10` the evening before. Look at the `prelab` column.

## Guide

The slide guide (`labs/lab10/guides/slides.html`, 51 slides) was rebuilt on 2026-11-05 in the pilot format: a personal archive name and number to keep, the backup script with its TODO, `oslab predict`, Core 1 and Core 2, Plus and Challenge, the live checkpoint and `oslab debrief`. If the guide and the Markdown instruction ever differ, the instruction governs. Slides 1 to 3 are the cover and opening question, 4 to 8 the concepts, 9 to 17 the lab overview and setup, 18 to 21 the guided part, 22 and 23 the prediction, 24 to 28 Core 1, 29 to 33 Core 2, 34 and 35 Plus and Challenge, 36 to 39 the checkpoint, 40 to 46 debrief, submission, grading and mistakes, 47 to 49 scheduling the backup, logs and date jobs, and 50 and 51 the takeaways.

## Timetable and What You Do

Keep `sudo oslab-teach board lab10 --roster FILE --watch 20` open on your own screen. Do not project it: it shows names.

| Minutes | Students | You |
|---|---|---|
| 0–10 | Setup | Check the `started` column. Ask students to read their archive name and number aloud to a neighbour: they differ |
| 10–25 | Guided: archiving and restoring | Type along. Ask what `-C` does, and why `cmp` and not `ls` proves the restore |
| 25–35 | Prediction | At minute 30 read the **prediction spread** aloud without names. The `assume` question (does it work under cron because it worked in the shell?) is the one to discuss |
| 35–55 | Core 1: write the retention | Nobody is given the loop. Sort your visits by the board: stuck at 3/4 is normal at first. Say "which names are yours? write that as a pattern" |
| 55–70 | Core 2: the environment trap | The most common TRY is milestone 2 or 3: a loose pattern such as `NAME-*` that deletes or counts `NAME-notes.tar.gz`. A second is `rm $(ls ...)` with a name that has a space |
| 70–85 | Instructor demonstration, Plus and Challenge | Run the script from `/` with `env -i` and a relative `project` path to show the failure. Students with cron do the Plus task |
| 85–100 | Live checkpoint | At minute 85 say "close AI tools" and run `sudo oslab-teach release lab10` |
| 100–110 | Debrief | Students run `oslab debrief lab10` first (two minutes), then use the script below |
| 110–120 | Submit | Run `sudo oslab-teach export lab10 --roster FILE > lab10.csv` |

## Expected Results

Every student has another archive name and another number to keep; the shape is the same. For a student whose `oslab values lab10` says `keep = 3` and `name = daily`:

- Each run makes `backups/daily-YYYYMMDDTHHMMSSNNNNNNNNN-PID.tar.gz`. The name sorts by time, so the oldest is first when sorted.
- After five runs exactly three `daily-...` archives remain, and they are the newest three. `keep-me.txt` and `daily-notes.tar.gz` are untouched.
- Under `env -i` from another folder the script still finds `project/`, because it computes its own folder, and it makes a new archive in its own `backups/`.

Public model: [backup_solution.sh](backup_solution.sh) is the sequential model for the current lab, with example values `keep=3` and `name=daily` at the top (a student's script has their own). The retention lines are:

```bash
shopt -s nullglob
owned=()
for path in "$work"/backups/"$name"-*.tar.gz; do
    base=${path##*/}
    if [[ -f "$path" && ! -L "$path" && "$base" =~ ^$name-[0-9]{8}T[0-9]{15}-[0-9]+\.tar\.gz$ ]]; then owned+=("$path"); fi
done
if (( ${#owned[@]} > keep )); then
    mapfile -t ordered < <(printf '%s\n' "${owned[@]}" | LC_ALL=C sort -r)
    for path in "${ordered[@]:$keep}"; do rm -- "$path"; done
fi
```

- **Milestone 2** runs the student's script `keep + 2` times in a clean folder with the two unrelated files already in `backups/`, and compares what is left with the newest names it saw.
- **Milestone 3** passes only when milestone 2 passes (a script that deletes nothing would pass it for free).
- **Plus:** `lab10-cron install` adds one marked line that appends a timestamp every minute; `remove` deletes only that line.
- **Challenge:** `30 2 * * * /full/path/to/backup.sh`. Five fields have no year, so a date-specific entry runs again next year unless the script guards it.

## Checkpoint Key and Marking

Key: `sudo oslab-teach key lab10 --roster FILE` prints each student's values and expected answers, including the checkpoint after release. Each student gets a new number to keep (different from their own) and runs the script that many plus two times.

The checkpoint asks four things: how many archives remain (the new number), which is removed first (oldest), whether `NAME-notes.tar.gz` must be deleted (no), and one sentence on what the script must contain so that the rule changes in one place (a variable such as `keep`, used by the retention). Then the student copies `backup.sh` to `backup-cp.sh`, changes only the `keep=` line, runs it, and saves the list in `checkpoint.txt`. A retention with the old number written into its logic fails.

The checkpoint is worth 3 points:

| Part | Points | Source |
|---|---:|---|
| The three marked answers: archives left, which goes first, the look-alike file (all right 1, at least half 0.5) | 1 | `checkpoint_auto_points` in the export |
| The file task: the copy keeps the new number, `checkpoint.txt` lists that many archives | 1 | milestone 5 of `oslab check` |
| The sentence: a variable used by the retention, not a number written into the loop | 1 | you read it in the export |

The `flag` column says `rewritten` when a prediction or checkpoint was sent more than once or removed; look at that student's work before marking.

## Debrief Script (10 minutes)

1. Show the prediction spread for `assume`. Ask a student who answered "yes" what the current folder is when cron starts a job.
2. Ask: "How do you know the backup can be restored?" Lead to: you restored it somewhere else and compared the bytes.
3. Ask who has a pattern that also matches `NAME-notes.tar.gz`, and what it would delete in a real backup folder.
4. Name the limit: sorting by name works because the stamp is UTC and the format is fixed; a clock that moves back would break the order.

## Misconceptions

- `tar` compresses (it only packs; `z` calls gzip).
- A backup without an error message can be restored (only a restore test shows it).
- `*.tar.gz` identifies my archives (anything with that ending matches, including other people's files).
- Cron runs a job in my current folder with my environment (it does not).

Use the hints in order (`oslab hint lab10 1` to `3`).

## Caveats Moved Out of the Student Text

- `oslab check lab10` runs only the caller's own script, in disposable folders inside the lab folder, with a 20-second limit for each run, no input, and a copy of the project. It never touches the student's own `backups/`, and never uses cron.
- The retention deletes files, so a student's mistake can remove their own archives. It cannot reach other folders because the script computes its own folder; tell students never to test with a path like `~` or `/`.
- Cron may be absent or disabled (WSL). That is not a failure of the lab: the fallback line in `automation.txt` is the evidence. Do not enable services on the shared server.
- `oslab reset lab10` saves the current attempt and creates a fresh script. Do not suggest it for one wrong pattern.

## Fallback

Without the class inbox, everything works in practice mode: answers stay in the student's workspace, the checkpoint uses practice values, and you collect predictions by a show of hands. If the server is down, students can do the whole lab in WSL or a local Linux with the [local setup](../../../labs/SETUP.md).

## Topic Rubric (10 points)

| Evidence | Points |
|---|---:|
| Script: `oslab check lab10` passes the four Core milestones | 2 |
| Tests: `restore.txt` and `automation.txt` show the restore, the retention and the environment test, and the README states what was not tested | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab10` | 2 |
| Live checkpoint: the answers and the copy keeping the new number | 3 |
| Complete submission: the required files in the repository, on time | 1 |

Every row is suggested on the marking screen: row 1 from the best `oslab check` record, row 3 from the prediction (1) and the last debrief (1 when all its answers are right, 0.5 when at least half are), row 4 from the checkpoint, and row 5 from the website's file check of the repository. Row 2 needs your reading of the README.
