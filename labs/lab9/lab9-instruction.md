# OS Lab 9 — Deadlock diagnosis and recovery

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account; `flock` |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | Lab 8 locking |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Draw a wait-for cycle.
2. Reproduce bounded opposite ordering.
3. Prevent deadlock with one global order.

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

Log in with your own account. Run `oslab doctor`, then `oslab start lab9`; `oslab status lab9` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab9`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
( flock -x -w 2 9 && printf 'Alpha acquired\n' ) 9>"$HOME/oslab-work/lab9/vault/alpha.lock"
```

Before continuing: What happens if both workers hold one lock and request the other?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** Worker 1 holds Alpha then requests Beta; worker 2 holds Beta then requests Alpha. Predict each wait edge.

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab9` after `oslab start lab9`. **Goal:** Write two short scripts that acquire owned Alpha/Beta lock files in opposite order, with a coordination barrier or documented teaching delay. Use `flock -w 2` for every acquisition. Capture a wait trace, then change both scripts to Alpha-before-Beta and explain why the cycle disappears.

Use `vault/worker.sh` as a starting skeleton. Use separate Alpha and Beta lock files in `vault/`.

**Suggested sequence:** Write the Alpha/Beta lock order for each worker. Add a line after each acquisition and a bounded barrier so both first locks are held before requesting the second. Then change both workers to the same order.

**Boundaries and editable files:** At most two workers; each has a five-second outer timeout; no broad `pkill` or partner dependency. Release through process exit or normal descriptor close. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Run the deliberately conflicting case and the ordered case; inspect exit codes. Timing may prevent the deadlock observation on a given run.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab9` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> A third worker needs Beta only. Does global Alpha-before-Beta require it to lock Alpha? Why?

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab9` and leave the workspace for review; `oslab clean lab9` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: Draw holdings and requests
2. Observation: verify both processes reached the barrier
3. Partial approach: use consistent acquisition order.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [Deadlock visualization](../../lectures/visualizations/rag-deadlock.html) and `man flock`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

Partner site-to-site scenario only in a narrowly prepared shared directory; timeout recovery policy. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
