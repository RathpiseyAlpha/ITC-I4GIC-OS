"""Lab 10 guide, Backups, Archiving, Scheduling and cron Automation. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

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
                  "Lab 10 guide: package a project, prove it can be restored, keep only three backups, and learn why cron is not your shell.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Create, list and restore a project archive, and tell archiving from compression.",
                    "Keep only the newest three completed archives that this lab made, and nothing else.",
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

d.slide("retention", "Retention: keep three, touch nothing else",
        lambda t: row(card(t, "The policy", "Keep the newest three completed archives that the script made. Remove older ones.", label="RULE", pad=40, title_size=36),
                      card(t, "Narrow on purpose", "Look only in your own backups/ folder. Consider only names like backup-*.tar.gz. Leave every other file alone.", label="SCOPE", pad=40, title_size=36),
                      card(t, "A safe deletion", "Sort the names, skip the first three, and remove the rest. Quote every path. Never write rm $(ls ...).", label="HOW", pad=40, title_size=36),
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
d.opener("lab-open", "LAB 10", "Backups you can restore", "QuantumTech needs repeatable backups that work. Package a project, keep three, and test under a bare environment.")

START_TREE = [("backup.sh", None), ("project", [("config.ini", None), ("report.txt", None)]), ("evidence", [])]

labkit.scenario(d, 10, "QuantumTech's backups", "Package a small project, keep only three completed archives that this lab made, and diagnose how the script runs in a restricted scheduling environment.",
                "Dated, graded cron jobs from the old lab are replaced by jobs you can watch in class.", START_TREE)
labkit.timetable(d, [["0 to 10", "Introduction, objectives and setup"],
                     ["10 to 25", "Levels 0 and 1, guided: archive and restore"],
                     ["25 to 35", "Written prediction"],
                     ["35 to 60", "Level 2: the backup script and retention"]],
                 [["60 to 70", "Levels 3 and 5: cron and the environment"],
                  ["70 to 85", "Tests and feedback"],
                  ["85 to 100", "Individual changed-case checkpoint"],
                  ["100 to 120", "Correction, cleanup and submission"]])
labkit.rules(d, safety="Do not enable services or edit /etc/crontab. Do not extract unknown archives.")
labkit.setup_slides(d, 10, START_TREE,
                    ["backup.sh is an editable skeleton.",
                     "project/ is the small project to back up: report.txt and config.ini.",
                     "The helper also writes a hidden file, .oslab-managed.json. Leave it as it is."])

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Archive and restore", "Levels 0 and 1, with the instructor: fifteen minutes.")

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
                      col(para(t, "Both archives use the same controlled member tree: project/....", size=32),
                          card(t, "Observe", "Which file is smaller? Is that always true for very small archives? What does -C make independent of your current folder?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-restore", "Step 3: restore the demo and compare",
        lambda t: row(term(t, ["mkdir -p restore-demo",
                               "tar -xzf demo.tar.gz -C restore-demo",
                               "cmp -- project/report.txt restore-demo/project/report.txt",
                               "cmp -- project/config.ini restore-demo/project/config.ini"], size=24),
                      col(para(t, "No output and status 0 mean the contents match.", size=32),
                          card(t, "Observe", "Is a successful archive creation the same as checking that you can recover? What did you check just now?", label="THINK", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.predict(d, "A cron entry runs backup.sh with no path, and the script assumes its working folder is the project. Must it work because it ran in your interactive shell? Name two assumptions you would verify.")

# ---- level 2 ---------------------------------------------------------------
d.opener("l2-open", "LEVEL 2", "The backup script and retention", "Twenty-five minutes, from minute 35 to 60. Work alone.")

B1 = ["#!/usr/bin/env bash",
      "set -euo pipefail",
      'work=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)',
      'mkdir -p "$work/backups"',
      "stamp=$(date -u +%Y%m%dT%H%M%S%N)",
      'final="$work/backups/backup-$stamp-$$.tar.gz"',
      'pending=$(mktemp "$work/backups/.pending-XXXXXX")',
      "trap 'rm -f -- \"$pending\"' EXIT",
      'tar -czf "$pending" -C "$work" project',
      'tar -tzf "$pending" >/dev/null',
      'mv -- "$pending" "$final"',
      "# TODO: retain only the newest three completed backup-*.tar.gz files.",
      "printf 'created %s\\n' \"$final\""]

d.slide("l2-code", "Step 1: the starting script",
        lambda t: row(listing(t, B1, title="backup.sh", size=24, hot=(11,), lh=1.15),
                      col(para(t, "Save it as backup.sh and run it with bash backup.sh. set -euo pipefail stops the script on an error, on an unset variable, or when a command in a pipeline fails.", size=28),
                          para(t, "work is the folder that holds the script (BASH_SOURCE[0] is its path, dirname drops the file name, pwd -P prints the real folder), so it works from any folder.", size=28),
                          para(t, "The archive is built under a temporary name and moved into place only when complete. trap removes the temporary file if something fails. The orange TODO is your work: retention.", size=28),
                          gap=18, flex=None),
                      gap=40, align="center"))

d.slide("l2-restore", "Step 2: restore the new archive, and save the proof",
        lambda t: row(term(t, ["archive=$(find backups -maxdepth 1 -type f -name 'backup-*.tar.gz' | sort | tail -n 1)",
                               "mkdir -p restore-backup",
                               "tar -tzf \"$archive\" | tee evidence/restore.txt",
                               "tar -xzf \"$archive\" -C restore-backup",
                               "cmp -- project/report.txt restore-backup/project/report.txt",
                               "printf 'report comparison=%s\\n' \"$?\" | tee -a evidence/restore.txt"], size=24),
                      col(para(t, "The first line finds the newest completed archive: sort puts the names in order, and tail -n 1 takes the last.", size=30),
                          para(t, "List it first, then extract and compare. Do the same for config.ini. tee saves a copy as evidence.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("l2-retain", "Step 3: write the retention",
        lambda t: row(col(h3(t, "Requirements"),
                          lst(t, ["Look only in your own backups/ folder.",
                                  "Consider only the backup-*.tar.gz names this script makes.",
                                  "Keep the newest three. Leave all other names alone.",
                                  "Do not use an unquoted rm $(ls ...)."], size=32),
                          gap=20, flex=3),
                      col(card(t, "You write it", "Hints: define the owned names before you delete. Put the completed archives in a sorted array. Loop only over the entries after the first three, with every path quoted.", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("l2-four", "Step 4: four backups, and a file that must survive",
        lambda t: row(term(t, ["printf 'unrelated; preserve me\\n' > backups/keep-me.txt",
                               "bash backup.sh",
                               "printf 'report v2\\n' > project/report.txt",
                               "bash backup.sh",
                               "bash backup.sh",
                               "find backups -maxdepth 1 -type f"], size=24),
                      col(para(t, "Count the first run and these three as four backups. Three archives and keep-me.txt must remain.", size=32),
                          para(t, "Change the project once between backups, so that the versions differ. Never delete by a broad path, and never scan your whole home.", size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- levels 3 and 5 ---------------------------------------------------------------
d.opener("l3-open", "LEVELS 3 AND 5", "Cron and the environment trap", "Ten minutes, from minute 60 to 70.")

d.slide("l3-env", "Step 1: run it under a bare environment",
        lambda t: row(term(t, ['cd "$HOME"',
                               'env -i HOME="$HOME" PATH=/usr/bin:/bin /bin/bash "$OSLAB_WORKSPACE/lab10/backup.sh"',
                               'cd "$OSLAB_WORKSPACE/lab10"'], size=24),
                      col(para(t, "env -i starts the command with an empty environment, and then only HOME and PATH are set. This is close to what cron gives a job.", size=30),
                          para(t, "This tests path and environment assumptions. It is not real cron delivery.", size=30),
                          para(t, "The script's own-folder line should still find the project.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("l3-cron", "Step 2: a practice cron job",
        lambda t: row(term(t, ["lab10-cron status",
                               "lab10-cron install",
                               "crontab -l"], size=28),
                      col(para(t, "The helper adds one uniquely marked entry of your own, with an absolute path, and leaves the others alone.", size=30),
                          para(t, "It writes a timestamp every minute. It does not run your backup.", size=30),
                          card(t, "Wait up to two minutes", "cron.log should show a timestamp. Cron may be missing in WSL. Then say that scheduling was not available, and use the bare-environment test.", label="CAREFUL", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- tests ---------------------------------------------------------------------
d.opener("test-open", "TESTS AND FEEDBACK", "Four cases, and what is untested", "Fifteen minutes, from minute 70 to 85.")

d.slide("tests-table", "The four cases",
        lambda t: tbl(t, ["Case", "Expected evidence"],
                      [["Archive and restore", "The member list, and restored files with the same bytes"],
                       ["Four backups in a row", "Three completed archives, and the unrelated file untouched"],
                       ["Another folder, bare environment", "The backup still finds its source, and retention still holds"],
                       ["Personal cron, if available", "A timestamp in the log, and only the marked entry removed afterwards"]],
                      [5, 10]),
        note="Save the retention, bare-environment and cron or fallback evidence in evidence/automation.txt. Write what you did not test: a source that changes during the backup, hostile archives, system-wide scheduling, time zones.")

d.slide("tests-auto", "Save the evidence",
        lambda t: row(term(t, ["{",
                               "  find backups -maxdepth 1 -type f",
                               "  printf 'completed archive count='",
                               "  find backups -maxdepth 1 -type f -name 'backup-*.tar.gz' | wc -l",
                               "  cat backups/keep-me.txt",
                               "} > evidence/automation.txt"], size=24),
                      col(para(t, "Then add the bare-environment result and the cron observation, or your fallback statement, with an editor.", size=30),
                          para(t, "If cron ran, add lab10-cron status before and after the removal. The saved crontab should hold only the practice line.", size=30),
                          para(t, "An empty log in the first seconds is not a failure. Check cron is available, the paths are absolute, and stderr.", size=30),
                          gap=22),
                      gap=48, align="center"))

# ---- checkpoint, correction, submission -------------------------------------------
labkit.checkpoint(d, "A cron entry finds /bin/bash, but runs a script that contains tar -czf backup.tar.gz project without changing folder. Explain the likely path fault, and one robust correction. Why does a five-field date entry not mean 'run once'?")
labkit.correction(d, "(a) How did you show that the backup can be restored? (b) What stopped retention from deleting unrelated data? (c) Did you see real scheduling, or only the fallback environment?")
labkit.submission(d, 10, ['cp -- backup.sh "$SUBMISSION_REPO/lab10/"',
                          'cp -- evidence/restore.txt evidence/automation.txt "$SUBMISSION_REPO/lab10/evidence/"'],
                  [("README.md", None), ("backup.sh", None), ("evidence", [("restore.txt", None), ("automation.txt", None)])],
                  note="Remove your practice cron entry before you finish. automation.txt holds the retention, environment and cron or fallback evidence.")
labkit.grading(d, [["A restorable archive, and keep-three retention in the right scope", "3"],
                   ["Restore, retention, unrelated-file and bare-environment evidence", "2"],
                   ["Archive versus compression, paths and scheduling limits explained; original prediction and correction", "2"],
                   ["Individual checkpoint: result or diagnosis, and mechanism", "2"],
                   ["Concise, attributable evidence and the required artifacts", "1"]])
labkit.mistakes(d, [["rm $(ls backups)", "Unrelated files removed", "Sort the matching names, quote every path"],
                    ["Relative paths in the script", "It works in your shell, fails in cron", "Find the script's own folder first"],
                    ["Trusting a backup you never restored", "A corrupt or incomplete archive", "Extract it and compare with cmp"],
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
    "s5": {"description": "Level 2: the backup script and retention. Levels 3 and 5: cron and the environment, then the tests.", "start": "l2-open"},
    "s6": {"description": "The individual checkpoint: why, and the practice question.", "start": "cp-open"},
    "s7": {"description": "Correction, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: scheduling the real backup, logs, health and date jobs, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
