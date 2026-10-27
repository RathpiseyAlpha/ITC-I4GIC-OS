"""Lab 3 guide, Wildcards, Links, GRUB and Shared Libraries. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

A guide for the lab session, built like the Lab 1 and Lab 2 guides with the shared look in labkit.py
(Ubuntu fonts, a wider canvas, dark terminal windows, folder trees drawn like `tree`).

It starts with the concepts the core needs: wildcards and quoting, inodes, hard and symbolic links and
how a relative link target is resolved. The lab part follows labs/lab3/lab3-instruction.md: Setup, the
guided example, the prediction, Task 2, tests, the checkpoint, explanation, cleanup and submission.
GRUB and shared libraries are optional extensions in that instruction; the earlier guide taught them,
so they stay as a short background section at the end, redrawn here (images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, flow, init)  # noqa: E402,F401

WEEK = "Lab 3"
TITLE = "Operating Systems — Lab 3"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-27T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 3)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-03", "Wildcards, Links, GRUB and Shared Libraries",
                  "Lab 3 guide: select files with patterns, then see what a rename does to a hard link and to a symbolic link.", size=88)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Select files with a wildcard and explain shell expansion versus a literal name.",
                    "Create and inspect hard links and symbolic links, using inode and target-path evidence.",
                    "Predict and diagnose what renaming or replacing a link target does."], ordered=True, size=36, flex=3),
            card(t, "Lab 3", "First the concepts, with examples. Then the lab on the server. GRUB and shared libraries are optional extensions, so they come at the end.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "You rename a report. What breaks?",
         "A shortcut on the desktop, a second name for the same file, a note that says where the file is. Which of them still work?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Wildcards and links", "Two ideas: the shell turns patterns into names, and one file can have more than one name.")

d.slide("wild-what", "A wildcard is a pattern, and the shell expands it",
        lambda t: row(lst(t, ["A wildcard is a character that stands for other characters, such as * for any characters.",
                              "The shell, not the command, expands the pattern into a list of matching names, then runs the command with that list.",
                              "If nothing matches, Bash keeps the pattern as typed. The command then looks for a file with that exact name.",
                              "Wildcards select file names. They are not the same as regular expressions."], size=34, flex=3),
                      card(t, "Why learn it here?", "One pattern replaces a long list of names. The same pattern, used carelessly with rm, removes more than you meant.", label="BEFORE THE LAB", pad=40, title_size=36, flex=2),
                      gap=48, align="stretch"),
        label=BG)

d.slide("wild-table", "The wildcard patterns",
        lambda t: tbl(t, ["Pattern", "Meaning", "Example", "Matches"],
                      [[mono("*"), "Zero or more characters", mono("*.txt"), "every .txt file"],
                       [mono("?"), "Exactly one character", mono("file?.txt"), "file1.txt, fileA.txt"],
                       [mono("[abc]"), "One character from the set", mono("file[123].txt"), "file1.txt, file2.txt, file3.txt"],
                       [mono("[a-z]"), "One character in the range", mono("[A-Z]*.txt"), "names that start with a capital"],
                       [mono("[!abc]"), "One character not in the set", mono("file[!0-9].txt"), "fileA.txt, not file1.txt"],
                       [mono("{a,b}"), "Brace expansion: generates words", mono("file.{txt,log}"), "the words file.txt and file.log"]],
                      [2, 5, 5, 6]),
        note="Square brackets match one character that exists. Braces only write words, before any file is looked at.",
        label=BG)

d.slide("wild-action", "Patterns at work",
        lambda t: row(term(t, ["ls *.txt",
                               "ls report0[1-3].txt",
                               "ls log_[!j]*.log",
                               "touch memo_{mon,tue,wed}.txt",
                               "cp *.csv archive/",
                               "ls *.tmp",
                               "rm *.tmp"], size=30),
                      col(para(t, "The first three list files. touch with braces creates three files in one command.", size=32),
                          para(t, "cp copies every .csv file into archive/.", size=32),
                          card(t, "Preview before you delete", "Run ls *.tmp first. If the list is what you expect, then run rm *.tmp.", label="CAUTION", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("wild-expand", "See what the shell really passes",
        lambda t: row(term(t, ["mkdir -p practice",
                               "printf 'one\\n' > practice/report1.txt",
                               "printf 'two\\n' > practice/report2.txt",
                               "printf 'log\\n' > practice/report.log",
                               ("blank",),
                               "printf '<%s>\\n' practice/*.txt",
                               ("out", "<practice/report1.txt>"),
                               ("out", "<practice/report2.txt>"),
                               "printf '<%s>\\n' 'practice/*.txt'",
                               ("out", "<practice/*.txt>")], size=28),
                      col(para(t, "printf prints each word it receives between angle brackets, one per line.", size=32),
                          para(t, "Without quotes, the shell sends two words: the two .txt files. With single quotes around the whole pattern, it sends one word with a literal *.", size=32),
                          para(t, "Use this trick to check a pattern before you give it to cp, mv or rm.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("wild-brace", "Brackets and braces are not the same",
        lambda t: row(col(h3(t, "Square brackets look at files"),
                          term(t, ["ls practice/report[12].txt",
                                   ("out", "practice/report1.txt  practice/report2.txt"),
                                   "ls practice/report[13].txt",
                                   ("out", "ls: cannot access 'practice/report3.txt': No such file")], size=26),
                          para(t, "Only names that exist can match. Bash keeps a pattern with no match, so the error names the pattern.", size=30),
                          gap=20, flex=None),
                      col(h3(t, "Braces only write words"),
                          term(t, ["echo practice/report{1,3}.txt",
                                   ("out", "practice/report1.txt practice/report3.txt")], size=26),
                          para(t, "The file report3.txt does not exist, and echo does not care. Brace expansion happens first, and no file is looked at.", size=30),
                          gap=20, flex=None),
                      gap=40, align="flex-start"),
        label=BG)

d.slide("inode", "A name is not the file",
        lambda t: row(lst(t, ["The data of a file lives on the disk. An inode is the record that describes it: size, owner, permissions and where the data is.",
                              "Every inode has a number. A file name is only an entry in a directory that points to an inode number.",
                              "Two entries can point to the same inode. They are two names for one file: hard links.",
                              "The data is freed only when the last name is gone."], size=32, flex=3),
                      term(t, ["ls -li",
                               ("out", "12345 -rw-r--r-- 2 student student 4 report1.txt"),
                               ("out", "12345 -rw-r--r-- 2 student student 4 hard-demo.txt"),
                               ("out", "99001 lrwxrwxrwx 1 student student 11 soft-demo.txt -> report1.txt")],
                           size=24, title="inode number, permissions, link count, ..."),
                      gap=48, align="center"),
        note="The 2 in the third column is the link count: two names point to inode 12345. The symbolic link has its own inode, 99001.",
        label=BG)

d.slide("hard-soft", "Hard link and symbolic link",
        lambda t: tbl(t, ["", "Hard link", "Symbolic link"],
                      [["Command", mono("ln target link"), mono("ln -s target link")],
                       ["What it is", "Another name for the same inode", "A small file that stores a path"],
                       ["Inode", "The same as the original", "Its own inode"],
                       ["Original is removed", "Data survives under the other name", "The link breaks: it is dangling"],
                       ["Across filesystems", "No", "Yes"],
                       ["Folders", "Not normally", "Yes"],
                       ["Seen in ls -l", "No arrow", "An arrow to the stored target"]],
                      [3, 6, 6]),
        note="Inspect with ls -li (inode numbers), stat (link count) and readlink (the stored path).",
        label=BG)

d.slide("rel-target", "A relative target is read from the link's folder",
        lambda t: row(term(t, ["cd ~/oslab-work/lab3",
                               "ls -l links",
                               ("out", "lrwxrwxrwx 1 student student 11 soft.txt -> source.txt"),
                               ("blank",),
                               "cat links/soft.txt",
                               ("out", "version 1"),
                               "cd links && cat soft.txt",
                               ("out", "version 1")], size=26),
                      col(para(t, "The stored target source.txt has no / at the front, so it is relative.", size=32),
                          para(t, "It is resolved from the folder that holds the link (links/), not from the folder where you are standing.", size=32),
                          para(t, "That is why the same link works from two places. Write the target as if you were standing next to the link.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("experiment", "The key experiment",
        lambda t: row(term(t, ["echo 'config data' > original.txt",
                               "ln original.txt hardlink.txt",
                               "ln -s original.txt symlink.txt",
                               "ls -li",
                               "rm original.txt",
                               "cat hardlink.txt",
                               ("out", "config data"),
                               "cat symlink.txt",
                               ("out", "cat: symlink.txt: No such file or directory")], size=26),
                      col(para(t, "echo with &gt; writes the text into a new file. rm removes only the name original.txt.", size=32),
                          para(t, "The data still has one name, hardlink.txt, so it survives.", size=32),
                          para(t, "symlink.txt still says original.txt, and no such name exists. The link is dangling.", size=32),
                          gap=24),
                      gap=48, align="center"),
        note="In practice: ls -la /usr/bin/python* shows programs that are managed with symbolic links.",
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 3", "Wildcards and links", "A file is renamed. The references that depend on it must still work, or you must say why they do not.")

START_TREE = [("links", [("source.txt", None), ("target-name.txt", None)]), ("evidence", [])]

d.slide("scenario", "The scenario",
        lambda t: row(col(card(t, "Alex at TechCorp", "Alex maintains file references. A file is being renamed, and the references that depend on it must still work.",
                               label="SCENARIO", pad=40, title_size=36),
                          para(t, "Wildcards and links are the core. Boot recovery and custom libraries are separate extensions.", size=30),
                          gap=28),
                      tree(t, "lab3", START_TREE, cmd="tree -a", title="student@server: ~/oslab-work/lab3", size=30),
                      gap=56, align="center"))

d.slide("time", "Inside the 120 minutes",
        lambda t: row(tbl(t, ["Minutes", "What happens"],
                          [["0 to 10", "Introduction, objectives and setup"],
                           ["10 to 25", "Guided example: commands and observations"],
                           ["25 to 35", "Written prediction"],
                           ["35 to 70", "Individual investigation, Task 2"]],
                          [1, 3], width=HALF),
                      tbl(t, ["Minutes", "What happens"],
                          [["70 to 85", "Normal and edge tests, feedback"],
                           ["85 to 100", "Individual changed-case checkpoint"],
                           ["100 to 110", "Correction and explanation"],
                           ["110 to 120", "Cleanup and submission"]],
                          [1, 3], width=HALF),
                      gap=32),
        gap=36)

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Your own account", "Log in with your own account. Use only your own files and processes. Privileged and boot work is never done on the shared server.", title_size=36),
                      rule(t, "AI tools", "Optional in the investigation and the tests. Not allowed in the prediction and the individual checkpoint.", title_size=36),
                      rule(t, "Evidence", "Keep what you observe in the evidence folder. Short, attributable evidence earns more than long output.", title_size=36)),
        note="Initial prediction accuracy is lightly weighted. A reasoned attempt and an evidence-based correction earn credit.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ["whoami",
                               "command -v oslab",
                               "oslab doctor",
                               'export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab3",
                               'cd "$OSLAB_WORKSPACE/lab3"',
                               "pwd",
                               "mkdir -p evidence",
                               "find . -maxdepth 3 -type f"], title="student@server: ~", size=26),
                      col(lst(t, ["whoami shows your account. command -v oslab and oslab doctor check the helper.",
                                  "If the helper is missing, follow the local setup guide in the course repository.",
                                  "oslab start lab3 makes the lab folder. It keeps your work if you start again, and it does not change your current folder, so cd into it yourself.",
                                  "If you are resuming, look at the existing files before you run a command that writes to them."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("start-tree", "Compare with the starting tree",
        lambda t: row(tree(t, "lab3", [("links", [("source.txt", None), ("target-name.txt", None)]), ("evidence", [])], cmd="tree -a -L 3", title="student@server: ~/oslab-work/lab3", size=30),
                      col(para(t, "The helper also writes a hidden file, .oslab-managed.json. It marks the folder as managed. Leave it as it is.", size=32),
                          para(t, "evidence/ was made by the mkdir -p in step 3.", size=32),
                          para(t, "The workspace is for experiments. Your personal course repository holds the final submission.", size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- guided example -----------------------------------------------------------
d.opener("g-open", "GUIDED", "Wildcards, then your first links", "Task 1, with the instructor: ten to twenty-five minutes.")

d.slide("g-files", "Step 1: three clearly different names",
        lambda t: row(term(t, ["mkdir -p practice",
                               "printf 'one\\n' > practice/report1.txt",
                               "printf 'two\\n' > practice/report2.txt",
                               "printf 'log\\n' > practice/report.log",
                               "ls practice",
                               ("out", "report1.txt  report2.txt  report.log")], size=28),
                      col(para(t, "Work in a separate practice folder, so the investigation files stay untouched.", size=32),
                          para(t, "printf with &gt; writes one line into a new file. The names differ on purpose: two .txt files and one .log file.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-expand", "Step 2: how the shell expands a pattern",
        lambda t: row(term(t, ["printf '<%s>\\n' practice/*.txt",
                               "printf '<%s>\\n' practice/report?.txt",
                               "printf '<%s>\\n' 'practice/*.txt'"], size=28),
                      col(para(t, "The first two commands name the two text files. The quotes around the whole pattern in the third leave a literal *.", size=32),
                          para(t, "Brace expansion such as {1,2} generates words. It is not a test against file names.", size=32),
                          card(t, "Observe", "Which pattern did not match report.log? Why does report?.txt need exactly one character after report?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-links", "Step 3: your first two links",
        lambda t: row(term(t, ["ln practice/report1.txt practice/hard-demo.txt",
                               "ln -s report1.txt practice/soft-demo.txt",
                               "ls -li practice/report1.txt practice/hard-demo.txt practice/soft-demo.txt",
                               "readlink practice/soft-demo.txt"], size=26),
                      col(para(t, "A hard link names the same inode, on one filesystem. A symbolic link stores a path. ls -l shows the stored target.", size=32),
                          para(t, "readlink prints the path stored in a symbolic link.", size=32),
                          card(t, "Observe", "Which inode numbers match? Why is report1.txt, not practice/report1.txt, the right target here?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- prediction -------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you rename the investigation source. Ten minutes.")

d.slide("predict", "The prediction",
        lambda t: row(col(card(t, "Write this down first", "After source.txt becomes renamed.txt, will a hard link still read the old bytes? Will a symbolic link storing source.txt still work? Explain each mechanism.",
                               label="PREDICTION", pad=40, title_size=36),
                          gap=24, flex=3),
                      col(card(t, "The rules", "Alone, and without AI. On paper or in the course worksheet, before you run mv. You may compare with a neighbour for five minutes, but keep your own answer.", label="HOW", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"),
        note="A wrong prediction costs nothing. It is marked for being made and for the evidence-based correction afterwards.")

# ---- task 2 -----------------------------------------------------------------
d.opener("t2-open", "TASK 2", "Hard links and symbolic links", "Thirty-five minutes, from minute 35 to 70. Work alone.")

d.slide("t2-one", "Step 1: two references to the source",
        lambda t: row(term(t, ['cd "$OSLAB_WORKSPACE/lab3/links"',
                               "cat source.txt",
                               "ln source.txt hard.txt",
                               "ln -s source.txt soft.txt",
                               "ls -li source.txt hard.txt soft.txt | tee ../evidence/links.txt"], size=26, title="student@server: ~/oslab-work/lab3/links"),
                      col(para(t, "| tee sends the output to the screen and into evidence/links.txt at the same time. Your first record is the before-state.", size=32),
                          card(t, "If you are resuming", "A destination that already exists must be inspected, not overwritten. Do not run ln again and again: ln refuses with File exists.", label="CAREFUL", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t2-two", "Step 2: rename the original, then look",
        lambda t: row(term(t, ["mv -- source.txt renamed.txt",
                               "cat hard.txt",
                               "readlink soft.txt",
                               "cat soft.txt 2>&1 | tee -a ../evidence/links.txt"], size=26, title="student@server: ~/oslab-work/lab3/links"),
                      col(para(t, "mv renames the directory entry. -- means no more options follow.", size=32),
                          para(t, "2&gt;&amp;1 sends the error message to the same place as normal output, so tee can record it. -a appends instead of replacing.", size=32),
                          card(t, "A deliberate failure", "The last command fails on purpose. Write down what the error means before you repair anything.", label="THINK", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t2-three", "Step 3: repair only the symbolic link",
        lambda t: row(col(h3(t, "What to do"),
                          lst(t, ["Look at the old link first: readlink soft.txt.",
                                  "Remove only that owned symbolic-link entry.",
                                  "Create it again with ln -s, and choose a relative target yourself.",
                                  "Do not replace hard.txt. It never broke."], ordered=True, size=32),
                          gap=20, flex=3),
                      col(card(t, "You write the target", "Nobody gives you the command here. Ask: from the folder links/, what is the name of the file now?", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("t2-four", "Step 4: inode identity after the repair",
        lambda t: row(term(t, ["{",
                               "  ls -li renamed.txt hard.txt soft.txt",
                               "  readlink soft.txt",
                               "  cat hard.txt soft.txt",
                               "} | tee -a ../evidence/links.txt"], size=28, title="student@server: ~/oslab-work/lab3/links"),
                      col(para(t, "The braces group four commands, so one tee records all of their output.", size=32),
                          card(t, "Observe", "Which inode numbers match now? Which name did you create again, and which one did not change?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t2-five", "Step 5: a changed case, a new source.txt",
        lambda t: row(term(t, ["printf 'version 2\\n' > source.txt",
                               "{ ls -li source.txt hard.txt; cat source.txt hard.txt; } | tee ../evidence/replacement.txt"], size=26, title="student@server: ~/oslab-work/lab3/links"),
                      col(para(t, "Create a new source.txt that contains version 2. Before you run the check, predict: will hard.txt read version 1 or version 2?", size=32),
                          para(t, "Then explain why reusing a file name does not reuse the old inode.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t2-done", "Complete when, and hints",
        lambda t: row(card(t, "Complete when", "The hard link survives the rename. The repaired symbolic link resolves correctly. Your changed-name test tells a file name from an inode.",
                           label="DONE", pad=40, title_size=36, flex=1),
                      col(h3(t, "Hints, one at a time"),
                          lst(t, ["A hard link is another directory entry.",
                                  "Compare ls -li with readlink.",
                                  "Resolve the symbolic target from links/, not from the folder where you are standing."], ordered=True, size=32),
                          gap=20, flex=1),
                      gap=48, align="stretch"))

# ---- tests ---------------------------------------------------------------------
d.opener("test-open", "TESTS AND FEEDBACK", "Check your work", "Fifteen minutes, from minute 70 to 85.")

d.slide("tests", "Three cases, three records",
        lambda t: tbl(t, ["Case", "Evidence", "What it tests"],
                      [["Normal", "All references read version 1 before the rename", "Building the links and the correct target path"],
                       ["Failure and repair", "The symbolic read fails after the rename and works after the repair", "Path indirection and diagnosis"],
                       ["Changed name", "The new source reads version 2, the hard link keeps version 1", "File name replacement versus inode identity"]],
                      [3, 8, 6]),
        note="Save the before, renamed and repaired observations in evidence/links.txt, and the recreated-name result as evidence/replacement.txt. Go back to the workspace root first.")

d.slide("tests-helper", "Links and the helper",
        lambda t: row(rule(t, "Internal links are fine", "The helper accepts symbolic links that stay inside the managed folder.", title_size=36),
                      rule(t, "Escaping links are refused", "It refuses links that point outside it. Do not link to /etc, other homes or unrelated folders.", title_size=36),
                      rule(t, "oslab clean lab3", "Removes only the managed folder. Internal links go as entries, and external links are refused.", title_size=36)),
        note="File exists means: look at the destination first. A dangling link can exist even when its target does not. Hard links cannot normally cross filesystems.")

# ---- checkpoint ----------------------------------------------------------------
d.opener("cp-open", "INDIVIDUAL CHECKPOINT", "Show what you can do alone", "Fifteen minutes, from minute 85 to 100. No AI, no neighbours.")

d.slide("cp-why", "Why there is a checkpoint",
        lambda t: row(rule(t, "It checks you, not the tools", "Everything before it may use AI and help. The checkpoint shows what you understood without them.", title_size=36),
                      rule(t, "A short question on paper", "You answer one question on paper or on the course worksheet. Your earlier work does not need to be finished.", title_size=36),
                      rule(t, "Practice question", "The question on the next slide is public practice. A graded session may use a fresh private variant.", title_size=36)))

d.slide("cp-question", "The question",
        lambda t: row(col(card(t, "Resolve the path", "A symbolic link inside lab3/links/ stores ../source.txt. Only lab3/links/source.txt exists. Resolve the stored path and explain why the link fails. Give a suitable target for the existing file.",
                               label="PRACTICE QUESTION", pad=40, title_size=36),
                          gap=24, flex=3),
                      col(lst(t, ["The result or diagnosis.", "The mechanism.", "One observation that could check it."], ordered=True, size=32),
                          h3(t, "What to give"),
                          gap=20, flex=2),
                      gap=48, align="stretch"),
        note="The instructor collects your answer before discussing the public key.")

# ---- explanation, submission -----------------------------------------------------
d.opener("end-open", "CORRECTION AND SUBMISSION", "Look back, then hand in", "Ten minutes of correction, ten to clean up and submit.")

d.slide("explain", "Correct your prediction",
        lambda t: row(lst(t, ["Keep your original prediction in view. Under it, write confirmed or corrected.",
                              "Cite the test that shows it.",
                              "Explain the OS mechanism in three to five sentences."], ordered=True, size=34, flex=3),
                      card(t, "Three questions", "(a) Which file change broke the symbolic reference? (b) Why did the hard link survive? (c) What happens if the new file name holds different bytes?", label="ANSWER", pad=40, title_size=36, flex=2),
                      gap=48, align="stretch"))

d.slide("submit-one", "Submit 1: your repository and the copy",
        lambda t: row(term(t, ['SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"',
                               'mkdir -p "$SUBMISSION_REPO/lab3/evidence"',
                               'cd "$OSLAB_WORKSPACE/lab3"',
                               'cp -- evidence/links.txt evidence/replacement.txt "$SUBMISSION_REPO/lab3/evidence/"'], title="student@server: ~", size=24),
                      col(para(t, "Replace YOUR_ID with your own ID. The orange text is the part you change. Use the absolute path of your existing course repository, never a neighbour's.", size=30),
                          para(t, "Example: with the ID 0123, the first line becomes SUBMISSION_REPO=\"$HOME/os-gic-0123/os-lab-0123\", and echo \"$SUBMISSION_REPO\" prints /home/student/os-gic-0123/os-lab-0123.", size=28),
                          para(t, "Copy the listed artifacts and two selected test records, not every terminal output.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("submit-two", "Submit 2: the final tree and Git",
        lambda t: row(tree(t, "lab3", [("README.md", None), ("evidence", [("links.txt", None), ("replacement.txt", None)])], cmd="tree", title="student@server: ~/os-gic-YOUR_ID/os-lab-YOUR_ID", size=30),
                      col(lst(t, ["Write README.md from the lab's template, in your own words.",
                                  "The prediction must have been written before you ran anything. Copying it into the README only records it.",
                                  "git status --short, then add only your lab files, then commit and push.",
                                  "No passwords, personal shell files, generated binaries or disk images."], ordered=True, size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("grading", "How it is marked: 10 points",
        lambda t: tbl(t, ["Evidence for the lab objectives", "Points"],
                      [["Correct wildcard explanation, and working hard and symbolic links", "3"],
                       ["Rename failure, repair and recreated-name evidence", "2"],
                       ["Inode identity and relative target resolution; original prediction and evidence-based correction", "2"],
                       ["Individual checkpoint: result or diagnosis, and mechanism", "2"],
                       ["Concise, attributable evidence and the required artifacts", "1"]],
                      [10, 1]),
        note="Other valid commands and names earn credit. A naming difference costs points only when it breaks the result. If you use AI, note one useful suggestion and how you verified it.")

d.slide("mistakes", "Common mistakes",
        lambda t: tbl(t, ["Mistake", "What you see", "Fix"],
                      [["Running ln again on an existing name", "File exists", "Look at the destination first"],
                       ["Target written from where you stand", "A dangling link", "Write it as if you stood next to the link"],
                       ["Replacing hard.txt to fix the link", "The experiment loses its point", "Repair only soft.txt"],
                       ["A bare pattern with rm", "More files removed than expected", "Run ls with the same pattern first"],
                       ["Brackets used like braces", "A name that does not exist", "[ ] match files, { } write words"]],
                      [6, 5, 6]),
        gap=36)

# ---- beyond the core (kept from the earlier guide) --------------------------------
d.opener("ext-open", "BEYOND THE CORE", "GRUB and shared libraries", "Optional extensions. They need a disposable virtual machine or a compiler, and they are not part of the two-hour core.")

d.slide("boot", "From power-on to login",
        lambda t: row(tbl(t, ["Stage", "What it does"],
                          [["BIOS or UEFI", "Self-test, then finds the boot device"],
                           ["GRUB", "Shows a menu and loads the kernel"],
                           ["Kernel", "Starts the hardware, mounts the root filesystem, runs the first process (PID 1)"],
                           ["init or systemd", "Starts the system services in order"],
                           ["Login", "User space is ready"]],
                          [4, 11], width=CW),
                      gap=32),
        label=EXT)

d.slide("grub-files", "GRUB files and key settings",
        lambda t: row(tbl(t, ["File", "Purpose", "Edit?"],
                          [[mono("/boot/grub/grub.cfg"), "The generated menu", "Never"],
                           [mono("/etc/default/grub"), "Timeout, kernel parameters", "Yes"],
                           [mono("/etc/grub.d/"), "Scripts, custom entries", "Yes"],
                           [mono("/boot/vmlinuz-*"), "The compressed kernel", "No"]],
                          [6, 7, 2], width=HALF),
                      tbl(t, ["Setting", "Meaning", "Example"],
                          [[mono("GRUB_DEFAULT"), "Entry to boot", "0"],
                           [mono("GRUB_TIMEOUT"), "Seconds at the menu", "10"],
                           [mono("GRUB_CMDLINE_LINUX_DEFAULT"), "Kernel parameters", "quiet splash"],
                           [mono("GRUB_BACKGROUND"), "A menu background image", "/boot/grub/bg.png"]],
                          [8, 5, 4], width=HALF),
                      gap=32),
        note="After you edit /etc/default/grub, run sudo update-grub. Custom entries go in /etc/grub.d/40_custom. Do this only in a disposable virtual machine, never on the shared server.",
        label=EXT)

d.slide("grub-recover", "GRUB recovery",
        lambda t: row(tbl(t, ["Mode", "How you enter", "Use"],
                          [["Recovery mode", "GRUB menu, Advanced options, recovery", "A root shell, fsck, limited services"],
                           ["GRUB command line", "Press c at the menu", "Boot by hand when the menu is broken"],
                           ["Live USB", "Boot from an external image", "Full rescue when GRUB is gone"]],
                          [4, 6, 6], width=HALF),
                      term(t, ["set root=(hd0,msdos1)",
                               "linux /boot/vmlinuz-VERSION root=/dev/sda1",
                               "initrd /boot/initrd.img-VERSION",
                               "boot"], title="grub>", size=24, width=HALF),
                      gap=32, align="center"),
        note="Take a snapshot of the virtual machine before you break anything on purpose.",
        label=EXT)

d.slide("libs", "Static and dynamic linking",
        lambda t: tbl(t, ["", "Static", "Dynamic"],
                      [["When linked", "At compile time", "When the program starts"],
                       ["Library code", "Copied into the executable", "Loaded from .so files"],
                       ["Executable size", "Larger", "Smaller"],
                       ["Memory", "Each program has its own copy", "Programs share one copy"],
                       ["Updates", "Recompile every program", "Replace the .so, and all programs benefit"],
                       ["File extension", ".a (archive)", ".so (shared object)"]],
                      [4, 6, 7]),
        label=EXT)

d.slide("linker", "How a program finds its libraries",
        lambda t: flow(t, [("1. The kernel loads the program", "an ELF file"), ("2. The dynamic linker starts", "ld-linux.so"),
                           ("3. It finds each .so", "LD_LIBRARY_PATH, /etc/ld.so.cache, then /lib and /usr/lib"),
                           ("4. It maps them in", "into the process, and the program runs")], 400, hot=2),
        label=EXT)

d.slide("libs-cmds", "Looking at shared libraries, and building one",
        lambda t: row(term(t, ["ldd /bin/ls",
                               "ldconfig -p | grep libc",
                               "gcc -fPIC -c mylib.c -o mylib.o",
                               "gcc -shared -o libmylib.so mylib.o",
                               "gcc main.c -L. -lmylib -o myprogram",
                               "LD_LIBRARY_PATH=. ./myprogram"], size=24),
                      col(para(t, "ldd lists the libraries a program needs. ldconfig -p searches the library cache.", size=30),
                          para(t, "-fPIC makes position-independent code, so the library can load at any address. -shared makes the .so file.", size=30),
                          para(t, "For a user-local library, set LD_LIBRARY_PATH instead of installing into system folders.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=EXT)

d.slide("libs-more", "More ways to look at a library",
        lambda t: row(term(t, ["file /lib/x86_64-linux-gnu/libc.so.6",
                               "readelf -h /bin/ls",
                               "grep '[.]so' /proc/$$/maps",
                               "sudo ldconfig"], size=26),
                      col(para(t, "file tells you the kind of file: an ELF shared object.", size=30),
                          para(t, "readelf -h prints the ELF header of a program. /proc/$$/maps lists what the current shell has loaded.", size=30),
                          para(t, "After you install a new .so in a system folder, sudo ldconfig refreshes the cache. Not on the shared server.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=EXT)

d.close([("Wildcards", "The shell expands a pattern into names before the command runs. Quote a pattern to keep it literal."),
         ("Name and inode", "A file name is an entry that points to an inode. Hard links are more names for one inode."),
         ("Symbolic links", "A symbolic link stores a path. A relative target is read from the link's folder."),
         ("Evidence", "Rename, look, repair, replace. Each step has a record you can check.")],
        "chapters 13 and 14, File-System Interface and File-System Implementation", ("Lab 4: I/O redirection, pipelines and processes", "Send output to files, connect commands with pipes, and see and stop processes."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: wildcards, quoting, inodes, hard and symbolic links and how a relative target is read.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the rules, setup and the starting tree.", "start": "lab-open"},
    "s4": {"description": "Guided example: wildcards and the first links, then the prediction.", "start": "g-open"},
    "s5": {"description": "Task 2: hard links and symbolic links, then the tests.", "start": "t2-open"},
    "s6": {"description": "The individual checkpoint: why, and the practice question.", "start": "cp-open"},
    "s7": {"description": "Correction, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: GRUB and shared libraries, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
