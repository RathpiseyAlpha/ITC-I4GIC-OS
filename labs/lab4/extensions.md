# Lab 4 — Optional Extensions

Follow [the required instruction](lab4-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. Redirection Order and Process Signals

1. In your lab, compare the two files created below. Explain where stderr is routed in each order.

   ```bash
   cd "$OSLAB_WORKSPACE/lab4"
   bash -c 'echo normal; echo problem >&2' > evidence/both.txt 2>&1
   bash -c 'echo normal; echo problem >&2' 2>&1 > evidence/only-out.txt
   ```

2. Start exactly one owned process and save its PID in this shell.

   ```bash
   sleep 30 & pid=$!
   ps -o pid,ppid,stat,comm -p "$pid"
   kill -STOP "$pid"
   ps -o pid,stat,comm -p "$pid"
   kill -CONT "$pid"
   kill -TERM "$pid"
   wait "$pid"; printf 'wait status=%s\n' "$?"
   ```

   Execute promptly: if the process has already exited, stop and start a fresh owned `sleep`; never reuse an old PID or use broad `pkill`. Predict state `T` while stopped. A signal-related nonzero wait status is expected, rather than arithmetic-report failure.

## B. Bounded Zombie and Orphan Observation

Requires a compiler. Run in local Linux/WSL or a disposable VM, for at most eight seconds; no root needed.

1. Create `process_demo.c` with a `fork()`: child prints its PID/PPID and exits; parent prints both IDs, waits two seconds, calls `waitpid(child, NULL, 0)`, then exits. Flush output before `fork`; check errors. Compile with `gcc -Wall -Wextra process_demo.c -o process_demo`.
2. Run it in background under `timeout 8`. From another shell inspect only the printed child PID before `waitpid` and after it. Explain the exited-but-not-reaped `Z` interval. Sampling may miss it.
3. Change the child to sleep two seconds and the parent to exit immediately. Have the child print PPID before/after the delay; keep the outer bound. Explain reparenting. Do not assume the new parent is always PID 1; containers/subreapers can change that result.
4. Confirm both bounded runs finish and preserve one process-state record. Do not create repeated zombie loops or leave background processes running.
