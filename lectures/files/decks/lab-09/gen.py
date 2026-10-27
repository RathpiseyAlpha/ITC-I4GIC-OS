"""Lab 9 guide, Vault Deadlock, Resource Ordering and Recovery. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

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

START_TREE = [("vault", [("alpha.txt", None), ("beta.txt", None), ("worker.sh", None)]), ("evidence", [])]

labkit.scenario(d, 9, "QuantumTech's recovery vaults", "Alpha and Beta freeze during a synchronization drill. Model them with two lock files you own, observe a bounded wait cycle, and repair the acquisition order.",
                "Every wait has a time limit. Nothing runs for ever, and you never delete a lock file while a worker uses it.", START_TREE)
labkit.timetable(d, [["0 to 10", "Introduction, objectives and setup"],
                     ["10 to 25", "Level 1, guided: locks and the vault"],
                     ["25 to 35", "Written prediction"],
                     ["35 to 55", "Levels 2 and 3: naive workers, local deadlock"]],
                 [["55 to 70", "Levels 5 and 6: global order, timeout recovery"],
                  ["70 to 85", "Tests and feedback"],
                  ["85 to 100", "Individual changed-case checkpoint"],
                  ["100 to 120", "Correction, cleanup and submission"]])
labkit.rules(d, safety="Use the saved PIDs and bounded waits. Never use pkill.")
labkit.setup_slides(d, 9, START_TREE,
                    ["vault/alpha.txt and beta.txt hold the data of the two vaults.",
                     "vault/worker.sh is an editable starter skeleton.",
                     "The helper also writes a hidden file, .oslab-managed.json. Leave it as it is."])

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "Locks and the vault", "Level 1, with the instructor: fifteen minutes.")

d.slide("g-lock", "Step 1 and 2: look, then take one lock",
        lambda t: row(term(t, ["cat vault/alpha.txt vault/beta.txt",
                               "mkdir -p vault/coord",
                               "(",
                               "    flock -x -w 2 8 || exit 3",
                               "    printf 'holding Alpha\\n'",
                               ") 8>vault/alpha.lock"], size=26),
                      col(para(t, "The text files are data. The .lock files stand for exclusive access.", size=32),
                          para(t, "Descriptor 8 is open until the group ends. A real program would keep the protected work inside this group.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-contend", "Step 3: one lock, two workers",
        lambda t: row(term(t, ["(",
                               "    flock -x -w 2 8 || exit 3",
                               "    sleep 3",
                               ") 8>vault/alpha.lock &",
                               "holder=$!",
                               "sleep 0.2",
                               "flock -x -w 1 vault/alpha.lock true",
                               "printf 'contender status=%s\\n' \"$?\"",
                               'wait "$holder"'], size=24),
                      col(para(t, "The first worker holds Alpha for three seconds. The second asks for it and gives up after one.", size=30),
                          para(t, "Expect a timeout if the holder got the lock first. The short sleep helps but does not prove it.", size=30),
                          card(t, "Observe", "What is held while another worker waits? Does a timeout prevent a deadlock, or only let a worker stop waiting?", label="THINK", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

labkit.predict(d, "A holds Alpha and requests Beta. B holds Beta and requests Alpha. Draw both wait edges, and predict whether either can get its second resource before someone releases a lock.")

# ---- levels 2 and 3 ---------------------------------------------------------------
d.opener("l2-open", "LEVELS 2 AND 3", "Naive workers and a local deadlock", "Twenty minutes, from minute 35 to 55. Work alone.")

W1 = ["#!/usr/bin/env bash",
      "set -euo pipefail",
      '[[ $# -eq 2 && "$1" =~ ^(A|B)$ && "$2" =~ ^(opposite|ordered)$ ]] || exit 2',
      "role=$1", "mode=$2",
      'vault=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)',
      "first=alpha", "second=beta",
      "# TODO: in ordered mode, every worker must use one global order.",
      'if [[ "$role" = B ]]; then first=beta; second=alpha; fi',
      'exec 8>"$vault/$first.lock"',
      'flock -x -w 2 8 || { echo "$role first lock timeout"; exit 3; }',
      "printf '%s holds %s\\n' \"$role\" \"$first\""]
W2 = ['if [[ "$mode" = opposite ]]; then',
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

d.slide("l2-code1", "Step 1: the starting worker, part 1",
        lambda t: row(listing(t, W1, title="vault/worker.sh (1 of 3)", size=24, hot=(8,), lh=1.15),
                      col(para(t, "Save the whole script as vault/worker.sh with the three parts on this and the next two slides. B reverses the order by default: that is the TODO you will fix.", size=28),
                          para(t, "set -euo pipefail: stop on an error (-e), on an unset variable (-u), and when any command in a pipeline fails (pipefail).", size=28),
                          para(t, "The vault= line finds the script's own folder: BASH_SOURCE[0] is its path, dirname drops the file name, pwd -P prints the real folder.", size=28),
                          para(t, "Each flock waits two seconds. Each failure exits with its own status: 3, 4 or 5.", size=28),
                          gap=18, flex=None),
                      gap=40, align="center"))

d.slide("l2-code2", "Step 1: the barrier, part 2",
        lambda t: row(listing(t, W2, title="vault/worker.sh (2 of 3)", size=24, lh=1.15),
                      col(para(t, "The barrier is a teaching instrument. Each worker says it is ready, then waits for the other to say so.", size=30),
                          para(t, "It makes sure both workers hold their first lock before either asks for its second.", size=30),
                          para(t, "In ordered mode it is skipped: one worker cannot take Alpha while the other holds it.", size=30),
                          gap=22, flex=None),
                      gap=40, align="center"))

d.slide("l2-code3", "Step 1: the second lock, part 3",
        lambda t: row(listing(t, W3, title="vault/worker.sh (3 of 3)", size=24, lh=1.15),
                      col(para(t, "After the barrier, each worker asks for its second lock, on descriptor 9, and reports what it holds.", size=30),
                          card(t, "Why exec 8> and exec 9>?", "exec with only a redirection opens the file for the rest of the script, so the lock lasts until the script ends.", label="SYNTAX", pad=32, title_size=32),
                          gap=22, flex=None),
                      gap=40, align="center"))

d.slide("l2-run", "Step 2: two workers, opposite order",
        lambda t: row(term(t, ["rm -f -- vault/coord/A.ready vault/coord/B.ready",
                               "timeout 6 bash vault/worker.sh A opposite > evidence/opposite-a.txt 2>&1 &",
                               "worker_a=$!",
                               "timeout 6 bash vault/worker.sh B opposite > evidence/opposite-b.txt 2>&1 &",
                               "worker_b=$!",
                               'if wait "$worker_a"; then rc_a=0; else rc_a=$?; fi',
                               'if wait "$worker_b"; then rc_b=0; else rc_b=$?; fi',
                               "printf 'A=%s B=%s\\n' \"$rc_a\" \"$rc_b\"",
                               "cat evidence/opposite-a.txt evidence/opposite-b.txt"], size=24),
                      col(para(t, "Clear only the two old ready markers, then start exactly two workers. timeout 6 stops a worker that waits too long.", size=30),
                          para(t, "The if wait ... construct keeps the status even when it is not zero. A status of 124 means timeout itself stopped the worker.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("l2-draw", "Step 3: draw it, and explain the recovery",
        lambda t: row(col(h3(t, "What to do"),
                          lst(t, ["Draw the holdings and requests at the barrier.",
                                  "At least one worker should time out on the second lock.",
                                  "Once it exits, it releases its first lock. The other worker may then finish instead of timing out too.",
                                  "Explain that recovery. Do not claim that both must fail."], ordered=True, size=30),
                          gap=20, flex=3),
                      col(term(t, ["{",
                                   "  printf 'opposite A=%s B=%s\\n' \"$rc_a\" \"$rc_b\"",
                                   "  cat evidence/opposite-a.txt evidence/opposite-b.txt",
                                   "} > evidence/opposite.txt"], size=24),
                          gap=24, flex=3),
                      gap=48, align="stretch"))

# ---- levels 5 and 6 ---------------------------------------------------------------
d.opener("l5-open", "LEVELS 5 AND 6", "Global order and timeout recovery", "Fifteen minutes, from minute 55 to 70.")

d.slide("l5-fix", "Step 1: one order for everyone",
        lambda t: row(col(h3(t, "Edit the TODO"),
                          lst(t, ["In ordered mode, every worker takes Alpha first, then Beta.",
                                  "Opposite mode stays as it is, so you can reproduce the conflict.",
                                  "Leave the barrier in opposite mode only."], size=32),
                          gap=20, flex=3),
                      col(card(t, "You write it", "Nobody gives you the lines. Ask: which line decides first and second, and for which workers?", label="YOUR TURN", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("l5-run", "Step 2: run the ordered case",
        lambda t: row(term(t, ["timeout 6 bash vault/worker.sh A ordered > evidence/ordered-a.txt 2>&1 &",
                               "worker_a=$!",
                               "timeout 6 bash vault/worker.sh B ordered > evidence/ordered-b.txt 2>&1 &",
                               "worker_b=$!",
                               'if wait "$worker_a"; then rc_a=0; else rc_a=$?; fi',
                               'if wait "$worker_b"; then rc_b=0; else rc_b=$?; fi',
                               "{",
                               "  printf 'ordered A=%s B=%s\\n' \"$rc_a\" \"$rc_b\"",
                               "  cat evidence/ordered-a.txt evidence/ordered-b.txt",
                               "} > evidence/ordered.txt"], size=24),
                      col(para(t, "Save separate logs and both statuses. Explain why a worker that waits for Alpha cannot also hold Beta.", size=30),
                          para(t, "Keep the timeouts. Ordering prevents this circle. Timeouts also bound waits from other causes. Neither gives fairness, and neither promises that a larger system is free of deadlock.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("l5-done", "Complete when, and hints",
        lambda t: row(card(t, "Complete when", "Your logs show the wait cycle in the first case. Both ordered workers finish. The global rule is applied the same way everywhere.", label="DONE", pad=40, title_size=36, flex=1),
                      col(h3(t, "Hints, one at a time"),
                          lst(t, ["Draw held and requested resources.", "Read the first-lock logs and the ready markers.",
                                  "Reverse B only in the teaching opposite mode, and skip the barrier in ordered mode."], ordered=True, size=30),
                          para(t, "If AI suggests a repair, check that it changes both workers' policy and adds no new barrier wait.", size=28),
                          gap=20, flex=1),
                      gap=48, align="stretch"))

# ---- tests ---------------------------------------------------------------------
d.opener("test-open", "TESTS AND FEEDBACK", "Three cases, and what each proves", "Fifteen minutes, from minute 70 to 85.")

d.slide("tests-table", "The three cases",
        lambda t: tbl(t, ["Case", "Intended evidence"],
                      [["Opposite, two workers", "Both hold distinct first locks. The second lock conflicts, and a timeout recovers"],
                       ["Ordered, two workers", "Both complete, one after the other, through Alpha"],
                       ["One opposite worker alone", "The barrier times out within three seconds, which explains the missing participant"]],
                      [4, 11]),
        note="Status 124 means the outer timeout fired. Do not call an unexplained timeout a recovery. One lucky run does not prove that opposite order is safe. Repeat the opposite case only after you delete the two ready markers.")

d.slide("tests-trouble", "If something does not work",
        lambda t: row(rule(t, "Old ready markers", "Reusing them makes the barrier pass when it should not. Clear only A.ready and B.ready.", title_size=36),
                      rule(t, "Lock files stay", "Never delete an active lock file. Its existence is normal.", title_size=36),
                      rule(t, "No pkill", "Use the saved PIDs and the bounded waits. See man flock and the deadlock visualization.", title_size=36)))

# ---- checkpoint, correction, submission -------------------------------------------
labkit.checkpoint(d, "A third worker needs only Beta. Must it also take Alpha to follow the global-order policy? Explain. Separately, say whether the timeout is prevention or recovery in the opposite-order example.")
labkit.correction(d, "(a) Which pair of edges formed the cycle? (b) Why must the teaching barrier be absent in ordered mode? (c) How can one timeout let the other worker finish?")
labkit.submission(d, 9, ['cp -- vault/worker.sh "$SUBMISSION_REPO/lab9/"',
                         'cp -- evidence/opposite.txt evidence/ordered.txt "$SUBMISSION_REPO/lab9/evidence/"'],
                  [("README.md", None), ("worker.sh", None), ("evidence", [("opposite.txt", None), ("ordered.txt", None)])],
                  note="opposite.txt should hold the holdings and requests, the statuses, the recovery and your wait diagram. Cleanup is part of the lab: leave no worker running.")
labkit.grading(d, [["A bounded conflict reproduced, and one consistent global order", "3"],
                   ["The opposite and ordered runs, and the missing-participant diagnosis", "2"],
                   ["Circular wait, the barrier and timeout recovery explained; original prediction and correction", "2"],
                   ["Individual checkpoint: result or diagnosis, and mechanism", "2"],
                   ["Concise, attributable evidence and the required artifacts", "1"]])
labkit.mistakes(d, [["Claiming both workers must time out", "One finishes after the other gives up", "Explain the recovery event"],
                    ["The barrier left in ordered mode", "A worker waits for a partner that cannot arrive", "Skip the barrier when ordered"],
                    ["Removing the timeouts after ordering", "A future wait with no limit", "Keep every flock bounded"],
                    ["Reusing the ready markers", "A false coordination condition", "rm only A.ready and B.ready first"]])

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
    "s5": {"description": "Levels 2 and 3: naive workers and a local deadlock. Levels 5 and 6: global order, then the tests.", "start": "l2-open"},
    "s6": {"description": "The individual checkpoint: why, and the practice question.", "start": "cp-open"},
    "s7": {"description": "Correction, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: wait traces and site-to-site sync, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
