# Lab 9 — Deadlock and Lock Ordering: individual report

Copy this template to `lab9/README.md` in your own course repository. Follow [the instructions](lab9-instruction.md). Your prediction, debrief and checkpoint answers are already saved by `oslab`; do not copy them here. The marks come from those records and your evidence files; this report is your own record of the lab.

- Student name/ID:
- Ubuntu username:
- My values (`oslab values lab9`): res1 = , res2 = , a_first =
- Files: `vault/worker.sh` (as `worker.sh`), `evidence/opposite.txt`, `evidence/ordered.txt`

## What I Did

| Step | My line or command | What happened |
|---|---|---|
| The opposite run: statuses of A and B | | |
| The line of `worker.sh` that I changed for the global order | | |
| The ordered run: statuses of A and B | | |
| The check that no worker or lock was left | | |

## The Circle

Draw (in text or as a picture in `images/`) what each worker held and requested at the barrier in the opposite run.

| Worker | Holds | Requests | Waits for |
|---|---|---|---|
| A | | | |
| B | | | |

## Explanation

`oslab debrief lab9` records which prediction answers you confirmed and which you corrected. Here, in 3–5 sentences for yourself:

- At least one worker ended with status 5 in the opposite run. What happened to the other worker after that, and why?
- Why does one global order remove the circular wait?
- Why do the timeouts stay in the script after the repair?

## What My Tests Do Not Prove

One or two sentences. The ordering fixes this model with two locks. What is not shown for a larger system?

## Plus / Challenge (only if you did them)

Your answers from `evidence/plus.txt`.

## AI Note (optional)

One suggestion an AI tool gave you and the test you used to check it.
