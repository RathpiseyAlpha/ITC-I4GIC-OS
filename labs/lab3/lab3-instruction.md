# OS Lab 3 — Links and user-local libraries

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account; disposable VM only for GRUB extension |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | Lab 2, basic C compiler for library extension |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Distinguish inode sharing from path indirection.
2. Repair a broken symbolic link.
3. Predict a link's response to target replacement.

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

Log in with your own account. Run `oslab doctor`, then `oslab start lab3`; `oslab status lab3` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab3`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
cd "$HOME/oslab-work/lab3/links"; ln source.txt hard.txt; ln -s source.txt soft.txt; ls -li source.txt hard.txt soft.txt; readlink soft.txt
```

Before continuing: Which links name the same inode, and which stores a path?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** If `source.txt` is renamed, which link still reads the original bytes? Explain.

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab3` after `oslab start lab3`. **Goal:** Inspect `source.txt`, a hard link and a symlink in your own workspace. Rename the source, observe both links, then repair the symlink without replacing the hard link. Record inode and path evidence.

Inspect the fixture files with `find . -maxdepth 3 -type f` before editing.

**Suggested sequence:** First create a hard link and symlink to `source.txt`. Record `ls -li` and `readlink`. Rename only the source, test both links, then repair the symlink target relative to its own directory.

**Boundaries and editable files:** Keep changes inside the lab workspace; no shared-server GRUB changes, `ldconfig`, or system library registration. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Test before and after rename and after repair; also test a deliberately missing symlink target. Inode equality establishes hard-link identity on one filesystem.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab3` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> A symlink points to `../source.txt` from inside `links/`. Predict where it resolves and explain whether it works.

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab3` and leave the workspace for review; `oslab clean lab3` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: Compare inodes
2. Observation: inspect `readlink`
3. Partial approach: draw the path relative to the symlink's directory.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [Lab 3 visual guide](guides/slides.html), `man ln`, and `man readlink`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

Wildcard selection; build a shared object with `gcc -fPIC -shared` and use a user-local loader path; GRUB observation and recovery only in a snapshot-backed disposable VM with instructor supervision. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
