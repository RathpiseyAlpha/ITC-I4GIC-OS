# OS Lab 3 — Wildcards, Links, GRUB & Shared Libraries (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Lab 2 navigation; understanding of filenames and directories |
| Required tools | `ln`, `ls`, `readlink`, `stat`, `mv`; compiler only for library extension |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** Alex is maintaining TechCorp file references. A file is being renamed, and dependent references must still work. Wildcards and links form the core; boot recovery and custom libraries are separate extensions.

## Lab Objectives

After the required core, you should be able to:

1. Select files with a wildcard and explain shell expansion versus a literal name.
2. Create and inspect hard links and symbolic links using inode and target-path evidence.
3. Predict and diagnose the effects of renaming or replacing a link target.

**Extension objectives:** Build/load a user-local shared library and practise GRUB observation, configuration and recovery in a snapshot-backed disposable VM. These retain the original lab's wider topics; they are not required to finish the two-hour core.

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

Original Task 1 wildcards introduces selection; Task 2 links is the central investigation. Original Tasks 3–5 GRUB/shared-library work are optional and keep their specific environment requirements.

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
   oslab start lab3
   cd "$OSLAB_WORKSPACE/lab3"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab3/
   ├── .oslab-managed.json
   ├── links/
   │   ├── source.txt
   │   └── target-name.txt
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Task 1 — Wildcards: Guided Example (10–25)

1. Work in a separate practice folder and create three clearly different names.

   ```bash
   mkdir -p practice
   printf 'one\n' > practice/report1.txt
   printf 'two\n' > practice/report2.txt
   printf 'log\n' > practice/report.log
   ls practice
   ```

2. Inspect how the shell expands patterns before using them in a file operation.

   ```bash
   printf '<%s>\n' practice/*.txt
   printf '<%s>\n' practice/report?.txt
   printf '<%s>\n' 'practice/*.txt'
   ```

   The first two commands name two text files; quotes around the whole pattern leave a literal `*`. Brace expansion such as `{1,2}` generates words; it is not a filename wildcard test.

3. Introduce links without changing the investigation files.

   ```bash
   ln practice/report1.txt practice/hard-demo.txt
   ln -s report1.txt practice/soft-demo.txt
   ls -li practice/report1.txt practice/hard-demo.txt practice/soft-demo.txt
   readlink practice/soft-demo.txt
   ```

   A hard link names the same inode on one filesystem. A symbolic link stores a path, resolved relative to the link's directory when that path is relative. `ls -l` displays the stored target.

   **Observe:** Which inode numbers match? Why is `report1.txt` the appropriate relative target here instead of `practice/report1.txt`?

## Prediction (25–35)

Before renaming the investigation source, write: **After `source.txt` becomes `renamed.txt`, will a hard link still read the old bytes? Will a symbolic link storing `source.txt` still work? Explain each mechanism.** Optional peer comparison is five minutes; keep your own answer.

## Task 2 — Hard Links and Symbolic Links (35–70)

1. Enter the supplied link folder and create two references to the source.

   ```bash
   cd "$OSLAB_WORKSPACE/lab3/links"
   cat source.txt
   ln source.txt hard.txt
   ln -s source.txt soft.txt
   ls -li source.txt hard.txt soft.txt | tee ../evidence/links.txt
   ```

   If resuming and a destination already exists, inspect it rather than repeatedly running `ln` or overwriting it. Record the before-state in `../evidence/links.txt`.

2. Rename the original directory entry and inspect both references.

   ```bash
   mv -- source.txt renamed.txt
   cat hard.txt
   readlink soft.txt
   cat soft.txt 2>&1 | tee -a ../evidence/links.txt
   ```

   The final command is a deliberate failure case. Write what the error means before repairing anything.

3. Repair **only** `soft.txt` so it refers to the renamed file. Choose a relative target path yourself. Inspect the old link first; remove only that owned symbolic-link entry and recreate it with `ln -s`. Do not replace `hard.txt`.
4. Inspect inode identity and content after repair:

   ```bash
   {
     ls -li renamed.txt hard.txt soft.txt
     readlink soft.txt
     cat hard.txt soft.txt
   } | tee -a ../evidence/links.txt
   ```

5. Investigate a changed case: create a **new** `source.txt` containing `version 2`. Predict whether `hard.txt` will now read version 1 or version 2, then check it. Explain why reusing a filename does not reuse the original inode automatically.

   ```bash
   printf 'version 2\n' > source.txt
   { ls -li source.txt hard.txt; cat source.txt hard.txt; } | tee ../evidence/replacement.txt
   ```

**Complete when:** the hard link survives rename, the repaired symbolic link resolves correctly, and your changed-name test distinguishes filename from inode.

**Hints:** (1) a hard link is another directory entry; (2) compare `ls -li` and `readlink`; (3) resolve the symbolic target from `links/`, not from the terminal's current directory.

## Tests and Feedback (70–85)

Save before/renamed/repaired observations in `evidence/links.txt`, returning to the workspace root first. Save the recreated-name result as `evidence/replacement.txt`.

| Case | Evidence | What it tests |
|---|---|---|
| Normal | All references read version 1 before rename | Link construction and correct target path |
| Failure/repair | Symbolic read fails after rename and succeeds after repair | Path indirection and diagnosis |
| Changed name | New source reads version 2 while hard link keeps version 1 | Filename replacement versus inode identity |

The helper accepts internal symbolic links for this lab; it refuses links that escape the managed directory. Do not use it to manage links to `/etc`, other homes or unrelated directories.

**Troubleshooting:** `File exists` means inspect the destination; a dangling link can exist even when its target does not. Hard links cannot normally cross filesystems. See [the Lab 3 guide](guides/slides.html), `man ln`, and `man readlink`.


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> A symbolic link inside `lab3/links/` stores `../source.txt`. Only `lab3/links/source.txt` exists. Resolve the stored path and explain why the link fails; give a suitable target for the existing file.

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) Which file change broke the symbolic reference? (b) Why did the hard link survive? (c) What happens if the new filename contains different bytes?

## Cleanup and Final Submission (110–120 minutes)

Save evidence before optional cleanup. If you later run `oslab clean lab3`, only the managed directory is removed; internal links are removed as entries and external links are refused. No boot configuration changes occur in the core.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab3/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cd "$OSLAB_WORKSPACE/lab3"
   cp -- evidence/links.txt evidence/replacement.txt "$SUBMISSION_REPO/lab3/evidence/"
   ```

   ```text
   lab3/
   ├── README.md
   └── evidence/
       ├── links.txt        # inode/target and before/failure/repair evidence
       └── replacement.txt  # recreated source name and content observations
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct wildcard explanation and working hard/symbolic links (objectives 1–3) | 3 |
| Rename failure, repair and recreated-name evidence | 2 |
| Explain inode identity and relative symbolic-target resolution; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
