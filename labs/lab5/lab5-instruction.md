# OS Lab 5 — Threads, Kernel Workers & Process Signals (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class. Before class: about 10 minutes for the pre-lab |
| Work | Individual. Your worker ids and step counts are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `gcc` with pthread support, `timeout`, `nano`, `cat`, `oslab` |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Lecture link | [Week 4 notes: threads and multicore](../../lectures/notes/week04-threads-multicore.md) |

> **Scenario:** Alex is making a TechCorp worker program concurrent. Each worker must finish before main reports its result. Compare thread completion with the separate question of protecting shared mutable memory.

## Lab Objectives

After the required core, you should be able to:

1. Create POSIX threads and check API return codes.
2. Join each worker before consuming its result and explain shared versus separate address spaces.
3. Use a bounded execution trace to diagnose missing completion synchronization.

**Extension objectives:** Compare forked processes with threads, inspect Linux LWPs/kernel workers, and handle signals in an owned process. These retain the original lab's wider topics; they are not required to finish the two-hour core. They are in the [optional extensions](extensions.md).

## How This Lab Works

| Command | What it does |
|---|---|
| `oslab values lab5` | Shows **your** worker ids and step counts. They are already written in your program |
| `oslab predict lab5` | Saves your prediction once, before the experiment |
| `oslab hint lab5 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab5` | Compiles and runs your program on test cases and shows your milestones |
| `oslab checkpoint lab5` | Opens when the instructor says so, near the end |
| `oslab debrief lab5` | After the lab: you give the right answers to your prediction questions |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint. Always test what an AI tells you.
- In Core 1 you receive a program with two gaps. You decide where each join goes and what main may read before it.

## Before the Lab

Do this before class. It takes about 10 minutes.

```bash
oslab doctor
oslab prelab lab5
```

## Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Setup |
| 10–25 | Guided: one worker |
| 25–35 | Prediction |
| 35–55 | Core 1: finish the two-worker program |
| 55–70 | Core 2: test and change |
| 70–85 | Instructor demonstration, Plus and Challenge |
| 85–100 | Live checkpoint |
| 100–110 | Debrief |
| 110–120 | Submit |

## Setup (0–10)

1. Log in to the server with your own account. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab5
   cd "$OSLAB_WORKSPACE/lab5"
   mkdir -p evidence
   oslab values lab5
   ```

2. **Read your personal values.** The last command prints four numbers that are only yours. For example:

   ```text
   Your personal values for lab5 (your-account):
     id_a     = 3
     id_b     = 9
     steps_a  = 5
     steps_b  = 2
   ```

   Your own numbers are different. Every step of a worker adds the worker's id to its result. So in this example worker A ends with 3 × 5 = 15 and worker B with 9 × 2 = 18. The numbers are already written in the line `struct job a = ...` of your program.

3. Your folder now looks like this:

   ```text
   lab5/
   ├── .oslab-managed.json
   ├── threads/
   │   ├── two_workers.c   # your program: it has two gaps (TODO) that you fill
   │   ├── starter.c       # short two-worker reminder
   │   └── trace.csv       # illustrative read/write interleaving
   └── evidence/
   ```

4. Check the compiler. Do not install packages on the shared server.

   ```bash
   command -v gcc
   command -v timeout
   oslab check lab5
   ```

   At the start every line says `TRY`, because the program has no joins and no report line yet.

## Guided — One Worker (10–25)

**Goal:** see the thread API before the two-worker program. This complete example has one worker.

1. Create `threads/one_worker.c`, compile it and run it. The line `rc = pthread_join(...)` is the one that makes main wait.

   ```bash
   cat > threads/one_worker.c <<'C'
   #include <pthread.h>
   #include <stdio.h>
   #include <string.h>
   static void *worker(void *arg) {
       int *result = arg;
       *result = 6 * 7;
       return NULL;
   }
   int main(void) {
       int result = 0;
       pthread_t thread;
       int rc = pthread_create(&thread, NULL, worker, &result);
       if (rc) { fprintf(stderr, "create: %s\n", strerror(rc)); return 1; }
       rc = pthread_join(thread, NULL);
       if (rc) { fprintf(stderr, "join: %s\n", strerror(rc)); return 1; }
       printf("result=%d\n", result);
       return 0;
   }
   C
   gcc -Wall -Wextra -pthread threads/one_worker.c -o threads/one_worker
   timeout 5 ./threads/one_worker
   ```

   The output is `result=42`. `pthread_create` starts the worker. `pthread_join` waits for that one worker to finish. These functions return an error code (0 means success), so the program tests `rc`.

2. Mark three lines in `threads/one_worker.c`: the line where the worker **writes** `result`, the line where main **waits**, and the line where main **reads** it. Threads share the address space of the process, so main sees what the worker wrote. After a `fork`, each process would have its own private copy.

   **Observe:** Would creating a thread alone tell main when the result is ready? Would a join also stop two workers from racing on one shared counter?

## Prediction (25–35)

Guess first, then try. Answer alone, without AI. Do not run the two-worker program yet.

```bash
oslab predict lab5
```

It asks three questions and one sentence, with your own ids and step counts. A wrong guess costs nothing. You compare it with the real result in the debrief.

## Core 1 — Finish the Two-Worker Program (35–55)

**Goal:** main must wait for both workers, check the return codes, and only then report the results.

1. Read your program with line numbers. Find the two workers, the two `pthread_create` calls and the two `TODO` lines.

   ```bash
   cat -n threads/two_workers.c
   ```

2. Compile and run it **as it is**. Main finishes without waiting: the workers may not have finished, or may not have printed.

   ```bash
   gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers
   timeout 5 ./threads/two_workers
   ```

   The 20 ms delay in every step only makes this easier to see. It is not a way to wait; it does not guarantee any order.

3. **Your decision.** Open the program with `nano threads/two_workers.c` and replace the two `TODO` comments:

   - Join **each** worker, with the thread variable of that worker, and test every return code like in the one-worker example.
   - **After** both joins, print one line in this exact form: `A result=NUMBER B result=NUMBER`, using `a.result` and `b.result`.

   Decide yourself which lines come before `main finishing`. Why must the report line come after the joins and not before them?

4. Compile again. Read every warning; the check wants none. Run it.

   ```bash
   gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers
   timeout 5 ./threads/two_workers
   ```

   Your own numbers are in the report line. Why does the order of the two `worker ... finished` lines not matter, while their position before the report line does?

5. Read `threads/trace.csv`. It shows two workers that **read and then write one shared value**. Joining them after their work would not stop the overlap in that design. What could go wrong?

**Hints:** `oslab hint lab5 1`, `2` and `3`. AI is allowed here; test every suggestion.

## Core 2 — Test and Change (55–70)

**Goal:** show that the program is right for other numbers too, not only the first run.

1. Save a normal run, with the compiler command and the exit status, in `evidence/normal.txt`.

   ```bash
   gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers
   timeout 5 ./threads/two_workers > evidence/normal.txt 2>&1
   rc=$?; printf 'exit=%s\n' "$rc" >> evidence/normal.txt
   cat evidence/normal.txt
   ```

   Status 124 would mean that `timeout` stopped the program. That is not a success.

2. Test a changed case in a **copy**, so that your own program keeps your own numbers. Worker A gets 0 steps and worker B gets 1 step. A worker with zero steps still needs a join.

   ```bash
   cp -- threads/two_workers.c threads/changed.c
   nano threads/changed.c
   ```

   In `threads/changed.c`, change the line `struct job a = ...` so that `a` has `0` steps and `b` has `1` step (keep both ids). **Predict first:** what will A and B print? Then compile and run the copy.

   ```bash
   gcc -Wall -Wextra -pthread threads/changed.c -o threads/changed
   timeout 5 ./threads/changed > evidence/changed.txt 2>&1
   rc=$?; printf 'exit=%s\n' "$rc" >> evidence/changed.txt
   cat evidence/changed.txt
   ```

3. Check your work. The four Core milestones must show `PASS`.

   ```bash
   oslab check lab5
   ```

   `oslab check` compiles your `threads/two_workers.c` and also runs a changed version of it. Several good runs do not prove that there is no race: a run can pass by luck.

4. Write down for your report: what makes it safe for main to read `a.result` after the join? Why is the delay not a lock? What would change if both workers updated one shared field?

## Instructor Demonstration, Plus and Challenge (70–85)

First, watch the instructor remove one join and run the program several times: the output is sometimes right, which is exactly why a test that passes does not prove the program. Then, if you finish early, try these. They are not needed for full marks. Save your answers in `evidence/plus.txt`.

**Plus**

- In a copy (`cp -- threads/two_workers.c threads/nojoin.c`), delete only the join of worker B. Run it three times, and write what main printed for B each time. When can main print B's final number? When can it print less?

**Challenge**

- `threads/trace.csv` has two workers that each read one shared value (it starts at 0), add 1, and write it back. In the order of the file, what is the final value? Is it 2? Which line of the trace shows the problem?

## Live Checkpoint (85–100)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab5
```

1. Answer the four questions. They use new numbers that were made for you at this moment.
2. Then do the file task that the command prints: copy your program under a new name, give the workers new step counts, run it, and save the output in `checkpoint.txt`.
3. Run `oslab check lab5`. A fifth milestone, `checkpoint`, must show `PASS`.

## Debrief (100–110)

Look at your prediction again. `oslab` saved it in a hidden folder, `.records`.

```bash
cat "$OSLAB_WORKSPACE/.records/lab5-predict.json"
```

Now give the right answer to each prediction question:

```bash
oslab debrief lab5
```

Your prediction stays saved as it was, so the comparison shows which answers you confirmed and which you corrected. Then the class discusses: a program printed the right numbers three times. What does that prove?

## Submit (110–120)

1. Copy your work to your course repository. Replace `YOUR_ID` with your own ID. Copy the source, not the compiled program.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab5/evidence"
   cp -- threads/two_workers.c "$SUBMISSION_REPO/lab5/"
   cp -- evidence/normal.txt evidence/changed.txt "$SUBMISSION_REPO/lab5/evidence/"
   ```

   If you did Plus or Challenge, copy `evidence/plus.txt` the same way.

2. Fill in the [report template](README.md) as `lab5/README.md`. Your repository then has:

   ```text
   lab5/
   ├── README.md
   ├── two_workers.c      # source only; no compiled program
   └── evidence/
       ├── normal.txt
       └── changed.txt
   ```

   The course website checks that these exact names are there.

3. Commit and push. `git pull` comes first, in case you pushed from your own computer since.

   ```bash
   cd ~/os-gic-YOUR_ID
   git pull
   git add os-lab-YOUR_ID/lab5
   git commit -m "Lab 5"
   git push
   ```

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Program: `oslab check lab5` passes the four Core milestones (builds, both joins, return codes, changed case) | 2 |
| Tests: `normal.txt` and `changed.txt` show the runs, and the README explains thread memory, completion and mutual exclusion | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab5` | 2 |
| Live checkpoint: the four answers and your copy running with the new step counts | 3 |
| Complete submission: the required files in your repository, on time | 1 |

Every row is marked from your `oslab` records and the files in your repository, so run `oslab check lab5` until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.

## Help and References

- `oslab hint lab5 1`, `2`, `3`
- `man pthread_create`, `man pthread_join`
- If `gcc` is missing on your machine, tell the instructor: the lab has a trace fallback. Executable behavior must then be reported as not tested.
- Forked processes versus threads, kernel workers and signals are in the [optional extensions](extensions.md).
