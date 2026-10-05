# Lab 1 — Optional Extensions

Follow [the required instruction](lab1-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. APT Package Inspection and Management

**Goal:** distinguish package metadata from installation. Read-only inspection works on the server; installation/removal needs a disposable Ubuntu VM with a snapshot and administrator access prepared before class.

1. On Ubuntu, inspect a small package without changing the system.

   ```bash
   apt-cache policy tree
   dpkg-query -W -f='${Package} ${Version}\n' tree
   ```

   A missing installed package may make `dpkg-query` return nonzero. Record the candidate versus installed version; the cache may be stale.
2. **VM only:** take a snapshot, confirm `tree` is not needed by the VM, then install it.

   ```bash
   sudo apt update
   sudo apt install tree
   tree --version
   ```

3. Inspect `apt-cache policy tree` again. If you installed it for this exercise, remove that package with `sudo apt remove tree`, inspect the result, then restore the snapshot. Do not remove packages that were present beforehand. Record what changed and what removal leaves behind. Do not run system upgrades or `autoremove` for this exercise.

## B. Virtualization and Process Observation

1. Use `systemd-detect-virt` if available, then inspect `lscpu`. An output such as `wsl` or `kvm` describes a detected environment, not proof that the server is physical or that you can create VMs.
2. Start one `sleep 15`, capture `$!`, and compare `ps -o pid,ppid,stat,comm -p "$pid"` with `top -b -n 1 -p "$pid"`. Finish with `wait "$pid"`; do not inspect or signal arbitrary classmates' processes.
3. Explain why a installed executable remains after its process exits. Save one package observation and one environment/process observation if you choose this extension.
