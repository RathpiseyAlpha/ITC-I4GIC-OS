# OS Lab 8 — Stock race and complete critical section

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account; `flock` |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | Bash conditionals and bounded background jobs |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Validate purchase quantities.
2. Identify the read-check-write critical section.
3. Use a lock covering the full update.

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

Log in with your own account. Run `oslab doctor`, then `oslab start lab8`; `oslab status lab8` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab8`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
( flock -x -w 2 9 && printf 'lock acquired\n' ) 9>"$HOME/oslab-work/lab8/store/stock.lock"
```

Before continuing: Does locking only the final write protect a preceding stock check?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** Stock is 5. Two buyers each request 4. If both read before either writes, what invalid outcome can occur?

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab8` after `oslab start lab8`. **Goal:** Create a purchase script in your lab8 workspace. It reads stock, rejects invalid or excessive quantities, updates stock and appends a sale log. Use a short teaching delay between read and write to observe a race, then protect the full read-check-write-log sequence with `flock -w 2`. Remove the delay for final version.

Use `store/buy.sh` as a starting skeleton. Keep stock and log in `store/`; put `stock.lock` there too.

**Suggested sequence:** Write the invariant `successful sales + remaining stock = initial stock`. Handle one valid and one invalid quantity first. Run the two-buyer teaching case, then move the lock to before the stock read and hold it through the log append.

**Boundaries and editable files:** Use at most two concurrent buyers, positive integer quantities, stock never below zero, and a timeout. Work only with owned files. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Test valid purchase, zero/negative/noninteger, too-large purchase, and two buyers requesting 4 from stock 5. Repeat controlled runs; success alone cannot prove race absence.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab8` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> Stock becomes 3. Two buyers request 2. Predict number of accepted purchases under correct locking and final stock.

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab8` and leave the workspace for review; `oslab clean lab8` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: Write the invariant
2. Observation: place lock before read
3. Partial approach: keep validation and update inside one lock scope.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [Week 7 notes](../../lectures/notes/week07-critical-sections.md) and `man flock`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

Audit log design; red-team review of a classmate's test only by consent; permission setup on prepared accounts. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
