"""Lab 8 guide, Secure Bash Scripting, Race Conditions and File Locking. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

A guide for the lab session, built like the Lab 2 guide, because Lab 8 is in the pilot format (personal
values, Core / Plus / Challenge, a live checkpoint, the oslab helper). The shared look and the standard
slides are in labkit.py. The concepts section is new: critical sections, a race condition, advisory locks and
flock. The lab part follows labs/lab8/lab8-instruction.md. The inventory checks and the prepared drop box
are optional extensions in that instruction, so they come last (images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, flow, init)  # noqa: E402,F401

WEEK = "Lab 8"
TITLE = "Operating Systems — Lab 8"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-28T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 8)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-08", "Race Conditions and File Locking",
                  "Lab 8 guide: watch two buyers oversell a shop, say why, and repair it with a lock.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Read a short script and find its critical section.",
                    "Reproduce a race condition, and show which rule it breaks.",
                    "Protect the whole critical section with a file lock, and test it."], ordered=True, size=36, flex=3),
            card(t, "Lab 8", "First the concepts, with examples. Then the lab on the server: Core for everyone, Plus and Challenge if you finish early, and a live checkpoint.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "Two people buy the last widget at the same moment. Who gets it?",
         "If the shop checks the stock and then sells, what can happen between the check and the sale?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Critical sections and locks", "Three ideas: a check followed by a change, two programs at once, and a lock that makes them take turns.")

d.slide("crit", "A critical section touches shared data",
        lambda t: row(lst(t, ["Shared data is something more than one program can change: here, a stock file.",
                              "A critical section is the part of a program that reads and then changes that shared data.",
                              "While one program is inside, no other program may be inside. This is mutual exclusion.",
                              "The rule must cover the whole sequence: read, decide, write."], size=34, flex=3),
                      card(t, "Why learn it here?", "Every shared file, database and counter has this problem. The same idea returns in the lectures on semaphores and monitors.", label="FOR THE WHOLE COURSE", pad=40, title_size=36, flex=2),
                      gap=48, align="stretch"),
        label=BG)

d.slide("race", "A race condition",
        lambda t: tbl(t, ["Step", "Buyer A", "Buyer B", "stock.txt"],
                      [["1", "reads the stock: 9", "", "9"],
                       ["2", "", "reads the stock: 9", "9"],
                       ["3", "decides: 7 is enough", "decides: 8 is enough", "9"],
                       ["4", "writes 9 - 7 = 2", "", "2"],
                       ["5", "", "writes 9 - 8 = 1", "1"]],
                      [2, 6, 6, 3]),
        note="Both buyers read 9 before either wrote. 15 widgets are sold, but only 9 existed. The result depends on who is faster: that is a race.",
        label=BG)

d.slide("invariant", "The rule that must stay true",
        lambda t: row(card(t, "An invariant", "A statement that must be true at all times. Here: units sold + units left = the starting stock.", label="RULE", pad=40, title_size=36),
                      card(t, "A race breaks it", "After the race above: 15 sold + 1 left = 16, not 9. The rule is false, so the program is wrong.", label="BROKEN", pad=40, title_size=36),
                      card(t, "Why a delay helps", "BUY_DELAY=1 makes the payment take one second. The two buyers then overlap on purpose, so you can see the problem every time.", label="IN THE LAB", pad=40, title_size=36),
                      gap=32, align="stretch"),
        label=BG)

d.slide("flock", "A lock with flock",
        lambda t: row(term(t, ["(",
                               "    flock -x -w 2 9 || exit 3",
                               "    echo 'I hold the lock'",
                               ") 9>store/demo.lock"], size=28),
                      col(para(t, "9>store/demo.lock opens the lock file as file descriptor 9 for this group of commands.", size=30),
                          para(t, "flock -x asks for an exclusive lock on it. -w 2 waits at most two seconds. If it cannot get the lock, exit 3 ends the group with status 3.", size=30),
                          para(t, "The lock is released when descriptor 9 is closed, at the closing bracket, or when the process ends for any reason.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=BG)

d.slide("advisory", "A lock only works if everybody asks for it",
        lambda t: row(rule(t, "Advisory", "flock does not stop a program that never asks. It only makes programs that ask take turns.", title_size=36),
                      rule(t, "One shared lock file", "All buyers must use the same lock file, or they do not meet at the lock.", title_size=36),
                      rule(t, "Cover the whole sequence", "Start the lock before the read, and release it after the last write. A lock around only the write is too late.", title_size=36)),
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 8", "Secure scripts, races and file locking", "QuantumTech sells widgets with a small Bash script. It works for one buyer. Two at once, and it oversells.")

START_TREE = [("store", [("buy.sh", None), ("stock.txt", None), ("sales.log", None), ("ai-answers", [])]), ("evidence", [])]

labkit.scenario(d, 8, "QuantumTech's widget shop", "The script works for one buyer. On a busy day two buyers arrive together and the shop sells widgets it does not have. You will see the problem, explain it, and repair it.",
                "Your numbers are your own. This guide shows example values.", START_TREE, cmd="tree")
labkit.timetable(d, [["0 to 5", "Setup"],
                     ["5 to 20", "Read and trace the script"],
                     ["20 to 30", "Prediction, then class discussion"],
                     ["30 to 50", "Core 1: break it"],
                     ["50 to 75", "Core 2: fix it"]],
                 [["75 to 90", "Plus and Challenge, or finish Core"],
                  ["90 to 105", "Live checkpoint"],
                  ["105 to 115", "Debrief"],
                  ["115 to 120", "Submit"]])

d.slide("helper", "Five helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does", "Why"],
                      [[mono("oslab values lab8"), "Shows your own numbers", "Your work is different from your neighbour's"],
                       [mono("oslab predict lab8"), "Saves your prediction once, before the experiment", "Guessing first makes you think. The first answer is kept"],
                       [mono("oslab hint lab8 1"), "A hint, levels 1 to 3", "You get unstuck without waiting, at no cost"],
                       [mono("oslab check lab8"), "Tests your script and shows your milestones", "You see at once what is still missing"],
                       [mono("oslab checkpoint lab8"), "Opens when the instructor says so, near the end", "It shows what you can do alone"]],
                      [5, 7, 8]),
        note="Before the lab, run oslab doctor and oslab prelab lab8. It takes about ten minutes.")

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Core, Plus, Challenge", "Core is for everyone. Plus and Challenge are for students who finish early. Full marks need only Core and the checkpoint.", title_size=36),
                      rule(t, "AI tools", "Allowed in Core, Plus and Challenge, so test what they tell you. Not allowed in the prediction and the checkpoint.", title_size=36),
                      rule(t, "Three wrong fixes", "In Plus you will see three AI fixes that use flock, look right, and are wrong.", title_size=36)),
        note="A wrong prediction costs nothing. It is marked for being made and corrected, not for being right.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ['export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab8",
                               'cd "$OSLAB_WORKSPACE/lab8"',
                               "mkdir -p evidence",
                               "oslab values lab8"], title="student@server: ~", size=26),
                      col(lst(t, ["The first line sets OSLAB_WORKSPACE to ~/oslab-work, unless it is already set. Type it as it is.",
                                  "oslab start lab8 makes the lab folder.",
                                  "cd takes you into it, and mkdir -p makes the evidence folder.",
                                  "oslab values lab8 prints your own numbers."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("values", "Your values, kept in variables",
        lambda t: row(col(h3(t, "1. The command prints your values"),
                          term(t, ["oslab values lab8",
                                   ("out", "Your personal values for lab8 (your-account):"),
                                   ("out", "  stock    = 9"),
                                   ("out", "  buyer_a  = 7"),
                                   ("out", "  buyer_b  = 8")], title="example: your values will be different", size=28),
                          gap=20, flex=None),
                      col(h3(t, "2. Type them into shell variables"),
                          term(t, ["stock=9", "buyer_a=7", "buyer_b=8"], title="type your own values", size=28),
                          para(t, "Write name=value with no spaces around =. In a new terminal, run cd into the lab folder and set them again.", size=28),
                          gap=20, flex=None),
                      gap=48, align="flex-start"))

d.slide("start-tree", "Your folder",
        lambda t: row(tree(t, "lab8", START_TREE, cmd="tree", title="student@server: ~/oslab-work/lab8", size=30),
                      col(para(t, "store/buy.sh is the shop script. It works for one buyer.", size=32),
                          para(t, "store/stock.txt holds your starting stock. sales.log is empty.", size=32),
                          para(t, "store/ai-answers/ holds three AI fixes for the Plus task.", size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- read and trace -------------------------------------------------------------
d.opener("g-open", "READ AND TRACE", "Understand the script first", "Fifteen minutes. Do not run two buyers yet.")

d.slide("g-read", "Step 1 and 2: one buyer, then put the data back",
        lambda t: row(term(t, ["cat -n store/buy.sh",
                               "bash store/buy.sh 1",
                               "cat store/stock.txt store/sales.log",
                               ("blank",),
                               "printf '%s\\n' \"$stock\" > store/stock.txt",
                               ": > store/sales.log"], size=24),
                      col(para(t, "cat -n shows the script with line numbers. Let one buyer buy one unit and look at the two files.", size=30),
                          para(t, "Then put the test data back. You will use the last two lines many times: one writes your stock, the other empties the log.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-trace", "Step 3: answer four questions in evidence/trace.txt",
        lambda t: row(lst(t, ["Which line reads the stock?",
                              "Which lines change a file?",
                              "After which line has the script decided that there is enough stock?",
                              "Finish the rule: units sold + units left = ..."], ordered=True, size=34, flex=3),
                      col(term(t, ["nano evidence/trace.txt"], size=28),
                          card(t, "In your own words", "Use line numbers from cat -n. You will use this reading again in Core 2.", label="TRACE", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

# ---- prediction -------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you run two buyers. Ten minutes.")

d.slide("predict", "The prediction",
        lambda t: row(col(term(t, ["oslab predict lab8"]),
                          para(t, "Answer the questions the command asks, about what will happen when two buyers run together.", size=32),
                          gap=24, flex=3),
                      col(card(t, "The rules", "Alone, and without AI. The first answer is the one that counts. A wrong guess costs nothing.", label="PREDICTION", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"),
        note="The class then looks at the spread of answers together, without names.")

# ---- core 1 -----------------------------------------------------------------
d.opener("c1-open", "CORE 1", "Break it", "Twenty minutes, from minute 30 to 50. Make two buyers run together.")

d.slide("c1-run", "Step 1: two buyers at the same time",
        lambda t: row(term(t, ['BUY_DELAY=1 bash store/buy.sh "$buyer_a" > evidence/a.txt 2>&1 &',
                               "pid_a=$!",
                               'BUY_DELAY=1 bash store/buy.sh "$buyer_b" > evidence/b.txt 2>&1 &',
                               "pid_b=$!",
                               'wait "$pid_a"; rc_a=$?',
                               'wait "$pid_b"; rc_b=$?'], size=24),
                      col(para(t, "A trailing &amp; starts a command in the background, so the next line runs at once. $! is the PID of the last background command.", size=30),
                          para(t, "wait PID waits for that one command and $? then holds its exit status. BUY_DELAY=1 makes the payment take a second, so the two buyers overlap.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c1-save", "Step 2: save what happened",
        lambda t: row(term(t, ["{",
                               '  echo "start=$stock  A wants $buyer_a (exit $rc_a)  B wants $buyer_b (exit $rc_b)"',
                               "  cat evidence/a.txt evidence/b.txt",
                               '  echo "stock.txt now: $(cat store/stock.txt)"',
                               "  cat store/sales.log",
                               "} | tee evidence/race.txt"], size=24),
                      col(para(t, "The braces group several commands, so tee saves the output of all of them in evidence/race.txt.", size=30),
                          para(t, "$(...) puts the output of a command into the text.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c1-check", "Step 3 to 5: check the rule, then choose your own quantities",
        lambda t: row(col(h3(t, "Check the rule"),
                          lst(t, ["How many units were sold? How many are left?",
                                  "Add one line to evidence/race.txt that says which number is wrong."], size=30),
                          h3(t, "Your decision"),
                          lst(t, ["Put the test data back. Choose two small quantities whose sum is less than your stock.",
                                  "Run the two buyers again. Is stock.txt correct now? Add your quantities, the result and one sentence.",
                                  "Run oslab check lab8: two milestones pass and one does not. That is expected."], size=30),
                          gap=20, flex=3),
                      col(card(t, "Why this matters", "With small quantities the race can hide. A passing run does not show that the script is safe.", label="THINK", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

# ---- core 2 -----------------------------------------------------------------
d.opener("c2-open", "CORE 2", "Fix it", "Twenty-five minutes, from minute 50 to 75. You decide where the lock goes.")

d.slide("c2-prep", "Step 1 to 3: keep a copy, try flock, plan the lock",
        lambda t: row(term(t, ["cp -- store/buy.sh store/buy_unsafe.sh",
                               "(",
                               "    flock -x -w 2 9 || exit 3",
                               "    echo 'I hold the lock'",
                               ") 9>store/demo.lock"], size=26),
                      col(para(t, "Keep the unsafe script. You will compare against it later.", size=30),
                          para(t, "Try flock alone first, as on the concepts slide.", size=30),
                          card(t, "Before you edit", "In evidence/trace.txt write the first line and the last line of buy.sh that must be inside the lock, and why.", label="PLAN", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-edit", "Step 4: edit buy.sh and add the lock",
        lambda t: row(col(h3(t, "You decide"),
                          lst(t, ["Where the lock starts.",
                                  "What the script does when it cannot get the lock: print a message and exit with status 3.",
                                  "Which lock file all buyers share.",
                                  "Keep the BUY_DELAY line."], size=32),
                          gap=20, flex=3),
                      col(term(t, ["nano store/buy.sh"], size=28),
                          card(t, "You write it", "Nobody gives you the lines. Use your plan from the trace.", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c2-test", "Step 5 and 6: test it again",
        lambda t: row(col(lst(t, ["Put the test data back.",
                                  "Run the two buyers from Core 1 again.",
                                  "Save the result in evidence/locked.txt, with the same block as before.",
                                  "Run oslab check lab8 until all three milestones pass."], ordered=True, size=32),
                          gap=20, flex=3),
                      col(card(t, "Core is complete when", "oslab check lab8 shows milestones: 3/3, and your trace names the lines inside the lock.", label="DONE", pad=32, title_size=32),
                          card(t, "Stuck for five minutes?", "oslab hint lab8 1, then 2, then 3. Hints cost no points.", label="HINTS", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("plus", "Plus: review three AI answers",
        lambda t: row(term(t, ["diff store/buy_unsafe.sh store/ai-answers/a.sh",
                               ("blank",),
                               "mkdir -p try",
                               "cp -- store/ai-answers/a.sh try/buy.sh",
                               "printf '%s\\n' \"$stock\" > try/stock.txt",
                               ": > try/sales.log",
                               'BUY_DELAY=1 bash try/buy.sh "$buyer_a" & BUY_DELAY=1 bash try/buy.sh "$buyer_b" & wait',
                               "cat try/stock.txt try/sales.log"], size=24),
                      col(para(t, "Each of the three answers uses flock, and each is wrong. Test them in a separate folder, so your own script stays safe.", size=30),
                          card(t, "For each answer, write in evidence/ai-review.txt", "The line that is wrong, and one sentence on why two buyers can still be inside the critical section together.", label="PLUS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("challenge", "Challenge: choose one",
        lambda t: row(card(t, "Killed buyer", "Start one buyer of your fixed script with BUY_DELAY=20 in the background, save its PID, and kill that PID while it holds the lock. Does the next buyer wait for ever? Explain what the kernel does with the lock.", label="CHALLENGE 1", pad=36, title_size=36),
                      card(t, "Smallest repair", "Make ai-answers/a.sh correct by moving lines only. Do not add or delete a line.", label="CHALLENGE 2", pad=36, title_size=36),
                      gap=32, align="stretch"),
        note="Save your commands and your explanation in evidence/challenge.txt.")

# ---- live checkpoint ----------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "Your numbers are new", "The questions use new numbers, made for you at that moment. An answer copied from a neighbour does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once, so a common mistake can be explained before the next lab.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task. You can answer the questions even if Core is not finished.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab8", "Answer the questions"),
                           ("3. Change buy.sh", "The small change the command prints"), ("4. oslab check lab8", "A fourth milestone must pass")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command says that the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab8 shows whether the checkpoint milestone passes. You can fix your script and check again.", title_size=36)),
        gap=56)

d.slide("cp-marks", "What the checkpoint asks",
        lambda t: tbl(t, ["Part", "What you do"],
                      [["Three numbers, with new values", "Three buyers run your repaired buy.sh together. How many purchases are accepted, what does stock.txt hold, how many units does sales.log show?"],
                       ["One sentence", "Which line of your script makes a later buyer see the earlier buyer's update?"],
                       ["One change to buy.sh", "One purchase may be at most a limit. A larger quantity prints a message, exits with status 4 and changes nothing. Then run oslab check lab8."]],
                      [6, 13]),
        lambda t: row(rule(t, "Can I answer again?", "No. Your answers are saved once. You can still fix your script and run oslab check lab8 again.", title_size=36),
                      rule(t, "Core not finished?", "Answer the questions first. They do not depend on a finished script.", title_size=36)),
        gap=48)

# ---- debrief and submit -----------------------------------------------------------
d.opener("end-open", "DEBRIEF AND SUBMIT", "Look back, then hand in", "Ten minutes of debrief, five to submit.")

d.slide("debrief", "Debrief: look at your prediction again",
        lambda t: row(term(t, ['cat "$OSLAB_WORKSPACE/.records/lab8-predict.json"'], size=26, title="student@server: ~/oslab-work/lab8"),
                      col(para(t, "For each answer write confirmed or corrected.", size=32),
                          card(t, "Explain in three to five sentences", "Why can the stock stay above zero while the shop sells too much? Which lines must share one lock?", label="ANSWER", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.submission(d, 8, ['cp -- store/buy.sh "$SUBMISSION_REPO/lab8/"',
                         'cp -- evidence/trace.txt evidence/race.txt evidence/locked.txt "$SUBMISSION_REPO/lab8/evidence/"'],
                  [("README.md", None), ("buy.sh", None), ("evidence", [("trace.txt", None), ("race.txt", None), ("locked.txt", None)])],
                  note="Add ai-review.txt or challenge.txt if you did them. Do not delete store/stock.lock while a buyer is running.")

d.slide("grading", "How it is marked: 10 points",
        lambda t: tbl(t, ["Evidence", "Points"],
                      [["A working script: oslab check lab8 passes the three Core milestones", "2"],
                       ["Tests: the unsafe run, your own quantities, and the run after the repair", "2"],
                       ["The prediction saved in time, and an honest confirmed or corrected explanation", "2"],
                       ["The live checkpoint: answers, the change to your script, and your sentence", "3"],
                       ["Clear, complete evidence files and report", "1"]],
                      [10, 1]),
        note="Plus and Challenge are not needed for full marks. They are noted in your feedback. Your prediction is marked for being made and corrected, not for being right.")

labkit.mistakes(d, [["Lock around only the write", "Both buyers still read the same stock", "Start the lock before the read"],
                    ["Each buyer uses its own lock file", "No waiting, and the race stays", "All buyers share one lock file"],
                    ["Forgetting the exit code on a failed lock", "The script goes on without the lock", "flock ... || exit 3"],
                    ["Testing with tiny quantities", "A race that does not show", "Use quantities that make the sum exceed the stock"]])

# ---- beyond the core --------------------------------------------------------------
d.opener("ext-open", "BEYOND THE CORE", "Conservation and the drop box", "Optional extensions. At most two buyers per run, and no stress loops on the shared server.")

d.slide("ext-inv", "Check the invariant with numbers",
        lambda t: row(term(t, ["awk '$1 == \"sold\" {sum += $2} END {print \"sold units:\", sum+0}' store/sales.log",
                               ("out", "sold units: 7"),
                               "cat store/stock.txt",
                               ("out", "2")], size=24),
                      col(para(t, "Add the units sold. Do not only count the lines of the log.", size=30),
                          para(t, "Check: starting stock = final stock + accepted sold units.", size=30),
                          para(t, "Try quantities whose sum exceeds the stock, and an invalid stock such as abc in an owned copy. No sale may be logged.", size=30),
                          gap=22),
                      gap=48, align="center"),
        note="Advisory locks only work when every writer takes part, and a crash between the two writes can still lose data. This is a teaching script, not a database.",
        label=EXT)

d.slide("ext-box", "A prepared drop box, and the log",
        lambda t: row(card(t, "A shared drop box", "Only if the instructor prepared a narrow folder. Check its parent folders, its group or ACL and its naming rule before you send one test request.", label="DROP BOX", pad=32, title_size=32),
                      card(t, "Log housekeeping", "Copy sales.log to a uniquely named evidence file before you start a new case. Never rotate a log while a buyer is running.", label="LOG", pad=32, title_size=32),
                      card(t, "Clean only what is yours", "Remove only known demonstration files you own, never files that match a wildcard in a classmate's folder.", label="CAREFUL", pad=32, title_size=32),
                      gap=32, align="stretch"),
        label=EXT)

d.close([("Critical section", "The read, the decision and the write belong together. Protect all of them."),
         ("A race is about timing", "It may pass many times and then fail. A delay makes it visible, it does not cause it."),
         ("flock", "An advisory lock on a shared file. Every program must ask, and all must use the same file."),
         ("Test the fix", "Use the same run as before, and check the rule: sold plus left equals the start.")],
        "chapter 6, Synchronization Tools", ("Lab 9: a vault deadlock", "Two workers each hold one lock and wait for the other. Find the order that avoids it."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: the critical section, a race condition, the invariant, flock and advisory locks.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the helper commands, the rules, setup and your values.", "start": "lab-open"},
    "s4": {"description": "Read and trace the script.", "start": "g-open"},
    "s5": {"description": "The prediction.", "start": "predict-open"},
    "s6": {"description": "Core 1 and 2, then Plus and Challenge.", "start": "c1-open"},
    "s7": {"description": "The live checkpoint: why it exists, what happens and how it is marked.", "start": "cp-open"},
    "s8": {"description": "Debrief, submission, grading, common mistakes, beyond the core, takeaways and the next lab.", "start": "end-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
