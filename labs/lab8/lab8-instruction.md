# OS Lab 8 - Secure Bash Scripting, Race Conditions & File Locking (Hands-on)

| Item | Details |
|---|---|
| Duration | 120 minutes in class, plus a 10-minute pre-lab |
| Work | Individual. Your values are different from your neighbour's |
| Environment | Shared Ubuntu server with an individual account for each student. Local Linux/WSL works for practice ([setup](../SETUP.md)) |
| Tools | `bash`, `flock`, `oslab` |
| Lab format | Pilot: personal values, Core / Plus / Challenge, live checkpoint |
| Lecture link | [Week 7 notes: critical sections](../../lectures/notes/week07-critical-sections.md) and the [semaphore sandbox](../../lectures/visualizations/pc-sandbox.html) |

> **Scenario:** QuantumTech sells widgets with a small Bash script. It works for one buyer. On a busy day, two buyers arrive at the same time and the shop sells widgets it does not have. You will see the problem, explain it, and repair it.

## Lab Objectives

After the Core, you can:

1. Read a short script and find its critical section.
2. Reproduce a race condition and show which rule it breaks.
3. Protect the whole critical section with a file lock and test it.

## How This Lab Works

| Command | What it does |
|---|---|
| `oslab values lab8` | Shows **your** numbers. Use them everywhere in this lab |
| `oslab predict lab8` | Saves your prediction once, before the experiment |
| `oslab hint lab8 1` | Gives a hint (levels 1, 2, 3). Hints cost no points |
| `oslab check lab8` | Tests your script and shows your milestones |
| `oslab checkpoint lab8` | Opens when the instructor says so, near the end |

- **Core** is for everyone. **Plus** and **Challenge** are for students who finish early. Full marks need only Core and the checkpoint.
- AI tools are allowed in Core, Plus and Challenge. They are **not** allowed in the prediction and the checkpoint.
- If AI gives you a fix, you must test it. In this lab you will see three AI fixes that look right and are wrong.

## Before the Lab

Do this before class. It takes about 10 minutes.

```bash
oslab doctor
oslab prelab lab8
```

## Timetable

| Minutes | Activity |
|---|---|
| 0–5 | Setup |
| 5–20 | Read and trace the script |
| 20–30 | Prediction, then class discussion |
| 30–50 | Core 1: break it |
| 50–75 | Core 2: fix it |
| 75–90 | Plus and Challenge (or finish Core) |
| 90–105 | Live checkpoint |
| 105–115 | Debrief |
| 115–120 | Submit |

## Setup (0–5)

1. Start the lab and go into its folder.

   ```bash
   export OSLAB_WORKSPACE="${OSLAB_WORKSPACE:-$HOME/oslab-work}"
   oslab start lab8
   cd "$OSLAB_WORKSPACE/lab8"
   mkdir -p evidence
   oslab values lab8
   ```

2. Type **your** three numbers into shell variables. The numbers below are only an example.

   ```bash
   stock=9
   buyer_a=7
   buyer_b=8
   ```

   If you open a new terminal, run `cd` and set these three variables again.

3. Your folder looks like this:

   ```text
   lab8/
   ├── store/
   │   ├── buy.sh          # the shop script: works for one buyer
   │   ├── stock.txt       # your starting stock
   │   ├── sales.log       # empty
   │   └── ai-answers/     # three "fixes" for the Plus task
   └── evidence/
   ```

## Read and Trace (5–20)

Do not run two buyers yet. First understand the script.

1. Read it with line numbers, then let one buyer buy one unit.

   ```bash
   cat -n store/buy.sh
   bash store/buy.sh 1
   cat store/stock.txt store/sales.log
   ```

2. Put the test data back. You will use these two lines many times.

   ```bash
   printf '%s\n' "$stock" > store/stock.txt
   : > store/sales.log
   ```

3. Answer in `evidence/trace.txt` (use `nano evidence/trace.txt`):
   - Which line **reads** the stock?
   - Which lines **change** a file?
   - After which line has the script decided "there is enough stock"?
   - Finish this rule: *units sold + units left = …*

## Prediction (20–30)

```bash
oslab predict lab8
```

Answer alone, without AI, before the experiment. A wrong prediction costs nothing. The class will look at the spread of answers together.

## Core 1 — Break It (30–50)

1. Run two buyers at the same time. `BUY_DELAY=1` makes the payment take one second, so the problem is easy to see.

   ```bash
   BUY_DELAY=1 bash store/buy.sh "$buyer_a" > evidence/a.txt 2>&1 &
   pid_a=$!
   BUY_DELAY=1 bash store/buy.sh "$buyer_b" > evidence/b.txt 2>&1 &
   pid_b=$!
   wait "$pid_a"; rc_a=$?
   wait "$pid_b"; rc_b=$?
   ```

2. Save what happened.

   ```bash
   {
     echo "start=$stock  A wants $buyer_a (exit $rc_a)  B wants $buyer_b (exit $rc_b)"
     cat evidence/a.txt evidence/b.txt
     echo "stock.txt now: $(cat store/stock.txt)"
     cat store/sales.log
   } | tee evidence/race.txt
   ```

3. Check the rule from your trace. How many units were sold? How many are left? Add one line to `evidence/race.txt` that says which number is wrong.
4. **Your decision.** Put the test data back. Choose two **small** quantities whose sum is less than your stock, so both sales are allowed. Run the two buyers again with your quantities. Is `stock.txt` correct now? Add your quantities, the result and one sentence to `evidence/race.txt`.
5. Run `oslab check lab8`. Two milestones pass and one does not. That is expected for now.

## Core 2 — Fix It (50–75)

1. Keep a copy of the unsafe script.

   ```bash
   cp -- store/buy.sh store/buy_unsafe.sh
   ```

2. Try `flock` alone first.

   ```bash
   (
       flock -x -w 2 9 || exit 3
       echo 'I hold the lock'
   ) 9>store/demo.lock
   ```

   `9>store/demo.lock` opens the lock file as file descriptor 9. `flock -x` asks for the lock, and `-w 2` waits at most two seconds. The lock ends when descriptor 9 is closed.

3. **Before you edit,** write in `evidence/trace.txt`: the first line and the last line of `buy.sh` that must be inside the lock, and why.
4. Edit `store/buy.sh` (`nano store/buy.sh`). Add the lock. You decide:
   - where the lock starts,
   - what the script does when it cannot get the lock (print a message, exit with status 3),
   - which lock file all buyers share.

   Keep the `BUY_DELAY` line.
5. Put the test data back, run the two buyers from Core 1 again, and save the result in `evidence/locked.txt` with the same block as before.
6. Run `oslab check lab8` until all three milestones pass.

Stuck for more than five minutes? Use `oslab hint lab8 1`, then `2`, then `3`.

**Core is complete when** `oslab check lab8` shows `milestones: 3/3` and your trace names the lines inside the lock.

## Plus — Review Three AI Answers (75–90)

Someone asked an AI assistant to fix `buy.sh`. It gave three answers: `store/ai-answers/a.sh`, `b.sh` and `c.sh`. Each one uses `flock`. Each one is wrong.

1. See what each answer changed.

   ```bash
   diff store/buy_unsafe.sh store/ai-answers/a.sh
   ```

2. Test an answer in a separate folder, so your own script stays safe.

   ```bash
   mkdir -p try
   cp -- store/ai-answers/a.sh try/buy.sh
   printf '%s\n' "$stock" > try/stock.txt
   : > try/sales.log
   BUY_DELAY=1 bash try/buy.sh "$buyer_a" & BUY_DELAY=1 bash try/buy.sh "$buyer_b" & wait
   cat try/stock.txt try/sales.log
   ```

3. For each of the three answers, write in `evidence/ai-review.txt`: the line that is wrong, and one sentence that says why two buyers can still be inside the critical section together.

## Challenge

Choose one. Save your commands and your explanation in `evidence/challenge.txt`.

- **Killed buyer.** Start one buyer of your fixed script with `BUY_DELAY=20` in the background, save its PID, and `kill` that PID while it holds the lock. Does the next buyer wait forever? Explain what the kernel does with the lock.
- **Smallest repair.** Make `ai-answers/a.sh` correct by moving lines only. Do not add or delete any line.

## Live Checkpoint (90–105)

Wait until the instructor opens it. Close AI tools. Work alone.

```bash
oslab checkpoint lab8
```

1. Answer the questions. They use new numbers, made for you at this moment.
2. Then make the small change to `store/buy.sh` that the command prints.
3. Run `oslab check lab8`. A fourth milestone, `checkpoint`, must pass.

You can do the checkpoint even if your Core is not finished: answer the questions first.

## Debrief (105–115)

Look at your prediction again.

```bash
cat "$OSLAB_WORKSPACE/.records/lab8-predict.json"
```

In your report, write **confirmed** or **corrected** for each answer, and explain in 3–5 sentences: why can the stock stay above zero while the shop sells too much, and which lines must share one lock?

## Submit (115–120)

1. Copy your work to your course repository. Replace the path with your own.

   ```bash
   SUBMISSION_REPO="$HOME/os-se-YOUR_ID/os-lab-YOUR_ID"
   mkdir -p "$SUBMISSION_REPO/lab8/evidence"
   cp -- store/buy.sh "$SUBMISSION_REPO/lab8/"
   cp -- evidence/trace.txt evidence/race.txt evidence/locked.txt "$SUBMISSION_REPO/lab8/evidence/"
   ```

2. Fill in the [report template](README.md) as `lab8/README.md`. Add `ai-review.txt` or `challenge.txt` if you did them.

   ```text
   lab8/
   ├── README.md
   ├── buy.sh              # your final script
   └── evidence/
       ├── trace.txt       # your reading of the script and the lock boundaries
       ├── race.txt        # the unsafe run and your own quantities
       └── locked.txt      # the same run after your repair
   ```

3. Commit and push in the usual way. Do not delete `store/stock.lock` while a buyer is running.

## Grading Criteria (10 points)

| Evidence | Points |
|---|---:|
| Working script: `oslab check lab8` passes the three Core milestones | 2 |
| Tests: unsafe run, your own quantities, and the run after repair | 2 |
| Prediction saved in time, and an honest confirmed/corrected explanation | 2 |
| Live checkpoint: answers, the change to your script, and your sentence | 3 |
| Clear, complete evidence files and report | 1 |

Plus and Challenge are not needed for full marks. They are noted in your feedback. Your prediction is marked for being made and corrected, not for being right.

## Help and References

- `oslab hint lab8 1`, `2`, `3`
- `man flock`
- Old wider topics (audit trail, drop box, log housekeeping) are in the [optional extensions](extensions.md).
