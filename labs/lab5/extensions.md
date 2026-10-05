# Lab 5 — Optional Extensions

Follow [the required instruction](lab5-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. Process versus Thread Memory

1. Adapt your joined two-worker program so a worker changes a dedicated field and main prints that field only after joining. Explain the shared address space.
2. Write a separate small `fork()` program: set an integer to 1, change it to 9 only in the child, have the parent `waitpid`, and print each process's value/PID. Check `fork`/`waitpid` errors and flush streams before `fork`.
3. Compile with warnings and bound each run with `timeout 5`. Predict the parent's value; separate memory after `fork` differs from per-thread shared memory. Neither example models intentionally shared memory between processes.

## B. LWP and Kernel Worker Observation

1. In an owned copy of the joined program, increase the bounded worker delay to two seconds per step, leaving at most three steps. Run it in background, capture `$!`, then use `ps -L -p "$pid" -o pid,lwp,nlwp,comm`.
2. Compare process PID with thread/LWP IDs while alive; `wait "$pid"` at finish. A late sample may miss workers.
3. Read `ps -eo pid,ppid,comm | head -n 20` for context. Kernel worker names may appear in a host but be hidden by a container/WSL. Do not claim their absence proves no kernel threads.

## C. Controlled Signal Handling

1. In a separate C demo, register SIGTERM with `sigaction`; the handler should only set a `volatile sig_atomic_t` flag. Print/cleanup in the normal main loop after checking that flag, rather than calling `printf` from the handler.
2. Keep a ten-second upper bound. Start it, record its own PID, and promptly send `kill -TERM "$pid"`. Compare graceful termination with default signal handling and inspect exit status.
3. Explain why a join waits for completion while a mutex protects an operation on shared mutable data; a signal flag is not a general thread synchronization mechanism.

Consult `man pthread_join`, `man sigaction`, and `man signal-safety`. Save source and one decisive observation; do not signal another user's process.
