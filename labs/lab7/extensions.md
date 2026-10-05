# Lab 7 — Optional Extensions

Follow [the required instruction](lab7-instruction.md) first. These procedures preserve the original lab's broader coverage and are not part of the 120-minute core.

Use your individual account on the shared Ubuntu server for unprivileged tasks. VM-only sections require a disposable snapshot and instructor preparation. State exactly what you executed versus interpreted from a supplied trace; extra tasks are not a prerequisite for full core credit.


## A. Personal PATH and Login Message

1. Copy your finished script into an owned `bin/` under this lab, then temporarily add it to PATH.

   ```bash
   cd "$OSLAB_WORKSPACE/lab7"
   mkdir -p bin
   cp -- count_words.sh bin/count-words
   chmod 700 bin/count-words
   previous_path=$PATH
   export PATH="$PWD/bin:$PATH"
   command -v count-words
   count-words 'input/one file.txt'
   export PATH="$previous_path"
   ```

2. Write `login-preview.sh` to print your username, time and a short reminder; run `bash login-preview.sh`. Explain when a real shell startup file would execute. Keep this a preview; do not automatically modify `.bashrc` or `.profile` for the lab.

## B. Owned Outbox and Harvester

1. Create `outbox/` and `harvested/`, then add `outbox/message 1.txt`. Build a script that loops over `"$base"/outbox/*.txt`, skips nonfiles (including unmatched literals), quotes each name, and copies to `harvested/` with `cp --`.
2. Test empty outbox, a filename with spaces, and two files. Compare source/destination contents and explain why unquoted `$@`, wildcard deletion and `eval` are unsuitable.
3. If the instructor has prepared a narrowly scoped cross-user drop box, inspect its permissions and use that exact path for a peer delivery test. No mandatory partner; the owned outbox is the individual equivalent. Do not open entire home directories or read other students' submissions.
4. Explain how ownership, directory traversal and write permissions affect delivery. The original SUID-helper idea is conceptual/VM-only: shell scripts are not a safe route to privileged student automation. Use an administrator-managed delivery service for any real privileged workflow.

**Evidence:** one successful delivery and one empty/error case, plus a permission explanation. Remove only your own test message copies after saving evidence.
