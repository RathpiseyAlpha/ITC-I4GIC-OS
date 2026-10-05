# OS Lab 5 — Processes, threads and joins

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account; C compiler |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | process basics, C source reading |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Distinguish process and thread address spaces.
2. Explain why joining matters.
3. Diagnose a missing join from a trace.

## 120-minute route

| Minutes | Activity |
|---|---|
| 0–10 | Opening question and safety/setup |
| 10–25 | Guided example |
| 25–35 | Prediction on paper; five-minute optional peer comparison |
| 35–70 | Individual investigation or build; AI optional |
| 70–85 | Normal and edge tests; feedback pause |
| 85–100 | Individual changed case, supervised; no AI or peers |
| 100–110 | Evidence-based correction and concept explanation |
| 110–120 | Cleanup and concise submission |

## Setup and guided example (0–25)

Log in with your own account. Run `oslab doctor`, then `oslab start lab5`; `oslab status lab5` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab5`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
printf 'thread,step\nA,read\nB,read\nA,write\nB,write\n' | column -s, -t 2>/dev/null || cat "$HOME/oslab-work/lab5/threads/trace.csv"
```

Before continuing: Can the trace alone prove the program was race-free?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** If main returns before joining a worker, must the worker's final print appear? Why?

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab5` after `oslab start lab5`. **Goal:** Use the provided trace to mark overlapping steps; write a minimal pthread program with two workers and joins in your workspace, and compare observed order to your prediction. Explain why joins ensure completion but do not protect a shared counter.

Use `threads/starter.c`; compile with `gcc -Wall -Wextra -pthread threads/starter.c -o threads/demo`. Keep the TODO as your own decision point.

**Suggested sequence:** Read the trace and mark where workers overlap. Compile the starter, run it, then add a join for each created worker. Explain separately what would need a mutex if both changed one counter.

**Boundaries and editable files:** Compile and run only your own code, without elevated privileges. Set bounded loop counts and a 10-second timeout. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Run a normal case and a changed loop count; verify both workers finish. A successful run does not prove race absence.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab5` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> Main joins only worker A. Can worker B's result be safely read? Explain the minimal change.

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab5` and leave the workspace for review; `oslab clean lab5` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: Separate completion from mutual exclusion
2. Observation: inspect `pthread_create` return values
3. Partial approach: join each created thread.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [Week 4 notes](../../lectures/notes/week04-threads-multicore.md) and `man pthread_join`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

Kernel worker observation with `ps`; owned-process signals; compare processes and threads using `/proc`. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
