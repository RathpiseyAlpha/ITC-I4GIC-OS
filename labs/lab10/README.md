# Lab 10 — Backups, Archiving and Scheduling: individual report

Copy this template to `lab10/README.md` in your own course repository. Follow [the instructions](lab10-instruction.md). Your prediction, debrief and checkpoint answers are already saved by `oslab`; do not copy them here. The marks come from those records and your evidence files; this report is your own record of the lab.

- Student name/ID:
- Ubuntu username and environment:
- My values (`oslab values lab10`): keep = , name =
- Files: `backup.sh`, `evidence/restore.txt`, `evidence/automation.txt`

## What I Did

| Step | My command or line | What it showed |
|---|---|---|
| Archive and restore: the `tar` options I used and why `-C` | | |
| The retention: the lines I wrote at the `TODO` | | |
| How my script recognises "an archive made by this script" | | |
| The run under `env -i` from another folder | | |

## What My Tests Show

| Test | Claim | A result that would contradict it | What I saw | What remains unproven |
|---|---|---|---|---|
| restore: member list and `cmp` (restore.txt) | | | | |
| several runs: how many archives remain | | | | |
| `keep-me.txt` and the look-alike file survive | | | | |
| restricted environment (automation.txt) | | | | |

## Explanation

`oslab debrief lab10` records which prediction answers you confirmed and which you corrected. Here, in 3–5 sentences for yourself:

- What is the difference between archiving and compressing? How did you establish that the archive can be restored?
- What stopped the retention from deleting files that are not yours?
- Which two assumptions would you check before you trust the script under cron?

## What My Tests Do Not Prove

One or two sentences. Real scheduling, a source that changes during the backup, or a clock that moves: which did you not test?

## Plus / Challenge (only if you did them)

Your answers from `evidence/plus.txt`. If cron was not available, say so here.

## AI Note (optional)

One suggestion an AI tool gave you and the test you used to check it.
