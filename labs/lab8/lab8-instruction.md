# OS Lab 8 - Secure Bash Scripting, Race Conditions & File Locking (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Lab 7 quoted arguments/exit status, positive-integer checks, background jobs |
| Required tools | `bash`, `flock` (util-linux), `timeout`, `awk` |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** QuantumTech’s widget store must not sell inventory twice. Use a five-unit teaching stock rather than the original 100-unit workload so you can reason about every sale. Inspect the supplied behavior, reproduce a stale read, and protect the complete transaction.

## Lab Objectives

After the required core, you should be able to:

1. Validate bounded purchase quantities and test rejection without changing stock.
2. Reproduce and explain a read-check-write race using stock plus logged sale quantities.
3. Protect the complete transaction with a bounded file lock and test the invariant.

**Extension objectives:** Audit trails, permissions and consent-based peer test review; prepared drop-zones and bounded log organization. These retain the original lab's wider topics; they are not required to finish the two-hour core.

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

Original Levels 0–2 warm-up/validation/logging introduce the store. Levels 3–4 exploit and lock repair are the required investigation. Cross-user permission/drop-zone/log-management levels are optional.

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
   oslab start lab8
   cd "$OSLAB_WORKSPACE/lab8"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab8/
   ├── .oslab-managed.json
   ├── store/
   │   ├── buy.sh       # skeleton; replaced by the guided starting implementation
   │   ├── stock.txt    # starts at 5
   │   └── sales.log    # starts empty
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Levels 0–2 — Store Engine: Guided Working Example (10–25)

1. Inspect the supplied state and save the skeleton if you have already edited it.

   ```bash
   cat store/stock.txt
   cat store/buy.sh
   ```

   Work on the owned `store/` copy. The guided implementation below is intentionally **unsafe under concurrency**; it is only a starting point for investigation.

2. Create a runnable single-buyer engine. Read each part: validation, state read, sufficient-stock check, update and audit log.

   ```bash
   cat > store/buy.sh <<'SH'
   #!/usr/bin/env bash
   set -euo pipefail
   store=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
   if [[ $# -ne 1 || ! "$1" =~ ^[1-9][0-9]{0,2}$ ]]; then
       echo 'usage: buy.sh QUANTITY (1..999, no leading zero)' >&2
       exit 2
   fi
   quantity=$1
   # TODO: a bounded lock must protect the complete transaction below.
   stock=$(<"$store/stock.txt")
   [[ "$stock" =~ ^(0|[1-9][0-9]{0,2})$ ]] || { echo 'invalid stock' >&2; exit 2; }
   if (( quantity > stock )); then echo 'insufficient stock' >&2; exit 1; fi
   sleep 1  # teaching delay to widen the stale-read window; remove in final version
   printf '%s\n' "$((stock - quantity))" > "$store/stock.txt"
   printf 'sold %s\n' "$quantity" >> "$store/sales.log"
   echo 'accepted'
   SH
   bash store/buy.sh 1
   cat store/stock.txt store/sales.log
   ```

   Expected: stock 4 and one `sold 1` log record. Each script finds its own folder rather than relying on the caller's current directory. Input bounds avoid octal/overflow surprises in this teaching script.

3. Reset **only test data** for the next experiment; this does not replace your program.

   ```bash
   printf '5\n' > store/stock.txt
   : > store/sales.log
   ```

   **Observe:** At which line has the script committed to an old stock value? Does the log by itself prove inventory was decremented consistently?

## Prediction (25–35)

Before running concurrent buyers, write: **Stock is 5. Both buyers request 4 and both read the stock before either writes it. What may the final stock and log show? Does that preserve `units sold + remaining stock = initial stock`?** No AI; an optional five-minute comparison is allowed.

## Level 3 — Observe the Stale-Read Race (35–50)

1. Run only two bounded buyers and capture each PID and exit status.

   ```bash
   timeout 5 bash store/buy.sh 4 > evidence/buyer-a.txt 2>&1 &
   buyer_a=$!
   timeout 5 bash store/buy.sh 4 > evidence/buyer-b.txt 2>&1 &
   buyer_b=$!
   if wait "$buyer_a"; then rc_a=0; else rc_a=$?; fi
   if wait "$buyer_b"; then rc_b=0; else rc_b=$?; fi
   printf 'A=%s B=%s\n' "$rc_a" "$rc_b"
   cat store/stock.txt store/sales.log
   ```

2. Count **quantities sold**, not just log lines. Two accepted sales of 4 with stock 1 would account for 9 units from an initial 5, exposing the lost update even though stock is nonnegative.
3. Save initial state, both exit statuses, final stock and log in `evidence/race.txt`. The one-second delay is a controlled teaching aid, not a production fix or a guarantee that every run reveals the race. If necessary, repeat once after resetting only stock/log.

   ```bash
   {
     printf 'initial stock=5; requests=4,4; A=%s B=%s\n' "$rc_a" "$rc_b"
     cat evidence/buyer-a.txt evidence/buyer-b.txt store/stock.txt store/sales.log
   } > evidence/race.txt
   ```

## Level 4 — Protect the Critical Section (50–70)

1. Preserve the flawed starting script for comparison.

   ```bash
   cp -- store/buy.sh store/buy_before_lock.sh
   ```

2. Learn the locking mechanism on a separate demo lock before editing the store.

   ```bash
   (
       flock -x -w 2 9 || exit 3
       printf 'demo lock acquired\n'
   ) 9>store/demo.lock
   ```

   Descriptor 9 refers to an opened lock file. `-x` requests exclusivity; `-w 2` bounds the wait. Processes must cooperate using the **same** lock file. Closing the descriptor releases its lock.

3. Mark the transaction boundaries on your script: stock read → sufficiency check → update → sale log. Add a dedicated `stock.lock` descriptor and bounded acquisition before the transaction. Decide where to handle a lock timeout and what status to return. Locking only the write still leaves the earlier check stale.
4. Keep the descriptor open until the transaction finishes. Remove the teaching delay from the final script; keep the separate flawed copy if you want to reproduce the original observation.

**Complete when:** concurrent buyers cannot both spend the same units, invalid inputs leave state unchanged, and your explanation identifies the whole protected section. AI may suggest a lock placement; verify that placement against the transaction boundaries.

**Hints:** (1) state the inventory invariant; (2) inspect the stock read before the lock; (3) use `exec 9>...` then `flock -x -w 2 9`, keeping read/check/write/log after acquisition.

## Tests and Feedback (70–85)

For each data-dependent case, reset stock to 5 and empty the log; preserve your source. Keep two selected test records, including the concurrent case.

| Case | Expected behavior |
|---|---|
| Quantity 2 | Accept; stock 3; one `sold 2` record |
| 0, -1, `abc`, or missing argument | Reject; no stock/log change |
| Quantity 6 | Reject as insufficient; stock stays 5 |
| Two concurrent quantities 4 | Exactly one sale, other rejected; final stock 1 |
| Forced lock contention | Bounded lock failure is reported; no state change |

The public `oslab check lab8` only checks nonnegative integer stock; it cannot establish the inventory invariant or prove race absence. Check log quantities and stock together. Successful runs support a bounded claim; they do not prove every possible execution safe or provide crash-safe transactions.

After your repaired concurrent run, save its statuses/output/state using the same record block as Level 3, but write to `evidence/locked.txt`. Add the invalid-input and normal-case observations using an editor or `tee -a`; keep the initial stock for each case explicit.

**Troubleshooting:** If `flock` is absent, ask for the instructor's trace fallback. A timeout status is not a successful purchase. Leave the lock file in place—deleting and recreating it while workers run can defeat the shared locking protocol. Read `man flock` and [Week 7 notes](../../lectures/notes/week07-critical-sections.md).


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> Stock is 3 and two buyers request 2 each. Under correct transaction locking, predict how many purchases are accepted, final stock, and total logged units. Explain why nonnegative stock alone is an insufficient test.

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) Why can stock remain nonnegative while sales exceed inventory? (b) Which lines must share one lock? (c) What does your test not establish about crash recovery?

## Cleanup and Final Submission (110–120 minutes)

Wait for only the two captured buyer jobs to finish. Save both test records, then leave lock/data files for review. Never delete an active lock file or kill unrelated processes.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-se-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab8/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- store/buy.sh "$SUBMISSION_REPO/lab8/"
   cp -- evidence/race.txt evidence/locked.txt "$SUBMISSION_REPO/lab8/evidence/"
   ```

   ```text
   lab8/
   ├── README.md
   ├── buy.sh              # final locked script
   └── evidence/
       ├── race.txt         # stale-read observation and initial data
       └── locked.txt       # normal/invalid/concurrent results after repair
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Validated purchase behavior and full transaction lock (objectives 1–3) | 3 |
| Flawed/locked concurrency and invalid-input evidence | 2 |
| Explain stale reads, lock scope and the units-sold inventory invariant; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
