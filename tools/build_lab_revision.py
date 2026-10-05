"""Build the first-revision teaching set from reviewed topic specifications."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# title, environment, prerequisites, targets, guided command, mechanism question,
# prediction, investigation, constraints, tests, changed case, answer, extensions, hints
LABS = {
1: ("OS inspection and owned processes", "shared Ubuntu account", "login, terminal, basic commands",
"identify kernel and distribution from evidence; distinguish a program from a running process; trace one owned process through start and exit",
"uname -s; cat /etc/os-release | head -6; sleep 10 & pid=$!; ps -o pid,ppid,stat,comm -p \"$pid\"; wait \"$pid\"",
"Which output describes installed software, and which describes a live instance?",
"If two `sleep 10` commands start, will they share a PID? Why?",
"Start two bounded `sleep` processes in your account. Record PID, PPID and state while alive, then check after `wait`. Explain which observations establish process identity and which only identify the executable.",
"Only signal your own PID. Do not install packages or alter the shared server.",
"Run once normally and once with `sleep 1`; check both while live and after exit. A missed snapshot does not prove the process never existed.",
"A script starts `sleep 1` twice in the background. Predict how many PIDs can be captured and whether `ps` must show both after two seconds.",
"Two distinct PIDs can be captured; after two seconds both may already have exited. Award for timing reasoning.",
"APT package management in a disposable VM; hypervisor detection; compare `top` and `ps`.",
"A process is an execution instance; inspect `$!` and `ps`; shorten duration and collect evidence promptly."),
2: ("Navigation and file placement", "shared Ubuntu account", "Lab 1 shell navigation",
"use absolute and relative paths correctly; move two files without losing their names; diagnose a path error",
"pwd; mkdir -p practice/reports; printf 'a\\n' > 'practice/quarter 1.txt'; mv -- 'practice/quarter 1.txt' practice/reports/; find practice -maxdepth 2 -type f",
"How does the destination change if the current directory changes?",
"From the fixture's `incoming` directory, where would `mv 'quarter 1.txt' ../reports/` place the file? Explain `..`.",
"The two quarterly files are misplaced in `incoming`. Move them to `reports` preserving names; show one absolute and one relative path that reach a report from different working directories.",
"Edit only your lab2 workspace. Quoted names contain spaces; do not overwrite a report without checking.",
"Check both filenames and contents; try from the workspace root and `incoming`. A path that works only from one directory is not generally correct.",
"Current directory becomes `reports`. Explain why `cat incoming/'quarter 1.txt'` fails and give a working relative path.",
"From reports use `../incoming/...`; after the move the source no longer exists, so the working report path is `./quarter 1.txt`. Credit recognition of both facts.",
"Company directory tree, wildcards and directory audit from the original lab.",
"Identify current directory; use `pwd` and `find`; trace each path component before moving."),
3: ("Links and user-local libraries", "shared Ubuntu account; disposable VM only for GRUB extension", "Lab 2, basic C compiler for library extension",
"distinguish inode sharing from path indirection; repair a broken symbolic link; predict a link's response to target replacement",
"cd \"$HOME/oslab-work/lab3/links\"; ln source.txt hard.txt; ln -s source.txt soft.txt; ls -li source.txt hard.txt soft.txt; readlink soft.txt",
"Which links name the same inode, and which stores a path?",
"If `source.txt` is renamed, which link still reads the original bytes? Explain.",
"Inspect `source.txt`, a hard link and a symlink in your own workspace. Rename the source, observe both links, then repair the symlink without replacing the hard link. Record inode and path evidence.",
"Keep changes inside the lab workspace; no shared-server GRUB changes, `ldconfig`, or system library registration.",
"Test before and after rename and after repair; also test a deliberately missing symlink target. Inode equality establishes hard-link identity on one filesystem.",
"A symlink points to `../source.txt` from inside `links/`. Predict where it resolves and explain whether it works.",
"It resolves from the symlink's directory to the workspace root's `source.txt`, which is absent in the fixture. Credit correct relative resolution.",
"Wildcard selection; build a shared object with `gcc -fPIC -shared` and use a user-local loader path; GRUB observation and recovery only in a snapshot-backed disposable VM with instructor supervision.",
"Compare inodes; inspect `readlink`; draw the path relative to the symlink's directory."),
4: ("Pipelines, redirection and owned processes", "shared Ubuntu account", "Lab 2, `grep`, `cut`, `awk` basics",
"predict pipeline data flow; produce the correct filtered total; distinguish stdout from stderr",
"printf 'ok,3\\nfail,2\\n' | grep '^ok,' | cut -d, -f2; printf 'error\\n' >&2",
"Which stream enters the next pipeline command?",
"Will `grep ok data/events.csv | cut -d, -f2` include the header or all successful counts? Why?",
"The report says `ok total: 8`, but a flawed pipeline selects only one row or wrong fields. Build a pipeline that counts all `ok` values from `events.csv`, store output in your workspace, and explain each stage.",
"Read fixture input; write only your workspace. Any process demonstration uses your own bounded `sleep`, not system processes.",
"Test expected data (3+5), no matching rows, and an extra `ok,0` row. Explain whether exit status alone proves arithmetic correctness.",
"Add a row `ok,7`. Predict the new total, then identify which stage needs no change.",
"Total becomes 15; filter and field extraction remain valid. Credit explanations of aggregation.",
"Redirection combinations; process tree; bounded orphan/zombie observation in a disposable local environment.",
"Check row selection; inspect fields with `cut`; sum only after validating intermediate output."),
5: ("Processes, threads and joins", "shared Ubuntu account; C compiler", "process basics, C source reading",
"distinguish process and thread address spaces; explain why joining matters; diagnose a missing join from a trace",
"printf 'thread,step\\nA,read\\nB,read\\nA,write\\nB,write\\n' | column -s, -t 2>/dev/null || cat \"$HOME/oslab-work/lab5/threads/trace.csv\"",
"Can the trace alone prove the program was race-free?",
"If main returns before joining a worker, must the worker's final print appear? Why?",
"Use the provided trace to mark overlapping steps; write a minimal pthread program with two workers and joins in your workspace, and compare observed order to your prediction. Explain why joins ensure completion but do not protect a shared counter.",
"Compile and run only your own code, without elevated privileges. Set bounded loop counts and a 10-second timeout.",
"Run a normal case and a changed loop count; verify both workers finish. A successful run does not prove race absence.",
"Main joins only worker A. Can worker B's result be safely read? Explain the minimal change.",
"No completion guarantee for B; join B before reading its result. Credit discussion of synchronization.",
"Kernel worker observation with `ps`; owned-process signals; compare processes and threads using `/proc`.",
"Separate completion from mutual exclusion; inspect `pthread_create` return values; join each created thread."),
6: ("Permissions and access decisions", "shared Ubuntu account", "octal permissions, Lab 2 paths",
"interpret file and directory permissions; set least-privilege access in an owned tree; diagnose a traversal failure",
"mkdir -p \"$HOME/oslab-work/lab6/demo\"; printf 'x\\n' > \"$HOME/oslab-work/lab6/demo/a\"; chmod 700 \"$HOME/oslab-work/lab6/demo\"; stat -c '%A %n' \"$HOME/oslab-work/lab6/demo\"",
"Which permission controls entering a directory?",
"If a file is mode 644 inside a directory mode 700, can another user read it? Explain each path component.",
"Inspect `private/record.txt` and `shared/notice.txt`; set and justify modes for owner-only record edits and read-only notice in your owned tree. Use `namei -l` if available to explain traversal.",
"Do not create accounts/groups, change another user's files, open home directories broadly, or use SUID. Administrator-prepared identities are an optional extension.",
"Test owner read/write and attempted execute, then reason about a peer using path permissions. Actual multi-user check requires instructor preparation.",
"Directory is 711 and file 600. A peer knows the filename. Can they read it? Which mode is decisive?",
"They can traverse directory but cannot read file. Credit distinction between directory search and file read.",
"ACLs, groups, sticky bit, and narrowly prepared two-account testing on a disposable VM or administrator-approved directory.",
"Check every parent directory; use `stat`/`namei`; change only one permission at a time."),
7: ("Bash arguments and safe paths", "shared Ubuntu account", "Lab 2, Bash basics",
"quote arguments containing spaces; handle a filename beginning with `-`; explain how script arguments map to files",
"bash -c 'printf \"argc=%s\\n\" \"$#\"; for item in \"$@\"; do printf \"<%s>\\n\" \"$item\"; done' _ 'one file.txt' '-dash.txt'",
"What changes if `$@` is unquoted?",
"If a script receives `one file.txt` as one argument, what happens with `for x in $@`? Why?",
"Build a Bash script that prints a labeled word count for each file argument, including `input/one file.txt` and `input/-dash.txt`. Reject missing inputs with a useful exit status. Use `--` where a utility parses filenames as options.",
"Edit scripts and fixture copies in your workspace; avoid `eval`, unquoted expansion and SUID helpers.",
"Test one file, both files, a missing file, and a path with spaces. Inspect exit status and output labels.",
"A filename is `-dash.txt` in the current directory. Explain why `wc -w -dash.txt` may fail and give a safe invocation.",
"`wc -w -- ./-dash.txt` is safe; `--` ends option parsing. Credit use of `./` with correct quoting.",
"PATH configuration, message scripts, narrowly prepared shared directories; cross-user automation only with instructor setup.",
"Print argument boundaries; use `\"$@\"`; test `--` and `./` for leading dash names."),
8: ("Stock race and complete critical section", "shared Ubuntu account; `flock`", "Bash conditionals and bounded background jobs",
"validate purchase quantities; identify the read-check-write critical section; use a lock covering the full update",
"( flock -x -w 2 9 && printf 'lock acquired\\n' ) 9>\"$HOME/oslab-work/lab8/store/stock.lock\"",
"Does locking only the final write protect a preceding stock check?",
"Stock is 5. Two buyers each request 4. If both read before either writes, what invalid outcome can occur?",
"Create a purchase script in your lab8 workspace. It reads stock, rejects invalid or excessive quantities, updates stock and appends a sale log. Use a short teaching delay between read and write to observe a race, then protect the full read-check-write-log sequence with `flock -w 2`. Remove the delay for final version.",
"Use at most two concurrent buyers, positive integer quantities, stock never below zero, and a timeout. Work only with owned files.",
"Test valid purchase, zero/negative/noninteger, too-large purchase, and two buyers requesting 4 from stock 5. Repeat controlled runs; success alone cannot prove race absence.",
"Stock becomes 3. Two buyers request 2. Predict number of accepted purchases under correct locking and final stock.",
"One accepted, one rejected, final stock 1. Credit an invariant-based explanation.",
"Audit log design; red-team review of a classmate's test only by consent; permission setup on prepared accounts.",
"Write the invariant; place lock before read; keep validation and update inside one lock scope."),
9: ("Deadlock diagnosis and recovery", "shared Ubuntu account; `flock`", "Lab 8 locking",
"draw a wait-for cycle; reproduce bounded opposite ordering; prevent deadlock with one global order",
"( flock -x -w 2 9 && printf 'Alpha acquired\\n' ) 9>\"$HOME/oslab-work/lab9/vault/alpha.lock\"",
"What happens if both workers hold one lock and request the other?",
"Worker 1 holds Alpha then requests Beta; worker 2 holds Beta then requests Alpha. Predict each wait edge.",
"Write two short scripts that acquire owned Alpha/Beta lock files in opposite order, with a coordination barrier or documented teaching delay. Use `flock -w 2` for every acquisition. Capture a wait trace, then change both scripts to Alpha-before-Beta and explain why the cycle disappears.",
"At most two workers; each has a five-second outer timeout; no broad `pkill` or partner dependency. Release through process exit or normal descriptor close.",
"Run the deliberately conflicting case and the ordered case; inspect exit codes. Timing may prevent the deadlock observation on a given run.",
"A third worker needs Beta only. Does global Alpha-before-Beta require it to lock Alpha? Why?",
"No: one-lock work has no order conflict. Credit explanation of cycle prevention.",
"Partner site-to-site scenario only in a narrowly prepared shared directory; timeout recovery policy.",
"Draw holdings and requests; verify both processes reached the barrier; use consistent acquisition order."),
10: ("Backup retention and scoped scheduling", "shared Ubuntu account; per-user cron if available", "Bash, tar, paths",
"create and verify a backup archive; retain a bounded number of owned archives; diagnose cron's restricted environment",
"tar -czf \"$HOME/oslab-work/lab10/test.tar.gz\" -C \"$HOME/oslab-work/lab10\" project; tar -tzf \"$HOME/oslab-work/lab10/test.tar.gz\"",
"Does creating an archive prove it can restore the expected files?",
"A cron entry uses `backup.sh` without an absolute path. Will it necessarily run if the command works interactively? Why?",
"Build an idempotent backup script for the fixture `project/`, verify archive members and a restore into a new owned directory, then retain the newest three lab-owned archives. If user cron is available, run `lab10-cron install`, observe `cron.log` after the next minute, then run `lab10-cron remove`; the helper changes only its marked practice entry.",
"No dated graded jobs. Cron has five ordinary fields and no year field; a date entry recurs unless separately guarded/removed. Never use `crontab -r`. Use `TZ=Asia/Phnom_Penh` only after checking server cron timezone behavior.",
"Test two backups with changed content, restore, retention after four archives, and cron log within two minutes. If cron is unavailable, run script with `env -i HOME=... PATH=/usr/bin:/bin` and explain the fallback.",
"A cron command uses `tar` but its script assumes current directory is `project`. Identify one robust correction.",
"Use absolute workspace paths or `cd` after checking success. Credit explicit environment reasoning.",
"Log rotation, health checks, and custom scheduled jobs; schedule dates only from instructor-supplied class date and timezone with a one-shot guard.",
"Inspect archive members; restore to a temporary owned folder; record cron's PATH and HOME explicitly."),
11: ("Regular-file disk images and filesystem evidence (bonus)", "shared Ubuntu account for image files; FUSE optional", "Lab 2 and storage lecture",
"distinguish file size from allocated blocks; create and inspect a regular image; explain filesystem metadata from safe evidence",
"truncate -s 32M \"$HOME/oslab-work/lab11/images/scratch.img\"; ls -lh \"$HOME/oslab-work/lab11/images/scratch.img\"; du -h \"$HOME/oslab-work/lab11/images/scratch.img\"",
"Why can apparent size and allocated space differ?",
"For a sparse 32 MiB image, will `du` necessarily show 32 MiB? Why?",
"Create a regular 32 MiB sparse image under `images/`; compare `ls -l`, `du`, and `stat`. If `mkfs.ext4` and `dumpe2fs` are installed, format only that regular file and inspect its superblock. Explain how formatting changes allocation.",
"Never name `/dev/*` or a block device as a target. Check `test -f` and `readlink -f` before formatting. No sudo or loop mounting.",
"Inspect empty sparse image and formatted image; compare apparent and allocated sizes. FUSE mounting is optional and requires local capability checks.",
"A second image is created with `dd if=/dev/zero ...` and fully written. Predict `du` relative to a sparse image of equal apparent length.",
"Fully written image typically allocates more blocks; filesystem compression/deduplication can affect exact figures. Credit distinction.",
"FUSE mount with `fuse2fs` only if available and permitted; resize and e2fsck on an unmounted regular image; custom diagnostic script.",
"Check file type; compare `stat -c '%s %b %B'`; use `dumpe2fs -h` only after formatting."),
}

TIMETABLE = [("0–10", "Opening question and safety/setup"), ("10–25", "Guided example"),
             ("25–35", "Prediction on paper; five-minute optional peer comparison"),
             ("35–70", "Individual investigation or build; AI optional"),
             ("70–85", "Normal and edge tests; feedback pause"),
             ("85–100", "Individual changed case, supervised; no AI or peers"),
             ("100–110", "Evidence-based correction and concept explanation"),
             ("110–120", "Cleanup and concise submission")]

READINGS = {
    1: "[Week 1 notes](../../lectures/notes/week01-introduction-to-os.md) and `man ps`",
    2: "[Lab 2 visual guide](guides/slides.html) and `man mv`",
    3: "[Lab 3 visual guide](guides/slides.html), `man ln`, and `man readlink`",
    4: "[Lab 4 visual guide](guides/slides.html), `man grep`, and `man cut`",
    5: "[Week 4 notes](../../lectures/notes/week04-threads-multicore.md) and `man pthread_join`",
    6: "[Lab 6 visual guide](guides/slides.html) and `man chmod`",
    7: "[Bash manual](https://www.gnu.org/software/bash/manual/bash.html) and `man wc`",
    8: "[Week 7 notes](../../lectures/notes/week07-critical-sections.md) and `man flock`",
    9: "[Deadlock visualization](../../lectures/visualizations/rag-deadlock.html) and `man flock`",
    10: "[crontab manual](https://man7.org/linux/man-pages/man5/crontab.5.html) and `man tar`",
    11: "[Week 12 notes](../../lectures/notes/week12-file-systems.md), `man du`, and `man mkfs.ext4`",
}
STARTERS = {
    5: "Use `threads/starter.c`; compile with `gcc -Wall -Wextra -pthread threads/starter.c -o threads/demo`. Keep the TODO as your own decision point.",
    7: "Use `count_words.sh` as a starting skeleton. Try `bash count_words.sh 'input/one file.txt' 'input/-dash.txt'`.",
    8: "Use `store/buy.sh` as a starting skeleton. Keep stock and log in `store/`; put `stock.lock` there too.",
    9: "Use `vault/worker.sh` as a starting skeleton. Use separate Alpha and Beta lock files in `vault/`.",
    10: "Use `backup.sh` as a starting skeleton; keep archives in an owned `backups/` directory. Use `lab10-cron status` to inspect the practice entry.",
}
SOLUTION_SKETCHES = {
    1: "Capture each `$!` immediately, inspect with `ps -p`, then `wait` each PID. Distinct process instances have distinct PIDs while alive; a later `ps` may miss exited processes.",
    2: "From the workspace root, `mv -- incoming/'quarter 1.txt' incoming/'quarter 2.txt' reports/`; verify with `find reports -maxdepth 1 -type f` and `cat` both files.",
    3: "`ln source.txt hard.txt` shares an inode; `ln -s source.txt soft.txt` stores a path. After rename, hard.txt still reads the old bytes. Recreate soft.txt with a target path that exists from the symlink's directory.",
    4: "Filter `^ok,`, extract the numeric second field, and sum all selected values with `awk -F, '$1==\"ok\" {s+=$2} END {print s+0}' data/events.csv`. Accept a correct grep/cut/awk pipeline too.",
    5: "Check each `pthread_create` result and join both thread IDs before consuming results. Joins establish completion; add a mutex or atomic operation only if the workers share mutable data.",
    6: "A private file can use 600 inside a searchable owner-only directory 700. A notice can use 644 only if every parent allows intended readers to traverse; avoid widening home permissions on the shared server.",
    7: "Loop with `for path in \"$@\"`, check `[[ -f $path ]]`, then call `wc -w -- \"$path\"`. A leading-dash filename can also be prefixed by `./`.",
    8: "Validate `^[1-9][0-9]*$`, open a dedicated lock descriptor, `flock -x -w 2` before reading stock, and keep read, sufficiency check, write and sale log inside the same scope. Compare two requests for four units from stock five: exactly one may succeed.",
    9: "A holds Alpha and waits for Beta while B holds Beta and waits for Alpha. Draw both edges. Timeouts bound the demonstration. In the repair, both workers acquire Alpha then Beta; no cycle can form.",
    10: "Use `tar -czf` with `-C` and an absolute source directory, then `tar -tzf` and restore to a new owned folder. Enumerate only lab-owned archive names and retain the newest three. Cron practice is installed/removed by `lab10-cron`.",
    11: "`truncate -s 32M images/scratch.img` creates an apparent size of 32 MiB with few allocated blocks. `du` reports allocation; `ls -l` reports length. After checking it is a regular file, `mkfs.ext4 -F` may allocate metadata blocks.",
}
SOLUTION_ASSETS = {
    8: "See `buy_flawed.sh` and `buy_solution.sh` in this directory. The first deliberately demonstrates a stale-read race with a one-second teaching delay; the second locks the entire update.",
    9: "See `worker_solution.sh` in this directory. Its barrier coordinates opposite-order acquisition; every wait is bounded. In ordered mode the barrier is skipped so both workers can complete.",
}
AUDIT = {
    1: ("OS identification, command guidance, process and virtualization observations", "APT install/upgrade and host-to-WSL transfer from required route"),
    2: ("path examples, company file tree, navigation challenges", "repeated screenshot and cross-environment submission sequence"),
    3: ("wildcard/link examples, GRUB and shared-object references", "shared-server GRUB/system-library changes and mandatory pair build"),
    4: ("redirection/pipeline references and process observations", "unbounded orphan/zombie production from required route"),
    5: ("pthread examples, kernel worker observations and signal review", "broad multi-task scope and non-owned signal targets"),
    6: ("permissions/ACL reference and drop-box challenge", "account creation, SUID and broad home access from ordinary-user core"),
    7: ("Bash/PATH examples and automation challenges", "SUID helper and mandatory cross-user dependency"),
    8: ("stock exploit, observation checkpoints and flock repair", "mandatory partner red-team and unrelated cleanup levels"),
    9: ("vault lock ordering and timeout recovery", "mandatory partner site-to-site setup"),
    10: ("archive/cron examples, retention and environment trap", "expired dated graded jobs and false one-time cron wording"),
    11: ("disk inventory, image/FUSE examples and bonus status", "sudo loop-mount fallback and real-device ambiguity"),
}
EXTENSION_TASKS = {
    1: ["On a disposable VM, inspect APT policy for one package and explain candidate versus installed version without changing the shared server.", "Compare `ps` and `top` snapshots of two owned bounded processes; explain why snapshots differ."],
    2: ["Rebuild the original company-style directory tree in your own workspace and write two navigation routes to the same file.", "Audit duplicate basenames in different folders and explain how relative paths disambiguate them."],
    3: ["Use a wildcard to select only `.txt` files, then show a counterexample for an overbroad pattern.", "Build a user-local shared object in a VM or account with `gcc`, load it with a private path, and compare with a missing-library failure. GRUB work is separately VM-only after snapshot and recovery preparation."],
    4: ["Send stdout and stderr to separate owned files and explain the resulting line counts.", "Run a bounded owned child process and inspect its parent/child relationship before and after exit. Do not manufacture persistent zombies on the shared server."],
    5: ["Observe kernel workers with `ps` without sending them signals; compare user threads in `/proc`.", "Add one shared counter and protect it with a mutex; state why joins alone are insufficient."],
    6: ["Compare a mode-bit decision with an ACL decision in an instructor-prepared narrow shared directory.", "On a disposable VM, test a sticky directory with two prepared accounts; keep both homes private."],
    7: ["Create a personal `~/bin` script and show how PATH changes command lookup.", "Design a safe personal automation script that handles one filename containing spaces and one leading dash."],
    8: ["Write a test that verifies sale-log total plus remaining stock equals initial stock for bounded purchases.", "With consent, exchange test cases with a peer; keep your own implementation and evidence."],
    9: ["Draw a three-resource wait graph and identify whether it contains a cycle.", "Compare global ordering with timeout-and-retry recovery, including a fairness limitation."],
    10: ["Add bounded log rotation for lab-owned logs and verify restoration from an older archive.", "Design a scheduled health snapshot in your personal crontab; add a unique marker and remove only that line at the end."],
    11: ["If `fuse2fs` and `/dev/fuse` are available, mount only your regular image in your own mountpoint, verify content, then unmount.", "On an unmounted image file, run `e2fsck` and compare filesystem metadata before and after a controlled resize."],
}
SCAFFOLD = {
    1: "Record `uname -r` and `ps` headings first. Start the two processes with `&`, capture each `$!` immediately, inspect before `wait`, then compare after both exit.",
    2: "Run `pwd` and `find . -maxdepth 2 -type f` before moving. Write the intended source and destination paths on paper, use `mv --`, then inspect both directories.",
    3: "First create a hard link and symlink to `source.txt`. Record `ls -li` and `readlink`. Rename only the source, test both links, then repair the symlink target relative to its own directory.",
    4: "Inspect the header and rows with `cat`. Check filtering output before extracting field 2; check numeric fields before aggregating them. Redirect the final answer to a new owned file.",
    5: "Read the trace and mark where workers overlap. Compile the starter, run it, then add a join for each created worker. Explain separately what would need a mutex if both changed one counter.",
    6: "Use `stat -c '%A %a %n'` on directories and files before changing modes. Decide who needs read, write and traversal, change one mode, then inspect the whole path with `namei -l` if available.",
    7: "Print each argument inside angle brackets before counting words. Loop over `\"$@\"`, check that each path is a regular file, and pass it after `--` to `wc`.",
    8: "Write the invariant `successful sales + remaining stock = initial stock`. Handle one valid and one invalid quantity first. Run the two-buyer teaching case, then move the lock to before the stock read and hold it through the log append.",
    9: "Write the Alpha/Beta lock order for each worker. Add a line after each acquisition and a bounded barrier so both first locks are held before requesting the second. Then change both workers to the same order.",
    10: "Create one archive, list its members, and restore it to a fresh owned directory before writing retention. Test retention with four archives. Check `lab10-cron status` before installation and after removal.",
    11: "Confirm the target path is a regular file under `images/`. Compare byte length and allocated blocks on a sparse image. If formatting tools exist, run them only on that checked file and inspect metadata again.",
}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")

for n, data in LABS.items():
    title, env, prereq, targets, guided, question, predict, investigation, constraints, tests, changed, answer, extension, hints = data
    lab = f"lab{n}"
    target_items = targets.split("; ")
    student = f"""# OS Lab {n} — {title}{' (optional bonus)' if n == 11 else ''}

| | |
|---|---|
| Duration | 120 minutes |
| Work | Individual solution and submission; peer exchange is optional and bounded |
| Primary environment | {env} |
| Practice fallback | Local Linux or WSL for unprivileged work; see topic constraints |
| Prerequisites | {prereq} |
| Required core | Guided example, prediction, one investigation, tests, changed case, concise report |
| Optional extensions | See below; they do not replace the core |

## Observable learning targets

""" + "\n".join(f"{i}. {x.capitalize()}." for i, x in enumerate(target_items, 1)) + f"""

## 120-minute route

| Minutes | Activity |
|---|---|
""" + "\n".join(f"| {span} | {activity} |" for span, activity in TIMETABLE) + f"""

## Setup and guided example (0–25)

Log in with your own account. Run `oslab doctor`, then `oslab start {lab}`; `oslab status {lab}` shows the workspace. The first start creates editable copies of the public fixtures in your own `~/oslab-work/{lab}`. Repeating start preserves your edits. If `oslab` is not installed, create an owned directory and use the commands below with your own paths; the instructor can supply the public fixtures. Keep your submission in your own course repository.

Run or adapt this small example in your own workspace:

```bash
{guided}
```

Before continuing: {question}

## Prediction (25–35)

On paper or the existing course worksheet, write the expected result **and why** before executing the investigation. Keep the original sentence visible; later add a correction beneath it. Initial accuracy is lightly weighted; an evidence-based correction earns credit.

**Predict:** {predict}

Spend at most five minutes comparing reasoning with a neighbour if one is available; otherwise compare against the guided example. Your written prediction remains your own.

## Individual investigation (35–70)

**Starting state:** `~/oslab-work/{lab}` after `oslab start {lab}`. **Goal:** {investigation}

{STARTERS.get(n, 'Inspect the fixture files with `find . -maxdepth 3 -type f` before editing.')}

**Suggested sequence:** {SCAFFOLD[n]}

**Boundaries and editable files:** {constraints} Create or edit only files in your owned workspace and your own submission directory. Treat supplied fixture files as data unless the task asks you to change a copy. Completion means you can show the intended behaviour and explain the mechanism, even if you reached it by a different valid command.

You may use AI during investigation and testing. Ask it for a hypothesis or alternative command, then inspect the command, test it on owned data, and take responsibility for the result. AI is optional; the example, three hints below, manual pages and lecture notes are enough. Record at most one useful suggestion and how you verified it. Do not submit chat history.

## Test, interpret, and explain (70–85)

{tests}

For two selected tests, record: **claim**, **result that would contradict it**, **observed result**, and **what remains unproven**. `oslab check {lab}` gives public fixture feedback only; it is not grading and cannot establish your understanding. Save concise terminal text rather than repetitive screenshots.

## Individual changed-case checkpoint (85–100)

Close AI and peer help. The instructor gives this question on paper or via the existing course mechanism; answer in short structured form even if your earlier build is incomplete:

> {changed}

State the result, reason, and one observation or command that could check it. Keep this answer separate from your investigation notes until collection.

## Correction, cleanup, and submission (100–120)

Compare prediction with evidence and preserve both original and corrected versions. Explain the OS concept in 3–5 sentences. Save your script or command transcript, two selected test records, and a short `README.md` using [the shared report template](../REPORT-TEMPLATE.md). If you used AI, add one sentence about a verified suggestion. Use `oslab status {lab}` and leave the workspace for review; `oslab clean {lab}` removes only the managed working copy after you have saved your submission. Never run reset or clean on another student's account.

The rubric totals 10 points: working behaviour 3, tests/diagnosis 2, conceptual explanation and corrected prediction 2, independent checkpoint 2, concise evidence 1. Equivalent valid solutions earn credit. The checkpoint is assessed separately from AI-assisted work.

## Progressive help and troubleshooting

1. Concept: {hints.split('; ')[0]}
2. Observation: {hints.split('; ')[1] if len(hints.split('; ')) > 1 else 'inspect the fixture and command output'}
3. Partial approach: {hints.split('; ')[2] if len(hints.split('; ')) > 2 else 'change one condition and retest'}

If `oslab` is missing, check `command -v oslab` and ask for the published script path. If a tool is absent, use the stated fallback or consult the instructor; do not install system packages yourself. If permissions fail, inspect ownership and parent directory traversal in your own workspace. If a process or cron observation is late, use a bounded repeat and record the limit.

**Reference:** {READINGS[n]}. Read the relevant example or manual section when you need a command; you do not need a paid AI account.

## Optional extensions

{extension} See [extension tasks](extensions.md) for concrete follow-up work. These extensions are for additional practice after the required route, using only environments and permissions stated above. They are not required for the 120-minute submission.
"""
    write(ROOT / "labs" / lab / f"{lab}-instruction.md", student)
    write(ROOT / "labs" / lab / "extensions.md", f"# Lab {n} optional extensions\n\nComplete these only after the [120-minute core]({lab}-instruction.md). Work independently on owned files and record a prediction, a normal and an edge test, and a short explanation. These tasks do not alter the required rubric.\n\n" + "\n".join(f"{i}. {task}" for i,task in enumerate(EXTENSION_TASKS[n],1)) + "\n")
    instructor = f"""# Instructor plan — OS Lab {n}: {title}

**Public repository notice:** this file and its answers are public. A folder called `instructor` does not make them confidential. Prepare fresh graded variants and private answer distribution outside this repository. Do not use this public checkpoint verbatim for secure assessment.

## Preparation and environment

- Confirm 25–30 individual accounts, Python 3.8+, the `oslab` installation, quota, and {env}.
- Run `oslab doctor`, `oslab start {lab}`, and `oslab check {lab}` as an ordinary test account. Verify no symlink or ownership surprises.
- Review prerequisites: {prereq}. Prepare paper prediction and checkpoint slips; collect the checkpoint before showing the key.
- Keep VM snapshots, compiler, FUSE and cron availability topic-specific. Do not add sudo to student accounts to make a task work.

## Exact timetable

| Minutes | Teacher action and evidence |
|---|---|
""" + "\n".join(f"| {span} | {activity}; circulate and collect a sample of evidence |" for span, activity in TIMETABLE) + f"""

## Expected observations and alternatives

Guided example: `{guided}`. Ask: {question}

Investigation goal: {investigation}

**Model solution or acceptable alternative:** {SOLUTION_SKETCHES[n]}

{SOLUTION_ASSETS.get(n, 'The model sketch is public preparation material. Use a fresh private variant if this checkpoint is graded.')}

Expected core evidence: an owned artifact or transcript; two tests including one edge case; a preserved prediction and evidence-based correction; a 3–5 sentence mechanism explanation. Accept equivalent commands and programs if they meet the invariant. Do not grade exact filenames unless a tool genuinely depends on them.

## Checkpoint key and quick marking

Question: {changed}

Key: {answer}

Of the checkpoint's two points, give one for a defensible result or diagnosis and one for mechanism plus a suitable verification observation. Partial credit applies if the result is wrong but the reasoning identifies a relevant mechanism. A student with unfinished earlier implementation can still earn both points.

## Misconceptions, hints, support

- Common mistake: treating one successful run as universal proof or confusing a displayed output with the underlying OS mechanism. Use anonymized errors during debrief.
- Progressive hints: {hints}
- For students behind pace: provide a clean fixture copy, narrow the investigation to one test, and preserve the independent checkpoint. Do not complete their artifact for them.
- Peer exchange is five minutes maximum and optional; an individual can compare with the guided example. No public random questioning or one-by-one oral examination is required.

## Extensions, outage fallback, cleanup

Extension: {extension}

If the server is unavailable, use local Linux/WSL for unprivileged work and a printed trace for the checkpoint. For machine-specific tasks, use a disposable VM only; a teacher-only VM demonstration does not establish each student's recovery competence. At finish, confirm bounded processes have exited, any lab-owned cron marker is removed, and only owned workspace artifacts remain. `oslab clean {lab}` is optional after submission and must never target unrelated files.

## Rubric (10 points)

| Evidence | Points |
|---|---:|
| Working behaviour against stated constraints | 3 |
| Tests and diagnosis, including a failure or edge case | 2 |
| Concept explanation and evidence-based correction | 2 |
| Independent changed-case checkpoint | 2 |
| Concise, attributable evidence | 1 |
"""
    write(ROOT / "teaching" / "instructor" / lab / "plan.md", instructor)
    write(ROOT / "labs" / lab / "README.md", f"""# Lab {n} submission template{' — optional bonus' if n == 11 else ''}

Copy [the shared report template](../REPORT-TEMPLATE.md) into your own submission repository as `lab{n}/README.md`, then fill it with your own evidence. Follow the current [Lab {n} instructions]({lab}-instruction.md). The supervised changed-case answer is collected separately by the instructor.

Student ID:
Environment:
Artifact filename or link:
Original prediction and reason:
Corrected prediction and evidence:
Normal test and contradictory result:
Edge/failure test and contradictory result:
OS mechanism explanation (3–5 sentences):
Optional AI suggestion and verification:

Use at most two decisive text excerpts or screenshots. The core rubric is 10 points and is shown in the instructions. No partner artifact, prescribed script name, or long chat transcript is required.
""")

write(ROOT / "labs" / "REPORT-TEMPLATE.md", """# OS lab N — individual report

Name or student ID:
Workspace and environment:

## Original prediction (written before running)

Expected outcome and reason:

## Investigation artifact

Link to script or paste at most ten decisive command lines. State the intended behaviour and one choice you made.

## Two test records

| Case | Claim | Contradicting result | Observation | What remains unproven |
|---|---|---|---|---|
| Normal | | | | |
| Edge/failure | | | | |

## Correction and explanation

Keep the original prediction above. Explain what changed in your understanding and the OS mechanism in 3–5 sentences.

## AI suggestion (optional)

One useful suggestion and how you checked it:

The supervised changed-case checkpoint is collected separately. Do not reconstruct it in this report after collection.
""")

write(ROOT / "teaching" / "REVISION-AUDIT.md", "# First revision audit\n\nThe original labs supplied objectives, organised tasks, guided commands, references, challenges and submissions. The new student route keeps those teaching structures and selects one 120-minute core investigation per lab. Broader topics are labelled optional; the source Git history contains the full previous versions.\n\n| Lab | Retained strength and learning target | Environment | Revised/extended/removed from core | Supporting files added | Technical correction |\n|---|---|---|---|---|---|\n" + "\n".join(f"| {n}{' bonus' if n == 11 else ''} | {AUDIT[n][0]}; core: {d[3]} | {d[1]} | Optional: {d[12]} Removed from core: {AUDIT[n][1]} | Individual fixture, report, instructor key{' and model scripts' if n in (8,9) else ''} | {d[8]} |" for n,d in LABS.items()) + "\n")

write(ROOT / "teaching" / "IMPLEMENTATION-PLAN.md", """# First revision implementation record

1. Audited all 11 lab instructions, READMEs, course outline, exam briefing, lecture activities/visualizations and app content loading; see `REVISION-AUDIT.md`.
2. Established the student/instructor pattern with Lab 1, then applied topic-specific 120-minute routes to Labs 2–11, including bonus Lab 11.
3. Added a common individual report, public instructor plans and checkpoint keys, safe per-user scenario fixtures, deployment scripts, and runbook.
4. Validation is recorded in `VALIDATION.md`. Server-only capability checks remain before class.

The source repository is preserved as the `source` remote. The new destination is `origin` (`RathpiseyAlpha/ITC-I4GIC-OS`). No push or server deployment is part of this local revision.
""")

write(ROOT / "README.md", """# Operating Systems course materials — ITC

Institute of Technology of Cambodia, Department of Information and Communication Engineering. This repository contains lecture resources, class activities, 11 lab instructions (Lab 11 is an optional bonus), and the existing course web application and exam functionality.

The first lab revision uses **120 minutes per lab**, individual solutions, a short optional peer exchange, and an independent changed-case checkpoint. AI is permitted for investigation and testing, but not for the initial prediction or checkpoint. The shared Ubuntu server is primary; local Linux/WSL is an unprivileged fallback. GRUB recovery needs a snapshot-backed disposable VM. Do not run system-wide administrative commands on the shared server.

## Start here

- [Course outline](course-outline.md), [exam briefing](EXAM-BRIEFING.md), [lecture notes](lectures/notes/README.md), [class activities](lectures/class-activity/README.md), and [visualizations](lectures/visualizations/README.md)
- [Shared lab report template](labs/REPORT-TEMPLATE.md)
- [Per-lab audit](teaching/REVISION-AUDIT.md), [implementation record](teaching/IMPLEMENTATION-PLAN.md), [validation](teaching/VALIDATION.md)
- [Server deployment runbook](server/RUNBOOK.md) and [per-user scenario helper](server/oslab.py)

| Lab | Core topic | Instruction |
|---|---|---|
""" + "\n".join(f"| {n}{' (bonus)' if n == 11 else ''} | {d[0]} | [Lab {n}](labs/lab{n}/lab{n}-instruction.md) |" for n,d in LABS.items()) + """

Students work in their own repositories and save only concise artifacts, selected tests, prediction/correction, and conceptual explanation. The common 10-point rubric appears in every instruction; the checkpoint is collected separately. Optional extensions preserve broader original topics without turning the core into a three-hour exercise.

Instructor files in this public repository are also public. Prepare fresh graded variants and keep confidential keys in a private distribution system. Public scenario checks give feedback, not secure grading.

## Website and repository origin

The static course site is in `index.html` and `app/`. Its GitHub file tree defaults to the new destination, [RathpiseyAlpha/ITC-I4GIC-OS](https://github.com/RathpiseyAlpha/ITC-I4GIC-OS), through `app/js/config.js`. The original source of this revision is [RathpiseyAlpha/ITC-OS-2026](https://github.com/RathpiseyAlpha/ITC-OS-2026). The application backend and exam features were preserved. Review and configure deployment separately; this revision does not deploy to the live server.
""")

outline = ROOT / "course-outline.md"
outline_text = outline.read_text(encoding="utf-8")
note = "\n## Revised lab route\n\nAll labs use a 120-minute individual core route. The lecture-week table above is a topic guide, not a one-to-one lab schedule. See the [lab index](README.md#start-here) for all 11 current instructions, including optional bonus Lab 11. Class dates, deadlines, and server availability are announced separately in Asia/Phnom_Penh time.\n"
if "## Revised lab route" not in outline_text:
    outline.write_text(outline_text.rstrip() + "\n" + note, encoding="utf-8")
