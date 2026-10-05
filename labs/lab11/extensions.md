# Lab 11 — Optional Extensions

Follow [the required instruction](lab11-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core. Lab 11 itself is optional bonus work.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. Optional FUSE Image Mount

**Goal:** observe a mounted image as a filesystem. Require an instructor-tested `fuse2fs`, `/dev/fuse` access and a supported `fusermount` tool. Container/WSL setups may lack these. The core does not need a mount.

1. Inspect `command -v fuse2fs`, `ls -l /dev/fuse`, and the installed `fuse2fs --help`/manual. Use only your formatted 32 MiB regular image, no loop devices or real partitions. Verify its exact path and type again.
2. In the owned lab create `mountpoint/`, verify it is empty and not already mounted, then invoke the locally supported command (normally `fuse2fs images/scratch.img mountpoint`). If it fails, stop and record the error; do not use sudo to bypass it.
3. If mounted, check `mountpoint mountpoint` and `findmnt -T "$PWD/mountpoint"`. Depending on the tool/default options it may be read-only; test only one small owned file if write access is explicitly available. Record `df -hT mountpoint` versus `du -sh mountpoint` and explain what each measures.
4. Unmount with the prepared tool (`fusermount -u mountpoint` or `fusermount3 -u mountpoint`), then verify `mountpoint mountpoint` returns nonzero and `findmnt` no longer identifies an image mount there. Do not clean/delete while mounted.
5. If unavailable, interpret a supplied mount/df trace and label it **not executed locally**. Do not claim practical mount competence from a trace.

## B. Filesystem Check and Resize — Unmounted Owned Image Only

Requires `e2fsck` and `resize2fs`, quota for at most 64 MiB, and no mount. Use a separate disposable copy of your image so core evidence remains unchanged.

1. Verify there is no active image mount, then `cp -- images/scratch.img images/resize-demo.img`. Check `test -f images/resize-demo.img && test ! -L images/resize-demo.img` and its resolved path inside your workspace.
2. Run `e2fsck -fn images/resize-demo.img` as an ordinary user for a read-only check; interpret its exit status using the local manual. Never check/repair a mounted image or substitute a device path.
3. Increase only that owned regular file with `truncate -s 48M images/resize-demo.img`, then run `resize2fs images/resize-demo.img`. Inspect `dumpe2fs -h` and compare block count×size before/after. File enlargement alone does not enlarge the contained filesystem.
4. Do not shrink, deliberately corrupt, or exceed the size bound in this exercise. If tools decline the operation, preserve the message rather than escalating privileges.

## C. Read-only Usage Diagnostic

Build a short script accepting one owned directory, rejecting a missing/non-directory argument, then reporting `df -hT`, `du -sh`, and the apparent versus allocated size of your image. Test one valid and one missing path. Save only the script and concise records; large images remain outside submission.

**Cleanup:** confirm every mount is unmounted, save evidence, then remove only the named owned regular images. `oslab reset` deliberately refuses an archive over 2 MB; it is not a large-image backup service.
