# OS Lab 9 - Vault Deadlock, Resource Ordering & Recovery (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class. Before class: about 10 minutes for the pre-lab |
| Work | Individual. Your two lock names and the worker who starts first are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `bash`, `flock`, `timeout`, `sleep`, `nano`, `oslab` |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Builds on | Lab 8 (locks, file descriptors, background jobs and exit statuses) |
| Lecture link | [Week 9 notes: deadlocks](../../lectures/notes/week09-deadlocks.md) |

> **Scenario:** QuantumTech’s Alpha and Beta recovery vaults freeze during a synchronization drill. Model their resources with two owned lock files, observe a bounded wait cycle, and repair the acquisition order.

## Lab Objectives

After the required core, you should be able to:

1. Draw holdings and requests that form a circular wait.
2. Reproduce a coordinated two-worker conflict with bounded waits and interpret timeout recovery.
3. Apply one global lock order and explain why it removes the cycle.

**Extension objectives:** Inspect process wait traces and practise consent-based site-to-site synchronization only in a narrow prepared directory. These retain the original lab's wider topics; they are not required to finish the two-hour core. They are in the [optional extensions](extensions.md).

## How This Lab Works

| Command | What it does |
|---|---|
| `oslab values lab9` | Shows **your** two lock names and which one worker A takes first |
| `oslab predict lab9` | Saves your prediction once, before the experiment |
| `oslab hint lab9 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab9` | Runs your `worker.sh` in both modes and shows your milestones (it takes about 10 seconds) |
| `oslab checkpoint lab9` | Opens when the instructor says so, near the end |
| `oslab debrief lab9` | After the lab: you give the right answers to your prediction questions |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint. Always test what an AI tells you.
- In Core 2 you decide the global lock order yourself. You write the rule, and you explain why it removes the cycle.
- Every wait has a time limit. You only ever start your own two workers, always with `timeout`.

## Before the Lab

Do this before class. It takes about 10 minutes.

```bash
oslab doctor
oslab prelab lab9
```

## Timetable

| Minutes | Activity |
|---|---|
| 0–10 | Setup |
| 10–25 | Guided: locks and bounded waiting |
| 25–35 | Prediction |
| 35–55 | Core 1: reproduce the deadlock |
| 55–70 | Core 2: repair it with a global order |
| 70–85 | Instructor demonstration, Plus and Challenge |
| 85–100 | Live checkpoint |
| 100–110 | Debrief |
| 110–120 | Submit |

## Setup (0–10)

1. Log in to the server with your own account. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab9
   cd "$OSLAB_WORKSPACE/lab9"
   mkdir -p evidence
   oslab values lab9
   ```

2. **Read your personal values.** The last command prints two lock names and the lock that worker A takes first. For example:

   ```text
   Your personal values for lab9 (your-account):
     res1     = haze
     res2     = ember
     a_first  = haze
   ```

   Your own names are different. Worker B always takes them in the other order. Write them down.

3. **Understand the capital words.** This instruction cannot know your names, so it writes `RES1` and `RES2` where your values belong. Never type the capital words. Type your own names.

   | The instruction says | With the example values above, you type |
   |---|---|
   | `vault/RES1.lock` | `vault/haze.lock` |
   | `cat vault/RES1.txt` | `cat vault/haze.txt` |

4. Your folder now looks like this:

   ```text
   lab9/
   ├── .oslab-managed.json
   ├── vault/
   │   ├── RES1.txt        # data of your first resource
   │   ├── RES2.txt        # data of your second resource
   │   └── worker.sh       # the worker, with one TODO for you
   └── evidence/
   ```

5. Try the checking command once. At the start the first line passes and the others say `TRY`.

   ```bash
   oslab check lab9
   ```

## Guided — Locks and Bounded Waiting (10–25)

**Goal:** see what a lock is, and how a worker can stop waiting for one.

1. The text files hold data. A **lock file** is separate: `flock` makes workers take turns on it. Creating a file called "locked" is not a lock.

   ```bash
   cat vault/RES1.txt vault/RES2.txt
   ls vault
   ```

2. Take one lock inside a small subshell. File descriptor 8 stays open until the subshell ends, and the lock is held as long as it is open. `-w 2` means: wait at most 2 seconds.

   ```bash
   (
       flock -x -w 2 8 || exit 3
       printf 'holding RES1\n'
   ) 8>vault/RES1.lock
   ```

3. Show bounded contention on that one lock. One subshell holds it for 3 seconds. The second command waits only 1 second.

   ```bash
   (
       flock -x -w 2 8 || exit 3
       sleep 3
   ) 8>vault/RES1.lock &
   holder=$!
   sleep 0.2
   flock -x -w 1 vault/RES1.lock true
   printf 'contender status=%s\n' "$?"
   wait "$holder"
   ```

   The status is not `0`: the wait timed out. **Observe:** what is held while another worker waits? Does a timeout *prevent* a deadlock, or only let a worker stop waiting?

## Prediction (25–35)

Guess first, then try. Answer alone, without AI.

```bash
oslab predict lab9
```

It asks four questions and one sentence about your own two locks. Draw the two workers and the two locks on paper first. A wrong guess costs nothing. You compare it with the real result in the debrief.

## Core 1 — Reproduce the Deadlock (35–55)

**Goal:** make worker A and worker B wait for each other, and read what the timeouts say.

1. Read the worker. Find where it takes the first lock, where it waits for the other worker (the **barrier**), and where it asks for the second lock. The line with `sleep "${HOLD:-0}"` is a teaching delay; keep it.

   ```bash
   cat -n vault/worker.sh
   ```

   The barrier makes both workers announce their first lock before they ask for the second one. It is a teaching tool. It is used only in `opposite` mode.

2. Start exactly two workers in `opposite` mode, each with `timeout 6`. Then save the statuses and logs.

   ```bash
   rm -f -- vault/coord/A.ready vault/coord/B.ready
   timeout 6 bash vault/worker.sh A opposite > evidence/opposite-a.txt 2>&1 &
   worker_a=$!
   timeout 6 bash vault/worker.sh B opposite > evidence/opposite-b.txt 2>&1 &
   worker_b=$!
   if wait "$worker_a"; then rc_a=0; else rc_a=$?; fi
   if wait "$worker_b"; then rc_b=0; else rc_b=$?; fi
   {
     printf 'opposite A=%s B=%s\n' "$rc_a" "$rc_b"
     cat evidence/opposite-a.txt evidence/opposite-b.txt
   } > evidence/opposite.txt
   cat evidence/opposite.txt
   ```

3. Draw what each worker holds and requests at the barrier. At least one worker ends with status `5` (the timeout of the second lock). When it exits, its first lock is released, so the other worker may finish instead of also timing out. Explain that recovery in your report. Do not claim that both workers must fail.

**Hints:** `oslab hint lab9 1`, `2` and `3`. AI is allowed here; test every suggestion.

## Core 2 — Repair It With a Global Order (55–70)

**Goal:** one rule for both workers, so that no worker waits for a lock while holding the one the other needs.

1. **Your decision.** Open the worker with `nano vault/worker.sh` and find the `TODO`. In `ordered` mode, both workers must take the locks in the **same** order. In `opposite` mode, worker B must still take them the other way round, so that you can reproduce the conflict. Keep the barrier only for `opposite` mode, and write your rule with the variables `$first` and `$second`, not with your lock names.

2. Run the two workers in `ordered` mode and save the statuses and logs.

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

   Both statuses should be `0`. Why can a worker that waits for the first lock not hold the second lock at the same time?

3. Clean up. No worker may still run, and the locks must be free.

   ```bash
   jobs
   flock -n vault/RES1.lock true; printf 'RES1 free: status=%s\n' "$?"
   flock -n vault/RES2.lock true; printf 'RES2 free: status=%s\n' "$?"
   ```

   Both statuses should be `0`. The timeouts stay in the script: ordering prevents *this* circular wait, but timeouts still bound other delays. Ordering does not give fairness and does not make every larger system safe.

4. Check your work. The four Core milestones must show `PASS`.

   ```bash
   oslab check lab9
   ```

   The check runs your `worker.sh` in a disposable folder: in `opposite` mode, in `ordered` mode, and in `ordered` mode again with two other lock names. The last test fails if your rule only works for your own lock names.

## Instructor Demonstration, Plus and Challenge (70–85)

First, watch the instructor draw the two workers and the two locks and show the circle on the board. Then, if you finish early, try these. They are not needed for full marks. Save your answers in `evidence/plus.txt`.

**Plus**

- Slow the first lock down. `HOLD=1` makes each worker keep its first lock for one second before it asks for the second. Run both workers in `ordered` mode with `HOLD=1`:

  ```bash
  HOLD=1 timeout 6 bash vault/worker.sh A ordered &
  HOLD=1 timeout 6 bash vault/worker.sh B ordered &
  wait
  ```

  Do both workers still finish? One of them waits longer. What does it wait for?

**Challenge**

- Three workers and three locks `x`, `y`, `z`: A holds `x` and requests `y`; B holds `y` and requests `z`; C holds `z` and requests `x`. Draw the circle. Choose a global order and say which worker must change the order of its two locks.

## Live Checkpoint (85–100)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab9
```

1. Read the case with a third worker, and answer the four questions.
2. Then do the file task that the command prints: copy **your** worker script, change only the two `res1=` and `res2=` lines to the new names, run the `ordered` mode, and save the logs in `checkpoint.txt`.
3. Run `oslab check lab9`. A fifth milestone, `checkpoint`, must show `PASS`.

## Debrief (100–110)

Look at your prediction again. `oslab` saved it in a hidden folder, `.records`.

```bash
cat "$OSLAB_WORKSPACE/.records/lab9-predict.json"
```

Now give the right answer to each prediction question:

```bash
oslab debrief lab9
```

Your prediction stays saved as it was, so the comparison shows which answers you confirmed and which you corrected. Then the class discusses: your timeout rescued the opposite run. Why is "wait less" not a repair for a deadlock?

## Submit (110–120)

1. Copy your work to your course repository. Replace `YOUR_ID` with your own ID.

   ```bash
   SUBMISSION_REPO="$HOME/os-gic-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab9/evidence"
   cp -- vault/worker.sh "$SUBMISSION_REPO/lab9/"
   cp -- evidence/opposite.txt evidence/ordered.txt "$SUBMISSION_REPO/lab9/evidence/"
   ```

   If you did Plus or Challenge, copy `evidence/plus.txt` the same way.

2. Fill in the [report template](README.md) as `lab9/README.md`. Your repository then has:

   ```text
   lab9/
   ├── README.md
   ├── worker.sh
   └── evidence/
       ├── opposite.txt
       └── ordered.txt
   ```

   The course website checks that these exact names are there.

3. Commit and push. `git pull` comes first, in case you pushed from your own computer since.

   ```bash
   cd ~/os-gic-YOUR_ID
   git pull
   git add os-lab-YOUR_ID/lab9
   git commit -m "Lab 9"
   git push
   ```

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Worker: `oslab check lab9` passes the four Core milestones (opposite conflict, ordered mode, rule independent of names, evidence files) | 2 |
| Tests: `opposite.txt` and `ordered.txt` show the conflict and the repair, and the README explains the recovery by timeout | 2 |
| Prediction saved in time, and corrected with `oslab debrief lab9` | 2 |
| Live checkpoint: the answers and your worker running with the new names | 3 |
| Complete submission: the required files in your repository, on time | 1 |

Every row is marked from your `oslab` records and the files in your repository, so run `oslab check lab9` until it shows what you expect. Your prediction earns its first point for being made, not for being right. Plus and Challenge are not needed for full marks.

## Help and References

- `oslab hint lab9 1`, `2`, `3`
- `man flock`, `man timeout`
- Wait traces and a partner exercise between two accounts are in the [optional extensions](extensions.md). They need an instructor-prepared directory.
