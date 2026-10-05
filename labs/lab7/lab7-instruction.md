# OS Lab 7 — Bash arguments and safe paths

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | shared Ubuntu account |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | Lab 2, Bash basics |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

1. Quote arguments containing spaces.
2. Handle a filename beginning with `-`.
3. Explain how script arguments map to files.

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

Log in with your own account. Run `oslab doctor`, then `oslab start lab7`; `oslab status lab7` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/lab7`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
bash -c 'printf "argc=%s\n" "$#"; for item in "$@"; do printf "<%s>\n" "$item"; done' _ 'one file.txt' '-dash.txt'
```

Before continuing: What changes if `$@` is unquoted?

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** If a script receives `one file.txt` as one argument, what happens with `for x in $@`? Why?

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/lab7` after `oslab start lab7`. **Goal:** Build a Bash script that prints a labeled word count for each file argument, including `input/one file.txt` and `input/-dash.txt`. Reject missing inputs with a useful exit status. Use `--` where a utility parses filenames as options.

Use `count_words.sh` as a starting skeleton. Try `bash count_words.sh 'input/one file.txt' 'input/-dash.txt'`.

**Suggested sequence:** Print each argument inside angle brackets before counting words. Loop over `"$@"`, check that each path is a regular file, and pass it after `--` to `wc`.

**Boundaries and editable files:** Edit scripts and fixture copies in your workspace; avoid `eval`, unquoted expansion and SUID helpers. Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

Test one file, both files, a missing file, and a path with spaces. Inspect exit status and output labels.

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check lab7` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> A filename is `-dash.txt` in the current directory. Explain why `wc -w -dash.txt` may fail and give a safe invocation.

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status lab7` and leave the workspace for review; `oslab clean lab7` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: Print argument boundaries
2. Observation: use `"$@"`
3. Partial approach: test `--` and `./` for leading dash names.

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** [Bash manual](https://www.gnu.org/software/bash/manual/bash.html) and `man wc`. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

PATH configuration, message scripts, narrowly prepared shared directories; cross-user automation only with instructor setup. See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
