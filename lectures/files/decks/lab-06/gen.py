"""Lab 6 guide, Linux Security, Users, Groups and File Permissions. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

Revised 2026-11-05 to the pilot-format instruction: a personal notice policy and demo folder name (BOX), Core 1 and
Core 2, Plus and Challenge, a live checkpoint, oslab predict and oslab debrief. Modelled on the Lab 8 guide.

A guide for the lab session, built like the Lab 3 to Lab 5 guides with the shared look and the shared standard
slides in labkit.py. The earlier Lab 6 guide was only a one-slide stub, so the concepts section is new:
users and groups, the mode string, octal and symbolic notation, directory search, and path traversal.
The lab part follows labs/lab6/lab6-instruction.md (Task 3 is the core). Account and group administration,
ACLs and special bits are optional extensions in that instruction, so they come last (images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, flow, init)  # noqa: E402,F401

WEEK = "Lab 6"
TITLE = "Operating Systems — Lab 6"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-28T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 6)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-06", "Users, Groups and File Permissions",
                  "Lab 6 guide: read the mode bits, set the least access that works, and follow the whole path to a file.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Read owner, group and other mode bits, in symbolic and octal notation.",
                    "Set least-privilege modes on files and directories you own, and explain directory traversal.",
                    "Diagnose an access failure from path and mode evidence, and separate what you observed from what you only reasoned."], ordered=True, size=34, flex=3),
            card(t, "Lab 6", "First the concepts, with examples. Then the lab on the server, using only files you own. Accounts, ACLs and special bits are optional extensions, so they come last.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "A file is readable by everyone. Can everyone read it?",
         "What if the folder that holds the file is private? Where does the check really start?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Who may do what to a file", "Three ideas: three kinds of user, three kinds of access, and a check on every folder of the path.")

d.slide("users", "Users and groups",
        lambda t: row(lst(t, ["Every file has an owner (a user) and an owning group.",
                              "Every process runs as a user, and has a primary group and sometimes more.",
                              "The kernel compares who is asking with the owner, the group and everybody else, in that order.",
                              "The first match decides. A normal user cannot give a file to another account."], size=32, flex=3),
                      term(t, ["id",
                               ("out", "uid=1004(student) gid=1004(student) groups=1004(student)"),
                               "ls -ld . private shared",
                               ("out", "drwx------ 4 student student 4096 .  ..."),
                               ], size=24, title="your account and your folders"),
                      gap=48, align="center"),
        label=BG)

d.slide("mode", "Reading the mode string",
        lambda t: col(term(t, ["ls -l report.txt",
                               ("out", "-rw-r----- 1 student staff 120 report.txt")], size=30),
                      tbl(t, ["Characters", "Part", "Here"],
                          [[mono("-"), "Type: - file, d directory, l link", "A plain file"],
                           [mono("rw-"), "Owner", "Read and write"],
                           [mono("r--"), "Owning group", "Read only"],
                           [mono("---"), "Everybody else", "No access"]],
                          [3, 8, 6]),
                      gap=32),
        note="The first character is the type. The next nine are three triples: owner, group, others. A dash means that access is not given.",
        label=BG)

d.slide("octal", "Octal and symbolic modes",
        lambda t: row(tbl(t, ["Bit", "Value", "On a file", "On a directory"],
                          [["r", "4", "Read the contents", "List the names inside"],
                           ["w", "2", "Change the contents", "Create, rename or remove entries"],
                           ["x", "1", "Run it as a program", "Search: pass through to what is inside"]],
                          [1, 1, 4, 6], width=CW),
                      gap=32),
        note="Add the values of one triple to get one digit. rw- is 4+2 = 6, r-- is 4. So rw-r----- is 640.",
        label=BG)

d.slide("chmod", "chmod, in two notations",
        lambda t: row(term(t, ["chmod 600 note.txt",
                               "chmod u=rw,g=r,o= note.txt",
                               "stat -c '%A %a %n' note.txt",
                               ("out", "-rw-r----- 640 note.txt"),
                               "chmod g-r note.txt",
                               "chmod u+x script.sh"], size=26),
                      col(para(t, "Octal sets all nine bits at once. Symbolic mode changes only what you name: u owner, g group, o others, = sets, + adds, - removes.", size=32),
                          para(t, "stat -c shows the mode in both forms: %A symbolic, %a octal.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("dir-x", "On a directory, x means search",
        lambda t: row(card(t, "r on a directory", "You may list the names inside it, with ls.", label="READ", pad=40, title_size=36),
                      card(t, "x on a directory", "You may pass through it to reach an entry whose name you already know. Without x you cannot open anything below it.", label="SEARCH", pad=40, title_size=36),
                      card(t, "Both are needed to browse", "To list names and open files you need r and x. A directory with only r shows names but opens nothing.", label="TOGETHER", pad=40, title_size=36),
                      gap=32, align="stretch"),
        note="Do not try to run a data file to test read permission. For a directory, x is not about running a program.",
        label=BG)

d.slide("path", "The whole path is checked",
        lambda t: row(term(t, ['namei -l "$PWD/demo/note.txt"',
                               ("out", "f: /home/student/oslab-work/lab6/demo/note.txt"),
                               ("out", "drwxr-xr-x root    root    /"),
                               ("out", "drwxr-xr-x root    root    home"),
                               ("out", "drwx------ student student student"),
                               ("out", "drwx------ student student oslab-work"),
                               ("out", "-rw-r----- student student note.txt")], size=24),
                      col(para(t, "To open a file you need x on every directory of the path, from / down to the file.", size=32),
                          para(t, "A file with mode 644 inside a 700 directory is out of reach for other users. The strictest folder wins.", size=32),
                          para(t, "If namei is missing, list each parent with ls -ld.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 6", "A private record and a public notice", "Configure your own copy first, and explain the access path before anyone prepares a multi-user exercise.")

START_TREE = [("private", [("record.txt", None)]), ("shared", [("notice.txt", None)]), ("evidence", [])]

labkit.scenario(d, 6, "Records at TechCorp", "TechCorp needs a private record and a notice that staff can eventually read. Configure your owned copy first and justify the whole access path.",
                "Your notice policy and your demo folder name are your own. This guide shows example values.", START_TREE)
labkit.timetable(d, [["0 to 10", "Setup"],
                     ["10 to 25", "Guided: permission basics"],
                     ["25 to 35", "Prediction"],
                     ["35 to 55", "Core 1: set the modes"],
                     ["55 to 70", "Core 2: prove it"]],
                 [["70 to 85", "Instructor demonstration, Plus and Challenge"],
                  ["85 to 100", "Live checkpoint"],
                  ["100 to 110", "Debrief"],
                  ["110 to 120", "Submit"]])

d.slide("helper", "Six helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does"],
                      [[mono("oslab values lab6"), "Shows your notice policy (a sentence) and the name of your demo folder"],
                       [mono("oslab predict lab6"), "Saves your prediction once, before the experiment"],
                       [mono("oslab hint lab6 1"), "A hint, levels 1 to 3. Hints cost no points"],
                       [mono("oslab check lab6"), "Reads the modes of your files and shows your milestones"],
                       [mono("oslab checkpoint lab6"), "Opens when the instructor says so, near the end"],
                       [mono("oslab debrief lab6"), "After the lab: you give the right answers to your prediction questions"]],
                      [5, 11]),
        note="Before the lab, run oslab doctor and oslab prelab lab6. It takes about ten minutes.")

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Core, Plus, Challenge", "Core is for everyone. Plus and Challenge are for students who finish early. Full marks need only Core and the checkpoint.", title_size=36),
                      rule(t, "AI tools", "Allowed in Core, Plus and Challenge, so test every suggestion with stat. Not allowed in the prediction and the checkpoint.", title_size=36),
                      rule(t, "Only your own files", "You never use sudo, never change your home folder, and never try to read a neighbour's files.", title_size=36)),
        note="In Core 1 nobody gives you the modes. You turn your policy sentence into numbers yourself. A wrong prediction costs nothing.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ['export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab6",
                               'cd "$OSLAB_WORKSPACE/lab6"',
                               "mkdir -p evidence",
                               "oslab values lab6"], title="student@server: ~", size=26),
                      col(lst(t, ["The first line sets OSLAB_WORKSPACE to ~/oslab-work, unless it is already set. Type it as it is.",
                                  "oslab start lab6 makes the lab folder.",
                                  "cd takes you into it, and mkdir -p makes the evidence folder.",
                                  "oslab values lab6 prints your own policy and name."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("values", "Your values: a policy and a name",
        lambda t: row(col(h3(t, "The last command prints them"),
                          term(t, ["oslab values lab6",
                                   ("out", "Your personal values for lab6 (your-account):"),
                                   ("out", "  notice = The owner may change the file."),
                                   ("out", "    The owner's group may read it and list"),
                                   ("out", "    the folder. Others have no access."),
                                   ("out", "  box    = sealed-maple")], title="example: your values will be different", size=24),
                          gap=20, flex=None),
                      col(h3(t, "What they are for"),
                          lst(t, ["The notice policy is the sentence you turn into modes in Core 1.",
                                  "The box value is the name of your demo folder in Core 2.",
                                  "Your own policy and name are different. Write them down."], size=30),
                          gap=20, flex=None),
                      gap=48, align="flex-start"))

d.slide("capital", "The capital word is a placeholder",
        lambda t: tbl(t, ["The instruction says", "With the example value, you type"],
                      [[mono("mkdir -p demo/BOX"), mono("mkdir -p demo/sealed-maple")]],
                      [1, 1]),
        note="The instruction cannot know your name, so it writes BOX where your box value belongs. Never type BOX. Type your own value in its place.")

d.slide("start-tree", "Your folder",
        lambda t: row(tree(t, "lab6", START_TREE, cmd="tree -a -L 3", title="student@server: ~/oslab-work/lab6", size=30),
                      col(para(t, "private/record.txt is your private record.", size=32),
                          para(t, "shared/notice.txt is the notice that others should be able to read, once an administrator puts it in a searchable place.", size=32),
                          para(t, "oslab check lab6 shows TRY on every line at the start. The hidden .oslab-managed.json is the helper's. Leave it.", size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Permission basics", "Ten to twenty-five minutes, with the instructor. Read modes, and change them on a demo file that is not part of your answer.")

d.slide("g-id", "Step 1: who am I, and what do I own?",
        lambda t: row(term(t, ["id",
                               "ls -ld . private shared",
                               "stat -c '%A %a %U:%G %n' private/record.txt shared/notice.txt"], size=24),
                      col(para(t, "Nothing is changed in this step. id shows your user and groups.", size=30),
                          para(t, "%A is the mode in letters, %a in octal, %U:%G the owner and the group, %n the name.", size=30),
                          para(t, "Each triple of the mode applies to the owner, the owning group and others. A directory's x bit is search, not running a program.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-modes", "Step 2: octal and symbolic, on a demo file",
        lambda t: row(term(t, ["mkdir -p demo",
                               "printf 'demo content\\n' > demo/note.txt",
                               "chmod 600 demo/note.txt",
                               "stat -c '%A %a %n' demo/note.txt",
                               ("out", "-rw------- 600 demo/note.txt"),
                               "chmod u=rw,g=r,o= demo/note.txt",
                               "stat -c '%A %a %n' demo/note.txt",
                               ("out", "-rw-r----- 640 demo/note.txt")], size=24),
                      col(para(t, "Use a separate demo file, so the lab files stay untouched.", size=32),
                          para(t, "The second mode, 640, lets the owning group read the file. It does not make any folder on the path enterable.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-path", "Step 3: look at every folder on the path",
        lambda t: row(term(t, ['namei -l "$PWD/demo/note.txt"'], size=28),
                      col(para(t, "If namei is not installed, list each parent with ls -ld.", size=32),
                          card(t, "Observe", "Does mode 644 on a file inside a 700 folder mean that other users can reach the file?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- prediction ---------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you set any mode. Ten minutes.")

d.slide("predict", "The prediction",
        lambda t: row(col(term(t, ["oslab predict lab6"]),
                          para(t, "It asks four questions and one sentence, about a folder with mode 600 and about your own notice policy. Answer alone, without AI.", size=32),
                          gap=24, flex=3),
                      col(card(t, "The rules", "The first answer is the one that counts. A wrong guess costs nothing. You compare it with the real result in the debrief.", label="PREDICTION", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

# ---- core 1 ---------------------------------------------------------------------
d.opener("c1-open", "CORE 1", "Set the modes", "Twenty minutes, from minute 35 to 55. Turn two policies into modes, apply them to your own files, and save the result.")

d.slide("c1-policy", "Two policies",
        lambda t: row(card(t, "The private record", "The same for everybody: only you may read and change private/record.txt, and nobody else may even enter private/.", label="POLICY 1", pad=40, title_size=36),
                      card(t, "The notice", "Your own sentence from oslab values lab6. It applies to shared/notice.txt and to the folder shared/.", label="POLICY 2", pad=40, title_size=36),
                      gap=32, align="stretch"),
        note="Example notice policy: the owner may change the file, the owner's group may read it and list the folder, others have no access.")

d.slide("c1-decide", "Step 3: your decision, four chmod commands",
        lambda t: row(col(h3(t, "Write four commands yourself"),
                          lst(t, ["One for private/, one for private/record.txt.",
                                  "One for shared/, one for shared/notice.txt.",
                                  "Work out each mode from the table of mode bits: which digits do you need for the owner, the group and the others?",
                                  "Does a folder need the x bit for the people who may read a file inside it?"], size=30),
                          gap=20, flex=3),
                      col(card(t, "You choose the modes", "Nobody gives you the numbers. Give the least access that still does the job.", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c1-save", "Steps 4 and 5: save the result, then check",
        lambda t: row(col(term(t, ["stat -c '%A %a %U:%G %n' private private/record.txt \\",
                                   "  shared shared/notice.txt | tee evidence/policy.txt",
                                   "oslab check lab6"], size=24),
                          para(t, "Run the stat line after your last chmod. The first two Core milestones must show PASS.", size=30),
                          gap=22, flex=3),
                      col(card(t, "Hints", "oslab hint lab6 1, then 2, then 3. AI is allowed here: test every suggestion with stat.", label="STUCK?", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

# ---- core 2 ---------------------------------------------------------------------
d.opener("c2-open", "CORE 2", "Prove it", "Fifteen minutes, from minute 55 to 70. Show that the modes work, and show a failure that you can explain.")

d.slide("c2-owner", "Step 1: use the record as its owner",
        lambda t: row(term(t, ["cat private/record.txt",
                               "printf 'owner update\\n' >> private/record.txt",
                               "if test -x private/record.txt; then printf 'unexpected execute bit\\n'; else printf 'not executable\\n'; fi"], size=24),
                      col(para(t, "Read and append as the owner. Then check that the file has no execute bit. A data file should not have one.", size=30),
                          para(t, "Do not run a data file to test read permission.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-sealed", "Step 2: a folder you can list but not enter",
        lambda t: row(term(t, ["mkdir -p demo/sealed-maple",
                               "printf 'inside\\n' > demo/sealed-maple/item.txt",
                               "chmod 600 demo/sealed-maple",
                               "ls demo/sealed-maple | tee evidence/traversal.txt",
                               "cat demo/sealed-maple/item.txt 2>&1 | tee -a evidence/traversal.txt",
                               "chmod 700 demo/sealed-maple",
                               "cat demo/sealed-maple/item.txt | tee -a evidence/traversal.txt"], title="example name: use your own box value", size=24),
                      col(para(t, "The failing cat is intended. Restore the folder right after, with chmod 700.", size=30),
                          para(t, "ls shows the name because the folder has r. cat fails because it has no x. 2&gt;&amp;1 saves the error message in the file too.", size=30),
                          card(t, "Think", "Which bit of the demo folder caused the failure?", label="TRY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-check", "Step 3: check your work",
        lambda t: row(term(t, ["oslab check lab6"], size=28),
                      col(para(t, "All four Core milestones must show PASS: your private record, your notice policy, the traversal test and policy.txt.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("c2-peer", "Step 4: a hypothetical peer",
        lambda t: row(col(term(t, ['namei -l "$PWD/shared/notice.txt"'], size=26),
                          para(t, "Could another student read shared/notice.txt under your policy? Look at every parent of the file, including oslab-work and your home folder. Do not change them to try it out.", size=30),
                          gap=22, flex=3),
                      col(card(t, "Write down for your report", "The notice's own mode is not enough. Which parent decides? What was a real test above, and what is only your reasoning?", label="REPORT", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c2-table", "What each case shows, and what it cannot show",
        lambda t: tbl(t, ["Case", "Evidence", "Limit"],
                      [["Owner access", "Read and append the private record, then inspect the modes", "Does not simulate another user"],
                       ["Search failure", "Before, failed and restored reads under your demo folder", "Shows traversal, not every ACL or capability effect"],
                       ["Peer access", "A full-path explanation of the modes", "Needs a prepared second account to confirm in practice"]],
                      [3, 8, 7]),
        note="Default ACLs can change the mode of new files. Look at the final modes again after your tests.")

d.slide("c2-trouble", "If something does not work",
        lambda t: row(rule(t, "Check who you are", "Run whoami and id, and confirm you own the file before you change its mode.", title_size=36),
                      rule(t, "chown is not for you", "A normal user cannot give a file to another account. Never edit sudoers, never create accounts.", title_size=36),
                      rule(t, "Read the manual", "man chmod, man stat, man namei and man path_resolution explain the details.", title_size=36)))

# ---- demonstration, plus and challenge ----------------------------------------------------
d.slide("plus", "Plus: the same mode in letters",
        lambda t: row(term(t, ["chmod u=rw,g=r,o= shared/notice.txt",
                               "stat -c '%A %a %n' shared/notice.txt"], title="example for 640: use the letters for your mode", size=24),
                      col(para(t, "Write the symbolic chmod command that gives shared/notice.txt the same mode as your numbers. Run it, then check that nothing changed.", size=30),
                          card(t, "Answer in evidence/plus.txt", "Which letters did you write, and why do they match your octal mode?", label="PLUS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"),
        note="First watch the instructor show two accounts on a prepared machine: a file with mode 644 inside a folder with mode 711, then 700. Plus and Challenge are not needed for full marks.")

d.slide("challenge", "Challenge: umask",
        lambda t: row(term(t, ["( umask 077; touch demo/umask-test.txt; stat -c '%A %a %n' demo/umask-test.txt )"], size=24),
                      col(para(t, "umask shows which bits a new file does not get. With umask 0022 a new file has mode 644 and a new folder 755.", size=30),
                          card(t, "Predict first", "What is the mode of a file you create after umask 077? The subshell keeps your session's umask unchanged.", label="CHALLENGE", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- live checkpoint ------------------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "The policy is new", "The questions use a new policy, made for you at that moment. An answer copied from a neighbour does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once, so a common mistake can be explained before the next lab.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task, with their own policy.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab6", "Read the policy, answer four questions"),
                           ("3. The file task", "New folder and data.txt, your modes"), ("4. oslab check lab6", "A fifth milestone must pass")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command says that the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab6 shows whether the fifth milestone, checkpoint, passes. You can fix the modes and check again.", title_size=36)),
        gap=56)

d.slide("cp-marks", "What the checkpoint asks",
        lambda t: tbl(t, ["Part", "What you do"],
                      [["Four questions", "Read the new policy. Answer two octal modes, one yes or no, and one sentence."],
                       ["The file task", "Make the new folder and data.txt that the command prints, set your two modes, and save the stat output in checkpoint.txt."],
                       ["The check", "Run oslab check lab6. The fifth milestone, checkpoint, must show PASS."]],
                      [4, 13]),
        note="The same skill as Core 1: policy sentence to octal modes, for a folder and a file.")

# ---- debrief and submit ---------------------------------------------------------------------
d.opener("end-open", "DEBRIEF AND SUBMIT", "Look back, then hand in", "Ten minutes of debrief, ten to submit.")

d.slide("debrief", "Debrief: look at your prediction again",
        lambda t: row(term(t, ['cat "$OSLAB_WORKSPACE/.records/lab6-predict.json"',
                               "oslab debrief lab6"], size=24, title="student@server: ~/oslab-work/lab6"),
                      col(para(t, "oslab saved your prediction in a hidden folder, .records. It stays as it was, so the comparison shows which answers you confirmed and which you corrected.", size=30),
                          card(t, "Class discussion", "A file is readable by its mode, but you still got Permission denied. Where do you look?", label="DISCUSS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

labkit.submission(d, 6, ['cp -- evidence/policy.txt evidence/traversal.txt "$SUBMISSION_REPO/lab6/evidence/"'],
                  [("README.md", None), ("evidence", [("policy.txt", None), ("traversal.txt", None)])],
                  note="If you did Plus or Challenge, copy evidence/plus.txt the same way. The course website checks that these exact names are there. Check the final modes once more.")

d.slide("submit-git", "Submit 3: commit and push",
        lambda t: row(term(t, ["cd ~/os-gic-YOUR_ID",
                               "git pull",
                               "git add os-lab-YOUR_ID/lab6",
                               'git commit -m "Lab 6"',
                               "git push"], title="student@server: ~", size=26),
                      col(para(t, "git pull comes first, in case you pushed from your own computer since.", size=32),
                          para(t, "Replace YOUR_ID with your own ID, as before.", size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.grading(d, [["Modes: oslab check lab6 passes the four Core milestones (private, your notice policy, the traversal test, policy.txt)", "2"],
                   ["Tests: policy.txt and traversal.txt show the modes and the failure, and the README separates what you tested from what you reasoned", "2"],
                   ["Prediction saved in time, and corrected with oslab debrief lab6", "2"],
                   ["Live checkpoint: the answers and the new folder with the right modes", "3"],
                   ["Complete submission: the required files in your repository, on time", "1"]],
               note="Every row is marked from your oslab records and the files in your repository, so run oslab check lab6 until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.")

labkit.mistakes(d, [["Mode 644 on a file in a 700 folder", "Others still cannot reach it", "Check every parent of the path"],
                    ["Directory with r but no x", "Names listed, file not opened", "Add x for search"],
                    ["Running a data file to test read", "Permission denied, and a wrong lesson", "Use cat, and test -x for execute"],
                    ["Widening your home to test a peer", "A private folder opened to everyone", "Reason it, or ask for a prepared account"],
                    ["Typing BOX, or leaving the demo folder at 600", "A folder named BOX, or a sealed folder in your evidence", "Use your own box value, and chmod 700 after the test"]])

# ---- beyond the core --------------------------------------------------------------
d.opener("ext-open", "BEYOND THE CORE", "Accounts, ACLs and special bits", "Optional extensions. They need prepared identities or a disposable virtual machine.")

d.slide("ext-acct", "Accounts and groups",
        lambda t: row(tbl(t, ["File", "Holds"],
                          [[mono("/etc/passwd"), "Accounts: name, uid, gid, home, shell"],
                           [mono("/etc/group"), "Groups and their members"],
                           [mono("/etc/shadow"), "Password hashes, readable by root only"]],
                          [4, 8], width=HALF),
                      term(t, ["id", "groups", "getent passwd student", "getent group student"], size=26, width=HALF),
                      gap=32, align="center"),
        note="Creating accounts and groups needs administrator rights. Do it only on a disposable virtual machine.",
        label=EXT)

d.slide("ext-acl", "ACLs and special bits",
        lambda t: row(card(t, "ACLs", "Extra rules for named users or groups, on top of the mode. getfacl shows them and setfacl changes them.", label="ACL", pad=32, title_size=32),
                      card(t, "setuid and setgid", "A program runs with its owner's or group's rights, not the caller's. On a directory, setgid makes new files inherit the group.", label="SPECIAL BITS", pad=32, title_size=32),
                      card(t, "Sticky bit", "In a shared folder such as /tmp, only a file's owner may remove it, even if others can write the folder.", label="STICKY", pad=32, title_size=32),
                      gap=32, align="stretch"),
        note="ls -l shows s and t in place of x, and chmod can set them with a fourth octal digit, for example 2755 or 1777.",
        label=EXT)

d.close([("Three triples", "Owner, group and others each get r, w and x. The first match decides."),
         ("Directory x is search", "Without x on a folder you cannot reach what is in it, whatever the file's own mode says."),
         ("Check the whole path", "The strictest folder between / and the file decides."),
         ("Observed or reasoned", "Say which claims you tested and which you only worked out.")],
        "chapter 17, Protection", ("Lab 7: Bash scripting and server automation", "Put commands in a script, pass it arguments, and make it safe to run."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: users and groups, the mode string, octal and symbolic modes, directory search and the whole path.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the rules, setup and the starting tree.", "start": "lab-open"},
    "s4": {"description": "Guided: permission basics, then the prediction.", "start": "g-open"},
    "s5": {"description": "Core 1 and Core 2: set the modes and prove them, then Plus and Challenge.", "start": "c1-open"},
    "s6": {"description": "The live checkpoint: why, the steps with oslab, and what it asks.", "start": "cp-open"},
    "s7": {"description": "Debrief, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: accounts, ACLs and special bits, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
