# Lab 4 — Redirection and Pipelines: individual report

Follow the [instruction](lab4-instruction.md). Copy this template into your own `lab4/README.md`. No script is required. Prediction/debrief/checkpoint answers stay in `oslab` records.

- Name / student ID:
- Linux account:
- Personal status and other word:

## Commands I Used

Save your actual commands, one per line, in `evidence/commands.txt`. Do not execute that file as a script.

| Stage | My command | Input received | Output produced |
|---|---|---|---|
| Select exact first field | | | |
| Extract field 2 | | | |
| Count selected records | | | |
| Save stdout and stderr separately | | | |
| Save exit status immediately | | | |

## What My Tests Show

| Test | Expected | Observed | Mistake it would catch |
|---|---|---|---|
| Original records | 3 exact matches | | |
| No match | 0 records | | |
| One added match plus a look-alike | 4 records | | |
| Missing input | empty stdout, diagnostic on stderr, nonzero status | | |

## Explain the Commands

1. Why does the comma in `grep '^WORD,'` matter?
2. Why does `wc -l` count records here, rather than add quantities?
3. Where did you use `>>`, and what would `>` do instead?
4. What does `tee` do that `>` alone does not?
5. Why must `echo $?` immediately follow the command being checked?
6. Why can `cat missing-file | wc -l` report pipeline status 0?

## Limits and Evidence

These commands assume simple comma-separated text without quoted commas. Saved results describe one run; they do not prove every future input works or who typed a command.

Check the submission tree in the instruction: include `checkpoint.txt` and all required evidence files, including the empty `stdout.txt`. No `report.sh` is required.

## Optional Work / AI Note

Record any Plus/Challenge observations and one suggestion you tested, if applicable.
