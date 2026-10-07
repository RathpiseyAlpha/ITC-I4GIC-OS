# OS Lab 5 — Threads, Kernel Workers & Process Signals (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Basic C functions/structs, processes, compiler use; review the supplied code first |
| Required tools | `gcc` with pthread support, `timeout`, `ps`; instructor provides trace fallback if compiler is unavailable |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** Alex is making a TechCorp worker program concurrent. Each worker must finish before main reports its result. Compare thread completion with the separate question of protecting shared mutable memory.

## Lab Objectives

After the required core, you should be able to:

1. Create POSIX threads and check API return codes.
2. Join each worker before consuming its result and explain shared versus separate address spaces.
3. Use a bounded execution trace to diagnose missing completion synchronization.

**Extension objectives:** Compare forked processes with threads, inspect Linux LWPs/kernel workers, and handle signals in an owned process. These retain the original lab's wider topics; they are not required to finish the two-hour core.

## Task Overview and 120-minute Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Introduction, objectives and setup |
| 10–25 | Guided example: commands and observations |
| 25–35 | Written prediction; optional five-minute peer comparison |
| 35–70 | Numbered individual investigation tasks; AI optional |
| 70–85 | Normal and edge tests; instructor feedback |
| 85–100 | Individual changed-case checkpoint; no AI or peers |
| 100–110 | Correction and conceptual explanation |
| 110–120 | Cleanup and submission |

Original Task 1 processes/threads introduces memory ownership; Task 2 thread interaction and joining is the core. Task 3 kernel mapping and Task 4 signals remain extensions.

## Lab Setup (0–10 minutes)

1. Log in to the Ubuntu server using **your own account**. All commands below run as that ordinary user in Bash. Use only your own files and processes.
2. Check the helper. If it is unavailable, follow [the local setup guide](../SETUP.md) to define `oslab` from your cloned course repository; it uses the same fixtures.

   ```bash
   whoami
   command -v oslab
   oslab doctor
   ```

3. Start the lab and **enter its directory**. `oslab start` preserves existing work and does not change the current directory. If resuming, inspect existing files before running commands that write to them.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab5
   cd "$OSLAB_WORKSPACE/lab5"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab5/
   ├── .oslab-managed.json
   ├── threads/
   │   ├── starter.c   # short two-worker reminder
   │   └── trace.csv   # illustrative read/write interleaving
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Task 1 — One Thread: Guided Working Example (10–25)

1. Check the compiler; do not install packages on the shared server.

   ```bash
   command -v gcc
   command -v timeout
   ```

2. Create `threads/one_worker.c`. This complete one-worker example demonstrates the API before the two-worker investigation.

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

   Expected output is `result=42`. `pthread_create` starts execution; `pthread_join` waits for that particular worker's completion. These functions return error codes directly, so use `strerror(rc)` rather than assuming `errno` holds the error.

3. Mark the line where the worker writes `result`, the line where main waits, and the line where main reads it. Threads share this process's address space. With `fork`, each process would normally have its own private copy after the fork.

   **Observe:** Would creating a thread alone establish when the result is ready? Would a join also prevent two workers from racing on one shared counter?

## Prediction (25–35)

Write: **If a program starts two workers and main returns without joining them, must both worker-completion messages appear? Explain.** Do not run the two-worker program yet. A five-minute peer comparison is optional.

## Task 2 — Two Workers and Completion (35–70)

1. Save the small fixture reminder, then create this richer starting program as `threads/two_workers.c`.

   ```bash
   cat > threads/two_workers.c <<'C'
   #define _POSIX_C_SOURCE 200809L
   #include <pthread.h>
   #include <stdio.h>
   #include <string.h>
   #include <time.h>
   struct job { int id; int steps; int result; };
   static void *worker(void *arg) {
       struct job *job = arg;
       const struct timespec delay = {0, 20000000};
       for (int i = 0; i < job->steps; ++i) {
           job->result += job->id;
           nanosleep(&delay, NULL); /* teaching delay, not synchronization */
       }
       printf("worker %d finished\n", job->id);
       return NULL;
   }
   int main(void) {
       struct job a = {2, 3, 0}, b = {3, 4, 0};
       pthread_t ta, tb;
       int rc = pthread_create(&ta, NULL, worker, &a);
       if (rc) { fprintf(stderr, "create A: %s\n", strerror(rc)); return 1; }
       rc = pthread_create(&tb, NULL, worker, &b);
       if (rc) {
           fprintf(stderr, "create B: %s\n", strerror(rc));
           pthread_join(ta, NULL);
           return 1;
       }
       /* TODO: join both workers and check each return code. */
       /* TODO: after both joins, print a.result and b.result. */
       puts("main finishing");
       return 0;
   }
   C
   gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers
   timeout 5 ./threads/two_workers
   ```

   The bounded 20 ms delay makes early main exit easier to observe; it does not guarantee a particular schedule. Without joins, main must not read the worker results concurrently as if they were complete.

2. Add the two joins and check their return codes using the single-worker example. Add result printing **after** both joins. Decide which lines should precede `main finishing`.
3. Compile again, inspect warnings, and run. Explain why A should produce 6 and B should produce 12 without needing a mutex here: each worker owns a different result field, and main reads only after completion.
4. Read `threads/trace.csv`. It depicts two workers reading and then writing one shared value. Explain what could go wrong in that different design; joining them after their work would not prevent the overlapping update.

**Complete when:** both workers complete before main reports results, creation/join errors are handled, and you can distinguish completion from mutual exclusion.

**Hints:** (1) match one join to each successfully created thread; (2) compare the two thread IDs passed to joins; (3) move result reads after both joins, then examine whether any mutable location is still shared between workers.

## Tests and Feedback (70–85)

1. Save a normal run and compiler command in `evidence/normal.txt`. State the expected results and explain why completion-message order may vary.

   ```bash
   gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers
   timeout 5 ./threads/two_workers > evidence/normal.txt 2>&1
   rc=$?; printf 'exit=%s\n' "$rc" >> evidence/normal.txt
   cat evidence/normal.txt
   ```
2. Change B to two steps, predict its new result (6), then recompile and save the result in `evidence/changed.txt`. Also try zero steps for one worker: it still needs joining even if it finishes quickly.

   ```bash
   gcc -Wall -Wextra -pthread threads/two_workers.c -o threads/two_workers
   timeout 5 ./threads/two_workers > evidence/changed.txt 2>&1
   rc=$?; printf 'exit=%s\n' "$rc" >> evidence/changed.txt
   cat evidence/changed.txt
   ```
3. Check exit status after `timeout`: status 124 means the time limit expired, not a successful run. Successful repeated executions do not prove absence of all races.

**Troubleshooting:** Missing `-pthread` can cause build/link failures. Check return codes before assuming a worker was created. If the compiler is unavailable, use the source and printed traces for the concept/checkpoint; report that executable behavior was not tested. See [Week 4 notes](../../lectures/notes/week04-threads-multicore.md) and `man pthread_join`.


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> Main joins worker A but not worker B, then reads B’s result. Explain what remains unestablished and identify the minimal synchronization change. Would that change alone protect a counter updated concurrently by both workers?

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) What makes the result read safe after joining? (b) Why is the delay not a lock? (c) What would change if both workers updated one field?

## Cleanup and Final Submission (110–120 minutes)

All core executions use a five-second timeout and joined workers; confirm the executable ended. Copy source, not binaries, into the submission. Kernel workers are observed only, never signalled.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab5/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- threads/two_workers.c "$SUBMISSION_REPO/lab5/"
   cp -- evidence/normal.txt evidence/changed.txt "$SUBMISSION_REPO/lab5/evidence/"
   ```

   ```text
   lab5/
   ├── README.md
   ├── two_workers.c      # source only; no compiled executable
   └── evidence/
       ├── normal.txt
       └── changed.txt
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct worker creation, joins and result use (objectives 1–3) | 3 |
| Normal and changed-step/zero-step evidence with build diagnosis | 2 |
| Explain thread memory, completion and mutual-exclusion differences; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
