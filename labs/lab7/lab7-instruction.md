# OS Lab 7 — Bash Scripting, Permissions & Server Automation (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Basic Bash variables, file commands and paths |
| Required tools | `bash`, `wc`, `printf`, `chmod`, `cmp` |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** Build a personal TechCorp command that can inspect files in your own server neighborhood. It must preserve argument boundaries before any cross-user automation is considered.

## Lab Objectives

After the required core, you should be able to:

1. Create and invoke a Bash script with understood arguments and execution permissions.
2. Handle spaces, leading-dash filenames and missing input without unintended word splitting.
3. Test a reusable command and explain its exit status and safe filename handling.

**Extension objectives:** Use personal PATH entries, login-message previews and an owned outbox; cross-user mailbox/feedback requires a narrow prepared shared directory. These retain the original lab's wider topics; they are not required to finish the two-hour core.

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

Original Task 1 script basics and Task 2 command lookup introduce a safe personal automation command. Original Tasks 3–8 login/outbox/mailbox tasks remain extensions; SUID work is a prepared-VM concept activity.

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
   oslab start lab7
   cd "$OSLAB_WORKSPACE/lab7"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab7/
   ├── .oslab-managed.json
   ├── count_words.sh      # editable starter skeleton
   ├── input/
   │   ├── one file.txt     # two words
   │   └── -dash.txt        # one word
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Task 1 — Script Basics: Guided Example (10–25)

1. Create a complete argument viewer. The quoted heredoc delimiter prevents your interactive shell from expanding the script's variables while writing the file.

   ```bash
   cat > show_args.sh <<'SH'
   #!/usr/bin/env bash
   printf 'argument count=%s\n' "$#"
   for argument in "$@"; do
       printf '<%s>\n' "$argument"
   done
   SH
   bash show_args.sh 'one file.txt' '-dash.txt'
   ```

   Expected output is a count of 2 followed by two angle-bracketed arguments. `"$@"` expands each argument separately while preserving spaces inside it.

2. Compare interpreter invocation with direct execution.

   ```bash
   chmod u+x show_args.sh
   ./show_args.sh 'one file.txt' '-dash.txt'
   ```

   The shebang chooses an interpreter for direct execution. `./` explicitly locates a command in the current directory; it need not be on PATH.

3. Introduce safe utility operands without revealing the final loop.

   ```bash
   wc -w -- 'input/one file.txt'
   wc -w -- 'input/-dash.txt'
   ```

   The expected counts are 2 and 1. `--` ends option parsing for `wc`. A path beginning `input/` is already not a leading-dash operand, so the changed-case test later also checks `-dash.txt` from inside `input/`.

   **Observe:** Why is the filename with a space one argument? What might `for argument in $@` do differently?

## Prediction (25–35)

Write: **A script receives `'one file.txt'` as one argument but loops over unquoted `$@`. What pieces might the loop see? Why might a file named `-dash.txt` cause a different problem?** No AI for the prediction; optional peer comparison is five minutes.

## Task 2 — Build Your Personal File Command (35–70)

1. Inspect the supplied skeleton and input before editing.

   ```bash
   cat count_words.sh
   cat 'input/one file.txt' 'input/-dash.txt'
   ```

2. Implement `count_words.sh` using the guided argument loop. Requirements:
   - With no arguments, print a usage message to stderr and exit nonzero.
   - For each regular file, print its word count and original path on one labeled line.
   - For a missing/nonregular input, print a useful stderr message, continue with other arguments, and return nonzero overall.
   - Preserve argument boundaries and pass utility operands safely. Do not use `eval`.
3. Start with one valid file, then two valid files. Verify each before adding error handling.

   ```bash
   bash count_words.sh 'input/one file.txt'
   bash count_words.sh 'input/one file.txt' 'input/-dash.txt'
   ```

4. Decide how to keep an error status while continuing through later arguments. Use a variable initialized to zero and change it when an input fails; return it at the end.
5. Make the script owner executable, run it as `./count_words.sh`, and compare its behavior with `bash count_words.sh`.

**Complete when:** both normal counts are correct, names remain intact, missing inputs are diagnosed, and the final status communicates whether any input failed. Different reasonable output labels are accepted.

**Hints:** (1) quote each expanded path; (2) display arguments with the viewer when a filename is split; (3) test `[[ -f "$path" ]]` and put `--` before filename operands.

## Tests and Feedback (70–85)

1. Save the normal two-file invocation and output in `evidence/normal.txt`.

   ```bash
   bash count_words.sh 'input/one file.txt' 'input/-dash.txt' | tee evidence/normal.txt
   ```
2. Run with a missing file followed by a valid file. Immediately inspect the status:

   ```bash
   {
     bash count_words.sh missing.txt 'input/one file.txt'
     printf 'status=%s\n' "$?"
   } > evidence/edge.txt 2>&1
   cat evidence/edge.txt
   ```

   Expected: diagnostic for the first input, a valid result for the second, and nonzero status overall. Save this in `evidence/edge.txt`.
3. Run from inside the input directory so the leading dash is an actual operand problem:

   ```bash
   cd input
   bash ../count_words.sh '-dash.txt' 'one file.txt'
   cd ..
   ```

4. Test no arguments and an empty file of your own. An empty regular file has a word count of zero; it is different from a missing file.

**Troubleshooting:** Permission denied on direct execution may be a missing execute bit or a `noexec` filesystem; `bash script.sh` is the permitted fallback. Diagnose quoting with `show_args.sh`. See [the Bash manual](https://www.gnu.org/software/bash/manual/bash.html) and `man wc`.


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> Current directory contains a file literally named `-dash.txt`. Explain why `wc -w -dash.txt` may be misinterpreted and give a safe command. Then explain why quoting alone does not end option parsing.

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) What does `"$@"` preserve? (b) Which problem does `--` solve? (c) How does your script communicate one failed input while processing the next?

## Cleanup and Final Submission (110–120 minutes)

No cron jobs or background processes are created. Leave personal PATH or shell startup changes to the optional extension; do not copy entire shell configuration into the submission.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-se-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab7/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- count_words.sh "$SUBMISSION_REPO/lab7/"
   cp -- evidence/normal.txt evidence/edge.txt "$SUBMISSION_REPO/lab7/evidence/"
   ```

   ```text
   lab7/
   ├── README.md
   ├── count_words.sh
   └── evidence/
       ├── normal.txt
       └── edge.txt
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Safe arguments, correct counts and aggregate failure status (objectives 1–3) | 3 |
| Space/leading-dash/missing/empty input tests | 2 |
| Explain quoting, option boundaries, execution mode and status; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
