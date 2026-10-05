# OS Lab 1 — OS inspection and owned processes

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | login, terminal, basic commands |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Identify kernel and distribution from evidence.
2. Distinguish a program from a running process.
3. Trace one owned process through start and exit.

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

Log in with your own account. Run `oslab doctor`, then `oslab start lab1`; `oslab status lab1` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab1`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
uname -s; cat /etc/os-release | head -6; sleep 10 & pid=$!; ps -o pid,ppid,stat,comm -p "$pid"; wait "$pid"
```

Before continuing: Which output describes installed software, and which describes a live instance?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** If two `sleep 10` commands start, will they share a PID? Why?

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab1` after `oslab start lab1`. **Goal:** Start two bounded `sleep` processes in your account. Record PID, PPID and state while alive, then check after `wait`. Explain which observations establish process identity and which only identify the executable.

Inspect the fixture files with `find . -maxdepth 3 -type f` before editing.

**Suggested sequence:** Record `uname -r` and `ps` headings first. Start the two processes with `&`, capture each `$!` immediately, inspect before `wait`, then compare after both exit.

**Boundaries and editable files:** Only signal your own PID. Do not install packages or alter the shared server. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Run once normally and once with `sleep 1`; check both while live and after exit. A missed snapshot does not prove the process never existed.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab1` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> A script starts `sleep 1` twice in the background. Predict how many PIDs can be captured and whether `ps` must show both after two seconds.

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab1` and leave the workspace for review; `oslab clean lab1` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: A process is an execution instance
2. Observation: inspect `$!` and `ps`
3. Partial approach: shorten duration and collect evidence promptly.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [Week 1 notes](../../lectures/notes/week01-introduction-to-os.md) and `man ps`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

APT package management in a disposable VM; hypervisor detection; compare `top` and `ps`. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
