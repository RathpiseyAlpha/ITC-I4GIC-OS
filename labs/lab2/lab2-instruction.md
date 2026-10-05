# OS Lab 2 — Linux Navigation & File Management (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Lab 1 file commands and quoting |
| Required tools | `pwd`, `ls`, `mkdir`, `cp`, `mv`, `find`, `cmp` |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** As Alex at TechCorp, organize incoming quarterly reports in a small company directory tree. Your work should still be understandable when you change the current directory.

## Lab Objectives

After the required core, you should be able to:

1. Navigate with absolute and relative paths and explain `.` and `..`.
2. Build a company directory tree and move/copy reports while preserving their contents.
3. Diagnose a path mistake and verify the final organization with directory listings.

**Extension objectives:** Explore read-only system directories and practise size/time sorting and wildcard directory audits. These retain the original lab's wider topics; they are not required to finish the two-hour core.

## Task Overview and 120-minute Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Introduction, objectives and setup |
| 10–25 | Guided example: commands and observations |
| 25–35 | Written prediction; optional five-minute peer comparison |
| 35–70 | Numbered individual investigation tasks; AI optional |
| 70–85 | Normal and edge tests; instructor feedback |
| 85–100 | Individual changed-case checkpoint; no AI or peers |
| 100–110 | Correction and conceptual explanation |
| 110–120 | Cleanup and submission |

Core retains the original sequence: navigation warm-up → company directory structure → absolute/relative paths → organization. Read-only system exploration and advanced listing remain optional.

## Lab Setup (0–10 minutes)

1. Log in to the Ubuntu server using **your own account**. All commands below run as that ordinary user in Bash. Use only your own files and processes.
2. Check the helper. If it is unavailable, follow [the local setup guide](../SETUP.md) to define `oslab` from your cloned course repository; it uses the same fixtures.

   ```bash
   whoami
   command -v oslab
   oslab doctor
   ```

3. Start the lab and **enter its directory**. `oslab start` preserves existing work and does not change the current directory. If resuming, inspect existing files before running commands that write to them.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab2
   cd "$OSLAB_WORKSPACE/lab2"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab2/
   ├── .oslab-managed.json
   ├── incoming/
   │   ├── quarter 1.txt
   │   └── quarter 2.txt
   ├── reports/
   │   └── README.txt
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Tasks 1–2 — Navigation Warm-Up: Guided Example (10–25)

1. Identify where you are, then list names with and without metadata.

   ```bash
   pwd
   ls
   ls -la
   ```

   An absolute path begins at `/`; a relative path begins at the current directory. Your home is one directory on the shared server, not the whole filesystem.

2. Build a separate practice folder so you do not reveal the report-organizing solution.

   ```bash
   mkdir -p practice/notes
   printf 'orientation\n' > 'practice/welcome note.txt'
   cd practice
   pwd
   ls -l
   cp -- 'welcome note.txt' notes/
   cat 'notes/welcome note.txt'
   cd ..
   ```

   The quotes keep the space inside one filename. `--` separates options from operands for commands that support it. `cd ..` moves to the parent; verify with `pwd` rather than assuming.

3. Compare a relative and absolute reference to the same file.

   ```bash
   cat 'practice/welcome note.txt'
   cat "$OSLAB_WORKSPACE/lab2/practice/welcome note.txt"
   ```

   **Observe:** Which command relies on your current directory? Does copying a file remove its original? Read `man cp` or `man mv` if uncertain.

## Prediction (25–35)

Write before moving reports: **From `incoming/`, what does `../reports/` mean? If the current directory instead becomes the workspace root, does the same relative path still mean the same destination?** Keep your initial answer. The five-minute peer comparison is optional.

## Task 3 — Build the Company Directory Structure (35–45)

1. Return explicitly to the workspace root and inspect incoming content.

   ```bash
   cd "$OSLAB_WORKSPACE/lab2"
   cat 'incoming/quarter 1.txt'
   cat 'incoming/quarter 2.txt'
   ```

   Expected values are `revenue,120` and `revenue,130`. Save these as your content-preservation expectations.

2. Create the owned company tree. This adapts the original company's wider tree to one coherent report workflow.

   ```bash
   mkdir -p TechCorp/Finance/archive TechCorp/Engineering TechCorp/HR
   find TechCorp -maxdepth 3 -type d
   ```

   ```text
   TechCorp/
   ├── Engineering/
   ├── Finance/
   │   └── archive/
   └── HR/
   ```

## Tasks 4–5 — Navigate and Organize Reports (45–70)

1. Enter `incoming/`. Move the first quarterly file to the supplied `reports/` folder using the relative destination you predicted. Write the command yourself; inspect `pwd` before executing it.
2. Return to the workspace root. Move the second file to the same destination, this time using absolute paths built from `$OSLAB_WORKSPACE`. Explain why the two commands need different path expressions.
3. Copy both organized files into `TechCorp/Finance/`. Keep the original organized reports; Finance needs copies, not another move. Copy the first Finance report into `TechCorp/Finance/archive/` as `q1-original.txt`.
4. From `TechCorp/HR/`, construct a **relative** path to Finance's first report and read it. Then read the same file with an absolute path. Record both commands in `evidence/paths.txt`.
5. Inspect the result:

   ```bash
   cd "$OSLAB_WORKSPACE/lab2"
   find incoming reports TechCorp -maxdepth 4 -type f | tee evidence/tree.txt
   oslab check lab2
   ```

   The public check only tests report presence. You must still verify content and explain paths yourself.

**Complete when:** both filenames exist under `reports/`, Finance has copies, the archive holds the first report, and you can reach a report from HR by both path types.

**Hints:** (1) draw current and destination folders; (2) count parent steps with `pwd`/`find`; (3) from HR, begin by returning to the shared `TechCorp` parent, then entering Finance.

## Task 6 — Directory Audit and Tests (70–85)

1. Verify file contents and that Finance's copies match the organized originals.

   ```bash
   cmp -- 'reports/quarter 1.txt' 'TechCorp/Finance/quarter 1.txt'
   cmp -- 'reports/quarter 2.txt' 'TechCorp/Finance/quarter 2.txt'
   ls -l reports TechCorp/Finance
   ```

   `cmp` returns zero when contents match. A name appearing in `ls` does not prove the bytes match.

2. Test one deliberately incorrect path from HR and record the error. Correct it without moving files again. Save the command, current directory and corrected path in `evidence/paths.txt`.
3. Save the final tree/listing in `evidence/tree.txt`. Record normal content preservation and the changed-directory failure as your two selected tests.

**Troubleshooting:** A `No such file` message can mean wrong current directory, spelling, missing quotes, or a source already moved. Check `pwd`, then `ls` the parent. Do not reset all work to solve one path error. See [the Lab 2 guide](guides/slides.html), `man mv`, and `man find`.


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> A report is now at `TechCorp/Finance/quarter 1.txt` and your current directory is `TechCorp/HR`. A command tries `cat "Finance/quarter 1.txt"`. Identify the fault and give a working relative path.

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) Why can a correct filename still produce a path error? (b) How did you establish content preservation? (c) What evidence would show you moved instead of copied a report?

## Cleanup and Final Submission (110–120 minutes)

No background process or cron job is created. Leave the owned tree for review; do not remove reports before saving evidence.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-se-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab2/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- evidence/paths.txt evidence/tree.txt "$SUBMISSION_REPO/lab2/evidence/"
   ```

   ```text
   lab2/
   ├── README.md
   └── evidence/
       ├── paths.txt   # current directory, two valid paths and one corrected error
       └── tree.txt    # organized report and company tree plus content checks
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct directory/report organization and preserved contents (objectives 1–3) | 3 |
| Content comparison and changed-current-directory test | 2 |
| Explain absolute/relative paths and copy versus move; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
