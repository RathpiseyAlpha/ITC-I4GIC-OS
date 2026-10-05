# Lab 8 — Optional Extensions

Follow [the required instruction](lab8-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. Inventory Conservation and Stronger Tests

1. Restore stock to 5 and empty the **owned test** sales log. Run requests for 1 and 2 with your repaired script; record final stock and sold units.
2. Compute sold units, rather than merely counting log lines.

   ```bash
   awk '$1 == "sold" {sum += $2} END {print "sold units:", sum+0}' store/sales.log
   cat store/stock.txt
   ```

3. Check `initial stock = final stock + accepted sold units`. Repeat a bounded concurrent pair with quantities whose sum exceeds 5, using the core's saved-PID/wait method. At most two buyers per run; no stress loop on the shared server.
4. Inject invalid stock in an owned copy (for example `abc`), then test input validation and confirm no sale is logged. Restore the fixture afterwards.
5. Explain limits: advisory locks require every writer to participate; a crash between stock and log writes can still break durability. Do not claim this teaching script is a transactional database.

## B. Prepared Drop Box and Log Housekeeping

If the instructor supplies a narrow cross-user directory, verify its parent traversal, group/ACL and naming policy before sending one test request. Use your own account; the local single-account store remains valid if no partner is available. Never run a privileged exploit or SUID student helper.

For owned housekeeping, copy `store/sales.log` to a uniquely named evidence file before starting a new case. Do not rotate an active log while a buyer is running; finish both saved PIDs first. Remove only known owned demonstration records, not wildcard-matched classmates' logs.

**Evidence:** invariant calculation plus one contradictory test condition. A successful run supports the case tested and does not prove all interleavings correct.
