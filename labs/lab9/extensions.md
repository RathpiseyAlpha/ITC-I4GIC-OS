# Lab 9 — Optional Extensions

Follow [the required instruction](lab9-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. Resource Graph and Timeout Recovery

1. From the core opposite-order logs, draw edges A→beta, beta→B, B→alpha, alpha→A while each worker holds its first lock. Mark when a timeout releases a descriptor and breaks the cycle.
2. Run A alone in opposite mode under `timeout 6`; record the barrier timeout. Compare missing partner with circular wait: both block progress, but their wait graphs differ.
3. Run the ordered pair twice, at most two workers per run. Identify the shared alpha-before-beta rule and explain why it removes the modeled circular wait without promising fairness.
4. Preserve acquisition/wait limits. Compare what happens when a first lock is deliberately held in a separate owned shell for three seconds; the worker should fail within its lock timeout. Close/release that descriptor afterwards.

## B. Optional Partner Demonstration

An administrator must prepare a small shared vault with dedicated group/ACL and a common lock directory. Both accounts must lock the **same files**, not their private copies. Inspect traversal and ownership before use; no broad home access.

1. Agree role A/B and launch one worker each with the instructor's prepared variant. Bound the run to six seconds and collect each local log/status.
2. Clear readiness markers only after both workers have exited, then apply the same resource order in both scripts and rerun.
3. Compare with the single-account two-process core. The individual equivalent meets core objectives; no partner is required for marking.

**Cleanup:** wait for both owned PIDs and remove only the lab's readiness files after exit. Removing a live lock pathname can create a second inode and invalidate the intended coordination; keep lock files until all participants have stopped.
