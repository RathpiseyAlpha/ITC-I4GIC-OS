# OS Lab 6 — Permissions and access decisions

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | octal permissions, Lab 2 paths |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Interpret file and directory permissions.
2. Set least-privilege access in an owned tree.
3. Diagnose a traversal failure.

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

Log in with your own account. Run `oslab doctor`, then `oslab start lab6`; `oslab status lab6` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab6`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
mkdir -p "$HOME/oslab-work/lab6/demo"; printf 'x\n' > "$HOME/oslab-work/lab6/demo/a"; chmod 700 "$HOME/oslab-work/lab6/demo"; stat -c '%A %n' "$HOME/oslab-work/lab6/demo"
```

Before continuing: Which permission controls entering a directory?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** If a file is mode 644 inside a directory mode 700, can another user read it? Explain each path component.

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab6` after `oslab start lab6`. **Goal:** Inspect `private/record.txt` and `shared/notice.txt`; set and justify modes for owner-only record edits and read-only notice in your owned tree. Use `namei -l` if available to explain traversal.

Inspect the fixture files with `find . -maxdepth 3 -type f` before editing.

**Suggested sequence:** Use `stat -c '%A %a %n'` on directories and files before changing modes. Decide who needs read, write and traversal, change one mode, then inspect the whole path with `namei -l` if available.

**Boundaries and editable files:** Do not create accounts/groups, change another user's files, open home directories broadly, or use SUID. Administrator-prepared identities are an optional extension. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Test owner read/write and attempted execute, then reason about a peer using path permissions. Actual multi-user check requires instructor preparation.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab6` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> Directory is 711 and file 600. A peer knows the filename. Can they read it? Which mode is decisive?

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab6` and leave the workspace for review; `oslab clean lab6` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: Check every parent directory
2. Observation: use `stat`/`namei`
3. Partial approach: change only one permission at a time.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [Lab 6 visual guide](guides/slides.html) and `man chmod`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

ACLs, groups, sticky bit, and narrowly prepared two-account testing on a disposable VM or administrator-approved directory. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
