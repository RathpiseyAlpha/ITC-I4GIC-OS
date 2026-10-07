# Lab 1 — Optional Extensions

Follow [the required instruction](lab1-instruction.md) first. These are extra tasks and are not needed for full marks.

Do the APT tasks on your own Ubuntu (WSL or a virtual machine), where you have `sudo`. Do not run `sudo` commands on the course server.

## A. More About APT

1. Look at a package before you install it. These commands only read information.

   ```bash
   apt-cache policy mc
   apt list --installed | grep mc
   ```

   `Installed: (none)` means it is not installed. `Candidate` is the version APT would install.

2. `update` and `upgrade` are different. `sudo apt-get update` only refreshes the list of available software. `sudo apt-get upgrade` installs newer versions of what you already have. Always run `update` first. Run `upgrade` only on your own machine, and read what it wants to change before you answer `Y`.

3. Install `tree`, then use it on your lab folder to see its structure.

   ```bash
   sudo apt-get install tree -y
   tree ~/os-gic-YOUR_ID
   ```

## B. More About Virtual Machines

1. Run `lscpu` without `grep` and find the lines about the hypervisor. Run `systemd-detect-virt` on your own Ubuntu and on the server. Do they give the same answer? Why?
2. A virtual machine can run inside another one. Look at `hostname` and `uname -r` on both machines. Which values are the same, and which are different?
