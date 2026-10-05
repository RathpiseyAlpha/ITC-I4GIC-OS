# Lab 6 — Optional Extensions

Follow [the required instruction](lab6-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. Account and Group Inspection

**Read-only server work:** use `id`, `groups`, `getent passwd "$USER"`, and `getent group "$(id -gn)"`. Explain UID, primary group and supplementary groups. Account creation and membership changes are administrator preparation, not student server tasks.

## B. ACL or Prepared Group Access

Requires instructor-provided peer username, a narrowly prepared test directory reachable by both accounts, and `getfacl`/`setfacl`. Do not broaden your home-directory permissions to make this work. If unavailable, use a labeled permission trace instead.

1. Set `TEST_DIR` to the instructor's exact owned test directory and `PEER` to the prepared account. Inspect `namei -l "$TEST_DIR"`, `id`, and `getfacl "$TEST_DIR"` before changes.
2. As the owner, create `acl-demo.txt`, mode 600, then grant only that peer read access with `setfacl -m "u:$PEER:r--" "$TEST_DIR/acl-demo.txt"`. Inspect the ACL and effective mask.
3. Peer tests `cat` and append using their own login. Expect read allowed and write denied, subject to parent traversal and mask. Record both actual outcomes; do not impersonate a peer or use their password.
4. Remove only the added entry with `setfacl -x "u:$PEER" "$TEST_DIR/acl-demo.txt"`; check the ACL and peer read failure again.

For a group alternative, the administrator prepares a dedicated group/directory. The owner can `chgrp PREPARED_GROUP` and use a justified mode such as 640 on the test file; verify membership and traversal first.

## C. Special Bits — Prepared Disposable VM

1. In an instructor-prepared two-account VM directory, compare a setgid collaboration directory (2770, dedicated group) and sticky writable directory (1770). The administrator supplies ownership/parent access.
2. Create one file per account. Inspect inherited group in the setgid case. In the sticky case, test whether the other ordinary account can remove the owner's file; compare the same isolated directory without sticky protection, then restore it.
3. Explain directory setgid inheritance versus sticky deletion restrictions. Read-only inspect a known system SUID executable's mode if available; do not create a privileged helper or run student code as root.

**Evidence:** modes/ACL, parent path and actual peer outcome. A single-user inspection alone cannot demonstrate peer access enforcement. Restore prepared directory policy after the exercise.
