# OS Lab 10 - Backups, Archiving, Scheduling & cron Automation (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class. Before class: about 10 minutes for the pre-lab |
| Work | Individual. Your archive name and the number of archives to keep are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `bash`, `tar`, `gzip`, `mktemp`, GNU `date`, `cmp`, `nano`, `oslab`. Personal cron and `lab10-cron` if available |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Builds on | Lab 7 (Bash paths, loops and exit status) and Lab 6 (permissions) |

> **Scenario:** QuantumTech needs repeatable backups that can actually be restored. Package a small project, retain only a fixed number of completed lab-owned archives, and diagnose execution under a restricted scheduling environment.

## Lab Objectives

After the required core, you should be able to:

1. Create/list/restore a project archive and distinguish archiving from compression.
2. Implement bounded retention for only the lab-owned completed archives.
3. Run the script with a restricted environment and verify/clean up a personal practice cron job when available.

**Extension objectives:** Schedule the repaired backup itself, rotate owned logs, implement a health snapshot, and design a guarded date-specific job from instructor-supplied dates/timezone. These retain the original lab's wider topics; they are not required to finish the two-hour core. They are in the [optional extensions](extensions.md).

## How This Lab Works

| Command | What it does |
|---|---|
| `oslab values lab10` | Shows **your** archive name and the number of archives to keep |
| `oslab predict lab10` | Saves your prediction once, before the experiment |
| `oslab hint lab10 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab10` | Runs your `backup.sh` in a disposable folder and shows your milestones |
| `oslab checkpoint lab10` | Opens when the instructor says so, near the end |
| `oslab debrief lab10` | After the lab: you give the right answers to your prediction questions |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint. Always test what an AI tells you.
- In Core 1 you receive a script that already makes a complete archive. **You** write the retention, and you prove that it deletes nothing else.
- Delete only inside your own `backups/` folder, only names that your script made. Never use a broad path and never scan your home folder.

## Before the Lab

Do this before class. It takes about 10 minutes.

```bash
oslab doctor
oslab prelab lab10
```

## Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Setup |
| 10–25 | Guided: archiving and restoring |
| 25–35 | Prediction |
| 35–55 | Core 1: write the retention |
| 55–70 | Core 2: restricted environment and evidence |
| 70–85 | Instructor demonstration, Plus and Challenge |
| 85–100 | Live checkpoint |
| 100–110 | Debrief |
| 110–120 | Submit |

## Setup (0–10)

1. Log in to the server with your own account. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab10
   cd "$OSLAB_WORKSPACE/lab10"
   mkdir -p evidence
   oslab values lab10
   ```

2. **Read your personal values.** The last command prints the name of your archives and how many to keep. For example:

   ```text
   Your personal values for lab10 (your-account):
     keep     = 3
     name     = daily
   ```

   Your own word and number are different. Write them down. They are already written at the top of `backup.sh`.

3. **Understand the capital words.** This instruction cannot know your values, so it writes `NAME` and `KEEP` where they belong. Never type the capital words. Type your own word and number.

   | The instruction says | With the example values above, you type |
   |---|---|
   | `backups/NAME-*.tar.gz` | `backups/daily-*.tar.gz` |
   | keep the newest `KEEP` archives | keep the newest 3 archives |

4. Your folder now looks like this:

   ```text
   lab10/
   ├── .oslab-managed.json
   ├── backup.sh          # makes a complete archive; the retention is your TODO
   ├── project/
   │   ├── report.txt
   │   └── config.ini
   └── evidence/
   ```

5. Try the checking command once. The archive part already works; the retention does not.

   ```bash
   oslab check lab10
   ```

## Guided — Archiving and Restoring (10–25)

**Goal:** make an archive, look inside, restore it elsewhere, and compare.

1. Look at the project and make a folder for the archives.

   ```bash
   find project -maxdepth 2 -type f
   cat project/report.txt project/config.ini
   mkdir -p backups
   ```

2. Make an uncompressed archive and a compressed one. `-C` changes the folder for `tar` first, so the names inside start with `project/` wherever you are.

   ```bash
   tar -cf demo.tar -C "$PWD" project
   tar -tf demo.tar
   tar -czf demo.tar.gz -C "$PWD" project
   tar -tzf demo.tar.gz
   ls -l demo.tar demo.tar.gz
   ```

   `tar` packs many files into one. `gzip` (the `z`) compresses its bytes. A very small archive can be larger than expected: do not count on a ratio.

3. Restore your own demo archive into a new folder and compare the bytes. Never unpack archives from other people on the server.

   ```bash
   mkdir -p restore-demo
   tar -xzf demo.tar.gz -C restore-demo
   cmp -- project/report.txt restore-demo/project/report.txt
   cmp -- project/config.ini restore-demo/project/config.ini
   ```

   `cmp` prints nothing and ends with status `0` when the files are the same. **Observe:** is making an archive without an error the same as being able to restore it? What does `-C` make independent of your current folder?

## Prediction (25–35)

Guess first, then try. Answer alone, without AI.

```bash
oslab predict lab10
```

It asks four questions and one sentence, with your own name and number. A wrong guess costs nothing. You compare it with the real result in the debrief.

## Core 1 — Write the Retention (35–55)

**Goal:** after every run, only the newest `KEEP` complete archives named `NAME-...` stay in `backups/`. Everything else in that folder stays.

1. Read the script. Find where it makes a pending file, packs the project, tests the archive, and only then gives it its final name. Find the `TODO`.

   ```bash
   cat -n backup.sh
   ```

2. Run it once and restore the new archive, as in the guided part. Save this normal test in `evidence/restore.txt`.

   ```bash
   bash backup.sh
   archive=$(find backups -maxdepth 1 -type f -name 'NAME-*.tar.gz' | sort | tail -n 1)
   mkdir -p restore-backup
   tar -tzf "$archive" | tee evidence/restore.txt
   tar -xzf "$archive" -C restore-backup
   cmp -- project/report.txt restore-backup/project/report.txt
   printf 'report comparison=%s\n' "$?" | tee -a evidence/restore.txt
   cmp -- project/config.ini restore-backup/project/config.ini
   printf 'config comparison=%s\n' "$?" | tee -a evidence/restore.txt
   ```

3. **Your decision.** Open the script with `nano backup.sh` and write the retention at the `TODO`:

   - look only at your own `backups/` folder,
   - consider only the complete archives that this script makes: names of the form `NAME-STAMP-PID.tar.gz`, where `STAMP` is the UTC date and time that sorts correctly,
   - keep the newest `$keep`, remove the others, and leave every other name alone,
   - sort the names; do not use an unquoted `rm $(ls ...)`; quote every path; write `rm -- "$path"`.

4. Test it. Add files that are not yours. One of them looks like an archive name but is not one.

   ```bash
   printf 'unrelated; preserve me\n' > backups/keep-me.txt
   printf 'not an archive made by the script\n' > backups/NAME-notes.tar.gz
   for run in 1 2 3 4 5; do bash backup.sh; done
   ls backups
   ```

5. Count the archives. You must get your `KEEP`, and the two files that are not yours must still be there.

   ```bash
   find backups -maxdepth 1 -type f -name 'NAME-[0-9]*.tar.gz' | wc -l
   cat backups/keep-me.txt
   ```

**Hints:** `oslab hint lab10 1`, `2` and `3`. AI is allowed here; test every suggestion against the two files that are not yours.

## Core 2 — The Environment Trap (55–70)

**Goal:** a scheduled job does not start in your terminal. It has another current folder and almost no environment. Show that your script does not depend on either.

1. Run the backup from your home folder, under a small environment.

   ```bash
   cd "$HOME"
   env -i HOME="$HOME" PATH=/usr/bin:/bin /bin/bash "$OSLAB_WORKSPACE/lab10/backup.sh"
   cd "$OSLAB_WORKSPACE/lab10"
   ```

   This tests the assumptions about the folder and the environment. It is not real cron. The script finds its project because it computes its **own** folder.

2. Save the retention and environment evidence.

   ```bash
   {
     find backups -maxdepth 1 -type f
     printf 'completed archive count='
     find backups -maxdepth 1 -type f -name 'NAME-[0-9]*.tar.gz' | wc -l
     cat backups/keep-me.txt
     printf 'restricted environment: done\n'
   } > evidence/automation.txt
   ```

   If you can use cron (see Plus), add what you saw. If you cannot, add a line that says cron was **not** available, so that nobody believes it was tested.

3. Check your work. The four Core milestones must show `PASS`.

   ```bash
   oslab check lab10
   ```

   `oslab check` runs your `backup.sh` in a disposable folder: once, several times with extra files around, and under `env -i` from another folder. It does not use your own `backups/`.

4. Write down for your report: how did you establish that the archive is recoverable? What stopped the retention from deleting `keep-me.txt` and `NAME-notes.tar.gz`? What did you not test (a source that changes during the backup, hostile archives, real scheduling)?

## Instructor Demonstration, Plus and Challenge (70–85)

First, watch the instructor run the script from `/` with `env -i` and with a deliberate mistake: the relative path `project`. Then, if you finish early, try these. They are not needed for full marks. Save your answers in `evidence/plus.txt`.

**Plus**

- If personal cron and `lab10-cron` are available, install the one-minute practice entry, wait up to two minutes for `cron.log`, and remove it. It schedules a timestamp, not your backup. Never edit `/etc/crontab`, and never remove the whole crontab.

  ```bash
  lab10-cron status
  lab10-cron install
  crontab -l
  ```

  After you have seen a timestamp in `cron.log`, run `lab10-cron remove` and then `lab10-cron status`. Write what you saw. If cron is not available, say so.

**Challenge**

- A cron entry has five time fields: minute, hour, day of month, month, day of week. Write (as text, do not install it) the line that would run your `backup.sh` every day at 02:30, with the full path to the script. Why does an entry for one calendar date still run again next year?

## Live Checkpoint (85–100)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab10
```

1. Read the new rule (a different number to keep), and answer the four questions.
2. Then do the file task that the command prints: copy your script, change **only** the `keep=` line, run the copy several times, and save the list of archives in `checkpoint.txt`.
3. Run `oslab check lab10`. A fifth milestone, `checkpoint`, must show `PASS`. It fails if your retention has the old number written into its logic.

## Debrief (100–110)

Look at your prediction again. `oslab` saved it in a hidden folder, `.records`.

```bash
cat "$OSLAB_WORKSPACE/.records/lab10-predict.json"
```

Now give the right answer to each prediction question:

```bash
oslab debrief lab10
```

Your prediction stays saved as it was, so the comparison shows which answers you confirmed and which you corrected. Then the class discusses: your backup worked in your terminal. Which two assumptions would you check before you trust it under cron?

## Submit (110–120)

1. If you installed the practice cron entry, remove it first (`lab10-cron remove`) and check with `crontab -l`. Then copy your work to your course repository. Replace `YOUR_ID` with your own ID.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab10/evidence"
   cp -- backup.sh "$SUBMISSION_REPO/lab10/"
   cp -- evidence/restore.txt evidence/automation.txt "$SUBMISSION_REPO/lab10/evidence/"
   ```

   If you did Plus or Challenge, copy `evidence/plus.txt` the same way.

2. Fill in the [report template](README.md) as `lab10/README.md`. Your repository then has:

   ```text
   lab10/
   ├── README.md
   ├── backup.sh
   └── evidence/
       ├── restore.txt
       └── automation.txt   # retention, environment, and cron or the stated fallback
   ```

   The course website checks that these exact names are there.

3. Commit and push. `git pull` comes first, in case you pushed from your own computer since.

   ```bash
   cd ~/os-gic-YOUR_ID
   git pull
   git add os-lab-YOUR_ID/lab10
   git commit -m "Lab 10"
   git push
   ```

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Script: `oslab check lab10` passes the four Core milestones (restorable archive, retention, files that are not yours, restricted environment) | 2 |
| Tests: `restore.txt` and `automation.txt` show the restore, the retention and the environment test, and the README states what was not tested | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab10` | 2 |
| Live checkpoint: the answers and your copy keeping the new number | 3 |
| Complete submission: the required files in your repository, on time | 1 |

Every row is marked from your `oslab` records and the files in your repository, so run `oslab check lab10` until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.

## Help and References

- `oslab hint lab10 1`, `2`, `3`
- `man tar`, `man date`, `man crontab`; the [crontab format](https://man7.org/linux/man-pages/man5/crontab.5.html)
- Scheduling the backup itself, rotating logs, a health snapshot and date-specific jobs are in the [optional extensions](extensions.md).
