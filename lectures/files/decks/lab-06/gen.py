"""Lab 6 guide, Linux Security, Users, Groups and File Permissions. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

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
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, init)  # noqa: E402,F401

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
                "You work only on files you own. Any real multi-user test needs an account the instructor has prepared.", START_TREE)
labkit.timetable(d, [["0 to 10", "Introduction, objectives and setup"],
                     ["10 to 25", "Guided example: permission basics"],
                     ["25 to 35", "Written prediction"],
                     ["35 to 70", "Task 3: policy, modes and traversal"]],
                 [["70 to 85", "Owner, search and peer-access tests"],
                  ["85 to 100", "Individual changed-case checkpoint"],
                  ["100 to 110", "Correction and explanation"],
                  ["110 to 120", "Cleanup and submission"]])
labkit.rules(d, safety="Never edit sudoers or create accounts for the core. Do not widen your home folder to test a peer.")
labkit.setup_slides(d, 6, START_TREE,
                    ["private/record.txt is your private record.",
                     "shared/notice.txt is the notice that others should be able to read, once an administrator puts it in a searchable place.",
                     "The helper also writes a hidden file, .oslab-managed.json. Leave it as it is."])

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Permission basics", "Task 3, guided part, with the instructor: fifteen minutes.")

d.slide("g-id", "Step 1: who am I, and what do I own?",
        lambda t: row(term(t, ["id",
                               "ls -ld . private shared",
                               "stat -c '%A %a %U:%G %n' private/record.txt shared/notice.txt"], size=24),
                      col(para(t, "Nothing is changed in this step. id shows your user and groups.", size=32),
                          para(t, "Each triple of the mode applies to the owner, the owning group and others. A directory's x bit is search, not running a program.", size=32),
                          gap=24),
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
                          para(t, "The second mode, 640, lets the owning group read the file. It does not make any directory on the path searchable.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-path", "Step 3: look at the path",
        lambda t: row(term(t, ['namei -l "$PWD/demo/note.txt"'], size=28),
                      col(para(t, "If namei is not installed, list each parent with ls -ld.", size=32),
                          card(t, "Observe", "Does mode 644 on a file inside a 700 directory mean other users can reach that file?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.predict(d, "A directory has mode 600 and holds a mode-600 file that you own. Can you list the directory's names? Can you open the file through that directory? Explain the directory bits.")

# ---- task 3 -----------------------------------------------------------------
d.opener("t3-open", "TASK 3", "Private record and public-notice policy", "Thirty-five minutes, from minute 35 to 70. Work alone.")

d.slide("t3-policy", "Step 1 and 2: write the policy, then the modes",
        lambda t: row(col(h3(t, "First, in words"),
                          lst(t, ["The owner reads and writes the private record. Nobody else reads it.",
                                  "Others may only read the notice, once it is in a searchable place."], size=30),
                          h3(t, "Then, in modes"),
                          lst(t, ["Choose a mode for private/, record.txt, shared/ and notice.txt.",
                                  "Apply them only to these four paths."], size=30),
                          gap=20, flex=3),
                      col(term(t, ["stat -c '%A %a %U:%G %n' private private/record.txt \\", "  shared shared/notice.txt | tee evidence/policy.txt"], size=24, title="save the result"),
                          card(t, "You choose the modes", "Nobody gives you the numbers. Give the least access that still does the job.", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=3),
                      gap=48, align="stretch"))

d.slide("t3-owner", "Step 3: use the record as its owner",
        lambda t: row(term(t, ["cat private/record.txt",
                               "printf 'owner update\\n' >> private/record.txt",
                               "if test -x private/record.txt; then printf 'unexpected execute bit\\n'; else printf 'not executable\\n'; fi"], size=24),
                      col(para(t, "Read and append as the owner. Then check the file has no execute bit. A data file should not have one.", size=32),
                          para(t, "test -x asks: may I execute this? Do not run a data file to try its read permission.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t3-sealed", "Step 4: a directory you can read but not search",
        lambda t: row(term(t, ["mkdir -p demo/sealed",
                               "printf 'inside\\n' > demo/sealed/item.txt",
                               "chmod 600 demo/sealed",
                               "ls demo/sealed | tee evidence/traversal.txt",
                               "cat demo/sealed/item.txt 2>&1 | tee -a evidence/traversal.txt",
                               "chmod 700 demo/sealed",
                               "cat demo/sealed/item.txt | tee -a evidence/traversal.txt"], size=24),
                      col(para(t, "The failing cat is intentional. Record the failure and the repair in evidence/traversal.txt.", size=32),
                          para(t, "Restore search permission at once with chmod 700. Some ls variants also read file details and may print errors, so compare a plain list of names with real access.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t3-peer", "Step 5: a peer's hypothetical access",
        lambda t: row(col(h3(t, "Reason it, do not fake it"),
                          lst(t, ["Look at every parent of the notice, including the private oslab-work folder.",
                                  "A mode on the notice alone cannot turn a private workspace into a public place.",
                                  "Do not widen your home folder or workspace to build a peer test."], ordered=True, size=32),
                          gap=20, flex=3),
                      col(card(t, "Observed or reasoned?", "A real test with another user needs an account the instructor prepared. Say clearly which statements you tested and which you only reasoned.", label="HONESTY", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("t3-done", "Complete when, and hints",
        lambda t: row(card(t, "Complete when", "The modes match your policy. The traversal failure is explained and repaired. The peer reasoning covers the whole path.",
                           label="DONE", pad=40, title_size=36, flex=1),
                      col(h3(t, "Hints, one at a time"),
                          lst(t, ["Keep file permissions apart from directory search.", "Use stat and namei.",
                                  "Restore search permission on the demo directory before you try the file again."], ordered=True, size=32),
                          gap=20, flex=1),
                      gap=48, align="stretch"))

# ---- tests ---------------------------------------------------------------------
d.opener("test-open", "TESTS AND FEEDBACK", "Three cases, three limits", "Fifteen minutes, from minute 70 to 85.")

d.slide("tests-table", "What each case shows, and what it cannot show",
        lambda t: tbl(t, ["Case", "Evidence", "Limit"],
                      [["Owner access", "Read and append the private record, then inspect the modes", "Does not simulate another user"],
                       ["Search failure", "Before, failed and restored reads under demo/sealed", "Shows traversal, not every ACL or capability effect"],
                       ["Peer access", "A full-path explanation of the modes", "Needs a prepared second account to confirm in practice"]],
                      [3, 8, 7]),
        note="Default ACLs can change the mode of new files. Use getfacl if it exists and report any ACL you did not expect. Look at the final modes again after your tests.")

d.slide("tests-trouble", "If something does not work",
        lambda t: row(rule(t, "Check who you are", "Run whoami and id, and confirm you own the file before you change its mode.", title_size=36),
                      rule(t, "chown is not for you", "A normal user cannot give a file to another account. Do not try.", title_size=36),
                      rule(t, "Stay within the core", "Never edit sudoers or create accounts for this lab. See man chmod and man path_resolution.", title_size=36)))

# ---- checkpoint, correction, submission -------------------------------------------
labkit.checkpoint(d, "A prepared shared directory has mode 711 and holds a file with mode 600, owned by another student. You know the file's name. Explain whether you can traverse the directory, list its names, and read the file.")
labkit.correction(d, "(a) Which directory bit caused the failed file read? (b) Why does a 644 notice not override a 700 parent? (c) Which observations were real tests, and which were reasoning?")
labkit.submission(d, 6, ['cp -- evidence/policy.txt evidence/traversal.txt "$SUBMISSION_REPO/lab6/evidence/"'],
                  [("README.md", None), ("evidence", [("policy.txt", None), ("traversal.txt", None)])],
                  note="Copy the two evidence files and two selected test records, not every terminal output. Check the final modes once more.")
labkit.grading(d, [["Modes match the owned-file policy, with reasoning about the full path", "3"],
                   ["Owner-access tests and the directory-search failure and repair", "2"],
                   ["rwx and octal explained, and the limits of peer-access claims; original prediction and correction", "2"],
                   ["Individual checkpoint: result or diagnosis, and mechanism", "2"],
                   ["Concise, attributable evidence and the required artifacts", "1"]])
labkit.mistakes(d, [["Mode 644 on a file in a 700 folder", "Others still cannot reach it", "Check every parent of the path"],
                    ["Directory with r but no x", "Names listed, file not opened", "Add x for search"],
                    ["Running a data file to test read", "Permission denied, and a wrong lesson", "Use cat, and test -x for execute"],
                    ["Widening your home to test a peer", "A private folder opened to everyone", "Reason it, or ask for a prepared account"]])

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
    "s5": {"description": "Task 3: policy, modes and traversal, then the tests.", "start": "t3-open"},
    "s6": {"description": "The individual checkpoint: why, and the practice question.", "start": "cp-open"},
    "s7": {"description": "Correction, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: accounts, ACLs and special bits, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
