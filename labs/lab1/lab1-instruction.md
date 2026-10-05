# OS Lab 1 — Introduction to Operating Systems (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Basic terminal use; your own server login; no programming required |
| Required tools | `bash`, `uname`, `cat`, `ps`, `sleep`, `find` |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** Your first day at TechCorp: identify the machine you logged into, create a small record of your work, and show how one installed program can produce two independent processes.

## Lab Objectives

After the required core, you should be able to:

1. Identify the distribution and running kernel using command output, explaining the difference.
2. Create and inspect files in an owned directory using basic Linux commands.
3. Start two instances of one program and distinguish their PIDs, parent PID, state and lifetime.

**Extension objectives:** Inspect APT package information, practise package installation/removal in a disposable VM, and interpret virtualization evidence. These retain the original lab's wider topics; they are not required to finish the two-hour core.

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

Core: Task 1 OS identification, a short Task 2 file warm-up, and Tasks 4–5 program/process investigation. Original Task 3 package changes and Task 6 virtualization work are extensions.

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
   oslab start lab1
   cd "$OSLAB_WORKSPACE/lab1"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab1/
   ├── .oslab-managed.json
   ├── process.txt       # short process-observation reminder
   └── evidence/         # selected command records
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Task 1 — Operating System Identification: Guided Example (10–25)

1. Ask the kernel for its name and release. Run each command separately so you can identify which field produced each result.

   ```bash
   uname -s
   uname -r
   uname -m
   ```

   On Ubuntu, the kernel name is usually `Linux`; the release and architecture depend on the server. A distribution release and a kernel release are different facts.

2. Read the distribution's identification file.

   ```bash
   cat /etc/os-release
   ```

   Find `NAME` and `VERSION_ID`. Record their values; do not assume the server uses the same Ubuntu version as your WSL machine.

3. Practise the original lab's file commands in an owned folder.

   ```bash
   mkdir -p practice
   printf 'My first OS observation\n' > practice/notes.txt
   cp -- practice/notes.txt practice/notes-copy.txt
   ls -l practice
   cat practice/notes-copy.txt
   ```

   `>` creates or replaces a file. `>>` appends. For a resumed session, inspect existing files before choosing either operator.

4. Save a compact OS record.

   ```bash
   {
     uname -srm
     grep -E '^(NAME|VERSION_ID)=' /etc/os-release
   } > evidence/os-info.txt
   ```

   **Observe:** Which result identifies the running kernel? Which identifies the distribution? Does a filename tell you whether a program is currently running?

## Prediction (25–35)

Before starting the process investigation, write: **If I run `sleep 30` twice, will the two instances have the same PID? Will either PID necessarily appear after both commands have finished? Explain.** Keep this answer. Spend at most five minutes comparing reasoning with a neighbour, or compare it yourself with the OS information above.

## Tasks 4–5 — Programs versus Processes and Multitasking (35–70)

1. Locate the executable and start one short-lived instance.

   ```bash
   command -v sleep
   sleep 30 &
   first_pid=$!
   printf 'first PID=%s\n' "$first_pid"
   ```

   `&` starts a background job. `$!` is the PID of the most recently started background command in this shell; capture it immediately.

2. Start a second instance and inspect both before 30 seconds elapse.

   ```bash
   sleep 30 &
   second_pid=$!
   printf 'second PID=%s\n' "$second_pid"
   ps -o pid,ppid,stat,comm -p "$first_pid,$second_pid" | tee evidence/processes.txt
   jobs -l
   ```

   `PID` identifies each process, `PPID` identifies its parent, `STAT` reports a sampled state, and `COMM` names its command. An `S` sleeping state is normal for `sleep`. Write your observed IDs into `evidence/processes.txt` while they are alive.

3. Wait for only those two jobs, then sample again.

   ```bash
   wait "$first_pid"
   wait "$second_pid"
   ps -o pid,ppid,stat,comm -p "$first_pid,$second_pid" | tee -a evidence/processes.txt
   ```

   A header with no matching rows is expected after exit. `ps` may then return a nonzero status. Explain why the executable still exists even though these process instances have ended.

4. Make one choice independently: repeat with a different short duration (1–10 seconds) and decide when to sample so you can capture a running instance. Record what a late sample would miss. Do not start large numbers of jobs or inspect another student's processes as your own evidence.

**Complete when:** you can identify the OS/kernel and show two distinct execution instances followed by their completion. AI may help interpret fields during this stage; verify its interpretation against `man ps` and your actual sample.

**Progressive hints:** (1) distinguish executable file from instance; (2) compare `$!` with `ps` PID/PPID columns; (3) use a longer bounded duration if your observation was too late.

## Tests and Feedback (70–85)

| Case | Commands/observation | Claim to assess |
|---|---|---|
| Normal | Two `sleep 30` instances sampled before exit | One executable can have two distinct live PIDs |
| Edge | `sleep 1`, sampled immediately and again after `wait` | A later missing row reflects lifetime, not missing software |

For each record, state the expected result, a contradictory result, what happened and what the snapshot cannot prove. A process state is a momentary observation, not a complete scheduling history.

**Troubleshooting:** If `ps` shows nothing, check timing rather than reinstalling software. If login failed, verify the announced host and your own username; the host is supplied by the instructor, not hard-coded here. See [Week 1 notes](../../lectures/notes/week01-introduction-to-os.md), `man uname`, and `man ps`.


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> A shell starts two `sleep 1` commands in the background and captures both `$!` values. It waits two seconds before running `ps`. Predict the captured PID values relative to one another and whether `ps` must still show the processes.

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) Why do both process rows name `sleep`? (b) What does the PPID tell you? (c) Why can `ps` alone not reconstruct every event?

## Cleanup and Final Submission (110–120 minutes)

Confirm both captured jobs finished with `wait`. Keep the workspace until your evidence is saved. If you stop a demonstration early, signal only the PID you captured in this shell, immediately verify its identity, and wait for it; otherwise let the bounded sleep end normally.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-se-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab1/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- evidence/os-info.txt evidence/processes.txt "$SUBMISSION_REPO/lab1/evidence/"
   ```

   ```text
   lab1/
   ├── README.md
   └── evidence/
       ├── os-info.txt
       └── processes.txt     # live/finished observations and chosen short case
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| OS/kernel identification and two owned-process observations (objectives 1–3) | 3 |
| Live/finished and short-duration tests, with timing diagnosis | 2 |
| Explain executable versus instance, PID/PPID and sampled state; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
