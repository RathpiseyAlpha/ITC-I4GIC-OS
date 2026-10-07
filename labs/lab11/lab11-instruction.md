# OS Extra Lab 11 (Bonus) — Linux Disk Management Utilities (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Lab 2 paths, storage lecture, regular file versus block-device distinction |
| Required tools | `truncate`, `stat`, `du`, `df`; `mkfs.ext4`, `dumpe2fs` for formatting; FUSE optional |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** QuantumTech’s build server is running low on storage. Rehearse safe capacity measurements on your own regular image files, distinguishing apparent length from allocated blocks before considering mounting or resizing.

## Lab Objectives

After the required core, you should be able to:

1. Read filesystem capacity and per-file allocation without confusing `df`, `du` and apparent size.
2. Create a bounded sparse regular image and explain the difference between length and allocation.
3. Format/inspect only an owned regular image when tools exist, or interpret a supplied metadata trace with a stated limitation.

**Extension objectives:** FUSE mount/unmount, image checking/growing, a small diagnostic utility, and storage threshold interpretation. These retain the original lab's wider topics; they are not required to finish the two-hour core. This entire lab is optional bonus work; skipping it carries no penalty.

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

The whole lab remains optional bonus. Original Levels 0–3 inventory/usage/image/metadata form its two-hour route. Levels 4–7 mount/utility/maintenance/capstone remain optional extensions, with cleanup always required.

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
   oslab start lab11
   cd "$OSLAB_WORKSPACE/lab11"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab11/
   ├── .oslab-managed.json
   ├── images/
   │   └── README.txt    # regular-image reminder
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Levels 0–1 — Storage Inventory and Usage: Guided Example (10–25)

1. Observe capacity without accessing raw devices or other students' directories.

   ```bash
   df -hT "$PWD"
   lsblk -o NAME,SIZE,TYPE,MOUNTPOINT
   ```

   `df` reports the containing mounted filesystem's capacity. `lsblk` describes visible devices; WSL/container views may differ. These are read-only observations, not permission to format any listed device.

2. Compare two small regular files in your owned folder.

   ```bash
   truncate -s 8M images/demo-sparse.img
   dd if=/dev/zero of=images/demo-written.img bs=1M count=8 status=none
   ls -lh images/demo-*.img
   du -h images/demo-*.img
   stat -c '%n length=%s blocks=%b block-unit=%B' images/demo-*.img
   ```

   `/dev/zero` is a read-only byte source here; the output paths are the owned regular files. Both apparent lengths are 8 MiB. The sparse file normally uses fewer allocated blocks; compression/deduplication and the host filesystem may affect exact figures.

3. Compute allocated bytes as `%b × %B`, then compare with the `%s` length. **Observe:** Does `df` show one file's allocation? Would `du` have to equal `ls -l` for a sparse file?

## Prediction (25–35)

Write: **A 32 MiB file is created with `truncate` without writing all its bytes. Predict its apparent size and whether its allocated space must also be 32 MiB. Explain what holes represent.** No AI; optional five-minute peer exchange is allowed.

## Level 2 — Create and Inspect a Virtual Disk Image (35–50)

1. Create the core image at the specified bounded size, then inspect its type and path.

   ```bash
   truncate -s 32M images/scratch.img
   test -f images/scratch.img && test ! -L images/scratch.img
   readlink -f images/scratch.img
   stat -c '%F %n length=%s blocks=%b block-unit=%B' images/scratch.img
   du -h images/scratch.img
   ```

   Confirm it is a **regular file inside your workspace** before any filesystem-creation command. Never substitute a `/dev/*` destination, partition or mountpoint.

2. Record apparent and allocated bytes in `evidence/sizes.txt`. Compare the new image with the two guided files and explain why a file's length is not the same as reserved physical space.

   ```bash
   {
     stat -c '%n length=%s blocks=%b block-unit=%B' images/*.img
     du -h images/*.img
     df -hT "$PWD"
   } > evidence/sizes.txt
   ```

## Level 3 — Format and Inspect Filesystem Metadata (50–70)

1. Check tool availability first.

   ```bash
   command -v mkfs.ext4
   command -v dumpe2fs
   ```

2. If both exist, format only the already checked regular image. This replaces its current contents; do it only once on a fresh owned image, never on work you need to retain.

   ```bash
   if test -f images/scratch.img && test ! -L images/scratch.img; then
       mkfs.ext4 -F images/scratch.img
   fi
   dumpe2fs -h images/scratch.img > evidence/filesystem.txt 2>&1
   stat -c '%n length=%s blocks=%b block-unit=%B' images/scratch.img
   du -h images/scratch.img
   ```

   `-F` permits formatting a regular image; it is not a safety check. The fixed owned path and pre-check are essential. Formatting writes metadata and may change block allocation even though length remains 32 MiB.
3. Identify filesystem UUID, block count, free blocks and block size from the header. Estimate filesystem bytes from block count × block size; explain why not all filesystem blocks are available for user data.
4. If tools are unavailable, use this **illustrative header excerpt**, not a claim about your local image. Save it in `evidence/filesystem.txt`, including its label, and state **metadata interpretation only; formatting not executed** in your report. Sparse-file creation/measurement and the independent checkpoint still work.

   ```bash
   cat > evidence/filesystem.txt <<'TRACE'
   Illustrative ext4 header excerpt; not measured on this machine.
   Filesystem UUID: 11111111-2222-3333-4444-555555555555
   Block count: 32768
   Free blocks: 25830
   Block size: 1024
   TRACE
   ```

   The numbers describe a 32 MiB filesystem with some space used or reserved; the excerpt does not establish the precise metadata layout or actual local free space.

**Complete when:** measurements distinguish capacity/length/allocation, the image stays bounded and regular, and metadata claims match either an actual header or a clearly identified supplied trace.

**Hints:** (1) separate three meanings of size; (2) compare `stat` fields before/after format; (3) multiply block count by block size, then account for metadata/reserved space.

## Tests and Feedback (70–85)

| Case | Evidence | Claim/limit |
|---|---|---|
| Sparse versus fully written 8 MiB | Length/allocated-block comparison | Allocation depends on content and host filesystem |
| Fresh versus formatted 32 MiB | Before/after size and superblock header | Formatting adds metadata; does not establish FUSE support |
| Capacity observation | `df` for containing filesystem | Reports whole filesystem, not just the image |

Append the formatted-image allocation observation to `evidence/sizes.txt`. If using a trace, label it as supplied evidence rather than a local successful formatting test.

**Troubleshooting:** FUSE availability is irrelevant to this core, which does not mount. A 2 MB `oslab reset` archive limit will refuse large image files; save evidence and remove only your unmounted image files before reset, or keep the workspace. See [Week 12 notes](../../lectures/notes/week12-file-systems.md), `man du`, and `man mkfs.ext4`.


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> Two files have equal apparent length. One was created sparsely with `truncate`; the other was fully written with zero bytes. Predict how their allocated blocks may differ and identify a command/field that checks your claim. Why is `df` insufficient to attribute usage to either file?

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) Why can a 32 MiB image occupy fewer allocated bytes? (b) Why does formatting change allocation? (c) What was observed locally and what requires real FUSE/server validation?

## Cleanup and Final Submission (110–120 minutes)

The core creates no mount. If you completed a FUSE extension, unmount it and verify it is unmounted before cleanup; never recursively clean a mounted directory. Save evidence, then remove only your own demo/image files if reclaiming quota. No real devices or loop mounts are used.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab11/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- evidence/sizes.txt evidence/filesystem.txt "$SUBMISSION_REPO/lab11/evidence/"
   ```

   ```text
   lab11/
   ├── README.md
   └── evidence/
       ├── sizes.txt
       └── filesystem.txt  # actual header or explicitly labelled supplied trace
   ```

   Keep large image files in the workspace; they are not submission artifacts.

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points — bonus)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct bounded regular-image measurements and metadata interpretation (objectives 1–3) | 3 |
| Sparse/written and fresh/formatted comparisons, with capability limits | 2 |
| Explain df versus du versus length and filesystem metadata; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
