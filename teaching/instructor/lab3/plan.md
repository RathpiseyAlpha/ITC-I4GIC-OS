# Instructor plan — OS Lab 3: Wildcards and Links

**Public repository notice:** this plan and its answers are public. Personal checkpoint names reduce direct copying; they do not make the answers private. Observe the individual checkpoint in class and keep any additional graded variants private.

## Objectives and scope

Students expand wildcard patterns, compare hard-link inode identity, and diagnose a symbolic link after a rename. The required experiment uses only ordinary-user files. GRUB and shared-library work remain [optional extensions](../../../labs/lab3/extensions.md).

Use the [student instruction](../../../labs/lab3/lab3-instruction.md) and [short report](../../../labs/lab3/README.md). The visual guide (62 slides, rebuilt 2026-11-05) follows the instruction, including the terminal prediction, checkpoint and debrief; if the two differ, the Markdown instruction governs. Slides 1 to 3 are the cover and opening question, 4 to 15 the concepts, 16 to 22 the lab overview and setup, 23 to 26 the guided example, 27 and 28 the prediction, 29 to 35 Task 2, 36 to 41 the tests with Plus and Challenge, 42 to 45 the checkpoint, 46 to 52 debrief, submission, grading and mistakes, 53 to 60 GRUB and shared libraries, and 61 and 62 the takeaways.

## Before class: make collection work

1. Update the installed helper **and the website's matching source** from this revision using the [server runbook](../../../server/RUNBOOK.md). Review and back up the current installation first. Restart the website service after updating it; no live deployment is performed by editing these files.
2. In an ordinary test account, verify `oslab doctor` says **class inbox: connected**. Confirm `oslab predict lab3` asks the rename questions, instead of saying the lab uses paper. Check that the website service account can read the inbox; see the runbook's `--inbox-reader` instructions.
3. Open the board before predictions and keep it running during class. Use your actual private account roster:

   ```bash
   sudo oslab-teach board lab3 --roster /secure/path/students.txt --watch 20
   ```

4. Give students their server/account and personal Git repository paths. Verify `ln`, `readlink`, Bash and Python are available. Students need no sudo, compiler or VM for the core.
5. Test the class release with a disposable account before class. A release stays open; do not silently replace an existing release or erase students' first answers. Use a separate test inbox/release directory when rehearsing.

## Exact 120-minute Timetable

| Minutes | Teacher action and evidence |
|---|---|
| 0–10 | Verify individual accounts, inbox connection and lab root |
| 10–25 | Demonstrate wildcard expansion, inode numbers and a relative symbolic target |
| 25–35 | Students run `oslab predict lab3`; check board for missing answers before Task 2 |
| 35–70 | Students create links, rename, repair and recreate the old filename |
| 70–85 | Students run `oslab check lab3`; use TRY reasons to target help |
| 85–100 | Release checkpoint; students answer and complete their separate link task alone |
| 100–110 | Students run debrief and complete the short report; discuss misconceptions |
| 110–120 | Verify three evidence files and report copied to the personal Git repository |

## Expected results and public model

Key: the two unquoted patterns each print `practice/report1.txt` and `practice/report2.txt`; the quoted pattern prints `practice/*.txt` literally. Capture this before the demo links add more `.txt` filenames.

In `links/`, `source.txt` starts with `version 1`. After the rename, `hard.txt` and `renamed.txt` still name the same inode. `soft.txt` stores `source.txt`, so it is dangling until repaired. A new `source.txt` containing `version 2` has a different inode and does not change the original data.

Public model for the repair (only after inspecting the owned link): `rm -- soft.txt`, then `ln -s renamed.txt soft.txt`. Never repair by replacing `hard.txt` or renaming the original back. Accept other targets that resolve to `renamed.txt`.

## Collection and checkpoint

- `oslab predict lab3` saves the first prediction and sends it to the class inbox. The student does not upload a prediction file. Wrong initial answers do not lose accuracy points.
- `oslab check lab3` sends **four core milestones**, including actual inode identity and symbolic target checks. Its records include hashes of evidence files; it does not establish that an earlier rename/failure happened. Review the labelled transcript for that.
- At minute 85, release the checkpoint:

  ```bash
  sudo oslab-teach release lab3
  ```

- Students run `oslab checkpoint lab3`. Each gets a separate `checkpoint-WORD/` folder and a named data file; `shortcut.txt` is described as storing an incorrect `../NAME.txt` target. They submit two path answers and one explanation, then create the small repaired example printed by the helper. Their next check adds a fifth milestone. This task is independent of unfinished `links/` work.
- Key: the described shortcut fails because `../NAME.txt` refers to a nonexistent file in the **lab root**. Use `NAME.txt` to reach a data file beside the link. Relative targets start from the **link's directory**, not the shell's current directory. `readlink shortcut.txt` and `cat shortcut.txt` verify the stored target and result.
- `oslab debrief lab3` collects the corrected prediction answers without replacing the original. Records are visible on the board and in the website's **view and mark** screen.
- Export one class CSV instead of opening each student's prediction file:

  ```bash
  sudo oslab-teach export lab3 --roster /secure/path/students.txt > lab3.csv
  ```

The CSV checkpoint automatic points are out of 2: one for the marked answers (0.5 if at least half correct), one for the working repaired link. It includes the explanation sentence for a quick human review. A practice checkpoint is flagged as practice and does not earn a class checkpoint suggestion.

The first-seen record/duplicate flag supports review; this is not tamper-proof assessment. The board must be open before collection to retain first-seen evidence. If students use a practice inbox, their work does not reach you.

## Pre-lab, hints, Plus and Challenge

Same style as the pilot labs. None of it changes the timetable or the 10 points.

- `oslab prelab lab3` asks three multiple-choice questions (who expands `*`, hard-link inode, what a symbolic link stores). Its result shows on the board's pre-lab column. Ask students to run it the evening before.
- `oslab hint lab3 1`, `2`, `3` give the ladder: compare inodes; read the stored target; the target is resolved from the link's folder. Hint use appears on the board.
- Plus (bracket wildcards `[12]` and `[!1]`) and Challenge (a chain of two symbolic links in `extra/`, `readlink` versus `readlink -f`) are optional. They write only to `extra/` and `evidence/plus.txt`, so `oslab check lab3` is unaffected. Key: `report[12].txt` prints `report1.txt` and `report2.txt`; `report[!1].*` prints only `report2.txt`. After renaming `end.txt`, `cat start.txt` fails because the chain ends in a missing name.

## Topic rubric (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Wildcard result, hard-link identity and repaired symbolic target: 1 point each | 3 |
| Labelled rename/failure/repair evidence and recreated-name comparison: 1 point each | 2 |
| Original prediction saved, followed by debrief and an evidence-based correction: 1 point each | 2 |
| Individual checkpoint: path answers and working repaired link: 1 point each | 2 |
| Complete short report and three evidence files submitted | 1 |

## Quick marking sequence

1. Open **view and mark**. The website suggests points from the four milestones, original prediction/debrief, checkpoint answers/task and required submitted files. Suggestions are provisional; saving remains the teacher's decision.
2. Review `evidence/links.txt`: BEFORE RENAME must show version 1 through both links; AFTER RENAME must show the dangling target and error; AFTER REPAIR must show the new target and successful read. Add the remaining evidence point after this review. Read `replacement.txt` only if the new-source milestone or report is inconsistent.
3. Read the short report's wildcard explanation, original versus new inode comparison and one-sentence correction. Check the checkpoint sentence identifies the link's directory. Correct suggestions if the explanation contradicts the files or is missing.
4. Save the five rubric rows. Use the existing publish-marks control when ready to show marks. Do not ask students for a second copy of terminal answers, long essays, or command screenshots.

Only the README and `wildcards.txt`, `links.txt`, `replacement.txt` go in the personal course submission. The terminal answers go to the inbox. Keep practical work until grading ends; cleanup is optional. Extensions do not affect the 10 core points.

## Common problems and support

- `File exists`: inspect the previous entry rather than repeating `ln` or resetting all work.
- More wildcard matches than expected: demo links were created before the wildcard record. Inspect the practice directory, preserve work, and record the original three-file example in a fresh practice attempt; do not fabricate output.
- Hard link prints version 2: the student wrote through the original inode rather than creating a new name after renaming. Compare the actual inode numbers.
- Symbolic link still fails: read its target from the link's own directory. Draw the two path components before supplying the repair.
- Missing prediction/checkpoint on the board: inspect `oslab doctor` and the installed helper version before telling students to submit again. The first prediction is deliberately retained.

The local lifecycle and walkthrough suites exercise disposable workspaces; live multi-account inbox ownership, website permissions and deployment still need the instructor's server checks.
