"""Lab 9 guide, Vault Deadlock, Resource Ordering and Recovery. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

Revised 2026-11-05 to the pilot-format instruction: two personal lock names and the lock worker A takes first (RES1
and RES2), Core 1 and Core 2, Plus and Challenge, a live checkpoint, oslab predict and oslab debrief. Modelled on the Lab 8 guide.

A guide for the lab session, built like the Lab 3 to Lab 7 guides with the shared look and the shared standard
slides in labkit.py. The concepts section is new: resources and holdings, the four conditions of a deadlock,
a wait cycle drawn as edges, prevention by lock order versus recovery by timeout. The lab part follows
labs/lab9/lab9-instruction.md. Process wait traces and the prepared site-to-site exercise are optional
extensions in that instruction, so they come last (images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, flow, init)  # noqa: E402,F401

WEEK = "Lab 9"
TITLE = "Operating Systems — Lab 9"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-28T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 9)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-09", "Deadlock, Lock Order and Recovery",
                  "Lab 9 guide: make two workers wait for each other, draw the cycle, and remove it with one lock order.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Draw holdings and requests that form a circular wait.",
                    "Reproduce a two-worker conflict with bounded waits, and read how a timeout recovers from it.",
                    "Apply one global lock order, and explain why it removes the cycle."], ordered=True, size=36, flex=3),
            card(t, "Lab 9", "First the concepts, with pictures. Then the lab on the server. Wait traces and the site-to-site exercise are optional extensions, so they come last.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "Two people each hold one key and want the other's. What happens?",
         "Neither will give theirs up first. How long will they wait? How could they have avoided it?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Holding, waiting and cycles", "Three ideas: a worker can hold one resource while it asks for another, waits can form a circle, and a rule or a timeout can break it.")

d.slide("four", "Four conditions for a deadlock",
        lambda t: grid(card(t, "Mutual exclusion", "A resource can be used by only one worker at a time.", number="01", pad=32, title_size=32),
                       card(t, "Hold and wait", "A worker holds one resource while it asks for another.", number="02", pad=32, title_size=32),
                       card(t, "No preemption", "A resource cannot be taken away. Its holder must release it.", number="03", pad=32, title_size=32),
                       card(t, "Circular wait", "Worker A waits for B, and B waits for A: the waits form a circle.", number="04", pad=32, title_size=32),
                       cols=2),
        note="All four must hold together. Removing any one of them prevents a deadlock. This lab removes the fourth.",
        label=BG, gap=36)

d.slide("edges", "Draw it as holdings and requests",
        lambda t: row(tbl(t, ["Worker", "Holds", "Requests"],
                          [["A", "Alpha", "Beta"],
                           ["B", "Beta", "Alpha"]],
                          [2, 3, 3], width=HALF),
                      col(para(t, "Draw an arrow from a resource to the worker that holds it, and from a worker to the resource it waits for.", size=32),
                          para(t, "Here: Alpha to A, A to Beta, Beta to B, B to Alpha. The arrows close a circle, so neither worker can go on.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=BG)

d.slide("flock-bounded", "A lock with a time limit",
        lambda t: row(term(t, ["(",
                               "    flock -x -w 2 8 || exit 3",
                               "    printf 'holding Alpha\\n'",
                               ") 8>vault/alpha.lock"], size=28),
                      col(para(t, "A data file holds the data. A lock file stands for cooperative exclusive access. Creating a file named locked is not a lock.", size=30),
                          para(t, "flock -x -w 2 waits at most two seconds for the lock. If it does not get it, the status is not zero, and the script can stop waiting.", size=30),
                          para(t, "Descriptor 8 stays open until the group of commands ends, and that is when the lock is released.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=BG)

d.slide("prev-rec", "Two ways to deal with a deadlock",
        lambda t: row(card(t, "Prevention: a global lock order", "Every worker takes Alpha before Beta. A worker that waits for Alpha holds nothing yet, so no circle can form.", label="BEFORE IT HAPPENS", pad=40, title_size=36),
                      card(t, "Recovery: a timeout", "A worker that waits too long gives up and releases what it holds. The others can then go on.", label="AFTER IT HAPPENS", pad=40, title_size=36),
                      card(t, "Use both", "Ordering stops this circle. Timeouts also bound waits that come from other causes. Neither gives fairness.", label="IN PRACTICE", pad=40, title_size=36),
                      gap=32, align="stretch"),
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 9", "The vault that freezes", "QuantumTech's Alpha and Beta recovery vaults freeze during a drill. Model them, watch the wait, and repair the order.")

START_TREE = [("vault", [("haze.txt", None), ("ember.txt", None), ("worker.sh", None)]), ("evidence", [])]

labkit.scenario(d, 9, "QuantumTech's recovery vaults", "Alpha and Beta freeze during a synchronization drill. Model them with two lock files you own, observe a bounded wait cycle, and repair the acquisition order.",
                "Your two lock names and the worker who starts first are your own. This guide shows example values.", START_TREE)
labkit.timetable(d, [["0 to 10", "Setup"],
                     ["10 to 25", "Guided: locks and bounded waiting"],
                     ["25 to 35", "Prediction"],
                     ["35 to 55", "Core 1: reproduce the deadlock"],
                     ["55 to 70", "Core 2: repair it with a global order"]],
                 [["70 to 85", "Instructor demonstration, Plus and Challenge"],
                  ["85 to 100", "Live checkpoint"],
                  ["100 to 110", "Debrief"],
                  ["110 to 120", "Submit"]])

d.slide("helper", "Six helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does"],
                      [[mono("oslab values lab9"), "Shows your two lock names and which one worker A takes first"],
                       [mono("oslab predict lab9"), "Saves your prediction once, before the experiment"],
                       [mono("oslab hint lab9 1"), "A hint, levels 1 to 3. Hints cost no points"],
                       [mono("oslab check lab9"), "Runs your worker.sh in both modes and shows your milestones. It takes about 10 seconds"],
                       [mono("oslab checkpoint lab9"), "Opens when the instructor says so, near the end"],
                       [mono("oslab debrief lab9"), "After the lab: you give the right answers to your prediction questions"]],
                      [5, 11]),
        note="Before the lab, run oslab doctor and oslab prelab lab9. It takes about ten minutes.")

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Core, Plus, Challenge", "Core is for everyone. Plus and Challenge are for students who finish early. Full marks need only Core and the checkpoint.", title_size=36),
                      rule(t, "AI tools", "Allowed in Core, Plus and Challenge, so test every suggestion. Not allowed in the prediction and the checkpoint.", title_size=36),
                      rule(t, "Every wait has a limit", "You only ever start your own two workers, always with timeout. Use the saved PIDs, and never use pkill.", title_size=36)),
        note="In Core 2 you decide the global lock order yourself. You write the rule, and you explain why it removes the cycle.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ['export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab9",
                               'cd "$OSLAB_WORKSPACE/lab9"',
                               "mkdir -p evidence",
                               "oslab values lab9"], title="student@server: ~", size=26),
                      col(lst(t, ["The first line sets OSLAB_WORKSPACE to ~/oslab-work, unless it is already set. Type it as it is.",
                                  "oslab start lab9 makes the lab folder.",
                                  "cd takes you into it, and mkdir -p makes the evidence folder.",
                                  "oslab values lab9 prints your own lock names."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("values", "Your values: two lock names and a start",
        lambda t: row(col(h3(t, "The last command prints them"),
                          term(t, ["oslab values lab9",
                                   ("out", "Your personal values for lab9 (your-account):"),
                                   ("out", "  res1     = haze"),
                                   ("out", "  res2     = ember"),
                                   ("out", "  a_first  = haze")], title="example: your values will be different", size=26),
                          gap=20, flex=None),
                      col(h3(t, "What they mean"),
                          lst(t, ["res1 and res2 are the names of your two locks.",
                                  "a_first is the lock that worker A takes first. Worker B always takes them in the other order.",
                                  "Your own names are different. Write them down."], size=30),
                          gap=20, flex=None),
                      gap=48, align="flex-start"))

d.slide("capital", "The capital words are placeholders",
        lambda t: tbl(t, ["The instruction says", "With the example values, you type"],
                      [[mono("vault/RES1.lock"), mono("vault/haze.lock")],
                       [mono("cat vault/RES1.txt"), mono("cat vault/haze.txt")]],
                      [1, 1]),
        note="The instruction cannot know your names, so it writes RES1 and RES2 where your values belong. Never type the capital words. Type your own names.")

d.slide("start-tree", "Your folder",
        lambda t: row(tree(t, "lab9", START_TREE, cmd="tree -a -L 3", title="student@server: ~/oslab-work/lab9", size=30),
                      col(para(t, "vault/ holds the data of your two resources, named with your own lock names, and worker.sh, with one TODO for you.", size=32),
                          para(t, "oslab check lab9 starts with the first line passing and the others saying TRY. The hidden .oslab-managed.json is the helper's. Leave it.", size=32),
                          gap=24),
                      gap=48, align="center"))

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Locks and bounded waiting", "Ten to twenty-five minutes, with the instructor. See what a lock is, and how a worker can stop waiting for one.")

d.slide("g-lock", "Steps 1 and 2: look, then take one lock",
        lambda t: row(term(t, ["cat vault/haze.txt vault/ember.txt",
                               "ls vault",
                               "(",
                               "    flock -x -w 2 8 || exit 3",
                               "    printf 'holding haze\\n'",
                               ") 8>vault/haze.lock"], title="example names: use your own", size=26),
                      col(para(t, "The text files hold data. A lock file is separate: flock makes workers take turns on it. Creating a file called locked is not a lock.", size=30),
                          para(t, "File descriptor 8 stays open until the subshell ends, and the lock is held as long as it is open. -w 2 means wait at most 2 seconds.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("g-contend", "Step 3: one lock, two workers",
        lambda t: row(term(t, ["(",
                               "    flock -x -w 2 8 || exit 3",
                               "    sleep 3",
                               ") 8>vault/haze.lock &",
                               "holder=$!",
                               "sleep 0.2",
                               "flock -x -w 1 vault/haze.lock true",
                               "printf 'contender status=%s\\n' \"$?\"",
                               'wait "$holder"'], title="example name: use your own", size=24),
                      col(para(t, "One subshell holds the lock for 3 seconds. The second command waits only 1 second, so its status is not 0: the wait timed out.", size=30),
                          card(t, "Observe", "What is held while another worker waits? Does a timeout prevent a deadlock, or only let a worker stop waiting?", label="THINK", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- prediction ---------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you start any worker. Ten minutes.")

d.slide("predict", "The prediction",
        lambda t: row(col(term(t, ["oslab predict lab9"]),
                          para(t, "It asks four questions and one sentence about your own two locks. Draw the two workers and the two locks on paper first. Answer alone, without AI.", size=32),
                          gap=24, flex=3),
                      col(card(t, "The rules", "The first answer is the one that counts. A wrong guess costs nothing. You compare it with the real result in the debrief.", label="PREDICTION", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

# ---- core 1 ---------------------------------------------------------------------
d.opener("c1-open", "CORE 1", "Reproduce the deadlock", "Twenty minutes, from minute 35 to 55. Make worker A and worker B wait for each other, and read what the timeouts say.")

W1 = ["#!/usr/bin/env bash",
      "set -euo pipefail",
      "# (the check of the two arguments is left out here)",
      "role=$1", "mode=$2",
      'vault=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)',
      "res1=haze", "res2=ember",
      'mkdir -p "$vault/coord"',
      "# Worker A takes haze first and ember second. Worker B the other way.",
      'first=$res1; second=$res2',
      "# TODO: in ordered mode, every worker must use one global order.",
      'if [[ "$role" = B ]]; then tmp=$first; first=$second; second=$tmp; fi']
W2 = ['exec 8>"$vault/$first.lock"',
      'flock -x -w 2 8 || { echo "$role first lock timeout"; exit 3; }',
      "printf '%s holds %s\\n' \"$role\" \"$first\"",
      'sleep "${HOLD:-0}"   # teaching delay; keep this line',
      'if [[ "$mode" = opposite ]]; then',
      '    touch "$vault/coord/$role.ready"',
      "    other=B",
      '    [[ "$role" = B ]] && other=A',
      "    for step in {1..30}; do",
      '        [[ -f "$vault/coord/$other.ready" ]] && break',
      "        sleep 0.1",
      "    done",
      '    [[ -f "$vault/coord/$other.ready" ]] || { echo \'barrier timeout\'; exit 4; }',
      "fi"]
W3 = ['exec 9>"$vault/$second.lock"',
      "printf '%s requests %s\\n' \"$role\" \"$second\"",
      'flock -x -w 2 9 || { echo "$role second lock timeout"; exit 5; }',
      "printf '%s holds both\\n' \"$role\""]

d.slide("c1-code1", "Step 1: read the worker, part 1",
        lambda t: row(listing(t, W1, title="vault/worker.sh (1 of 3)", size=24, hot=(11, 12), lh=1.15),
                      col(para(t, "Read it with cat -n vault/worker.sh. The values are an example: yours hold your own names, and your own first lock for A.", size=28),
                          para(t, "set -euo pipefail stops on an error, on an unset variable, and when any command in a pipeline fails.", size=28),
                          para(t, "The vault= line finds the script's own folder. B reverses the order by default: the TODO is yours to fix in Core 2.", size=28),
                          gap=18, flex=None),
                      gap=40, align="center"))

d.slide("c1-code2", "Step 1: the first lock and the barrier, part 2",
        lambda t: row(listing(t, W2, title="vault/worker.sh (2 of 3)", size=24, lh=1.1),
                      col(para(t, "Each worker takes its first lock on descriptor 8, waiting two seconds at most. The sleep line is a teaching delay: keep it.", size=28),
                          para(t, "The barrier makes both workers announce their first lock before either asks for the second. It is used only in opposite mode.", size=28),
                          gap=22, flex=None),
                      gap=40, align="center"))

d.slide("c1-code3", "Step 1: the second lock, part 3",
        lambda t: row(listing(t, W3, title="vault/worker.sh (3 of 3)", size=24, lh=1.15),
                      col(para(t, "After the barrier, each worker asks for its second lock, on descriptor 9, and reports what it holds.", size=30),
                          card(t, "Why exec 8> and exec 9>?", "exec with only a redirection opens the file for the rest of the script, so the lock lasts until the script ends.", label="SYNTAX", pad=32, title_size=32),
                          gap=22, flex=None),
                      gap=40, align="center"))

d.slide("c1-run", "Step 2: two workers, opposite order",
        lambda t: row(term(t, ["rm -f -- vault/coord/A.ready vault/coord/B.ready",
                               "timeout 6 bash vault/worker.sh A opposite > evidence/opposite-a.txt 2>&1 &",
                               "worker_a=$!",
                               "timeout 6 bash vault/worker.sh B opposite > evidence/opposite-b.txt 2>&1 &",
                               "worker_b=$!",
                               'if wait "$worker_a"; then rc_a=0; else rc_a=$?; fi',
                               'if wait "$worker_b"; then rc_b=0; else rc_b=$?; fi',
                               "{",
                               "  printf 'opposite A=%s B=%s\\n' \"$rc_a\" \"$rc_b\"",
                               "  cat evidence/opposite-a.txt evidence/opposite-b.txt",
                               "} > evidence/opposite.txt",
                               "cat evidence/opposite.txt"], size=24),
                      col(para(t, "Clear only the two old ready markers, then start exactly two workers, each with timeout 6.", size=30),
                          para(t, "The if wait ... construct keeps the status even when it is not zero. A status of 124 means timeout itself stopped the worker.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c1-draw", "Step 3: draw it, and explain the recovery",
        lambda t: row(col(h3(t, "What to do"),
                          lst(t, ["Draw what each worker holds and requests at the barrier.",
                                  "At least one worker ends with status 5, the timeout of the second lock.",
                                  "When it exits, its first lock is released, so the other worker may finish instead of timing out too.",
                                  "Explain that recovery in your report. Do not claim that both workers must fail."], ordered=True, size=30),
                          gap=20, flex=3),
                      col(card(t, "Hints", "oslab hint lab9 1, then 2, then 3. AI is allowed here: test every suggestion.", label="STUCK?", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

# ---- core 2 ---------------------------------------------------------------------
d.opener("c2-open", "CORE 2", "Repair it with a global order", "Fifteen minutes, from minute 55 to 70. One rule for both workers, so that no worker waits for a lock while holding the one the other needs.")

d.slide("c2-fix", "Step 1: one order for everyone",
        lambda t: row(col(h3(t, "Edit the TODO"),
                          lst(t, ["Open the worker with nano vault/worker.sh and find the TODO.",
                                  "In ordered mode, both workers must take the locks in the same order.",
                                  "In opposite mode, worker B must still take them the other way round.",
                                  "Keep the barrier only for opposite mode. Write your rule with $first and $second, not with your lock names."], size=30),
                          gap=20, flex=3),
                      col(card(t, "You write it", "Nobody gives you the lines. Ask: which line decides first and second, and for which workers and modes?", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c2-run", "Step 2: run the ordered case",
        lambda t: row(term(t, ["timeout 6 bash vault/worker.sh A ordered > evidence/ordered-a.txt 2>&1 &",
                               "worker_a=$!",
                               "timeout 6 bash vault/worker.sh B ordered > evidence/ordered-b.txt 2>&1 &",
                               "worker_b=$!",
                               'if wait "$worker_a"; then rc_a=0; else rc_a=$?; fi',
                               'if wait "$worker_b"; then rc_b=0; else rc_b=$?; fi',
                               "{",
                               "  printf 'ordered A=%s B=%s\\n' \"$rc_a\" \"$rc_b\"",
                               "  cat evidence/ordered-a.txt evidence/ordered-b.txt",
                               "} > evidence/ordered.txt",
                               "cat evidence/ordered.txt"], size=24),
                      col(para(t, "Both statuses should be 0.", size=30),
                          card(t, "Think", "Why can a worker that waits for the first lock not hold the second lock at the same time?", label="WHY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-clean", "Step 3: clean up",
        lambda t: row(term(t, ["jobs",
                               "flock -n vault/haze.lock true; printf 'haze free: status=%s\\n' \"$?\"",
                               "flock -n vault/ember.lock true; printf 'ember free: status=%s\\n' \"$?\""], title="example names: use your own", size=24),
                      col(para(t, "No worker may still run, and both locks must be free. Both statuses should be 0.", size=30),
                          para(t, "The timeouts stay in the script. Ordering prevents this circular wait, but timeouts still bound other delays. Ordering does not give fairness, and does not make every larger system safe.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-check", "Step 4: check your work",
        lambda t: row(term(t, ["oslab check lab9"], size=28),
                      col(para(t, "The four Core milestones must show PASS: the opposite conflict, ordered mode, a rule that does not depend on names, and the evidence files.", size=30),
                          card(t, "What the check does", "It runs your worker.sh in a disposable folder: in opposite mode, in ordered mode, and in ordered mode again with two other lock names. The last test fails if your rule only works for your own names.", label="CHECK", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-table", "The three runs",
        lambda t: tbl(t, ["Run", "Intended evidence"],
                      [["Opposite, two workers", "Both hold distinct first locks. The second lock conflicts, and a timeout recovers"],
                       ["Ordered, two workers", "Both complete, one after the other, through the first lock of the order"],
                       ["Ordered, two other lock names", "The rule still works, so it is written with $first and $second"]],
                      [5, 11]),
        note="Status 124 means the outer timeout fired. Do not call an unexplained timeout a recovery. Repeat the opposite case only after you delete the two ready markers.")

d.slide("c2-trouble", "If something does not work",
        lambda t: row(rule(t, "Old ready markers", "Reusing them makes the barrier pass when it should not. Clear only A.ready and B.ready.", title_size=36),
                      rule(t, "Lock files stay", "Never delete an active lock file. Its existence is normal.", title_size=36),
                      rule(t, "No pkill", "Use the saved PIDs and the bounded waits. See man flock and man timeout.", title_size=36)))

# ---- demonstration, plus and challenge ----------------------------------------------------
d.slide("plus", "Plus: slow the first lock down",
        lambda t: row(term(t, ["HOLD=1 timeout 6 bash vault/worker.sh A ordered &",
                               "HOLD=1 timeout 6 bash vault/worker.sh B ordered &",
                               "wait"], size=24),
                      col(para(t, "HOLD=1 makes each worker keep its first lock for one second before it asks for the second. Run both workers in ordered mode with it.", size=30),
                          card(t, "Answer in evidence/plus.txt", "Do both workers still finish? One of them waits longer. What does it wait for?", label="PLUS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"),
        note="First watch the instructor draw the two workers and the two locks and show the circle on the board. Plus and Challenge are not needed for full marks.")

d.slide("challenge", "Challenge: three workers, three locks",
        lambda t: row(card(t, "The circle", "Three locks x, y and z. A holds x and requests y. B holds y and requests z. C holds z and requests x.", label="CHALLENGE", pad=40, title_size=36),
                      card(t, "Answer in evidence/plus.txt", "Draw the circle. Choose a global order, and say which worker must change the order of its two locks.", label="YOUR TURN", pad=40, title_size=36),
                      gap=32, align="stretch"))

# ---- live checkpoint ------------------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "The names are new", "The case uses new lock names, made for you at that moment. An answer copied from a neighbour does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once, so a common mistake can be explained before the next lab.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task, with their own names.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab9", "Read the case, answer four questions"),
                           ("3. The file task", "Copy your worker, new names"), ("4. oslab check lab9", "A fifth milestone must pass")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command says that the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab9 shows whether the fifth milestone, checkpoint, passes. You can fix your copy and check again.", title_size=36)),
        gap=56)

d.slide("cp-marks", "What the checkpoint asks",
        lambda t: tbl(t, ["Part", "What you do"],
                      [["Four questions", "Read the case with a third worker, made for you at this moment. Answer them in the terminal."],
                       ["The file task", "Copy your worker script, change only the two res1= and res2= lines to the new names, run the ordered mode, and save the logs in checkpoint.txt."],
                       ["The check", "Run oslab check lab9. The fifth milestone, checkpoint, must show PASS."]],
                      [4, 13]),
        note="This is why Core 2 asked for a rule written with $first and $second, not with your own lock names.")

# ---- debrief and submit ---------------------------------------------------------------------
d.opener("end-open", "DEBRIEF AND SUBMIT", "Look back, then hand in", "Ten minutes of debrief, ten to submit.")

d.slide("debrief", "Debrief: look at your prediction again",
        lambda t: row(term(t, ['cat "$OSLAB_WORKSPACE/.records/lab9-predict.json"',
                               "oslab debrief lab9"], size=24, title="student@server: ~/oslab-work/lab9"),
                      col(para(t, "oslab saved your prediction in a hidden folder, .records. It stays as it was, so the comparison shows which answers you confirmed and which you corrected.", size=30),
                          card(t, "Class discussion", "Your timeout rescued the opposite run. Why is wait less not a repair for a deadlock?", label="DISCUSS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

labkit.submission(d, 9, ['cp -- vault/worker.sh "$SUBMISSION_REPO/lab9/"',
                         'cp -- evidence/opposite.txt evidence/ordered.txt "$SUBMISSION_REPO/lab9/evidence/"'],
                  [("README.md", None), ("worker.sh", None), ("evidence", [("opposite.txt", None), ("ordered.txt", None)])],
                  note="If you did Plus or Challenge, copy evidence/plus.txt the same way. The course website checks that these exact names are there. Leave no worker running.")

d.slide("submit-git", "Submit 3: commit and push",
        lambda t: row(term(t, ["cd ~/os-gic-YOUR_ID",
                               "git pull",
                               "git add os-lab-YOUR_ID/lab9",
                               'git commit -m "Lab 9"',
                               "git push"], title="student@server: ~", size=26),
                      col(para(t, "git pull comes first, in case you pushed from your own computer since.", size=32),
                          para(t, "Replace YOUR_ID with your own ID, as before.", size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.grading(d, [["Worker: oslab check lab9 passes the four Core milestones (opposite conflict, ordered mode, rule independent of names, evidence files)", "2"],
                   ["Tests: opposite.txt and ordered.txt show the conflict and the repair, and the README explains the recovery by timeout", "2"],
                   ["Prediction saved in time, and corrected with oslab debrief lab9", "2"],
                   ["Live checkpoint: the answers and your worker running with the new names", "3"],
                   ["Complete submission: the required files in your repository, on time", "1"]],
               note="Every row is marked from your oslab records and the files in your repository, so run oslab check lab9 until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.")

labkit.mistakes(d, [["Claiming both workers must time out", "One finishes after the other gives up", "Explain the recovery event"],
                    ["The barrier left in ordered mode", "A worker waits for a partner that cannot arrive", "Skip the barrier when ordered"],
                    ["Removing the timeouts after ordering", "A future wait with no limit", "Keep every flock bounded"],
                    ["Reusing the ready markers", "A false coordination condition", "rm only A.ready and B.ready first"],
                    ["A rule written with your own lock names", "The last check, with other names, fails", "Write it with $first and $second"]])

# ---- beyond the core --------------------------------------------------------------
d.opener("ext-open", "BEYOND THE CORE", "Wait traces and site-to-site sync", "Optional extensions. They stay bounded, and they use only a narrow folder the instructor prepared.")

d.slide("ext-trace", "Looking at who waits",
        lambda t: row(term(t, ["timeout 6 bash vault/worker.sh A opposite &",
                               "ps -o pid,ppid,stat,wchan:20,comm -p $!",
                               "wait"], size=26),
                      col(para(t, "While a worker waits for a lock, ps shows it asleep, state S. The wchan column names the kernel place where it sleeps.", size=30),
                          para(t, "Take one sample, and say what you saw. A late sample may miss the wait entirely.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=EXT)

d.slide("ext-sync", "Site-to-site synchronization",
        lambda t: row(card(t, "Consent first", "Two people agree on a narrow folder the instructor prepared. Nobody writes into another person's home.", label="CONSENT", pad=32, title_size=32),
                      card(t, "Same order on both sides", "Both sites must take their locks in the same global order, or the circle comes back across machines.", label="ORDER", pad=32, title_size=32),
                      card(t, "Bounded and logged", "Every wait has a limit, and each side keeps a log of what it held and asked for.", label="SAFE", pad=32, title_size=32),
                      gap=32, align="stretch"),
        label=EXT)

d.close([("Four conditions", "Mutual exclusion, hold and wait, no preemption and circular wait. Break one."),
         ("Draw the edges", "Holdings and requests that close a circle are a deadlock."),
         ("Order prevents, timeout recovers", "One global lock order stops this circle. A timeout only ends a wait that has started."),
         ("Keep every wait bounded", "Even with an order, a limit stops a hidden problem from hanging for ever.")],
        "chapter 8, Deadlocks", ("Lab 10: backups, archives and cron", "Make a backup you can restore, and schedule it to run by itself."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: the four conditions, holdings and requests as edges, bounded locks, prevention and recovery.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the rules, setup and the starting tree.", "start": "lab-open"},
    "s4": {"description": "Guided: locks and the vault, then the prediction.", "start": "g-open"},
    "s5": {"description": "Core 1 and Core 2: reproduce the deadlock and repair it with a global order, then Plus and Challenge.", "start": "c1-open"},
    "s6": {"description": "The live checkpoint: why, the steps with oslab, and what it asks.", "start": "cp-open"},
    "s7": {"description": "Debrief, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: wait traces and site-to-site sync, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
