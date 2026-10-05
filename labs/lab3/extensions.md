# Lab 3 — Optional Extensions

Follow [the required instruction](lab3-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. More Wildcard Selection

1. In the owned lab folder, create `wildcards/` with `report1.txt`, `report2.txt`, `reportA.txt`, and `.report3.txt` using `touch`.
2. Predict before executing `printf '%s\n' wildcards/report?.txt` and `printf '%s\n' wildcards/report[0-9].txt`. Explain `?`, a character class, and why the hidden filename is excluded.
3. Test a nonmatching pattern with `printf`, then compare with `find wildcards -name 'missing*.txt'`. By default Bash leaves an unmatched glob literal; `find` interprets its quoted pattern itself. Do not use wildcard deletion for this task.

## B. Build and Load a User-local Shared Library

**Goal:** compile a reusable function and resolve it at runtime. Requires `gcc`; all output stays in your lab. Never register it with system `ldconfig`.

1. Create these two tiny sources.

   ```bash
   cd "$OSLAB_WORKSPACE/lab3"
   mkdir -p library
   cd library
   cat > greet.c <<'C'
   const char *greet(void) { return "hello from the library"; }
   C
   cat > main.c <<'C'
   #include <stdio.h>
   extern const char *greet(void);
   int main(void) { puts(greet()); return 0; }
   C
   gcc -Wall -Wextra -fPIC -shared greet.c -o libgreet.so
   gcc -Wall -Wextra main.c -L. -lgreet -o hello
   LD_LIBRARY_PATH="$PWD" ./hello
   ```

2. Predict whether `./hello` works without that environment assignment. Try it and record stderr; another loader configuration may affect the result.
3. Rebuild `greet.c` with a changed message and rerun the existing executable. Explain compile/link versus runtime loading. Limit `LD_LIBRARY_PATH` to this invocation rather than altering login configuration.

## C. GRUB Exploration and Recovery — Disposable VM Only

**Goal:** trace configuration to generated boot menu, then recover a transient boot mistake. Before starting, require a VM snapshot, working console, a known bootable kernel, and an instructor-tested recovery route. If those are absent, use a recorded demonstration and label recovery as untested.

1. Inside that VM, inspect `cat /etc/default/grub`, `ls /etc/grub.d`, and (if readable) `grep -n '^menuentry' /boot/grub/grub.cfg`. Explain source configuration versus generated output; menu entries can be nested/indented, so the grep is only a sample.
2. Snapshot and back up `/etc/default/grub` as an administrator. Using `sudoedit /etc/default/grub`, set a visible menu with `GRUB_TIMEOUT_STYLE=menu` and `GRUB_TIMEOUT=5`. Run `sudo update-grub`, inspect its messages, then reboot the VM and record the observed menu. Do not edit generated `grub.cfg` directly.
3. For a reversible boot fault, at the VM's GRUB menu press `e`, find the Linux kernel line, and replace only its `root=...` value with a deliberately nonexistent UUID provided by the instructor. Photograph the original line first. Boot the one-time edit with the displayed key (usually Ctrl-X or F10).
4. Observe the failure, then restart the VM and boot the unchanged saved entry. The interactive edit is not persisted. If the VM fails to return, restore its snapshot using the hypervisor console. Explain the wrong root mapping and why the saved entry still works.
5. Restore the original configuration/snapshot and demonstrate one normal boot. This exercise does not damage or reinstall GRUB itself. Bootloader installation/device recovery requires a separate instructor-tested VM exercise; never substitute a physical disk command on the server.

**Evidence:** source/config distinction, one VM boot observation and recovery record, or clearly labeled demonstration analysis. Consult the [GNU GRUB manual](https://www.gnu.org/software/grub/manual/grub/grub.html) for the VM version.
