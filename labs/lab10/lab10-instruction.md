# OS Lab 10 — Backup retention and scoped scheduling

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account; per-user cron if available |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | Bash, tar, paths |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Create and verify a backup archive.
2. Retain a bounded number of owned archives.
3. Diagnose cron's restricted environment.

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

Log in with your own account. Run `oslab doctor`, then `oslab start lab10`; `oslab status lab10` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab10`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
tar -czf "$HOME/oslab-work/lab10/test.tar.gz" -C "$HOME/oslab-work/lab10" project; tar -tzf "$HOME/oslab-work/lab10/test.tar.gz"
```

Before continuing: Does creating an archive prove it can restore the expected files?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** A cron entry uses `backup.sh` without an absolute path. Will it necessarily run if the command works interactively? Why?

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab10` after `oslab start lab10`. **Goal:** Build an idempotent backup script for the fixture `project/`, verify archive members and a restore into a new owned directory, then retain the newest three lab-owned archives. If user cron is available, run `lab10-cron install`, observe `cron.log` after the next minute, then run `lab10-cron remove`; the helper changes only its marked practice entry.

Use `backup.sh` as a starting skeleton; keep archives in an owned `backups/` directory. Use `lab10-cron status` to inspect the practice entry.

**Suggested sequence:** Create one archive, list its members, and restore it to a fresh owned directory before writing retention. Test retention with four archives. Check `lab10-cron status` before installation and after removal.

**Boundaries and editable files:** No dated graded jobs. Cron has five ordinary fields and no year field; a date entry recurs unless separately guarded/removed. Never use `crontab -r`. Use `TZ=Asia/Phnom_Penh` only after checking server cron timezone behavior. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Test two backups with changed content, restore, retention after four archives, and cron log within two minutes. If cron is unavailable, run script with `env -i HOME=... PATH=/usr/bin:/bin` and explain the fallback.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab10` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> A cron command uses `tar` but its script assumes current directory is `project`. Identify one robust correction.

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab10` and leave the workspace for review; `oslab clean lab10` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: Inspect archive members
2. Observation: restore to a temporary owned folder
3. Partial approach: record cron's PATH and HOME explicitly.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [crontab manual](https://man7.org/linux/man-pages/man5/crontab.5.html) and `man tar`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

Log rotation, health checks, and custom scheduled jobs; schedule dates only from instructor-supplied class date and timezone with a one-shot guard. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
