# OS Lab 4 — Linux I/O Redirection, Pipelines & Process Management (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Lab 2 paths and Lab 3 shell expansion; simple text files |
| Required tools | `grep`, `cut`, `awk`, `wc`, `printf`, `ps`, `sleep` |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** TechCorp receives small CSV event logs. Produce a trustworthy success-count report and distinguish command output from diagnostics; use owned-process examples for process-management practice.

## Lab Objectives

After the required core, you should be able to:

1. Use redirection and pipelines while distinguishing stdout, stderr and exit status.
2. Filter and aggregate a CSV fixture, checking intermediate stages.
3. Diagnose incorrect selection/aggregation using normal and changed-input tests.

**Extension objectives:** Monitor and signal bounded owned processes; observe orphan/zombie lifecycle in a disposable local environment. These retain the original lab's wider topics; they are not required to finish the two-hour core.

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

Original Tasks 1–3 redirection/pipelines/data analysis form the core. Tasks 4–5 process tools and orphan/zombie observations are extensions with bounded owned processes.

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
   oslab start lab4
   cd "$OSLAB_WORKSPACE/lab4"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab4/
   ├── .oslab-managed.json
   ├── data/
   │   ├── events.csv      # header and three records
   │   └── expected.txt    # intended report: ok total: 8
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Task 1 — I/O Redirection: Guided Example (10–18)

1. Create separate normal output and an error.

   ```bash
   printf 'normal output\n' > evidence/stdout-demo.txt
   cat missing-demo.txt 2> evidence/stderr-demo.txt
   cat evidence/stdout-demo.txt
   cat evidence/stderr-demo.txt
   ```

   The missing-file command intentionally fails. `>` redirects file descriptor 1 (stdout), `2>` redirects descriptor 2 (stderr), and `>>` appends instead of replacing.

2. Compare the ordering of descriptor redirections using a controlled command:

   ```bash
   bash -c 'printf "out\n"; printf "err\n" >&2' > evidence/both.txt 2>&1
   cat evidence/both.txt
   ```

   `2>&1` makes stderr refer to stdout's current destination. Reversing the two redirections can change where stderr goes.

## Task 2 — Pipelines and Filters: Guided Example (18–25)

1. Inspect a tiny example before adding a pipeline.

   ```bash
   printf 'ok,3\nfail,2\n'
   printf 'ok,3\nfail,2\n' | grep '^ok,'
   printf 'ok,3\nfail,2\n' | grep '^ok,' | cut -d, -f2
   ```

   You should see `3` at the last stage. `|` forwards stdout to the next command; stderr is not included by default.

2. Inspect the actual input; the lab uses simple two-field CSV without quoted commas.

   ```bash
   cat data/events.csv
   cat data/expected.txt
   ```

   **Observe:** Does `wc -l` count successful events or selected rows? What stage would combine numeric counts rather than count records?

## Prediction (25–35)

Write: **What will `grep '^ok,' data/events.csv | cut -d, -f2 | head -n 1` print? Will that equal the required successful total? Explain what information it discards.** Keep your answer; optional peer comparison lasts at most five minutes.

## Task 3 — Data Analysis and Report Construction (35–70)

1. Run the deliberately incomplete pipeline you predicted. Compare its intermediate output with the original data.

   ```bash
   grep '^ok,' data/events.csv
   grep '^ok,' data/events.csv | cut -d, -f2
   grep '^ok,' data/events.csv | cut -d, -f2 | head -n 1
   ```

2. Build your own `report.sh` in the workspace. It takes one CSV path argument, selects every record whose first field is exactly `ok`, sums field 2, and prints `ok total: NUMBER` once. It must reject a missing input and print zero when no matching rows exist.
3. Use `awk` as an arithmetic tool if needed. This separate demonstration teaches summing without giving the full CSV solution:

   ```bash
   printf '2\n4\n' | awk '{ total += $1 } END { print total+0 }'
   ```

   Decide where selection, field extraction and summing belong in your report. Acceptable implementations include a staged pipeline or a correctly constrained single `awk` program.
4. Run your implementation and compare with the supplied expected report.

   ```bash
   bash report.sh data/events.csv > evidence/normal.txt
   diff -u data/expected.txt evidence/normal.txt
   ```

   A matching report is useful evidence. Explain why matching one file does not establish correctness for every CSV.

**Hints:** (1) distinguish rows from counts; (2) print each pipeline stage; (3) sum only the selected numeric field and format the label at the end. AI is permitted here; test suggestions on these small owned files.

## Tests and Feedback (70–85)

1. Create two changed inputs without altering the original fixture.

   ```bash
   printf 'status,count\nfail,2\n' > data/no-ok.csv
   cp -- data/events.csv data/changed.csv
   printf 'ok,7\n' >> data/changed.csv
   ```

2. Run the report for each. Expect `ok total: 0` and `ok total: 15`. Try a missing input and check its exit status. Save command, input description and result in `evidence/edge.txt`.

   ```bash
   {
     bash report.sh data/no-ok.csv
     bash report.sh data/changed.csv
     bash report.sh data/missing.csv
     printf 'missing-input status=%s\n' "$?"
   } > evidence/edge.txt 2>&1
   cat evidence/edge.txt
   ```
3. Explain what each test contradicts: counting rows, retaining only the first match, or ignoring input errors. The exercise does not cover full quoted-field CSV parsing; state that limit.

**Troubleshooting:** `grep` returns 1 for no matching lines, which is different from a file-reading error; pipeline success alone does not prove every stage succeeded. Inspect stderr and intermediate values. See [the Lab 4 guide](guides/slides.html), `man grep`, `man awk`, and [the optional original post-lab challenge](lab4-challenge.md).


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> The original fixture gains `ok,7` and `fail,20`. Predict the report total. A student uses `wc -l` after filtering; identify why their answer would measure a different quantity.

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) Why is row count different from summed event count? (b) Which stream carries a missing-file error? (c) What inputs are outside your parser assumptions?

## Cleanup and Final Submission (110–120 minutes)

The core creates no background job. Finish any owned-process extension with its captured `wait` and keep selected evidence. Do not kill processes by name.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab4/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- report.sh "$SUBMISSION_REPO/lab4/"
   cp -- evidence/normal.txt evidence/edge.txt "$SUBMISSION_REPO/lab4/evidence/"
   ```

   ```text
   lab4/
   ├── README.md
   ├── report.sh
   └── evidence/
       ├── normal.txt
       └── edge.txt
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Correct report selection/aggregation and clear stdout/stderr handling (objectives 1–3) | 3 |
| No-match, changed-count and missing-input diagnosis | 2 |
| Explain each pipeline stage and the claim each test supports; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
