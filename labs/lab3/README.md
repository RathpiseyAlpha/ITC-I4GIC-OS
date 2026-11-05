# Lab 3 — Wildcards and Links: short report

Copy this template to `lab3/README.md` in your personal course repository. Replace the blanks with your observations. Follow [the instructions](lab3-instruction.md).

- Student name/ID:
- Linux username and environment:
- `oslab status lab3` shows prediction, checkpoint and debrief saved: yes/no (explain anything missing).

Prediction and checkpoint answers are submitted through `oslab`; do not rewrite them here.

## 1. Wildcards

Evidence: `evidence/wildcards.txt`

- Names printed by `practice/*.txt` before the demo links were created:
- Does `practice/report?.txt` print the same names?
- Why does the quoted `'practice/*.txt'` print a literal pattern?

## 2. Rename and repair

Evidence: `evidence/links.txt`, with BEFORE RENAME, AFTER RENAME and AFTER REPAIR sections.

- After the rename, before repair: stored target of `soft.txt` = ___; missing filename = ___.
- After repair: stored target = ___; contents read through the link = ___.
- Why can `hard.txt` still read the original after the rename? One sentence using the inode observation:

## 3. New file using the old name

Evidence: `evidence/replacement.txt`

| Name | Your inode number | Contents |
|---|---|---|
| `source.txt` (new file) | | |
| `hard.txt` (original file) | | |

Why did the new `source.txt` not change what `hard.txt` reads? One sentence:

My original prediction was **confirmed / corrected** because this observation showed ___ .

## Optional AI note

If used: one suggestion and the command/result you used to check it. Otherwise remove this section.
