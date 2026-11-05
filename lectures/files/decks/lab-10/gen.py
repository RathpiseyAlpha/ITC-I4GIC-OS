"""Lab 10 guide, Backups, Archiving, Scheduling and cron Automation. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

Revised 2026-11-05 to the pilot-format instruction: a personal archive name and number to keep (NAME and KEEP),
Core 1 (the retention) and Core 2 (the restricted environment), Plus and Challenge, a live checkpoint,
oslab predict and oslab debrief. Modelled on the Lab 8 guide.

A guide for the lab session, built like the Lab 3 to Lab 9 guides with the shared look and the shared standard
slides in labkit.py. The concepts section is new: archiving versus compression, tar, restoring to prove a
backup, retention, and what cron does and does not give a script. The lab part follows
labs/lab10/lab10-instruction.md. Scheduling the repaired backup, log rotation and a health snapshot are
optional extensions in that instruction, so they come last (images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, flow, init)  # noqa: E402,F401

WEEK = "Lab 10"
TITLE = "Operating Systems — Lab 10"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-28T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 10)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-10", "Backups, Archives and cron",
                  "Lab 10 guide: package a project, prove it can be restored, keep only your own number of backups, and learn why cron is not your shell.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Create, list and restore a project archive, and tell archiving from compression.",
                    "Keep only the newest completed archives that this lab made, as many as your own number says, and nothing else.",
                    "Run the script in a bare environment, and check and clean up a practice cron job when cron is available."], ordered=True, size=34, flex=3),
            card(t, "Lab 10", "First the concepts, with examples. Then the lab on the server. Scheduling the real backup, log rotation and a health snapshot are optional extensions, so they come last.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "You made a backup last week. Can you restore it?",
         "A file that exists is not a backup that works. How would you find out before you need it?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Archives, retention and cron", "Four ideas: tar joins files, restoring proves a backup, retention must stay narrow, and cron runs in a bare environment.")

d.slide("tar-gzip", "tar joins files, gzip shrinks them",
        lambda t: row(term(t, ["tar -cf demo.tar -C \"$PWD\" project",
                               "tar -tf demo.tar",
                               "tar -czf demo.tar.gz -C \"$PWD\" project",
                               "tar -tzf demo.tar.gz"], size=24),
                      col(para(t, "tar combines files and folders into one archive. gzip compresses the bytes of that archive.", size=30),
                          para(t, "-c creates, -t lists, -x extracts, -f names the archive file, and -z adds gzip.", size=30),
                          para(t, "-C \"$PWD\" project stores the folder as project/..., so the paths inside do not depend on where you stood.", size=30),
                          gap=22),
                      gap=48, align="center"),
        note="A very small archive can be larger when compressed, so no compression ratio is promised.",
        label=BG)

d.slide("restore", "A backup is proven by restoring it",
        lambda t: row(term(t, ["mkdir -p restore-demo",
                               "tar -xzf demo.tar.gz -C restore-demo",
                               "cmp -- project/report.txt restore-demo/project/report.txt",
                               "cmp -- project/config.ini restore-demo/project/config.ini"], size=24),
                      col(para(t, "Extract into a new, empty folder you own. Then compare each file with the original.", size=30),
                          para(t, "cmp prints nothing and returns 0 when the bytes are equal. Creating an archive without error does not show it can be restored.", size=30),
                          card(t, "Only your own archives", "Extract only archives you made. Never extract an unknown archive on the server.", label="CAREFUL", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"),
        label=BG)

d.slide("retention", "Retention: keep a fixed number, touch nothing else",
        lambda t: row(card(t, "The policy", "Keep the newest completed archives that the script made, as many as your keep value says. Remove older ones.", label="RULE", pad=40, title_size=36),
                      card(t, "Narrow on purpose", "Look only in your own backups/ folder. Consider only names like NAME-*.tar.gz, with your own name. Leave every other file alone.", label="SCOPE", pad=40, title_size=36),
                      card(t, "A safe deletion", "Sort the names, skip the newest ones you keep, and remove the rest. Quote every path. Never write rm $(ls ...).", label="HOW", pad=40, title_size=36),
                      gap=32, align="stretch"),
        label=BG)

d.slide("cron", "What cron gives a script",
        lambda t: row(tbl(t, ["Field", "Range", "Example"],
                          [["Minute", "0 to 59", "*/5 is every five minutes"],
                           ["Hour", "0 to 23", "2 is 02:00"],
                           ["Day of month", "1 to 31", "*"],
                           ["Month", "1 to 12", "*"],
                           ["Day of week", "0 to 7", "1 is Monday"]],
                          [3, 3, 6], width=HALF),
                      col(para(t, "A cron line has five time fields and a command. There is no year, so a date entry comes back every year unless something guards or removes it.", size=30),
                          para(t, "Cron starts the job in your home folder, with a small environment. Your shell's PATH and settings are not there.", size=30),
                          para(t, "Use absolute paths, and let the script find its own folder.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 10", "Backups you can restore", "QuantumTech needs repeatable backups that work. Package a project, keep your own number of archives, and test under a bare environment.")

START_TREE = [("backup.sh", None), ("project", [("config.ini", None), ("report.txt", None)]), ("evidence", [])]

labkit.scenario(d, 10, "QuantumTech's backups", "Package a small project, keep only a fixed number of completed archives that this lab made, and diagnose how the script runs in a restricted scheduling environment.",
                "Your archive name and the number to keep are your own. This guide shows example values.", START_TREE)
labkit.timetable(d, [["0 to 10", "Setup"],
                     ["10 to 25", "Guided: archiving and restoring"],
                     ["25 to 35", "Prediction"],
                     ["35 to 55", "Core 1: write the retention"],
                     ["55 to 70", "Core 2: restricted environment and evidence"]],
                 [["70 to 85", "Instructor demonstration, Plus and Challenge"],
                  ["85 to 100", "Live checkpoint"],
                  ["100 to 110", "Debrief"],
                  ["110 to 120", "Submit"]])

d.slide("helper", "Six helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does"],
                      [[mono("oslab values lab10"), "Shows your archive name and the number of archives to keep"],
                       [mono("oslab predict lab10"), "Saves your prediction once, before the experiment"],
                       [mono("oslab hint lab10 1"), "A hint, levels 1 to 3. Hints cost no points"],
                       [mono("oslab check lab10"), "Runs your backup.sh in a disposable folder and shows your milestones"],
                       [mono("oslab checkpoint lab10"), "Opens when the instructor says so, near the end"],
                       [mono("oslab debrief lab10"), "After the lab: you give the right answers to your prediction questions"]],
                      [5, 11]),
        note="Before the lab, run oslab doctor and oslab prelab lab10. It takes about ten minutes.")

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Core, Plus, Challenge", "Core is for everyone. Plus and Challenge are for students who finish early. Full marks need only Core and the checkpoint.", title_size=36),
                      rule(t, "AI tools", "Allowed in Core, Plus and Challenge, so test every suggestion. Not allowed in the prediction and the checkpoint.", title_size=36),
                      rule(t, "You write the retention", "You receive a script that already makes a complete archive. You write the retention, and you prove that it deletes nothing else.", title_size=36)),
        note="Delete only inside your own backups/ folder, only names that your script made. Never use a broad path, never scan your home folder, never edit /etc/crontab. A wrong prediction costs nothing.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ['export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab10",
                               'cd "$OSLAB_WORKSPACE/lab10"',
                               "mkdir -p evidence",
                               "oslab values lab10"], title="student@server: ~", size=26),
                      col(lst(t, ["The first line sets OSLAB_WORKSPACE to ~/oslab-work, unless it is already set. Type it as it is.",
                                  "oslab start lab10 makes the lab folder.",
                                  "cd takes you into it, and mkdir -p makes the evidence folder.",
                                  "oslab values lab10 prints your archive name and your number."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("values", "Your values: a name and a number",
        lambda t: row(col(h3(t, "The last command prints them"),
                          term(t, ["oslab values lab10",
                                   ("out", "Your personal values for lab10 (your-account):"),
                                   ("out", "  keep     = 3"),
                                   ("out", "  name     = daily")], title="example: your values will be different", size=26),
                          gap=20, flex=None),
                      col(h3(t, "What they mean"),
                          lst(t, ["name is the start of the name of every archive your script makes.",
                                  "keep is how many completed archives stay.",
                                  "Both are already written at the top of backup.sh. Write them down."], size=30),
                          gap=20, flex=None),
                      gap=48, align="flex-start"))

d.slide("capital", "The capital words are placeholders",
        lambda t: tbl(t, ["The instruction says", "With the example values, you type"],
                      [[mono("backups/NAME-*.tar.gz"), mono("backups/daily-*.tar.gz")],
                       ["keep the newest " + mono("KEEP") + " archives", "keep the newest 3 archives"]],
                      [1, 1]),
        note="The instruction cannot know your values, so it writes NAME and KEEP where they belong. Never type the capital words. Type your own word and number.")

d.slide("start-tree", "Your folder",
        lambda t: row(tree(t, "lab10", START_TREE, cmd="tree -a -L 3", title="student@server: ~/oslab-work/lab10", size=30),
                      col(para(t, "backup.sh makes a complete archive. The retention is your TODO.", size=32),
                          para(t, "project/ is the small project to back up: report.txt and config.ini.", size=32),
                          para(t, "oslab check lab10 now passes the archive part. The retention does not pass yet. The hidden .oslab-managed.json is the helper's. Leave it.", size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Archive and restore", "Ten to twenty-five minutes, with the instructor. Make an archive, look inside, restore it elsewhere, and compare.")

d.slide("g-look", "Step 1: look at the project",
        lambda t: row(term(t, ["find project -maxdepth 2 -type f",
                               "cat project/report.txt project/config.ini",
                               "mkdir -p backups"], size=26),
                      col(para(t, "find lists the files of the project, down to two levels. cat shows what they hold.", size=32),
                          para(t, "mkdir -p backups makes the folder that will hold your archives.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-tar", "Step 2: an archive, then a compressed one",
        lambda t: row(term(t, ["tar -cf demo.tar -C \"$PWD\" project",
                               "tar -tf demo.tar",
                               "tar -czf demo.tar.gz -C \"$PWD\" project",
                               "tar -tzf demo.tar.gz",
                               "ls -l demo.tar demo.tar.gz"], size=24),
                      col(para(t, "-C changes the folder for tar first, so the names inside start with project/ wherever you are.", size=30),
                          para(t, "tar packs many files into one. gzip, the z, compresses its bytes. A very small archive can be larger than expected: do not count on a ratio.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-restore", "Step 3: restore the demo and compare",
        lambda t: row(term(t, ["mkdir -p restore-demo",
                               "tar -xzf demo.tar.gz -C restore-demo",
                               "cmp -- project/report.txt restore-demo/project/report.txt",
                               "cmp -- project/config.ini restore-demo/project/config.ini"], size=24),
                      col(para(t, "cmp prints nothing and ends with status 0 when the files are the same. Never unpack archives from other people on the server.", size=30),
                          card(t, "Observe", "Is making an archive without an error the same as being able to restore it? What does -C make independent of your current folder?", label="THINK", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- prediction ---------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you write the retention. Ten minutes.")

d.slide("predict", "The prediction",
        lambda t: row(col(term(t, ["oslab predict lab10"]),
                          para(t, "It asks four questions and one sentence, with your own name and number. Answer alone, without AI.", size=32),
                          gap=24, flex=3),
                      col(card(t, "The rules", "The first answer is the one that counts. A wrong guess costs nothing. You compare it with the real result in the debrief.", label="PREDICTION", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

# ---- core 1 ---------------------------------------------------------------------
d.opener("c1-open", "CORE 1", "Write the retention", "Twenty minutes, from minute 35 to 55. After every run, only the newest KEEP complete archives named NAME stay in backups/.")

B1 = ["#!/usr/bin/env bash",
      "set -euo pipefail",
      "keep=3",
      "name=daily",
      'work=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)',
      'mkdir -p "$work/backups"',
      "stamp=$(date -u +%Y%m%dT%H%M%S%N)",
      'final="$work/backups/$name-$stamp-$$.tar.gz"',
      'pending=$(mktemp "$work/backups/.pending-XXXXXX")',
      "trap 'rm -f -- \"$pending\"' EXIT",
      'tar -czf "$pending" -C "$work" project',
      'tar -tzf "$pending" >/dev/null',
      'mv -- "$pending" "$final"',
      "# TODO: retain only the newest $keep completed $name-*.tar.gz files.",
      "printf 'created %s\\n' \"$final\""]

d.slide("c1-code", "Step 1: read your script",
        lambda t: row(listing(t, B1, title="backup.sh (example values)", size=24, hot=(13,), lh=1.15),
                      col(para(t, "Read it with cat -n backup.sh. The keep= and name= lines hold your own values.", size=28),
                          para(t, "work is the folder that holds the script, so it works from any folder. The archive is built under a temporary name and moved into place only when complete.", size=28),
                          para(t, "trap removes the temporary file if something fails. The orange TODO is your work: the retention.", size=28),
                          gap=18, flex=None),
                      gap=40, align="center"))

d.slide("c1-restore", "Step 2: run it once, restore, and save the proof",
        lambda t: row(term(t, ["bash backup.sh",
                               "archive=$(find backups -maxdepth 1 -type f -name 'daily-*.tar.gz' | sort | tail -n 1)",
                               "mkdir -p restore-backup",
                               'tar -tzf "$archive" | tee evidence/restore.txt',
                               'tar -xzf "$archive" -C restore-backup',
                               "cmp -- project/report.txt restore-backup/project/report.txt",
                               "printf 'report comparison=%s\\n' \"$?\" | tee -a evidence/restore.txt",
                               "cmp -- project/config.ini restore-backup/project/config.ini",
                               "printf 'config comparison=%s\\n' \"$?\" | tee -a evidence/restore.txt"], title="example name: use your own", size=24),
                      col(para(t, "The find line finds the newest completed archive: sort puts the names in order, and tail -n 1 takes the last.", size=28),
                          para(t, "List it first, then extract and compare both files. tee saves a copy as evidence.", size=28),
                          gap=20),
                      gap=40, align="center"))

d.slide("c1-retain", "Step 3: your decision, the retention",
        lambda t: row(col(h3(t, "Open nano backup.sh and write it at the TODO"),
                          lst(t, ["Look only at your own backups/ folder.",
                                  "Consider only the complete archives this script makes: NAME-STAMP-PID.tar.gz.",
                                  "Keep the newest $keep, remove the others, and leave every other name alone.",
                                  "Sort the names. No unquoted rm $(ls ...). Quote every path, and write rm -- \"$path\"."], size=30),
                          gap=20, flex=3),
                      col(card(t, "You write it", "Nobody gives you the lines. Define the owned names before you delete. Loop only over the entries after the first $keep, with every path quoted.", label="YOUR TURN", pad=32, title_size=32),
                          card(t, "Hints", "oslab hint lab10 1, then 2, then 3. AI is allowed here: test every suggestion against the two files that are not yours.", label="STUCK?", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c1-test", "Steps 4 and 5: test it with files that are not yours",
        lambda t: row(term(t, ["printf 'unrelated; preserve me\\n' > backups/keep-me.txt",
                               "printf 'not an archive made by the script\\n' > backups/daily-notes.tar.gz",
                               "for run in 1 2 3 4 5; do bash backup.sh; done",
                               "ls backups",
                               "find backups -maxdepth 1 -type f -name 'daily-[0-9]*.tar.gz' | wc -l",
                               "cat backups/keep-me.txt"], title="example name: use your own", size=24),
                      col(para(t, "One of the extra files looks like an archive name but is not one.", size=30),
                          card(t, "Check", "You must count exactly your keep number of archives, and both files that are not yours must still be there.", label="TRY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- core 2 ---------------------------------------------------------------------
d.opener("c2-open", "CORE 2", "The environment trap", "Fifteen minutes, from minute 55 to 70. A scheduled job has another folder and almost no environment.")

d.slide("c2-env", "Step 1: run it under a bare environment",
        lambda t: row(term(t, ['cd "$HOME"',
                               'env -i HOME="$HOME" PATH=/usr/bin:/bin /bin/bash "$OSLAB_WORKSPACE/lab10/backup.sh"',
                               'cd "$OSLAB_WORKSPACE/lab10"'], size=24),
                      col(para(t, "env -i starts the command with an empty environment, and then only HOME and PATH are set. This is close to what cron gives a job.", size=30),
                          para(t, "This tests the assumptions about the folder and the environment. It is not real cron. The script finds its project because it computes its own folder.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-save", "Step 2: save the evidence",
        lambda t: row(term(t, ["{",
                               "  find backups -maxdepth 1 -type f",
                               "  printf 'completed archive count='",
                               "  find backups -maxdepth 1 -type f -name 'daily-[0-9]*.tar.gz' | wc -l",
                               "  cat backups/keep-me.txt",
                               "  printf 'restricted environment: done\\n'",
                               "} > evidence/automation.txt"], title="example name: use your own", size=24),
                      col(para(t, "If you can use cron (see Plus), add what you saw. If you cannot, add a line that says cron was not available, so that nobody believes it was tested.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-check", "Steps 3 and 4: check, then explain",
        lambda t: row(term(t, ["oslab check lab10"], size=28),
                      col(para(t, "The four Core milestones must show PASS: a restorable archive, the retention, the files that are not yours, and the restricted environment.", size=28),
                          para(t, "oslab check runs your backup.sh in a disposable folder: once, several times with extra files around, and under env -i from another folder. It does not use your own backups/.", size=28),
                          card(t, "Write down for your report", "How did you establish that the archive is recoverable? What stopped the retention from deleting your extra files? What did you not test?", label="REPORT", pad=32, title_size=32),
                          gap=18),
                      gap=48, align="center"))

d.slide("c2-table", "What each case shows",
        lambda t: tbl(t, ["Case", "Expected evidence"],
                      [["Archive and restore", "The member list, and restored files with the same bytes"],
                       ["Several backups in a row", "Your keep number of completed archives, and the files that are not yours untouched"],
                       ["Another folder, bare environment", "The backup still finds its source, and retention still holds"],
                       ["Personal cron, if available", "A timestamp in the log, and only the marked entry removed afterwards"]],
                      [5, 10]),
        note="Write what you did not test: a source that changes during the backup, hostile archives, real scheduling.")

# ---- demonstration, plus and challenge ----------------------------------------------------
d.slide("plus", "Plus: a practice cron job",
        lambda t: row(term(t, ["lab10-cron status",
                               "lab10-cron install",
                               "crontab -l",
                               "lab10-cron remove",
                               "lab10-cron status"], size=26),
                      col(para(t, "The helper adds one marked entry of your own that appends a timestamp every minute. It does not run your backup.", size=28),
                          para(t, "Wait up to two minutes for cron.log, then remove it. Write what you saw, or that cron is not available.", size=28),
                          card(t, "Careful", "Never edit /etc/crontab, and never remove the whole crontab.", label="PLUS", pad=32, title_size=32),
                          gap=20),
                      gap=48, align="center"),
        note="First watch the instructor run the script from / with env -i and with a deliberate mistake: the relative path project. Save your answers in evidence/plus.txt. Plus and Challenge are not needed for full marks.")

d.slide("challenge", "Challenge: a cron line, as text",
        lambda t: row(term(t, ["# minute hour day-of-month month day-of-week command",
                               "30 2 * * * /full/path/to/backup.sh"], size=26),
                      col(para(t, "A cron entry has five time fields. Write the line that would run your backup.sh every day at 02:30, with the full path to the script. Do not install it.", size=30),
                          card(t, "Answer in evidence/plus.txt", "Why does an entry for one calendar date still run again next year?", label="CHALLENGE", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- live checkpoint ------------------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "The number is new", "The rule uses a different number to keep, made for you at that moment. An answer copied from a neighbour does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once, so a common mistake can be explained before the next lab.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task, with their own number.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab10", "Read the new rule, answer four questions"),
                           ("3. The file task", "Copy your script, change keep= only"), ("4. oslab check lab10", "A fifth milestone must pass")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command says that the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab10 shows whether the fifth milestone passes. It fails if your retention has the old number written into its logic.", title_size=36)),
        gap=56)

d.slide("cp-marks", "What the checkpoint asks",
        lambda t: tbl(t, ["Part", "What you do"],
                      [["Four questions", "Read the new rule, with a different number to keep. Answer in the terminal."],
                       ["The file task", "Copy your script, change only the keep= line, run the copy several times, and save the list of archives in checkpoint.txt."],
                       ["The check", "Run oslab check lab10. The fifth milestone, checkpoint, must show PASS."]],
                      [4, 13]),
        note="This is why the retention uses the variable $keep, not a number written into its logic.")

# ---- debrief and submit ---------------------------------------------------------------------
d.opener("end-open", "DEBRIEF AND SUBMIT", "Look back, then hand in", "Ten minutes of debrief, ten to submit.")

d.slide("debrief", "Debrief: look at your prediction again",
        lambda t: row(term(t, ['cat "$OSLAB_WORKSPACE/.records/lab10-predict.json"',
                               "oslab debrief lab10"], size=24, title="student@server: ~/oslab-work/lab10"),
                      col(para(t, "oslab saved your prediction in a hidden folder, .records. It stays as it was, so the comparison shows which answers you confirmed and which you corrected.", size=30),
                          card(t, "Class discussion", "Your backup worked in your terminal. Which two assumptions would you check before you trust it under cron?", label="DISCUSS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

labkit.submission(d, 10, ['cp -- backup.sh "$SUBMISSION_REPO/lab10/"',
                          'cp -- evidence/restore.txt evidence/automation.txt "$SUBMISSION_REPO/lab10/evidence/"'],
                  [("README.md", None), ("backup.sh", None), ("evidence", [("restore.txt", None), ("automation.txt", None)])],
                  note="If you installed the practice cron entry, run lab10-cron remove first, and check with crontab -l. If you did Plus or Challenge, copy evidence/plus.txt the same way.")

d.slide("submit-git", "Submit 3: commit and push",
        lambda t: row(term(t, ["cd ~/os-gic-YOUR_ID",
                               "git pull",
                               "git add os-lab-YOUR_ID/lab10",
                               'git commit -m "Lab 10"',
                               "git push"], title="student@server: ~", size=26),
                      col(para(t, "git pull comes first, in case you pushed from your own computer since.", size=32),
                          para(t, "Replace YOUR_ID with your own ID, as before. The course website checks that the exact file names are there.", size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.grading(d, [["Script: oslab check lab10 passes the four Core milestones (restorable archive, retention, files that are not yours, restricted environment)", "2"],
                   ["Tests: restore.txt and automation.txt show the restore, the retention and the environment test, and the README states what was not tested", "2"],
                   ["Prediction saved in time, and corrected with oslab debrief lab10", "2"],
                   ["Live checkpoint: the answers and your copy keeping the new number", "3"],
                   ["Complete submission: the required files in your repository, on time", "1"]],
               note="Every row is marked from your oslab records and the files in your repository, so run oslab check lab10 until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.")

labkit.mistakes(d, [["rm $(ls backups)", "Unrelated files removed", "Sort the matching names, quote every path"],
                    ["Relative paths in the script", "It works in your shell, fails in cron", "Find the script's own folder first"],
                    ["Trusting a backup you never restored", "A corrupt or incomplete archive", "Extract it and compare with cmp"],
                    ["The number written into the logic", "The checkpoint copy keeps the old number", "Use $keep everywhere, change only keep="],
                    ["Leaving the practice cron entry", "A job that keeps running after the lab", "lab10-cron remove, then check crontab -l"]])

# ---- beyond the core --------------------------------------------------------------
d.opener("ext-open", "BEYOND THE CORE", "Schedule it, rotate logs, a health snapshot", "Optional extensions. They need your own cron and dates the instructor gives you.")

d.slide("ext-sched", "Schedule the repaired backup",
        lambda t: col(term(t, ["crontab -l",
                               "*/5 * * * * /bin/bash /home/student/oslab-work/lab10/backup.sh >> /home/student/oslab-work/lab10/cron.log 2>&1"], size=24),
                      row(para(t, "Install it only after backup.sh works under the bare environment. Use absolute paths for the shell, the script and the log.", size=30),
                          para(t, "2&gt;&amp;1 sends error messages to the log too, so you can see why a run failed. Remove the entry when you have seen it run.", size=30),
                          gap=48, align="flex-start"),
                      gap=36),
        label=EXT)

d.slide("ext-more", "Logs, a health snapshot, a guarded date job",
        lambda t: row(card(t, "Rotate your own logs", "Move an owned log to a dated name and start a new one, but never while a job is writing it.", label="LOGS", pad=32, title_size=32),
                      card(t, "A health snapshot", "A small script that saves df -h, uptime and the newest backup name to one file, and is safe to run again.", label="HEALTH", pad=32, title_size=32),
                      card(t, "A guarded date job", "Cron has no year. Use dates and the Asia/Phnom_Penh time zone from the instructor, and make the script check the date itself.", label="DATES", pad=32, title_size=32),
                      gap=32, align="stretch"),
        note="Check which time zone the cron daemon on the server uses. Changing TZ in your shell does not change how the schedule is read.",
        label=EXT)

d.close([("Archive, then compress", "tar joins the files. gzip shrinks the bytes. -C keeps the paths inside the archive stable."),
         ("Restore to prove it", "A backup is a backup when you have extracted it and compared the bytes."),
         ("Keep the scope narrow", "Retention touches only the names this script made, in your own folder."),
         ("cron is a bare shell", "Absolute paths, no assumptions about your folder, and test with env -i first.")],
        "chapter 14, File-System Implementation", ("Lab 11 (bonus): disk management utilities", "Look at disks, partitions and filesystems, with tools that only read."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: tar and gzip, restoring to prove a backup, retention, and what cron gives a script.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the rules, setup and the starting tree.", "start": "lab-open"},
    "s4": {"description": "Guided: archive and restore, then the prediction.", "start": "g-open"},
    "s5": {"description": "Core 1 and Core 2: write the retention and test the restricted environment, then Plus and Challenge.", "start": "c1-open"},
    "s6": {"description": "The live checkpoint: why, the steps with oslab, and what it asks.", "start": "cp-open"},
    "s7": {"description": "Debrief, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: scheduling the real backup, logs, health and date jobs, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
