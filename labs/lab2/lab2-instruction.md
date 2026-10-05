# OS Lab 2 — Navigation and file placement

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | Lab 1 shell navigation |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Use absolute and relative paths correctly.
2. Move two files without losing their names.
3. Diagnose a path error.

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

Log in with your own account. Run `oslab doctor`, then `oslab start lab2`; `oslab status lab2` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab2`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
pwd; mkdir -p practice/reports; printf 'a\n' > 'practice/quarter 1.txt'; mv -- 'practice/quarter 1.txt' practice/reports/; find practice -maxdepth 2 -type f
```

Before continuing: How does the destination change if the current directory changes?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** From the fixture's `incoming` directory, where would `mv 'quarter 1.txt' ../reports/` place the file? Explain `..`.

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab2` after `oslab start lab2`. **Goal:** The two quarterly files are misplaced in `incoming`. Move them to `reports` preserving names; show one absolute and one relative path that reach a report from different working directories.

Inspect the fixture files with `find . -maxdepth 3 -type f` before editing.

**Suggested sequence:** Run `pwd` and `find . -maxdepth 2 -type f` before moving. Write the intended source and destination paths on paper, use `mv --`, then inspect both directories.

**Boundaries and editable files:** Edit only your lab2 workspace. Quoted names contain spaces; do not overwrite a report without checking. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Check both filenames and contents; try from the workspace root and `incoming`. A path that works only from one directory is not generally correct.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab2` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> Current directory becomes `reports`. Explain why `cat incoming/'quarter 1.txt'` fails and give a working relative path.

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab2` and leave the workspace for review; `oslab clean lab2` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: Identify current directory
2. Observation: use `pwd` and `find`
3. Partial approach: trace each path component before moving.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [Lab 2 visual guide](guides/slides.html) and `man mv`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

Company directory tree, wildcards and directory audit from the original lab. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
