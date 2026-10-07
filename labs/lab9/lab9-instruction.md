# OS Lab 9 - Vault Deadlock, Resource Ordering & Recovery (Hands-on)

| Item | Details |
|---|---|
| Course | Operating Systems, Institute of Technology of Cambodia |
| Duration | 120 minutes; installation and VM preparation happen before class |
| Ownership | Individual work and submission; optional short peer exchange |
| Primary environment | Shared Ubuntu server with an individual account for each student |
| Prerequisites | Lab 8 locks, file descriptors, background jobs and exit statuses |
| Required tools | `bash`, `flock`, `timeout`, `ps` |
| Practice fallback | Local Linux/WSL for unprivileged tasks; disposable VM for boot/system administration |
| Core versus extensions | Follow the core below; [optional extensions](extensions.md) retain wider original coverage |

> **Scenario:** QuantumTech’s Alpha and Beta recovery vaults freeze during a synchronization drill. Model their resources with two owned lock files, observe a bounded wait cycle, and repair the acquisition order.

## Lab Objectives

After the required core, you should be able to:

1. Draw holdings and requests that form a circular wait.
2. Reproduce a coordinated two-worker conflict with bounded waits and interpret timeout recovery.
3. Apply one global lock order and explain why it removes the cycle.

**Extension objectives:** Inspect process wait traces and practise consent-based site-to-site synchronization only in a narrow prepared directory. These retain the original lab's wider topics; they are not required to finish the two-hour core.

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

Original Levels 1–3 workspace/naive scripts/local deadlock form the core, followed by Levels 5–6 ordering/timeout. Partner Level 4 is optional; Level 7 cleanup stays required.

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
   oslab start lab9
   cd "$OSLAB_WORKSPACE/lab9"
   pwd
   mkdir -p evidence
   find . -maxdepth 3 -type f
   ```

4. Compare your files with the starting tree. `.oslab-managed.json` identifies the managed workspace; leave it intact. `evidence/` was created in step 3. If `tree` is installed, `tree -a -L 3` can display the same structure.

   ```text
   lab9/
   ├── .oslab-managed.json
   ├── vault/
   │   ├── alpha.txt
   │   ├── beta.txt
   │   └── worker.sh    # editable starter skeleton
   └── evidence/
   ```

The workspace is for experiments. Your personal course Git repository holds the final submission; you will copy selected files there at the end. VM work and privileged commands are never performed on the shared server.

## Level 1 — Locks and Vault Workspace: Guided Example (10–25)

1. Inspect resources and create an owned coordination folder.

   ```bash
   cat vault/alpha.txt vault/beta.txt
   mkdir -p vault/coord
   ```

   The text files represent data; dedicated `.lock` files represent cooperative exclusive access. A lock is not the same thing as merely creating a file named “locked”.

2. Acquire and release one lock in a small subprocess.

   ```bash
   (
       flock -x -w 2 8 || exit 3
       printf 'holding Alpha\n'
   ) 8>vault/alpha.lock
   ```

   Descriptor 8 stays open until the subshell ends. In a production application you would keep the protected operation inside this scope.

3. Demonstrate bounded contention on that one lock.

   ```bash
   (
       flock -x -w 2 8 || exit 3
       sleep 3
   ) 8>vault/alpha.lock &
   holder=$!
   sleep 0.2
   flock -x -w 1 vault/alpha.lock true
   printf 'contender status=%s\n' "$?"
   wait "$holder"
   ```

   A timeout is expected if the holder acquired first. The short delay aids the demonstration but does not prove acquisition occurred; the coordinated investigation below removes that uncertainty about first holdings.

   **Observe:** What is held while another worker waits? Does a timeout prevent deadlock, or provide a way to stop waiting after a conflict?

## Prediction (25–35)

Write: **A holds Alpha and requests Beta. B holds Beta and requests Alpha. Draw both wait edges and predict whether either can obtain its second resource before someone releases a lock.** No AI; five-minute peer comparison is optional.

## Levels 2–3 — Naive Workers and Local Deadlock (35–55)

1. Create the bounded starting worker. Every acquisition has a timeout; a readiness barrier coordinates the intentionally opposite-order demonstration.

   ```bash
   cat > vault/worker.sh <<'SH'
   #!/usr/bin/env bash
   set -euo pipefail
   [[ $# -eq 2 && "$1" =~ ^(A|B)$ && "$2" =~ ^(opposite|ordered)$ ]] || exit 2
   role=$1
   mode=$2
   vault=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
   first=alpha
   second=beta
   # TODO: in ordered mode, every worker must use one global order.
   if [[ "$role" = B ]]; then first=beta; second=alpha; fi
   exec 8>"$vault/$first.lock"
   flock -x -w 2 8 || { echo "$role first lock timeout"; exit 3; }
   printf '%s holds %s\n' "$role" "$first"
   if [[ "$mode" = opposite ]]; then
       touch "$vault/coord/$role.ready"
       other=B
       [[ "$role" = B ]] && other=A
       for step in {1..30}; do
           [[ -f "$vault/coord/$other.ready" ]] && break
           sleep 0.1
       done
       [[ -f "$vault/coord/$other.ready" ]] || { echo 'barrier timeout'; exit 4; }
   fi
   exec 9>"$vault/$second.lock"
   printf '%s requests %s\n' "$role" "$second"
   flock -x -w 2 9 || { echo "$role second lock timeout"; exit 5; }
   printf '%s holds both\n' "$role"
   SH
   ```

   The barrier is a teaching instrument: both workers announce their first holdings before requesting second locks. It must be skipped in the repaired ordered mode because one worker cannot acquire Alpha while another holds it.

2. Clear only the two old readiness markers, then start exactly two bounded workers.

   ```bash
   rm -f -- vault/coord/A.ready vault/coord/B.ready
   timeout 6 bash vault/worker.sh A opposite > evidence/opposite-a.txt 2>&1 &
   worker_a=$!
   timeout 6 bash vault/worker.sh B opposite > evidence/opposite-b.txt 2>&1 &
   worker_b=$!
   if wait "$worker_a"; then rc_a=0; else rc_a=$?; fi
   if wait "$worker_b"; then rc_b=0; else rc_b=$?; fi
   printf 'A=%s B=%s\n' "$rc_a" "$rc_b"
   cat evidence/opposite-a.txt evidence/opposite-b.txt
   ```

3. Draw the holdings/requests at the barrier. At least one worker should time out on the second lock. Once it exits and releases its first lock, the other may complete instead of also timing out. Explain that recovery event rather than claiming both must fail.

   ```bash
   {
     printf 'opposite A=%s B=%s\n' "$rc_a" "$rc_b"
     cat evidence/opposite-a.txt evidence/opposite-b.txt
   } > evidence/opposite.txt
   ```

## Levels 5–6 — Global Ordering and Timeout Recovery (55–70)

1. Edit the TODO order rule so **ordered** mode always acquires Alpha before Beta. Opposite mode remains available to reproduce the teaching conflict. Leave the barrier restricted to opposite mode.
2. Rerun the two workers with `ordered` instead of `opposite`. Save separate logs and both statuses. Explain why a worker waiting for Alpha cannot simultaneously hold Beta under this rule.

   ```bash
   timeout 6 bash vault/worker.sh A ordered > evidence/ordered-a.txt 2>&1 &
   worker_a=$!
   timeout 6 bash vault/worker.sh B ordered > evidence/ordered-b.txt 2>&1 &
   worker_b=$!
   if wait "$worker_a"; then rc_a=0; else rc_a=$?; fi
   if wait "$worker_b"; then rc_b=0; else rc_b=$?; fi
   {
     printf 'ordered A=%s B=%s\n' "$rc_a" "$rc_b"
     cat evidence/ordered-a.txt evidence/ordered-b.txt
   } > evidence/ordered.txt
   cat evidence/ordered.txt
   ```
3. Keep the timeouts even after ordering. Ordering prevents this modeled circular wait; timeouts also bound delays from other issues. It does not ensure fairness or guarantee every larger system avoids deadlocks.

**Complete when:** your logs support the wait cycle in the first case, both ordered workers finish, and the global rule is applied consistently. AI may suggest a repair; check that it changes both workers' resource policy and does not introduce a new barrier wait.

**Hints:** (1) draw held/requested resources; (2) read the first-lock logs and readiness markers; (3) restrict B's reversal to the teaching opposite mode, and skip the barrier for ordered acquisition.

## Tests and Feedback (70–85)

Save the opposite-order traces/statuses in `evidence/opposite.txt` and ordered traces/statuses in `evidence/ordered.txt`. Repeat the opposite case only after removing the two owned readiness markers.

| Case | Intended evidence |
|---|---|
| Opposite, two workers | Both hold distinct first locks; second-lock conflict and bounded recovery |
| Ordered, two workers | Both complete, with sequential access through Alpha |
| One opposite worker alone | Barrier times out within three seconds; explains missing participant |

Status 124 means the external timeout fired. Do not grade an unexplained timeout as successful recovery. Completion in one uncontrolled run does not prove that opposite ordering is safe.

**Troubleshooting:** Reusing readiness files can falsify the coordination condition. Never delete active lock files; their existence is normal. Use the captured PIDs and bounded waits instead of `pkill`. See [the deadlock visualization](../../lectures/visualizations/rag-deadlock.html) and `man flock`.


## Individual Changed-case Checkpoint (85–100 minutes)

Close AI tools and peer help. Answer the instructor's short question on paper or the existing course worksheet. Your earlier implementation need not be complete to answer it.

> A third worker needs only Beta. Must it also acquire Alpha to follow the global-order policy? Explain. Separately, identify whether timeout is prevention or recovery in the opposite-order example.

Give the result or diagnosis, the mechanism, and one observation that could check it. The instructor collects this answer before discussing the public key; the public question is practice, so a graded session may use a fresh private variant.

## Explanation and Correction (100–110 minutes)

Keep your original prediction visible. Under it, write **confirmed** or **corrected**, cite the relevant test, and explain the OS mechanism in 3–5 sentences. Initial prediction accuracy is lightly weighted; a reasoned attempt and evidence-based correction earn credit.

Answer: (a) Which pair of edges formed the cycle? (b) Why must the teaching barrier be absent in ordered mode? (c) How can one timeout allow the other worker to finish?

## Cleanup and Final Submission (110–120 minutes)

Wait for the two captured workers; all waits are bounded. After both exit, remove only their two readiness markers. Leave lock files in place and never kill by a broad name match.

1. Set `SUBMISSION_REPO` to the **absolute path of your existing personal course repository**. Replace the example ID/path below with your own; do not copy another student's repository.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab9/evidence"
   ```

2. Use [this lab's README template](README.md). Copy the listed artifacts and **two selected test records**, rather than every terminal output. Check the final tree below before submitting.

   ```bash
   cp -- vault/worker.sh "$SUBMISSION_REPO/lab9/"
   cp -- evidence/opposite.txt evidence/ordered.txt "$SUBMISSION_REPO/lab9/evidence/"
   ```

   ```text
   lab9/
   ├── README.md
   ├── worker.sh
   └── evidence/
       ├── opposite.txt    # holdings/requests, status, recovery and wait diagram
       └── ordered.txt
   ```

3. Write your own explanations. The prediction must have been captured before execution on paper or the existing course mechanism; copying it into the README afterwards is only a record, not proof of timing. The independent checkpoint is collected separately.
4. Inspect your course repository with `git status --short`, add only your lab files, and commit/push using the normal course submission procedure. Do not include passwords, personal shell configuration, generated binaries or disk images.

## Grading Criteria (10 points)

| Evidence mapped to lab objectives | Points |
|---|---:|
| Bounded conflict reproduction and consistent global ordering (objectives 1–3) | 3 |
| Opposite/ordered and missing-participant diagnosis | 2 |
| Explain circular wait, barrier role and timeout recovery; original prediction and evidence-based correction | 2 |
| Individual changed-case checkpoint: result/diagnosis and mechanism | 2 |
| Concise, attributable evidence and required artifacts | 1 |

Equivalent valid commands, filenames and approaches earn credit if the evidence meets the objectives. A naming difference is penalized only when it actually breaks execution. AI is permitted during investigation and tests, optional throughout, and excluded from the initial prediction and individual checkpoint. If used, note one helpful suggestion and its verification; no paid tool, chat history or AI detector is required.

## Help, References and Optional Work

Use the progressive hints in the task sections before requesting a full solution. See [the extension guide](extensions.md) for follow-up tasks with their own environment requirements. Existing visual guides are background references and may show the older broader sequence; this Markdown instruction defines the current required core.
