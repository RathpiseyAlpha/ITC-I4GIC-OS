"""Lab 5 guide, Threads, Kernel Workers and Process Signals. Single source of truth for this deck.

Run `python gen.py` to rewrite project/deck.json and project/slides/*.html.
Never edit the generated slides by hand.

Revised 2026-11-05 to the pilot-format instruction: personal worker ids and step counts, Core 1 (two TODO joins)
and Core 2, Plus and Challenge, a live checkpoint, oslab predict and oslab debrief. Modelled on the Lab 8 guide.

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
from labkit import (h2, para, lst, row, col, grid, card, rule, h3, mono, tbl, term, tree, listing, flow, init)  # noqa: E402,F401

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

START_TREE = [("threads", [("two_workers.c", None), ("starter.c", None), ("trace.csv", None)]), ("evidence", [])]

labkit.scenario(d, 5, "Alex at TechCorp", "Make a worker program concurrent. Each worker must finish before main reports its result. Compare thread completion with protecting shared mutable memory.",
                "Your worker ids and step counts are your own. This guide shows example values.", START_TREE)
labkit.timetable(d, [["0 to 10", "Setup"],
                     ["10 to 25", "Guided: one worker"],
                     ["25 to 35", "Prediction"],
                     ["35 to 55", "Core 1: finish the two-worker program"],
                     ["55 to 70", "Core 2: test and change"]],
                 [["70 to 85", "Instructor demonstration, Plus and Challenge"],
                  ["85 to 100", "Live checkpoint"],
                  ["100 to 110", "Debrief"],
                  ["110 to 120", "Submit"]])

d.slide("helper", "Six helper commands, and why you use them",
        lambda t: tbl(t, ["Command", "What it does"],
                      [[mono("oslab values lab5"), "Shows your worker ids and step counts. They are already written in your program"],
                       [mono("oslab predict lab5"), "Saves your prediction once, before the experiment"],
                       [mono("oslab hint lab5 1"), "A hint, levels 1 to 3. Hints cost no points"],
                       [mono("oslab check lab5"), "Compiles and runs your program on test cases and shows your milestones"],
                       [mono("oslab checkpoint lab5"), "Opens when the instructor says so, near the end"],
                       [mono("oslab debrief lab5"), "After the lab: you give the right answers to your prediction questions"]],
                      [5, 11]),
        note="Before the lab, run oslab doctor and oslab prelab lab5. It takes about ten minutes.")

d.slide("rules", "How you work",
        lambda t: row(rule(t, "Core, Plus, Challenge", "Core is for everyone. Plus and Challenge are for students who finish early. Full marks need only Core and the checkpoint.", title_size=36),
                      rule(t, "AI tools", "Allowed in Core, Plus and Challenge, so test what they tell you. Not allowed in the prediction and the checkpoint.", title_size=36),
                      rule(t, "A program with two gaps", "In Core 1 you receive a program with two gaps. You decide where each join goes and what main may read before it.", title_size=36)),
        note="Never signal a kernel worker or another user's process. A wrong prediction costs nothing.")

d.slide("start", "Setup: start the lab",
        lambda t: row(term(t, ['export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"',
                               "oslab start lab5",
                               'cd "$OSLAB_WORKSPACE/lab5"',
                               "mkdir -p evidence",
                               "oslab values lab5"], title="student@server: ~", size=26),
                      col(lst(t, ["The first line sets OSLAB_WORKSPACE to ~/oslab-work, unless it is already set. Type it as it is.",
                                  "oslab start lab5 makes the lab folder.",
                                  "cd takes you into it, and mkdir -p makes the evidence folder.",
                                  "oslab values lab5 prints your own numbers."], size=30),
                          gap=20),
                      gap=48, align="center"))

d.slide("values", "Your values: four numbers that are only yours",
        lambda t: row(col(h3(t, "The last command prints them"),
                          term(t, ["oslab values lab5",
                                   ("out", "Your personal values for lab5 (your-account):"),
                                   ("out", "  id_a     = 3"),
                                   ("out", "  id_b     = 9"),
                                   ("out", "  steps_a  = 5"),
                                   ("out", "  steps_b  = 2")], title="example: your values will be different", size=26),
                          gap=20, flex=None),
                      col(h3(t, "What they mean"),
                          lst(t, ["Every step of a worker adds the worker's id to its result.",
                                  "In the example, worker A ends with 3 x 5 = 15 and worker B with 9 x 2 = 18.",
                                  "The numbers are already written in the line struct job a = ... of your program."], size=30),
                          gap=20, flex=None),
                      gap=48, align="flex-start"))

d.slide("start-tree", "Your folder",
        lambda t: row(tree(t, "lab5", START_TREE, cmd="tree -a -L 3", title="student@server: ~/oslab-work/lab5", size=30),
                      col(para(t, "threads/two_workers.c is your program. It has two gaps, marked TODO, that you fill.", size=32),
                          para(t, "starter.c is a short two-worker reminder. trace.csv is an illustration of two workers reading and writing one shared value.", size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-check", "Check the compiler",
        lambda t: row(term(t, ["command -v gcc", "command -v timeout", "oslab check lab5"], size=30),
                      col(para(t, "command -v prints the path of a program, and nothing if it does not exist. timeout stops a command after a time limit. Every run in this lab uses it.", size=30),
                          para(t, "At the start every line of oslab check says TRY, because the program has no joins and no report line yet.", size=30),
                          card(t, "Do not install", "Do not install packages on the shared server. If gcc is missing, tell the instructor: the lab has a trace fallback, and you must report that the behaviour was not tested.", label="CAREFUL", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- guided -------------------------------------------------------------------
d.opener("g-open", "GUIDED", "One worker", "Ten to twenty-five minutes, with the instructor. A complete example with one worker.")

ONE = ["#include <pthread.h>", "#include <stdio.h>", "#include <string.h>",
       "static void *worker(void *arg) {", "    int *result = arg;", "    *result = 6 * 7;", "    return NULL;", "}",
       "int main(void) {", "    int result = 0;", "    pthread_t thread;",
       "    int rc = pthread_create(&thread, NULL, worker, &result);",
       '    if (rc) { fprintf(stderr, "create: %s\\n", strerror(rc)); return 1; }',
       "    rc = pthread_join(thread, NULL);",
       '    if (rc) { fprintf(stderr, "join: %s\\n", strerror(rc)); return 1; }',
       '    printf("result=%d\\n", result);', "    return 0;", "}"]

d.slide("g-code", "Step 1: the one-worker program",
        lambda t: row(listing(t, ONE, size=24, hot=(5, 13, 15), lh=1.12),
                      col(para(t, "Create threads/one_worker.c with cat &gt; threads/one_worker.c &lt;&lt;'C', paste the lines, and end with a line that holds only C.", size=28),
                          lst(t, ["The worker writes result.", "Main waits with pthread_join.", "Main reads result after the join."], ordered=True, size=28),
                          para(t, "The worker gets a pointer to result, so both threads use the same memory.", size=28),
                          gap=20, flex=None),
                      gap=40, align="center"))

d.slide("g-run", "Step 1: compile and run",
        lambda t: row(term(t, ["gcc -Wall -Wextra -pthread threads/one_worker.c -o threads/one_worker",
                               "timeout 5 ./threads/one_worker",
                               ("out", "result=42")], size=24),
                      col(para(t, "-Wall -Wextra turn on warnings. -pthread links the thread library. -o names the program.", size=30),
                          para(t, "pthread_create starts the worker and pthread_join waits for that one worker. Both return an error code, where 0 means success, so the program tests rc.", size=30),
                          gap=24),
                      gap=48, align="center"))

d.slide("g-observe", "Step 2: mark three lines",
        lambda t: row(card(t, "Mark them on your copy", "The line where the worker writes result. The line where main waits. The line where main reads it.", label="TRY", pad=40, title_size=36),
                      card(t, "Observe", "Would creating a thread alone tell main when the result is ready? Would a join also stop two workers from racing on one shared counter?", label="THINK", pad=40, title_size=36),
                      card(t, "Compare with fork", "Threads share the address space, so main sees what the worker wrote. After fork, each process would have its own private copy.", label="REMEMBER", pad=40, title_size=36),
                      gap=32, align="stretch"))

# ---- prediction ---------------------------------------------------------------
d.opener("predict-open", "PREDICT", "Guess first, then try", "Before you run the two-worker program. Ten minutes.")

d.slide("predict", "The prediction",
        lambda t: row(col(term(t, ["oslab predict lab5"]),
                          para(t, "It asks three questions and one sentence, with your own ids and step counts. Answer alone, without AI.", size=32),
                          gap=24, flex=3),
                      col(card(t, "The rules", "Do not run the two-worker program yet. The first answer is the one that counts. A wrong guess costs nothing.", label="PREDICTION", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"),
        note="You compare it with the real result in the debrief.")

# ---- core 1 ---------------------------------------------------------------------
d.opener("c1-open", "CORE 1", "Finish the two-worker program", "Twenty minutes, from minute 35 to 55. Main must wait for both workers, check the return codes, and only then report.")

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
      "    struct job a = {3, 5, 0}, b = {9, 2, 0};",
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

d.slide("c1-worker", "Step 1: read your program, the worker",
        lambda t: row(listing(t, W1, title="threads/two_workers.c (1 of 2)", size=24),
                      col(para(t, "Read it with cat -n threads/two_workers.c. Find the two workers, the two pthread_create calls and the two TODO lines.", size=30),
                          para(t, "Each worker adds its own id to its own result field, once per step.", size=30),
                          para(t, "The 20 ms delay only makes an early exit by main easier to see. It is not a way to wait, and it guarantees no order.", size=30),
                          gap=22, flex=None),
                      gap=40, align="center"))

d.slide("c1-main", "Step 1: read your program, main",
        lambda t: row(listing(t, W2, title="threads/two_workers.c (2 of 2)", size=24, hot=(11, 12)),
                      col(para(t, "Main creates both workers. If the second create fails, it joins the first before it leaves.", size=30),
                          para(t, "The line with struct job holds your own numbers. The example shows ids 3 and 9, steps 5 and 2.", size=30),
                          para(t, "The two marked TODO lines are your work.", size=30),
                          gap=22, flex=None),
                      gap=40, align="center"))

d.slide("c1-run0", "Step 2: run it as it is",
        lambda t: row(term(t, ["gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers",
                               "timeout 5 ./threads/two_workers"], size=24),
                      col(para(t, "Main finishes without waiting. The workers may not have finished, or may not have printed.", size=32),
                          card(t, "Think", "Does main finishing mean the workers finished?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("c1-todo", "Step 3: your decision",
        lambda t: row(col(h3(t, "Replace the two TODO lines"),
                          lst(t, ["Join each worker, with the thread variable of that worker, and test every return code like in the one-worker example.",
                                  "After both joins, print one line: A result=NUMBER B result=NUMBER, using a.result and b.result.",
                                  "Decide yourself which lines come before main finishing."], ordered=True, size=30),
                          gap=20, flex=3),
                      col(card(t, "Open it with nano", "nano threads/two_workers.c. With the example numbers the line reads A result=15 B result=18. Yours are different.", label="YOUR TURN", pad=32, title_size=32),
                          card(t, "Think", "Why must the report line come after the joins and not before them?", label="WHY", pad=32, title_size=32),
                          gap=24, flex=2),
                      gap=48, align="stretch"))

d.slide("c1-run", "Step 4: compile again and run",
        lambda t: row(term(t, ["gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers",
                               "timeout 5 ./threads/two_workers"], size=24),
                      col(para(t, "Read every warning. The check wants none.", size=32),
                          card(t, "Think", "Why does the order of the two worker finished lines not matter, while their position before the report line does?", label="TRY", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("c1-trace", "Step 5: a different design, the trace",
        lambda t: row(term(t, ["cat threads/trace.csv"], size=28, title="student@server: ~/oslab-work/lab5"),
                      col(para(t, "The trace shows two workers that read and then write one shared value.", size=32),
                          card(t, "Think", "Joining them after their work would not stop the overlap in that design. What could go wrong?", label="THINK", pad=32, title_size=32),
                          gap=24),
                      gap=48, align="center"))

d.slide("c1-hints", "Complete when, and hints",
        lambda t: row(card(t, "Complete when", "Both workers complete before main reports. Every creation and join return code is tested. The report line shows your own numbers.",
                           label="DONE", pad=40, title_size=36, flex=1),
                      col(h3(t, "Hints: oslab hint lab5 1, 2, 3"),
                          lst(t, ["Match one join to each thread that was created.",
                                  "Compare the two thread variables you pass to the joins.",
                                  "AI is allowed here. Test every suggestion."], ordered=True, size=32),
                          gap=20, flex=1),
                      gap=48, align="stretch"))

# ---- core 2 ---------------------------------------------------------------------
d.opener("c2-open", "CORE 2", "Test and change", "Fifteen minutes, from minute 55 to 70. Show that the program is right for other numbers too.")

d.slide("c2-normal", "Step 1: save a normal run",
        lambda t: row(term(t, ["gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers",
                               "timeout 5 ./threads/two_workers > evidence/normal.txt 2>&1",
                               "rc=$?; printf 'exit=%s\\n' \"$rc\" >> evidence/normal.txt",
                               "cat evidence/normal.txt"], size=24),
                      col(para(t, "The file holds the program output and the exit status. Exit status 124 would mean that timeout stopped the program. That is not a success.", size=30),
                          para(t, "$? is the exit status of the last command.", size=30),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-changed", "Step 2: a changed case, in a copy",
        lambda t: row(term(t, ["cp -- threads/two_workers.c threads/changed.c",
                               "nano threads/changed.c",
                               "gcc -Wall -Wextra -pthread threads/changed.c -o threads/changed",
                               "timeout 5 ./threads/changed > evidence/changed.txt 2>&1",
                               "rc=$?; printf 'exit=%s\\n' \"$rc\" >> evidence/changed.txt",
                               "cat evidence/changed.txt"], size=24),
                      col(para(t, "Work in a copy, so your own program keeps your own numbers. In changed.c give worker A 0 steps and worker B 1 step, and keep both ids.", size=30),
                          card(t, "Predict first", "What will A and B print? A worker with zero steps still needs a join.", label="TRY", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

d.slide("c2-table", "What each run shows",
        lambda t: tbl(t, ["Run", "Expected", "What it tests"],
                      [["Normal", "A result=id_a x steps_a, B result=id_b x steps_b, exit=0", "Creation, joins, results read after completion"],
                       ["Changed: A 0 steps, B 1 step", "A result=0, B result=id_b", "That the result follows the steps, and a fast worker needs a join too"],
                       ["Exit status 124", "Not a success", "That the time limit expired"]],
                      [5, 7, 8]),
        note="Several good runs do not prove that there is no race: a run can pass by luck. Without -pthread the build can fail.")

d.slide("c2-check", "Steps 3 and 4: check, then explain",
        lambda t: row(term(t, ["oslab check lab5"], size=28),
                      col(para(t, "The four Core milestones must show PASS: the program builds, both joins, the return codes, and the changed case. oslab check also runs a changed version of your program.", size=30),
                          card(t, "Write down for your report", "What makes it safe for main to read a.result after the join? Why is the delay not a lock? What would change if both workers updated one shared field?", label="REPORT", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- demonstration, plus and challenge ----------------------------------------------------
d.slide("plus", "Plus: remove one join",
        lambda t: row(term(t, ["cp -- threads/two_workers.c threads/nojoin.c"], size=24),
                      col(para(t, "In the copy, delete only the join of worker B. Run it three times, and write what main printed for B each time.", size=30),
                          card(t, "Answer in evidence/plus.txt", "When can main print B's final number? When can it print less?", label="PLUS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"),
        note="First watch the instructor remove one join and run the program several times. The output is sometimes right, which is why a passing test does not prove the program. Plus and Challenge are not needed for full marks.")

d.slide("challenge", "Challenge: read the trace",
        lambda t: row(term(t, ["cat threads/trace.csv"], size=28),
                      col(para(t, "Two workers each read one shared value, which starts at 0, add 1, and write it back.", size=30),
                          card(t, "Answer in evidence/plus.txt", "In the order of the file, what is the final value? Is it 2? Which line of the trace shows the problem?", label="CHALLENGE", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

# ---- live checkpoint ------------------------------------------------------------------------
d.opener("cp-open", "LIVE CHECKPOINT", "Show what you can do alone", "Fifteen minutes near the end of the lab. Worth 3 of the 10 points.")

d.slide("cp-why", "Why is there a checkpoint?",
        lambda t: grid(card(t, "It shows what you can do alone", "For most of the lab you may use hints and AI tools. The checkpoint is the one moment without them.", icon_name="CheckCircle", pad=28, title_size=32),
                       card(t, "Your numbers are new", "The questions use new numbers, made for you at that moment. An answer copied from a neighbour does not fit.", icon_name="Key", pad=28, title_size=32),
                       card(t, "The instructor sees who needs help", "Your answers arrive at once, so a common mistake can be explained before the next lab.", icon_name="Users", pad=28, title_size=32),
                       card(t, "It is fair", "Everyone gets the same kind of task, with their own numbers.", icon_name="ThumbsUp", pad=28, title_size=32),
                       cols=2),
        gap=36)

d.slide("cp-steps", "What happens, step by step",
        lambda t: flow(t, [("1. The instructor opens it", "Close your AI tools"), ("2. oslab checkpoint lab5", "Answer the four questions"),
                           ("3. The file task", "Copy your program, new step counts"), ("4. oslab check lab5", "A fifth milestone must pass")], 400, hot=1),
        lambda t: row(rule(t, "Before it opens", "The command says that the checkpoint is not open yet. Wait for the instructor.", title_size=36),
                      rule(t, "While you work", "Use your terminal and what you learned in this lab. No AI tools, and no help from a neighbour.", title_size=36),
                      rule(t, "When you finish", "oslab check lab5 shows whether the fifth milestone, checkpoint, passes. You can fix your copy and check again.", title_size=36)),
        gap=56)

d.slide("cp-marks", "What the checkpoint asks",
        lambda t: tbl(t, ["Part", "What you do"],
                      [["Four questions", "They use new numbers that were made for you at this moment. Answer them in the terminal."],
                       ["The file task", "Copy your program under a new name, give the workers the new step counts the command prints, run it, and save the output in checkpoint.txt."],
                       ["The check", "Run oslab check lab5. The fifth milestone, checkpoint, must show PASS."]],
                      [4, 13]),
        note="Your own two_workers.c stays as it is. The task uses a copy.")

# ---- debrief and submit ---------------------------------------------------------------------
d.opener("end-open", "DEBRIEF AND SUBMIT", "Look back, then hand in", "Ten minutes of debrief, ten to submit.")

d.slide("debrief", "Debrief: look at your prediction again",
        lambda t: row(term(t, ['cat "$OSLAB_WORKSPACE/.records/lab5-predict.json"',
                               "oslab debrief lab5"], size=24, title="student@server: ~/oslab-work/lab5"),
                      col(para(t, "oslab saved your prediction in a hidden folder, .records. It stays as it was, so the comparison shows which answers you confirmed and which you corrected.", size=30),
                          card(t, "Class discussion", "A program printed the right numbers three times. What does that prove?", label="DISCUSS", pad=32, title_size=32),
                          gap=22),
                      gap=48, align="center"))

labkit.submission(d, 5, ['cp -- threads/two_workers.c "$SUBMISSION_REPO/lab5/"',
                         'cp -- evidence/normal.txt evidence/changed.txt "$SUBMISSION_REPO/lab5/evidence/"'],
                  [("README.md", None), ("two_workers.c", None), ("evidence", [("normal.txt", None), ("changed.txt", None)])],
                  note="Copy the source, not the compiled program. If you did Plus or Challenge, copy evidence/plus.txt the same way. The course website checks that these exact names are there.")

d.slide("submit-git", "Submit 3: commit and push",
        lambda t: row(term(t, ["cd ~/os-gic-YOUR_ID",
                               "git pull",
                               "git add os-lab-YOUR_ID/lab5",
                               'git commit -m "Lab 5"',
                               "git push"], title="student@server: ~", size=26),
                      col(para(t, "git pull comes first, in case you pushed from your own computer since.", size=32),
                          para(t, "Replace YOUR_ID with your own ID, as before.", size=32),
                          gap=24),
                      gap=48, align="center"))

labkit.grading(d, [["Program: oslab check lab5 passes the four Core milestones (builds, both joins, return codes, changed case)", "2"],
                   ["Tests: normal.txt and changed.txt show the runs, and the README explains thread memory, completion and mutual exclusion", "2"],
                   ["Prediction saved in time, and corrected with oslab debrief lab5", "2"],
                   ["Live checkpoint: the four answers and your copy running with the new step counts", "3"],
                   ["Complete submission: the required files in your repository, on time", "1"]],
               note="Every row is marked from your oslab records and the files in your repository, so run oslab check lab5 until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.")

labkit.mistakes(d, [["No -pthread in the gcc line", "A build or link error", "Add -pthread"],
                    ["Reading a result before the join", "An old value, sometimes right", "Move the reads after both joins"],
                    ["Joining only one worker", "A message that sometimes goes missing", "Join every thread that was created"],
                    ["Trusting the delay as a lock", "It works until the timing changes", "Join, and use a mutex for shared writes"],
                    ["Changing two_workers.c for the changed case", "Your evidence no longer has your numbers", "Change the copy, changed.c"]])

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
    "s5": {"description": "Core 1 and Core 2: finish the two-worker program and test it, then Plus and Challenge.", "start": "c1-open"},
    "s6": {"description": "The live checkpoint: why, the steps with oslab, and what it asks.", "start": "cp-open"},
    "s7": {"description": "Debrief, submission, grading, common mistakes.", "start": "end-open"},
    "s8": {"description": "Beyond the core: fork, kernel workers and signals, then takeaways and the next lab.", "start": "ext-open"},
}

if __name__ == "__main__":
    d.build(HERE, TITLE, CREATED_AT, SECTIONS)
