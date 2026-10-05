# OS Lab 11 — Regular-file disk images and filesystem evidence (bonus) (optional bonus)

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account for image files; FUSE optional |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | Lab 2 and storage lecture |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Distinguish file size from allocated blocks.
2. Create and inspect a regular image.
3. Explain filesystem metadata from safe evidence.

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

Log in with your own account. Run `oslab doctor`, then `oslab start lab11`; `oslab status lab11` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab11`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
truncate -s 32M "$HOME/oslab-work/lab11/images/scratch.img"; ls -lh "$HOME/oslab-work/lab11/images/scratch.img"; du -h "$HOME/oslab-work/lab11/images/scratch.img"
```

Before continuing: Why can apparent size and allocated space differ?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** For a sparse 32 MiB image, will `du` necessarily show 32 MiB? Why?

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab11` after `oslab start lab11`. **Goal:** Create a regular 32 MiB sparse image under `images/`; compare `ls -l`, `du`, and `stat`. If `mkfs.ext4` and `dumpe2fs` are installed, format only that regular file and inspect its superblock. Explain how formatting changes allocation.

Inspect the fixture files with `find . -maxdepth 3 -type f` before editing.

**Suggested sequence:** Confirm the target path is a regular file under `images/`. Compare byte length and allocated blocks on a sparse image. If formatting tools exist, run them only on that checked file and inspect metadata again.

**Boundaries and editable files:** Never name `/dev/*` or a block device as a target. Check `test -f` and `readlink -f` before formatting. No sudo or loop mounting. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Inspect empty sparse image and formatted image; compare apparent and allocated sizes. FUSE mounting is optional and requires local capability checks.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab11` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> A second image is created with `dd if=/dev/zero ...` and fully written. Predict `du` relative to a sparse image of equal apparent length.

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab11` and leave the workspace for review; `oslab clean lab11` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: Check file type
2. Observation: compare `stat -c '%s %b %B'`
3. Partial approach: use `dumpe2fs -h` only after formatting.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [Week 12 notes](../../lectures/notes/week12-file-systems.md), `man du`, and `man mkfs.ext4`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

FUSE mount with `fuse2fs` only if available and permitted; resize and e2fsck on an unmounted regular image; custom diagnostic script. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
