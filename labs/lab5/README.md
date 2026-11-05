# Lab 5 — Threads and Completion: individual report

Copy this template to `lab5/README.md` in your own course repository. Follow [the instructions](lab5-instruction.md). Your prediction, debrief and checkpoint answers are already saved by `oslab`; do not copy them here. The marks come from those records and your evidence files; this report is your own record of the lab.

- Student name/ID:
- Ubuntu username and environment:
- My values (`oslab values lab5`): id_a = , id_b = , steps_a = , steps_b =
- Files: `two_workers.c`, `evidence/normal.txt`, `evidence/changed.txt`

## What I Did

| Step | My line or command | What it printed |
|---|---|---|
| The program before I added any join | | |
| The join of worker A and the test of its return code | | |
| The join of worker B and the test of its return code | | |
| The report line, and where it is in the program | | |
| The changed case (A 0 steps, B 1 step): my prediction and the result | | |

## Explanation

`oslab debrief lab5` records which prediction answers you confirmed and which you corrected. Here, in 3–5 sentences for yourself:

- What makes it safe for main to read `a.result` after the join?
- Why is the 20 ms delay in each step not a lock?
- What would change if both workers updated one shared field? Use `threads/trace.csv` as your example.

## What My Tests Do Not Prove

One or two sentences. A run that passes three times: what can it still hide?

## Plus / Challenge (only if you did them)

Your answers from `evidence/plus.txt`.

## AI Note (optional)

One suggestion an AI tool gave you and the test you used to check it.
