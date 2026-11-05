# Lab 3 — Wildcards, Hard Links and Symbolic Links: individual report

Copy this template to `lab3/README.md` in your own course repository. Follow [the instructions](lab3-instruction.md). Your prediction, debrief and checkpoint answers are already saved by `oslab`; do not copy them here. The marks come from those records and your evidence files; this report is your own record of the lab.

- Student name/ID:
- Ubuntu username:
- My values (`oslab values lab3`): name = , tag = , v1 = , v2 =
- Files: `evidence/wildcards.txt`, `evidence/links.txt`, `evidence/replacement.txt`, `evidence/checkpoint.txt`

## What I Saw

| State | What `cat` printed for the hard link | What `cat` printed for the symbolic link | What `readlink` printed |
|---|---|---|---|
| Before the rename | | | |
| After the rename, before the repair | | | |
| After a new file took the old name | | | |
| After my repair | | | |

My repair (the two commands I wrote):

## Explanation

`oslab debrief lab3` records which prediction answers you confirmed and which you corrected. Here, in 3–5 sentences for yourself: why did the symbolic link read `version <v2>` after the new file took the old name, while the hard link still read `version <v1>`? Use your own inode numbers from `evidence/replacement.txt`.

## What My Tests Do Not Prove

One or two sentences. Think about what `cat` shows and what only `ls -li` shows.

## Plus / Challenge (only if you did them)

Your bracket-pattern answer, or your link counts.

## AI Note (optional)

One suggestion an AI tool gave you and the test you used to check it.
