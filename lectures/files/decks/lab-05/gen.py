"""Lab 5 guide, Threads, Kernel Workers and Process Signals. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

A guide for the lab session, built like the Lab 3 and Lab 4 guides with the shared look and the shared
standard slides in labkit.py. The earlier Lab 5 guide was only a one-slide stub, so the concepts section is
new: processes and threads, what a thread shares, create and join, completion versus mutual exclusion.
The lab part follows labs/lab5/lab5-instruction.md. Process-versus-thread memory, LWPs and kernel workers,
and signal handling are optional extensions in that instruction, so they come last (images.json is empty).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import labkit  # noqa: E402  (it puts the shared library on the path)
import labcoverart  # noqa: E402
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, init)  # noqa: E402,F401

WEEK = "Lab 5"
TITLE = "Operating Systems — Lab 5"
DECK_URL = None  # not published as a Slides artifact
CREATED_AT = "2026-10-28T09:00:00Z"
BG = "Concepts first"
EXT = "Beyond the core"

d = init(HERE, 5)
S = d.S
CW, HALF = labkit.CW, labkit.HALF

# ---- opening --------------------------------------------------------------
labcoverart.cover(d, "lab-05", "Threads, Workers and Signals",
                  "Lab 5 guide: start workers, wait for each one to finish, and tell completion apart from protecting shared data.", size=96)

d.slide("objectives", "Learning objectives",
        lambda t: row(
            lst(t, ["Create POSIX threads, and check the return codes of the API.",
                    "Join each worker before using its result, and explain shared versus separate address spaces.",
                    "Use a bounded run to find missing completion synchronization."], ordered=True, size=36, flex=3),
            card(t, "Lab 5", "First the concepts, with code. Then the lab on the server. Process versus thread memory, kernel workers and signals are optional extensions, so they come last.", label="THIS LAB", flex=2),
            gap=48, align="stretch"))

d.opener("question", "DISCUSSION", "Two workers start, and main returns at once. What happens to them?",
         "Do both finish their work and print? Does main know when they are done?")

# ---- concepts first ---------------------------------------------------------
d.opener("bg-open", "CONCEPTS FIRST", "Processes, threads and joining", "Three ideas: what a thread shares, how you wait for it, and what waiting does not do.")

d.slide("proc-thread", "A process and a thread",
        lambda t: tbl(t, ["", "Process", "Thread"],
                      [["What it is", "A running program with its own resources", "A line of execution inside a process"],
                       ["Address space", "Its own: memory is private", "Shared with the other threads of the process"],
                       ["Created by", mono("fork()"), mono("pthread_create()")],
                       ["Waited for with", mono("waitpid()"), mono("pthread_join()")],
                       ["Cost to create", "Higher", "Lower"],
                       ["Risk", "Needs a channel to share data", "Threads can overwrite each other's data"]],
                      [4, 7, 7]),
        note="After fork, parent and child have separate copies of memory. Threads of one process see the same variables.",
        label=BG)

d.slide("shared", "What threads share, and what they do not",
        lambda t: row(card(t, "Shared by all threads", "Code, global variables, the heap, open files. A change made by one thread is visible to the others.", label="SHARED", pad=40, title_size=36),
                      card(t, "Private to each thread", "Its own stack with local variables, its registers and its place in the code.", label="PRIVATE", pad=40, title_size=36),
                      card(t, "Why it matters", "Sharing makes communication cheap, and it also lets two threads change one value at the same time.", label="TRADE-OFF", pad=40, title_size=36),
                      gap=32, align="stretch"),
        label=BG)

d.slide("api", "Create and join",
        lambda t: tbl(t, ["Function", "What it does", "Error reporting"],
                      [[mono("pthread_create"), "Starts a new thread that runs a function", "Returns an error number, 0 on success"],
                       [mono("pthread_join"), "Waits until one particular thread has finished", "Returns an error number, 0 on success"],
                       [mono("strerror(rc)"), "Turns an error number into text", "Use it instead of errno here"]],
                      [5, 9, 8]),
        note="These functions return the error number directly. They do not set errno. Check every return value. Compile with -pthread.",
        label=BG)

d.slide("two-ideas", "Completion is not protection",
        lambda t: row(card(t, "Joining answers: is it finished?", "pthread_join waits for one worker to finish. After the join, main may read what that worker wrote.", label="COMPLETION", pad=40, title_size=36),
                      card(t, "A mutex answers: who goes now?", "A lock lets only one thread at a time touch a shared value. A join does not do this.", label="MUTUAL EXCLUSION", pad=40, title_size=36),
                      card(t, "This lab", "Each worker writes its own field, so no lock is needed. Joining is the core. Locks come in a later lab.", label="SCOPE", pad=40, title_size=36),
                      gap=32, align="stretch"),
        label=BG)

# ---- the lab ----------------------------------------------------------------
d.opener("lab-open", "LAB 5", "Workers that finish before main reports", "Alex is making a TechCorp worker program concurrent. Each worker must finish before main reports its result.")

START_TREE = [("threads", [("starter.c", None), ("trace.csv", None)]), ("evidence", [])]

labkit.scenario(d, 5, "Alex at TechCorp", "Make a worker program concurrent. Each worker must finish before main reports its result. Compare thread completion with protecting shared mutable memory.",
                "Every run is bounded by a five-second timeout, and every worker is joined.", START_TREE)
labkit.timetable(d, [["0 to 10", "Introduction, objectives and setup"],
                     ["10 to 25", "Task 1, guided: one thread"],
                     ["25 to 35", "Written prediction"],
                     ["35 to 70", "Task 2: two workers and completion"]],
                 [["70 to 85", "Normal and changed runs, feedback"],
                  ["85 to 100", "Individual changed-case checkpoint"],
                  ["100 to 110", "Correction and explanation"],
                  ["110 to 120", "Cleanup and submission"]])
labkit.rules(d, safety="Never signal a kernel worker or another user's process.")
labkit.setup_slides(d, 5, START_TREE,
                    ["threads/starter.c is a short two-worker reminder.",
                     "threads/trace.csv is an illustration of two workers reading and writing one shared value.",
                     "If gcc is missing, do not install anything. Use the source and the printed traces, and say that you did not run the program."])

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "One thread", "Task 1, with the instructor: fifteen minutes.")

d.slide("g-check", "Step 1: check the tools",
        lambda t: row(term(t, ["command -v gcc", "command -v timeout"], size=30),
                      col(para(t, "command -v prints the path of a program, and nothing if it does not exist.", size=32),
                          para(t, "timeout runs a command and stops it after a time limit. Every run in this lab uses it.", size=32),
                          card(t, "Do not install", "Do not install packages on the shared server. Ask the instructor if gcc is missing.", label="CAREFUL", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

ONE = ["#include <pthread.h>", "#include <stdio.h>", "#include <string.h>",
       "static void *worker(void *arg) {", "    int *result = arg;", "    *result = 6 * 7;", "    return NULL;", "}",
       "int main(void) {", "    int result = 0;", "    pthread_t thread;",
       "    int rc = pthread_create(&thread, NULL, worker, &result);",
       '    if (rc) { fprintf(stderr, "create: %s\\n", strerror(rc)); return 1; }',
       "    rc = pthread_join(thread, NULL);",
       '    if (rc) { fprintf(stderr, "join: %s\\n", strerror(rc)); return 1; }',
       '    printf("result=%d\\n", result);', "    return 0;", "}"]

d.slide("g-code", "Step 2: the one-worker program",
        lambda t: row(listing(t, ONE, size=24, hot=(5, 13, 15), lh=1.12),
                      col(para(t, "Save it as threads/one_worker.c. The three marked lines matter most.", size=30),
                          lst(t, ["The worker writes result.", "Main waits with pthread_join.", "Main reads result after the join."], ordered=True, size=30),
                          para(t, "The worker gets a pointer to result, so both threads use the same memory.", size=30),
                          gap=22, flex=None),
                      gap=40, align="center"))

d.slide("g-run", "Step 2: compile and run",
        lambda t: row(term(t, ["gcc -Wall -Wextra -pthread threads/one_worker.c -o threads/one_worker",
                               "timeout 5 ./threads/one_worker",
                               ("out", "result=42")], size=24),
                      col(para(t, "-Wall -Wextra turn on warnings. -pthread links the thread library. -o names the program.", size=32),
                          para(t, "pthread_create starts the worker. pthread_join waits for that worker. strerror(rc) gives readable error text.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-observe", "Step 3: mark three lines",
        lambda t: row(card(t, "Mark them on your copy", "The line where the worker writes result. The line where main waits. The line where main reads it.", label="TRY", pad=40, title_size=36),
                      card(t, "Observe", "Would creating a thread alone tell you when the result is ready? Would a join also stop two workers from racing on one shared counter?", label="THINK", pad=40, title_size=36),
                      card(t, "Compare with fork", "After fork, each process would normally have its own private copy of result.", label="REMEMBER", pad=40, title_size=36),
                      gap=32, align="stretch"))

labkit.predict(d, "If a program starts two workers and main returns without joining them, must both worker-completion messages appear? Explain.",
               rules_text="Do not run the two-worker program yet. Alone, and without AI. A five-minute comparison with a neighbour is optional, but keep your own answer.")

# ---- task 2 -----------------------------------------------------------------
d.opener("t2-open", "TASK 2", "Two workers and completion", "Thirty-five minutes, from minute 35 to 70. Work alone.")

W1 = ["struct job { int id; int steps; int result; };",
      "static void *worker(void *arg) {",
      "    struct job *job = arg;",
      "    const struct timespec delay = {0, 20000000};",
      "    for (int i = 0; i < job->steps; ++i) {",
      "        job->result += job->id;",
      "        nanosleep(&delay, NULL); /* teaching delay, not synchronization */",
      "    }",
      '    printf("worker %d finished\\n", job->id);',
      "    return NULL;", "}"]
W2 = ["int main(void) {",
      "    struct job a = {2, 3, 0}, b = {3, 4, 0};",
      "    pthread_t ta, tb;",
      "    int rc = pthread_create(&ta, NULL, worker, &a);",
      '    if (rc) { fprintf(stderr, "create A: %s\\n", strerror(rc)); return 1; }',
      "    rc = pthread_create(&tb, NULL, worker, &b);",
      "    if (rc) {",
      '        fprintf(stderr, "create B: %s\\n", strerror(rc));',
      "        pthread_join(ta, NULL);",
      "        return 1;", "    }",
      "    /* TODO: join both workers and check each return code. */",
      "    /* TODO: after both joins, print a.result and b.result. */",
      '    puts("main finishing");', "    return 0;", "}"]

d.slide("t2-worker", "Step 1: the starting program, the worker",
        lambda t: row(listing(t, W1, title="threads/two_workers.c (1 of 2)", size=24),
                      col(para(t, "Create threads/two_workers.c with the two parts on this slide and the next. The file also starts with the includes and #define _POSIX_C_SOURCE 200809L.", size=30),
                      para(t, "Each worker adds its own id to its own result field, once per step.", size=30),
                          para(t, "The 20 ms delay only makes an early exit by main easier to see. It is not synchronization and it guarantees no order.", size=30),
                          gap=22, flex=None),
                      gap=40, align="center"))

d.slide("t2-main", "Step 1: the starting program, main",
        lambda t: row(listing(t, W2, title="threads/two_workers.c (2 of 2)", size=24, hot=(11, 12)),
                      col(para(t, "Main creates both workers. If the second create fails, it joins the first before it leaves.", size=30),
                          para(t, "The two marked TODO lines are your work.", size=30),
                          card(t, "Run it first", "Compile and run it as it is. Does main finishing mean the workers finished?", label="TRY", pad=32, title_size=32),
                          gap=22, flex=None),
                      gap=40, align="center"))

d.slide("t2-two", "Step 2 and 3: join both, then print",
        lambda t: row(col(h3(t, "What to do"),
                          lst(t, ["Join each worker and check each return code, as in the single-worker example.",
                                  "Print a.result and b.result after both joins.",
                                  "Decide which lines belong before main finishing.",
                                  "Compile, read the warnings, and run."], ordered=True, size=32),
                          gap=20, flex=3),
                      col(card(t, "Why no mutex here?", "A should give 6 and B should give 12. Each worker owns a different field, and main reads only after completion.", label="THINK", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("t2-trace", "Step 4: a different design, the trace",
        lambda t: row(term(t, ["cat threads/trace.csv"], size=28, title="student@server: ~/oslab-work/lab5"),
                      col(para(t, "The trace shows two workers that each read one shared value, and then write it back.", size=32),
                          card(t, "Think", "What can go wrong in that design? Would joining the workers after their work prevent the overlapping update?", label="THINK", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("t2-done", "Complete when, and hints",
        lambda t: row(card(t, "Complete when", "Both workers complete before main reports results. Creation and join errors are handled. You can tell completion from mutual exclusion.",
                           label="DONE", pad=40, title_size=36, flex=1),
                      col(h3(t, "Hints, one at a time"),
                          lst(t, ["Match one join to each thread that was created.",
                                  "Compare the two thread variables you pass to the joins.",
                                  "Move the result reads after both joins, then ask whether any mutable location is still shared."], ordered=True, size=32),
                          gap=20, flex=1),
                      gap=48, align="stretch"))

# ---- tests ---------------------------------------------------------------------
d.opener("test-open", "TESTS AND FEEDBACK", "Normal run, then a changed run", "Fifteen minutes, from minute 70 to 85.")

d.slide("tests-normal", "Test 1: a normal run, saved",
        lambda t: row(term(t, ["gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers",
                               "timeout 5 ./threads/two_workers > evidence/normal.txt 2>&1",
                               "rc=$?; printf 'exit=%s\\n' \"$rc\" >> evidence/normal.txt",
                               "cat evidence/normal.txt"], size=24),
                      col(para(t, "State the expected results, and explain why the order of the two finished messages may vary.", size=32),
                          para(t, "$? is the exit status of timeout. 124 means the time limit ran out, not success.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("tests-changed", "Test 2: change a worker, predict again",
        lambda t: row(term(t, ["timeout 5 ./threads/two_workers > evidence/changed.txt 2>&1",
                               "rc=$?; printf 'exit=%s\\n' \"$rc\" >> evidence/changed.txt",
                               "cat evidence/changed.txt"], size=24),
                      col(para(t, "Change B to two steps. Predict its new result: 6. Recompile with the same gcc line, then run.", size=32),
                          para(t, "Also try zero steps for one worker. It must still be joined, even if it finishes at once.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("tests-table", "What each run shows",
        lambda t: tbl(t, ["Run", "Expected", "What it tests"],
                      [["Normal", "A is 6, B is 12, exit=0", "Creation, joins, results read after completion"],
                       ["B with two steps", "B is 6", "That the result follows the steps, not a timing accident"],
                       ["A with zero steps", "A is 0, and still joined", "That a fast worker needs a join as well"],
                       ["Exit status 124", "Not a success", "That the time limit expired"]],
                      [4, 6, 9]),
        note="Repeated successful runs do not prove there is no race. Without -pthread the build can fail. If gcc is missing, report that the behaviour was not tested.")

# ---- checkpoint, correction, submission -------------------------------------------
labkit.checkpoint(d, "Main joins worker A but not worker B, then reads B's result. Explain what remains unestablished and name the smallest synchronization change. Would that change alone protect a counter that both workers update at the same time?")
labkit.correction(d, "(a) What makes the result read safe after joining? (b) Why is the delay not a lock? (c) What would change if both workers updated one field?")
labkit.submission(d, 5, ['cp -- threads/two_workers.c "$SUBMISSION_REPO/lab5/"',
                         'cp -- evidence/normal.txt evidence/changed.txt "$SUBMISSION_REPO/lab5/evidence/"'],
                  [("README.md", None), ("two_workers.c", None), ("evidence", [("normal.txt", None), ("changed.txt", None)])],
                  note="Copy the source, not the compiled program, with the two evidence files. Make sure every program has ended.")
labkit.grading(d, [["Correct worker creation, joins and result use", "3"],
                   ["Normal and changed-step or zero-step evidence, with the build diagnosed", "2"],
                   ["Thread memory, completion and mutual exclusion explained; original prediction and correction", "2"],
                   ["Individual checkpoint: result or diagnosis, and mechanism", "2"],
                   ["Concise, attributable evidence and the required artifacts", "1"]])
labkit.mistakes(d, [["No -pthread in the gcc line", "A build or link error", "Add -pthread"],
                    ["Reading a result before the join", "An old value, sometimes right", "Move the reads after both joins"],
                    ["Joining only one worker", "A message that sometimes goes missing", "Join every thread that was created"],
                    ["Trusting the delay as a lock", "It works until the timing changes", "Join, and use a mutex for shared writes"]])

# ---- beyond the core --------------------------------------------------------------
d.opener("ext-open", "BEYOND THE CORE", "Fork, kernel workers and signals", "Optional extensions. Each uses a bounded run and your own processes.")

d.slide("ext-fork", "Fork copies memory, threads share it",
        lambda t: row(term(t, ["./fork_demo",
                               ("out", "child: value=9 pid=4242"),
                               ("out", "parent: value=1 pid=4241")], size=26, title="a small fork() program"),
                      col(para(t, "Set an integer to 1. Change it to 9 only in the child. The parent waits with waitpid, then prints.", size=32),
                          para(t, "The parent still sees 1: after fork the two processes have separate memory. Threads would see 9.", size=32),
                          para(t, "Check fork and waitpid for errors, flush output before fork, and run under timeout 5.", size=32),
                          gap=24),
                      gap=48, align="center"),
        label=EXT)

d.slide("ext-lwp", "Looking at threads from outside",
        lambda t: row(term(t, ["./threads/two_workers & pid=$!",
                               'ps -L -p "$pid" -o pid,lwp,nlwp,comm',
                               'wait "$pid"',
                               "ps -eo pid,ppid,comm | head -n 20"], size=24),
                      col(para(t, "ps -L lists each thread: LWP is the thread's ID, and NLWP counts the threads of the process.", size=30),
                          para(t, "Raise the worker delay to about two seconds per step, so you have time to look.", size=30),
                          para(t, "Kernel workers may be hidden inside a container or WSL. Not seeing them does not prove they are absent. Observe them only; never signal them.", size=30),
                          gap=22),
                      gap=48, align="center"),
        label=EXT)

d.slide("ext-signal", "A signal handler that does almost nothing",
        lambda t: row(listing(t, ["static volatile sig_atomic_t stop;",
                                  "static void on_term(int sig) {", "    (void)sig;", "    stop = 1;  /* only set a flag */", "}",
                                  "/* in main: register it, then loop */",
                                  "struct sigaction sa = {0};", "sa.sa_handler = on_term;", "sigaction(SIGTERM, &sa, NULL);",
                                  "while (!stop) { /* work */ }", "/* print and clean up here, after the loop */"],
                              title="signal_demo.c", size=24),
                      col(para(t, "The handler only sets a flag. Printing and cleanup happen in the normal loop, not inside the handler.", size=30),
                          para(t, "Keep a ten-second limit. Start it, note its own PID, and send kill -TERM to that PID only.", size=30),
                          para(t, "A join waits for completion. A mutex protects shared data. A signal flag is neither.", size=30),
                          gap=22, flex=None),
                      gap=40, align="center"),
        label=EXT)

d.close([("Thread or process", "Threads share memory in one process. Forked processes get separate copies."),
         ("Create, then join", "Check every return code, and join each thread you created."),
         ("Completion is not protection", "A join says it finished. A mutex says who may write now."),
         ("Bound every run", "timeout 5 keeps a mistake from running forever. Exit 124 means it ran out of time.")],
        "chapter 4, Threads and Concurrency", ("Lab 6: users, groups and file permissions", "Who may read, write or run a file, and how Linux decides."))

ORDER = list(S)

SECTIONS = {
    "s1": {"description": "Cover, learning objectives and an opening question.", "start": "cover"},
    "s2": {"description": "Concepts first: processes and threads, what threads share, create and join, completion versus mutual exclusion.", "start": "bg-open"},
    "s3": {"description": "How the lab works: the scenario, the timetable, the rules, setup and the starting tree.", "start": "lab-open"},
    "s4": {"description": "Guided: one thread, then the prediction.", "start": "g-open"},
    "s5": {"description": "Task 2: two workers and completion, then the tests.", "start": "t2-open"},
    "s6": {"description": "The individual checkpoint: why, and the practice question.", "start": "cp-open"},
    "s7": {"description": "Correction, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: fork, kernel workers and signals, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
