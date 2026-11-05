# Lab 7 — Bash Arguments and Exit Status: individual report

Copy this template to `lab7/README.md` in your own course repository. Follow [the instructions](lab7-instruction.md). Your prediction, debrief and checkpoint answers are already saved by `oslab`; do not copy them here. The marks come from those records and your evidence files; this report is your own record of the lab.

- Student name/ID:
- Ubuntu username:
- My values (`oslab values lab7`): file1 = , file2 =
- Files: `count_words.sh`, `evidence/normal.txt`, `evidence/edge.txt`

## What I Did

| Step | My line of `count_words.sh` or command | What it does |
|---|---|---|
| The loop over the arguments | | |
| The test for a missing or non-regular file | | |
| The call to `wc` with `--` | | |
| The line that keeps the final status | | |

## What My Tests Show

| Test | Claim | A result that would contradict it | What I saw | What remains unproven |
|---|---|---|---|---|
| both files (normal.txt) | | | | |
| a missing file first, then a valid file (edge.txt) | | | | |
| the leading-dash name from inside `input/` | | | | |

## Explanation

`oslab debrief lab7` records which prediction answers you confirmed and which you corrected. Here, in 3–5 sentences for yourself:

- Why is a file name with a space one argument with `"$@"` and several pieces with `$@`?
- Why does a leading dash need `--`, and what would `wc` do without it?
- Why keep your own `status` variable instead of using the status of the last command?

## What My Tests Do Not Prove

One or two sentences. Name a file name your script might still not handle.

## Plus / Challenge (only if you did them)

Your answers from `evidence/plus.txt`.

## AI Note (optional)

One suggestion an AI tool gave you and the test you used to check it.
