# OS Lab 6 — Linux Security, Users, Groups & File Permissions (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | File/directory paths; ordinary owner permissions; no administrator access |
| Required tools | `id`, `stat`, `chmod`, `ls`; `namei` recommended, ACL tools optional |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** TechCorp needs a private record and a notice that staff can eventually read. Configure your owned copy first and justify the full access path before an administrator prepares any multi-user exercise.

## Lab Objectives

After the required core, you should be able to:

1. Interpret owner/group/other mode bits and symbolic versus octal notation.
2. Set least-privilege modes on owned files/directories and explain directory traversal.
3. Diagnose an access failure using path/mode evidence, distinguishing observed access from a hypothetical peer decision.

**Extension objectives:** Inspect accounts/groups, ACLs and special bits; use narrowly prepared identities or disposable VM accounts for actual cross-user experiments. These retain the original lab's wider topics; they are not required to finish the two-hour core.

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

Original Task 3 file/directory permissions is the required investigation. Tasks 1–2 account/group administration and Tasks 4–5 special bits/ACLs are optional with prepared permissions.

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
   oslab start lab6
   cd "$OSLAB_WORKSPACE/lab6"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab6/
   ├── .oslab-managed.json
   ├── private/
   │   └── record.txt
   ├── shared/
   │   └── notice.txt
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Task 3 — Permission Basics: Guided Example (10–25)

1. Identify your credentials without changing any account.

   ```bash
   id
   ls -ld . private shared
   stat -c '%A %a %U:%G %n' private/record.txt shared/notice.txt
   ```

   Mode triples apply to owner, owning group and others. Each triple adds read=4, write=2 and execute/search=1. A directory's execute bit means search/traversal, not running a program.

2. Use a separate demo file to compare octal and symbolic modes.

   ```bash
   mkdir -p demo
   printf 'demo content\n' > demo/note.txt
   chmod 600 demo/note.txt
   stat -c '%A %a %n' demo/note.txt
   chmod u=rw,g=r,o= demo/note.txt
   stat -c '%A %a %n' demo/note.txt
   ```

   Expected modes are 600 (`rw-------`) and 640 (`rw-r-----`). The latter grants the file's owning group read permission; it does not make every directory on the path searchable.

3. Inspect path components.

   ```bash
   namei -l "$PWD/demo/note.txt"
   ```

   If `namei` is unavailable, list each parent with `ls -ld`. **Observe:** Does mode 644 on a file inside a 700 directory imply other users can reach that file?

## Prediction (25–35)

Write: **A directory is mode 600 and contains a mode-600 file owned by you. Can you list the directory's names? Can you open the file through that directory? Explain the directory bits.** No AI for this prediction; the optional comparison is bounded to five minutes.

## Task 3 — Private Record and Public-Notice Policy (35–70)

1. Write a small policy before issuing `chmod`: owner can read/write the private record; nobody else should read it. The notice is read-only for nonowners when placed in an administrator-prepared searchable location.
2. Choose modes for `private/`, `private/record.txt`, `shared/`, and `shared/notice.txt`. Apply them only to these owned paths. Save the resulting `stat` output in `evidence/policy.txt`.

   ```bash
   stat -c '%A %a %U:%G %n' private private/record.txt shared shared/notice.txt | tee evidence/policy.txt
   ```
3. Read/write the private record as its owner and inspect whether its execute bit is absent. Do not try to execute a data file to test read permission.

   ```bash
   cat private/record.txt
   printf 'owner update\n' >> private/record.txt
   if test -x private/record.txt; then printf 'unexpected execute bit\n'; else printf 'not executable\n'; fi
   ```

4. Test directory read versus traversal using the separate demo, then restore access immediately.

   ```bash
   mkdir -p demo/sealed
   printf 'inside\n' > demo/sealed/item.txt
   chmod 600 demo/sealed
   ls demo/sealed | tee evidence/traversal.txt
   cat demo/sealed/item.txt 2>&1 | tee -a evidence/traversal.txt
   chmod 700 demo/sealed
   cat demo/sealed/item.txt | tee -a evidence/traversal.txt
   ```

   The failing `cat` is intentional. Some `ls` variants also try to read metadata and can issue errors; compare a plain listing of names with actual access. Record the failure and repair in `evidence/traversal.txt`.
5. Explain a peer's hypothetical access to the notice by inspecting **every** parent, including the private `oslab-work` directory. A notice mode alone cannot make the private workspace a public location. Do not widen your home/workspace permissions to manufacture a peer test.

**Complete when:** the modes match your stated policy, the traversal failure is explained/repaired, and peer reasoning accounts for the whole path. Actual multi-user behavior requires the instructor-prepared extension; it is not claimed from an owner-only test.

**Hints:** (1) separate file permissions from directory search; (2) use `stat`/`namei`; (3) restore search permission on the demo directory before retrying the file read.

## Tests and Feedback (70–85)

| Case | Evidence | Limit |
|---|---|---|
| Owner normal access | Read/append private record and inspect modes | Does not simulate another user |
| Directory-search failure | Before/failed/restored read under demo/sealed | Shows traversal, not all possible ACL/capability effects |
| Hypothetical peer access | Full path mode explanation | Needs a prepared second account for empirical confirmation |

Default ACLs can affect new-file permissions; use `getfacl` if available and report unexpected ACLs. Reinspect final modes after your tests.

**Troubleshooting:** Run `whoami`/`id` and confirm ownership first. A normal user cannot `chown` a file to arbitrary accounts. Never edit sudoers or create accounts for this core. See [the Lab 6 guide](guides/slides.html), `man chmod`, and `man path_resolution`.


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> A prepared shared directory is 711 and its file is 600, owned by another student. You know the filename. Explain whether you can traverse the directory, list names, and read the file.

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) Which directory bit caused the failed file read? (b) Why does a 644 notice not override a 700 parent? (c) Which observations were actual tests and which were hypothetical?

## Cleanup and Final Submission (110–120 minutes)

Restore the demo directory to 700 and keep private files at your stated policy. No new accounts/groups or jobs were created. Do not change home access or another student’s files.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-se-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab6/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- evidence/policy.txt evidence/traversal.txt "$SUBMISSION_REPO/lab6/evidence/"
   ```

   ```text
   lab6/
   ├── README.md
   └── evidence/
       ├── policy.txt
       └── traversal.txt
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Modes match the owned-file policy and full-path reasoning (objectives 1–3) | 3 |
| Owner-access and directory-search failure/repair tests | 2 |
| Explain rwx/octal interpretation and the limits of peer-access claims; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
