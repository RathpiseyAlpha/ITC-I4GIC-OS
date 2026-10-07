# OS Lab 10 - Backups, Archiving, Scheduling & cron Automation (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Lab 7 Bash paths/loops/status, basic tar usage |
| Required tools | `bash`, `tar`, `gzip`, `mktemp`, GNU `date`; Python 3 for the helper, personal cron if available |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** QuantumTech needs repeatable backups that can actually be restored. Package a small project, retain only three completed lab-owned archives, and diagnose execution under a restricted scheduling environment.

## Lab Objectives

After the required core, you should be able to:

1. Create/list/restore a project archive and distinguish archiving from compression.
2. Implement bounded retention for only the lab-owned completed archives.
3. Run the script with a restricted environment and verify/clean up a personal practice cron job when available.

**Extension objectives:** Schedule the repaired backup itself, rotate owned logs, implement a health snapshot, and design a guarded date-specific job from instructor-supplied dates/timezone. These retain the original lab's wider topics; they are not required to finish the two-hour core.

## Task Overview and 120-minute Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Introduction, objectives and setup |
| 10–25 | Guided example: commands and observations |
| 25–35 | Written prediction; optional five-minute peer comparison |
| 35–70 | Numbered individual investigation tasks; AI optional |
| 70–85 | Normal and edge tests; instructor feedback |
| 85–100 | Individual changed-case checkpoint; no AI or peers |
| 100–110 | Correction and conceptual explanation |
| 110–120 | Cleanup and submission |

Original Levels 0–2 automation/archive/backup are core, followed by Level 5 environment diagnosis and scoped practice scheduling. Expired dated graded jobs are replaced with observable in-class jobs. Log rotation/health/design-your-own remain extensions.

## Lab Setup (0–10 minutes)

1. Log in to the Ubuntu server using **your own account**. All commands below run as that ordinary user in Bash. Use only your own files and processes.
2. Check the helper. If it is unavailable, follow [the local setup guide](../SETUP.md) to define `oslab` from your cloned course repository; it uses the same fixtures.

   ```bash
   whoami
   command -v oslab
   oslab doctor
   ```

3. Start the lab and **enter its directory**. `oslab start` preserves existing work and does not change the current directory. If resuming, inspect existing files before running commands that write to them.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab10
   cd "$OSLAB_WORKSPACE/lab10"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab10/
   ├── .oslab-managed.json
   ├── backup.sh          # editable skeleton
   ├── project/
   │   ├── report.txt
   │   └── config.ini
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Levels 0–1 — Archiving and Restoration: Guided Example (10–25)

1. Inspect the project and create an owned archive directory.

   ```bash
   find project -maxdepth 2 -type f
   cat project/report.txt project/config.ini
   mkdir -p backups
   ```

2. Create and inspect an uncompressed archive, then a compressed archive. Both use a controlled relative member tree.

   ```bash
   tar -cf demo.tar -C "$PWD" project
   tar -tf demo.tar
   tar -czf demo.tar.gz -C "$PWD" project
   tar -tzf demo.tar.gz
   ls -l demo.tar demo.tar.gz
   ```

   `tar` combines files; `gzip` compresses their bytes. Very small archives can have overhead, so a specific compression ratio is not promised.

3. Restore the **known owned** demo archive into a new owned directory and compare bytes. Do not extract untrusted archives on the server.

   ```bash
   mkdir -p restore-demo
   tar -xzf demo.tar.gz -C restore-demo
   cmp -- project/report.txt restore-demo/project/report.txt
   cmp -- project/config.ini restore-demo/project/config.ini
   ```

   No `cmp` output with zero status means contents match. **Observe:** Is a successful archive creation the same as verifying recoverability? What does `-C` make independent of your current directory?

## Prediction (25–35)

Write: **A cron entry invokes `backup.sh` with no path, and the script assumes its working directory is the project. Must it work because it ran in your interactive shell? Identify two assumptions to verify.** Optional peer comparison is five minutes; no AI for the prediction.

## Level 2 — Backup Script and Retention (35–60)

1. Replace the skeleton with this starting implementation. It produces a completed archive atomically in the owned backup directory; retention remains your task.

   ```bash
   cat > backup.sh <<'SH'
   #!/usr/bin/env bash
   set -euo pipefail
   work=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
   mkdir -p "$work/backups"
   stamp=$(date -u +%Y%m%dT%H%M%S%N)
   final="$work/backups/backup-$stamp-$$.tar.gz"
   pending=$(mktemp "$work/backups/.pending-XXXXXX")
   trap 'rm -f -- "$pending"' EXIT
   tar -czf "$pending" -C "$work" project
   tar -tzf "$pending" >/dev/null
   mv -- "$pending" "$final"
   # TODO: retain only the newest three completed backup-*.tar.gz files.
   printf 'created %s\n' "$final"
   SH
   bash backup.sh
   ls -l backups
   ```

   Generated names sort by their UTC timestamp in this lab; a moving system clock is outside this exercise's assumptions. The script removes only its own pending file on failure. Completed archives are not removed until your retention policy is implemented.

2. Restore the new archive into a fresh directory. List it first, identify its `project/` members, then compare the two restored files. Save this normal test in `evidence/restore.txt`.

   ```bash
   archive=$(find backups -maxdepth 1 -type f -name 'backup-*.tar.gz' | sort | tail -n 1)
   mkdir -p restore-backup
   tar -tzf "$archive" | tee evidence/restore.txt
   tar -xzf "$archive" -C restore-backup
   cmp -- project/report.txt restore-backup/project/report.txt
   printf 'report comparison=%s\n' "$?" | tee -a evidence/restore.txt
   cmp -- project/config.ini restore-backup/project/config.ini
   printf 'config comparison=%s\n' "$?" | tee -a evidence/restore.txt
   ```
3. Implement retention in the TODO region. Requirements: inspect only the owned `backups/` directory, consider only the completed `backup-*.tar.gz` names generated by this script, keep the newest three, and preserve unrelated names. Use sorted names for the specified naming convention; do not use an unquoted `rm $(ls ...)` pipeline.
4. Create four backups sequentially and add an unrelated `backups/keep-me.txt`. Check that three matching archives remain and `keep-me.txt` still exists. Modify the project once between backups to distinguish versions.

   ```bash
   printf 'unrelated; preserve me\n' > backups/keep-me.txt
   bash backup.sh
   printf 'report v2\n' > project/report.txt
   bash backup.sh
   bash backup.sh
   find backups -maxdepth 1 -type f
   ```

   Count the initial run plus these three runs as four; if you already made extra runs, assess the same keep-three invariant. Do not delete by a broad path or scan your entire home.

**Hints:** (1) define owned names before deletion; (2) inspect a sorted array of completed archives; (3) iterate only over entries after the first three, quoting every full path. AI suggestions must be checked against the unrelated-file test.

## Levels 3/5 — Cron and the Environment Trap (60–70)

1. Run the backup from a different directory under a small environment.

   ```bash
   cd "$HOME"
   env -i HOME="$HOME" PATH=/usr/bin:/bin /bin/bash "$OSLAB_WORKSPACE/lab10/backup.sh"
   cd "$OSLAB_WORKSPACE/lab10"
   ```

   This tests path/environment assumptions, not actual cron delivery. The script's own-directory calculation should still find the project.

2. If personal cron and `lab10-cron` are available, inspect then install the one-minute heartbeat practice entry.

   ```bash
   lab10-cron status
   lab10-cron install
   crontab -l
   ```

   The helper creates one uniquely marked personal entry using an absolute command path. It leaves unrelated entries intact. It schedules a timestamp heartbeat, not your backup; scheduling the actual repaired backup is a separate optional extension.
3. While completing tests, allow up to two minutes for `cron.log` to show a timestamp. Cron may be absent/disabled in WSL; use the restricted-environment test and state that scheduling was unavailable. Do not enable services or edit `/etc/crontab` yourself.

Ordinary cron has five time fields (minute, hour, day of month, month, day of week) and no year field. A date-based entry recurs unless guarded or removed. The instructor supplies class dates in Asia/Phnom_Penh; check the server daemon's timezone rather than assuming `TZ` changes schedule interpretation.

## Tests and Feedback (70–85)

| Case | Expected evidence |
|---|---|
| Archive/restore | Member listing and matching restored bytes |
| Four sequential backups | Three completed lab-owned archives plus untouched unrelated file |
| Changed working directory/restricted environment | Backup still finds its source; bounded retention still holds |
| Personal cron, if available | Timestamp log and removal of only the marked entry |

Save retention, restricted-environment and cron/fallback evidence in `evidence/automation.txt`. Record what remains untested: backup consistency while a source changes concurrently, hostile archives, system-wide scheduling, or timezone behavior you did not inspect.

   ```bash
   {
     find backups -maxdepth 1 -type f
     printf 'completed archive count='
     find backups -maxdepth 1 -type f -name 'backup-*.tar.gz' | wc -l
     cat backups/keep-me.txt
   } > evidence/automation.txt
   ```

Append the restricted-environment result and cron observation or stated fallback with an editor. If cron ran, add `lab10-cron status` before and after removal; a saved crontab should contain only the relevant practice line, not unrelated personal schedules.

**Troubleshooting:** An empty cron log in the first seconds does not prove failure. Check user cron availability, absolute paths and stderr. `set -e` is not a replacement for understanding each command's status. See `man tar` and [crontab format](https://man7.org/linux/man-pages/man5/crontab.5.html).


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> A cron entry finds `/bin/bash` but runs a script containing `tar -czf backup.tar.gz project` without changing directory. Explain the likely path fault and one robust correction. Why does a five-field date entry not by itself mean “one time”?

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) How did you establish recoverability? (b) What prevented retention from deleting unrelated data? (c) Was actual scheduling observed or only the fallback environment tested?

## Cleanup and Final Submission (110–120 minutes)

If you installed the practice entry, run `lab10-cron remove`, then `lab10-cron status` and inspect `crontab -l`. Remove only the managed practice line, never the whole crontab. Save evidence before `oslab clean lab10`; retain only three completed lab-owned archives. A missing cron capability is reported, not silently claimed as tested.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab10/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- backup.sh "$SUBMISSION_REPO/lab10/"
   cp -- evidence/restore.txt evidence/automation.txt "$SUBMISSION_REPO/lab10/evidence/"
   ```

   ```text
   lab10/
   ├── README.md
   ├── backup.sh
   └── evidence/
       ├── restore.txt
       └── automation.txt   # retention, environment and cron or stated fallback
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Restorable archive and scoped keep-three retention (objectives 1–3) | 3 |
| Restore/retention/unrelated-file/restricted-environment evidence | 2 |
| Explain archive versus compression, paths and scheduling limits; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
