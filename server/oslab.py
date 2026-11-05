#!/usr/bin/env python3
"""Per-user OS lab fixtures, personal values, predictions, checks and checkpoints.

No privileged operations. `check lab8` runs only the caller's own script, as the
caller, in a disposable copy of the store.
"""
import argparse
import fcntl
import hashlib
import json
import os
import posixpath
import pwd
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import readline  # noqa: F401  arrow keys, Backspace and history while typing an answer
except ImportError:
    pass

LABS = tuple(f"lab{n}" for n in range(1, 12))
MARKER = ".oslab-managed.json"
MAX_ARCHIVES = 3
MAX_BYTES = 2_000_000
RECORDS = ".records"
TERM_FILE = "/opt/itc-os-labs/term.conf"
DEFAULT_INBOX = "/var/lib/itc-oslab/inbox"
DEFAULT_RELEASE = "/var/lib/itc-oslab/release"
LOCAL_SALT = "local-practice"
TOKEN = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")

BUY_SH = """#!/usr/bin/env bash
# Quantum Widget store: sell QUANTITY units.
set -euo pipefail
store=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
if [[ $# -ne 1 || ! "$1" =~ ^[1-9][0-9]{0,2}$ ]]; then
    echo 'usage: buy.sh QUANTITY (1..999)' >&2
    exit 2
fi
quantity=$1
stock=$(<"$store/stock.txt")
[[ "$stock" =~ ^(0|[1-9][0-9]{0,2})$ ]] || { echo 'invalid stock' >&2; exit 2; }
if (( quantity > stock )); then
    echo 'insufficient stock' >&2
    exit 1
fi
sleep "${BUY_DELAY:-0}"   # the payment takes time; keep this line
printf '%s\\n' "$((stock - quantity))" > "$store/stock.txt"
printf 'sold %s\\n' "$quantity" >> "$store/sales.log"
echo 'accepted'
"""
READ_STOCK = 'stock=$(<"$store/stock.txt")\n'
PAY_DELAY = 'sleep "${BUY_DELAY:-0}"   # the payment takes time; keep this line\n'
# Three plausible but wrong repairs for the "review an AI answer" task.
AI_ANSWERS = {
    "a": BUY_SH.replace(PAY_DELAY, PAY_DELAY + 'exec 9>"$store/stock.lock"\nflock -x -w 5 9 || { echo \'lock timeout\' >&2; exit 3; }\n'),
    "b": BUY_SH.replace(READ_STOCK, 'exec 9>"$store/stock.$$.lock"\nflock -x -w 5 9 || { echo \'lock timeout\' >&2; exit 3; }\n' + READ_STOCK),
    "c": BUY_SH.replace(READ_STOCK, '(\n    flock -x -w 5 9 || exit 3\n) 9>"$store/stock.lock"\n' + READ_STOCK),
}

FIXTURES = {
    "lab1": {"README.txt": "Work in this folder. Save your result files in this folder.\n"},
    "lab2": lambda v: {f"incoming/{v['file1']}": f"amount,{v['amount1']}\n",
                       f"incoming/{v['file2']}": f"amount,{v['amount2']}\n",
                       "reports/README.txt": "Move the two incoming files here; keep their names.\n"},
    "lab3": lambda v: lab3_fixture(v),
    "lab4": lambda v: lab4_fixture(v),
    "lab5": lambda v: lab5_fixture(v),
    "lab6": lambda v: lab6_fixture(v),
    "lab7": lambda v: lab7_fixture(v),
    "lab8": lambda v: {"store/stock.txt": f"{v['stock']}\n", "store/sales.log": "", "store/buy.sh": BUY_SH,
                       **{f"store/ai-answers/{name}.sh": text for name, text in AI_ANSWERS.items()}},
    "lab9": lambda v: lab9_fixture(v),
    "lab10": lambda v: lab10_fixture(v),
    "lab11": {"images/README.txt": "Create regular image files here. Never use a device path.\n"},
}

GENERIC_HINTS = ("Identify the resource and expected invariant.",
                 "Inspect the fixture and the command's exit status.",
                 "Try one controlled change, then compare before and after.")
HINTS = {
    "lab1": ("Read the step again slowly. Which command did you run, and in which folder? Check with `pwd` and `ls`.",
             "Run `oslab check lab1` and read the line that says TRY. It tells you which file it looked at. Look inside that file with `cat`.",
             "A missing line in a file often means the command ran in the wrong folder, or `>` was used where `>>` was needed (`>` replaces the whole file)."),
    "lab2": ("Draw the folders on paper. Mark where you are (`pwd`) and where the file must go.",
             "Each `..` goes up one folder. From `incoming/`, one `..` brings you to the lab folder. Which folders are next to `incoming` there?",
             "From one department folder, go up once to TechCorp, then down into the other department: `../DEPARTMENT/'file name'`."),
    "lab3": ("Which command did you run, and in which folder? Check with `pwd`, then run `ls -li` in links/ and compare the inode numbers in the first column. Your own names are in `oslab values lab3`.",
             "A hard link shares the inode of the original, so it still works after the rename. A symbolic link stores a name; run `readlink` on it and ask: is there a file with that name now? A NEW file with that name makes the link work again, but on the wrong file.",
             "A relative target is read from the folder that holds the link. To point the soft link at the renamed file in the same folder, the stored target is only that file name. Remove the old link with `rm --`, then `ln -s TARGET LINK` again, with your own names."),
    "lab4": ("Run each stage of the pipeline alone and read what it prints. Which stage still shows the word `STATUS` or rows you do not want?",
             "The total is a sum, not a count of lines. `wc -l` counts rows. Which command can add the numbers in column 2? Try `awk -F, '{ total += $2 } END { print total+0 }'` on the selected rows only.",
             "Select the rows whose FIRST field is exactly your status: `$1 == \"STATUS\"` in awk, or `grep '^STATUS,'` (the comma stops a look-alike such as `STATUS-late`). Print the label and the total once, in `END`. For a missing file, print the message with `>&2` and `exit 1`."),
    "lab5": ("Read main from top to bottom. A thread starts at pthread_create, but main keeps going. Which line makes main wait for worker A, and which for worker B? Run `oslab check lab5` and read the TRY line.",
             "Each worker you created needs its own pthread_join, with the thread variable of THAT worker (ta, then tb). Put the joins before the line that prints the results, and test the return code: `rc = pthread_join(ta, NULL); if (rc) return 1;`",
             "After both joins, print the report line: `printf(\"A result=%d B result=%d\\n\", a.result, b.result);`. The worker prints `worker N finished` before it returns, so both of those lines come before your report line."),
    "lab6": ("Write your policy in plain words first: who may read, who may change, who may list the folder? Then run `stat -c '%A %a %n' private shared` and compare with `oslab check lab6`.",
             "Each octal digit is one group: owner, group, others. Add read=4, write=2, execute/search=1. Example: rw-r----- is 4+2=6, 4, 0, so 640. A folder needs the x bit for anyone who must enter it.",
             "File and folder are two separate chmod commands: `chmod 640 shared/notice.txt` and `chmod 750 shared`. Do the file first. If a read fails with Permission denied, look at every folder on the path with `namei -l`, not only at the file."),
    "lab7": ("Print what your script really receives: run `bash show_args.sh` with your file names in single quotes and look at the angle brackets. Which name is cut into pieces?",
             "Quote every expansion: \"$@\" in the loop and \"$file\" inside it. A leading dash is read as an option by `wc`, so end the options first: `wc -w -- \"$file\"`. Keep the final status in a variable that starts at 0.",
             "Skeleton: `status=0`, then `for file in \"$@\"; do`, test `[[ -f \"$file\" ]]` (print to stderr with `>&2`, set `status=1`, `continue` if it fails), count with `wc -w -- \"$file\"`, `done`, and finally `exit \"$status\"`. Check the no-argument case with `[[ $# -gt 0 ]]` first."),
    "lab9": ("Draw two boxes for the two locks and two arrows for the workers. Who holds which lock at the barrier, and who is waiting for it? Run the opposite mode and read both logs.",
             "A deadlock needs a circle. If every worker takes the locks in the same order, no worker can hold the second lock while waiting for the first. Look at the line that makes worker B swap `first` and `second`: when must it do that, and when not?",
             "Make the swap happen only in opposite mode: `if [[ \"$role\" = B && \"$mode\" = opposite ]]; then ...`. Keep the barrier and the `sleep \"${HOLD:-0}\"` line, and write the rule with `$first` and `$second`, not with the names."),
    "lab10": ("What must always be true after a run? Write it as a sentence with the number `keep`. Then list `backups` and count the archives that have YOUR name at the start.",
             "The names contain a time stamp, so sorting the names puts the oldest first. Collect only the complete archives made by this script into an array, sort it, and remove everything except the last `keep` entries. Do not touch other names.",
             "Use the exact pattern of the names: `[[ \"$name\" =~ ^NAME-[0-9]{8}T[0-9]{15}-[0-9]+\\.tar\\.gz$ ]]` with your own prefix in `$name`. After `mapfile -t ordered < <(printf '%s\\n' \"${owned[@]}\" | LC_ALL=C sort -r)`, the entries to remove are `\"${ordered[@]:$keep}\"`. Quote every path and write `rm -- \"$path\"`."),
    "lab8": ("Write the rule that must always be true: units sold + units left = starting stock. Which lines of buy.sh read or change these numbers?",
             "Run `cat -n store/buy.sh`. Find the line that reads stock.txt and the lines that write. No other buyer may run between the first and the last of them.",
             "Syntax: `exec 9>\"$store/stock.lock\"` opens the lock file, `flock -x -w 5 9 || exit 3` waits for it. Where must these two lines go so that the stock check uses a fresh value?"),
}

PRELAB = {
    "lab1": (("Which command shows the name and release of the kernel?", ("uname -a", "pwd", "ls"), "a",
              "`uname` asks the running kernel about itself. `-a` means all the information."),
             ("What does `>>` do when you put it after a command?", ("it replaces the file", "it adds the output to the end of the file", "it deletes the file"), "b",
              "`>` replaces the file. `>>` adds to the end and keeps what is already there."),
             ("Program and process:", ("they are the same thing", "a program is a file on disk, a process is a running copy of it", "a process is a file on disk"), "b",
              "One program file can be running as several processes at the same time.")),
    "lab2": (("An absolute path always starts with:", ("./", "/", "../"), "b",
              "It starts at the root directory `/`, so it means the same place from anywhere."),
             ("`..` means:", ("the current directory", "your home directory", "the parent directory"), "c",
              "`.` is the current directory and `..` is one level up."),
             ("Which command keeps the original file in place?", ("mv", "cp", "both"), "b",
              "`cp` makes a second file. `mv` changes the location of the one file.")),
    "lab3": (("`ls *.txt` lists all names that end in `.txt`. Who turns the `*` into file names?", ("the ls program", "the shell, before ls runs", "the kernel"), "b",
              "Bash expands the pattern first and gives `ls` the finished list. Quotes stop this."),
             ("A hard link and the original file have:", ("different inode numbers", "the same inode number", "no inode"), "b",
              "They are two names for one inode, so they show the same data."),
             ("A symbolic link stores:", ("a copy of the data", "the inode of the file", "the path of the file it points to"), "c",
              "If that path stops existing, the link is dangling.")),
    "lab4": (("Which number is standard error?", ("1", "2", "0"), "b",
              "0 is input, 1 is output, 2 is error. `2>` sends only the error messages."),
             ("In `a | b`, what goes into `b`?", ("the files of a", "the output of a", "the error messages of a"), "b",
              "The pipe connects the standard output of `a` to the input of `b`. Errors still go to the screen."),
             ("`grep '^ok,' file | wc -l` prints:", ("the sum of the numbers", "the number of matching lines", "the number of words in the file"), "b",
              "`wc -l` counts lines. A sum of field 2 needs a different command, such as `awk`.")),
    "lab5": (("`pthread_join(t, NULL)` makes the calling thread:", ("start the thread t", "wait until the thread t has finished", "stop the thread t at once"), "b",
              "It waits for that one thread. Without it, main can read a result that is not ready, or return and end the process."),
             ("Threads of one process share:", ("the address space (global data and the heap)", "nothing at all", "only the program counter"), "a",
              "That is why a worker can write into a struct that main reads. Separate processes after `fork` have separate copies."),
             ("Does joining two workers also stop them from updating one shared counter at the same time?", ("yes, join does both", "no, join only waits for the end; mutual exclusion needs a lock", "only if the delay is long"), "b",
              "Completion and mutual exclusion are two different problems. A delay is not a lock.")),
    "lab6": (("What are the three digits of the mode `640`, in order?", ("owner, group, others", "others, group, owner", "read, write, execute"), "a",
              "6 is for the owner (read + write), 4 for the group (read), 0 for others (nothing)."),
             ("For a directory, the x bit means:", ("you may run the directory as a program", "you may enter it and reach the files inside it by name", "you may delete it"), "b",
              "x on a folder is search permission. Without it you cannot open the files inside, even if their own mode allows it. r only lets you list the names."),
             ("A file has mode 644 but sits in a folder with mode 700 owned by someone else. Can you read the file?", ("yes, the file mode allows it", "no, you cannot enter the folder", "only if you know the file name"), "b",
              "The system checks every folder on the path. A 700 folder of another user stops you before the file mode is looked at.")),
    "lab7": (("`\"$@\"` (with the quotes) in a script gives:", ("all arguments as one string", "each argument as a separate word, with its spaces kept", "only the first argument"), "b",
              "Each argument stays one piece, even if it contains spaces. Without the quotes the shell splits it again."),
             ("What does `--` mean in `wc -w -- file`?", ("everything after it is a file name, not an option", "wc counts two words", "wc reads from the keyboard"), "a",
              "It ends option parsing. A file called `-x.txt` is then read as a file name."),
             ("The first command of a script fails but the last command succeeds. The script's exit status is:", ("always the first failure", "the status of the last command, unless you set your own", "always 0"), "b",
              "Keep your own variable (`status=1`) and finish with `exit \"$status\"`.")),
    "lab9": (("Two workers each hold one lock and wait for the lock of the other. This is called:", ("starvation", "deadlock", "a race condition"), "b",
              "A circular wait: nobody can continue, and nobody releases what they hold."),
             ("`flock -x -w 2 9` waits at most:", ("2 seconds, then it gives up with a failure status", "2 seconds, then it takes the lock anyway", "forever"), "a",
              "A timeout does not remove a deadlock; it only ends the waiting so the program can recover."),
             ("Which rule removes the circular wait?", ("every worker takes the locks in the same global order", "every worker waits longer", "every worker uses a different lock file"), "a",
              "With one order, a worker that waits for the first lock cannot hold the second one at the same time.")),
    "lab10": (("`tar -czf a.tar.gz dir` does two things. Which?", ("it packs the files into one archive and compresses it", "it encrypts the files and deletes them", "it copies the files to a second disk"), "a",
              "`tar` packs many files into one; `gzip` (the `z`) compresses the bytes. Neither one proves that you can restore."),
             ("How do you know a backup can be restored?", ("tar printed no error", "you extracted it somewhere else and compared the files", "the file is not empty"), "b",
              "Only a restore test shows that the data comes back. Compare with `cmp`."),
             ("A script is started by cron. Which assumption is risky?", ("it uses the folder where the script itself is stored", "it assumes the current folder is the project folder and that PATH holds every program", "it prints a message"), "b",
              "Cron starts a script from another folder with a very small environment. Use the script's own folder and full paths.")),
    "lab8": (("Two buyers both read stock=5. Then each writes 5-4. What is in the stock file at the end?", ("-3", "1", "5"), "b",
              "Each one writes its own result, 1. The second write replaces the first. One update is lost."),
             ("A critical section is:", ("code that must not be mixed with other code using the same data", "the slowest part of a program", "code that runs as root"), "a",
              "Only one process at a time may be inside it."),
             ("`flock` locks are advisory. This means:", ("the kernel blocks every write to the file", "they work only if every program asks for the same lock", "they end after one second"), "b",
              "A program that does not ask for the lock is not stopped by it.")),
}

REPORT_NAMES = ("budget 2026.txt", "sales north.txt", "audit notes.txt", "payroll may.txt",
                "travel claims.txt", "tax summary.txt", "vendor list.txt", "cash flow.txt")
OWNER_DEPTS = ("Finance", "Sales", "Legal", "Audit")
OTHER_DEPTS = ("HR", "Engineering", "Support", "Marketing")


def fail(message):
    raise ValueError(message)


def current_user():
    # A test name is honoured only where no server term file is installed.
    test_name = os.environ.get("OSLAB_TEST_USER", "")
    if test_name and not Path(TERM_FILE).exists() and TOKEN.match(test_name):
        return test_name
    return pwd.getpwuid(os.getuid()).pw_name


def term_salt():
    path = Path(os.environ.get("OSLAB_TERM_FILE", TERM_FILE))
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                return line.strip() if TOKEN.match(line.strip()) else LOCAL_SALT
    except OSError:
        pass
    return LOCAL_SALT


def picker(user, lab, nonce=""):
    salt = term_salt()

    def pick(label, count):
        text = "|".join((salt, user, lab, nonce, label))
        return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big") % count
    return pick


def question(key, text, kind, expect=None):
    return {"key": key, "text": text, "kind": kind, "expect": expect}


WORDS = ("maple", "river", "cloud", "stone", "tiger", "lemon", "ocean", "panda",
         "candle", "garden", "pencil", "rocket", "forest", "silver", "bridge", "market")


def two_words(pick, first, second):
    a = pick(first, len(WORDS))
    b = (a + 1 + pick(second, len(WORDS) - 1)) % len(WORDS)
    return WORDS[a], WORDS[b]


def lab1_values(pick):
    file1, file2 = two_words(pick, "file1", "file2")
    return {"count": 2 + pick("count", 3), "file1": file1, "file2": file2}


def lab1_predict(v):
    n = v["count"]
    return [question("sleeps", f"You start {n} copies of `sleep` in the background at the same time, then run `ps`. How many lines with `sleep` does `ps` show?", "int", [n]),
            question("file", "All the copies have finished. Is the program file `sleep` still on the disk? (yes/no)", "yesno", "y"),
            question("remove", "You run `apt-get remove` on a package. Is the package's configuration folder in /etc deleted by that command? (yes/no)", "yesno", "n"),
            question("why", "One sentence: what is the difference between a program and a process?", "text")]


def lab1_checkpoint(pick, v):
    folder, note = two_words(pick, "folder", "note")
    n = 2 + pick("n", 3)
    cv = {"folder": f"cp-{folder}", "note": f"{note}.txt", "copy": f"{note}-copy.txt", "old": f"{note}-old.txt",
          "text": f"hello {folder}", "n": n}
    intro = ["Work alone, with AI tools closed. Use only commands from this lab."]
    qs = [question("sleeps", f"You start {n} copies of `sleep 300` in the background, then run `ps`. How many lines with `sleep` does `ps` show?", "int", [n]),
          question("file", "300 seconds later they have all finished. Does `which sleep` still print a path? (yes/no)", "yesno", "y"),
          question("kernel", "Type the kernel release of this server: the number that `uname -r` prints.", "word", os.uname().release),
          question("files", "In the task below, how many files are in the new folder after step 4?", "int", [2]),
          question("why", "One sentence: what is the difference between a program and a process?", "text")]
    after = ["Now do it for real, in your lab1 folder:",
             f"  1. Make a folder named {cv['folder']} and go into it.",
             f"  2. Create a file named {cv['note']} that contains the text: {cv['text']}",
             f"  3. Copy it to a file named {cv['copy']}.",
             f"  4. Rename {cv['note']} to {cv['old']}.",
             f"  5. Go back to the lab1 folder and save the list of files of {cv['folder']} in checkpoint.txt",
             "Then run: oslab check lab1"]
    return cv, intro, qs, after


def lab2_values(pick):
    first = pick("file1", len(REPORT_NAMES))
    second = (first + 1 + pick("file2", len(REPORT_NAMES) - 1)) % len(REPORT_NAMES)
    reader = pick("reader", len(OTHER_DEPTS))
    third = (reader + 1 + pick("third", len(OTHER_DEPTS) - 1)) % len(OTHER_DEPTS)
    amount = 100 + pick("amount", 800)
    return {"file1": REPORT_NAMES[first], "file2": REPORT_NAMES[second],
            "owner": OWNER_DEPTS[pick("owner", len(OWNER_DEPTS))],
            "reader": OTHER_DEPTS[reader], "third": OTHER_DEPTS[third],
            "amount1": amount, "amount2": amount + 1 + pick("gap", 90)}


def lab2_predict(v):
    f1, owner = v["file1"], v["owner"]
    return [question("relative", "Your current directory is `incoming/`. Type the relative path of the `reports` directory.", "path", ["incoming", "reports"]),
            question("same", "You change to the lab folder (the parent of `incoming`). Does the path you just typed still point to `reports`? (yes/no)", "yesno", "n"),
            question("after_mv", f"After `mv 'incoming/{f1}' reports/`, how many files named `{f1}` are in the lab folder tree?", "int", [1]),
            question("after_cp", f"Then after `cp 'reports/{f1}' TechCorp/{owner}/`, how many are there?", "int", [2]),
            question("why", "One sentence: why did you answer like this?", "text")]


def lab2_checkpoint(pick, v):
    owner, f2 = v["owner"], v["file2"]
    cases = ((f"TechCorp/{v['third']}/drafts", f"TechCorp/{owner}/archive/first-original.txt", v["amount1"]),
             (f"TechCorp/{owner}/archive", f"reports/{f2}", v["amount2"]),
             (f"TechCorp/{v['reader']}/drafts", f"TechCorp/{owner}/{f2}", v["amount2"]),
             ("incoming", f"TechCorp/{owner}/archive/first-original.txt", v["amount1"]))
    cwd, target, amount = cases[pick("case", len(cases))]
    cv = {"cwd": cwd, "target": target, "content": f"amount,{amount}"}
    ups = posixpath.relpath(target, cwd).split("/").count("..")
    intro = [f"Your current directory is `{cwd}` (inside your lab2 folder; create it if it does not exist).",
             f"You must read the file `{target}` without changing directory."]
    qs = [question("path", "Type a relative path from that directory to the file. Do not type quotes.", "path", [cwd, target]),
          question("ups", "How many `..` does the shortest such path need?", "int", [ups]),
          question("args", f"From the lab folder you type  cat reports/{f2}  with no quotes. How many arguments does `cat` receive?", "int", [f2.count(" ") + 1]),
          question("parent", "Which folder is `..` from that directory? Type its path from the lab folder, for example reports. "
                   "Type . if it is the lab folder itself.", "dir", posixpath.normpath(posixpath.join(cwd, "..")))]
    after = ["Now do it for real from that directory and save the output:",
             "  cat 'YOUR RELATIVE PATH' | tee \"$OSLAB_WORKSPACE/lab2/evidence/checkpoint.txt\"",
             "Then run: oslab check lab2"]
    return cv, intro, qs, after


LAB3_TAGS = ("old", "saved", "final", "draft", "backup")


def lab3_values(pick):
    """Your report's name, the word added when it is renamed, and two version numbers."""
    first = 100 + pick("v1", 800)
    return {"name": WORDS[pick("name", len(WORDS))], "tag": LAB3_TAGS[pick("tag", len(LAB3_TAGS))],
            "v1": first, "v2": first + 1 + pick("v2", 90)}


def lab3_notes(v):
    """The notes/ folder of the wildcard task: two one-digit names, one two-digit name, a log and a hidden file."""
    n = v["name"]
    return {f"notes/{n}1.txt": "note 1\n", f"notes/{n}2.txt": "note 2\n", f"notes/{n}12.txt": "note 12\n",
            f"notes/{n}.log": "log\n", f"notes/.{n}.txt": "hidden note\n"}


def lab3_fixture(v):
    return {f"links/{v['name']}.txt": f"version {v['v1']}\n", **lab3_notes(v)}


def lab3_predict(v):
    n, t = v["name"], v["tag"]
    return [question("broken", f"You run  mv {n}.txt {n}-{t}.txt  in links/. {n}-soft.txt was made with  ln -s {n}.txt {n}-soft.txt.  "
                     f"Can  cat {n}-soft.txt  read a file now? (yes/no)", "yesno", "n"),
            question("hard", f"{n}-hard.txt was made with  ln {n}.txt {n}-hard.txt  before the rename. You now create a NEW {n}.txt that holds "
                     f"`version {v['v2']}`. `cat {n}-hard.txt` prints `version N`. What is N?", "int", [v["v1"]]),
            question("soft", f"At the same moment, `cat {n}-soft.txt` prints `version N`. What is N?", "int", [v["v2"]]),
            question("why", "One sentence: why do a hard link and a symbolic link behave differently when a new file takes the old name?", "text")]


def lab3_checkpoint(pick, v):
    folder, data = two_words(pick, "folder", "data")
    tag = LAB3_TAGS[pick("tag", len(LAB3_TAGS))]
    box = f"cp-{folder}"
    cv = {"folder": box, "data": f"{data}.txt", "moved": f"{data}-{tag}.txt", "content": f"checkpoint {folder} {data}"}
    intro = [f"New case, in the folder lab3/{box}/. It holds the data file {cv['data']} and a folder links/.",
             f"links/hard.txt is a hard link to {cv['data']}. links/first.txt is a symbolic link that stores ../{cv['data']}.",
             "links/second.txt is a symbolic link that stores first.txt. Then you rename "
             f"{cv['data']} to {cv['moved']}, and change nothing else."]
    qs = [question("hard", "Does links/hard.txt still read the data? (yes/no)", "yesno", "y"),
          question("chain", "Does links/second.txt read the data? (yes/no)", "yesno", "n"),
          question("target", f"Type the relative target that links/first.txt must store to reach {cv['moved']}. Type only the path.", "path",
                   [f"{box}/links", f"{box}/{cv['moved']}"]),
          question("second", "You repair ONLY links/first.txt. Does links/second.txt read the data now, with no change to it? (yes/no)", "yesno", "y"),
          question("why", "One sentence: from which folder does Linux read the stored target of links/first.txt?", "text")]
    after = ["Now build this case and repair it, in your lab3 folder:",
             '  cd "$OSLAB_WORKSPACE/lab3"',
             f"  mkdir -p {box}/links",
             f"  cd {box}",
             f"  printf '%s\\n' '{cv['content']}' > {cv['data']}",
             f"  ln {cv['data']} links/hard.txt",
             f"  ln -s ../{cv['data']} links/first.txt",
             "  ln -s first.txt links/second.txt",
             f"  mv {cv['data']} {cv['moved']}",
             "  (repair links/first.txt: write the two commands yourself, with rm -- and ln -s)",
             '  { ls -li . links; cat links/hard.txt links/second.txt; } | tee "$OSLAB_WORKSPACE/lab3/evidence/checkpoint.txt"',
             "Then run: oslab check lab3"]
    return cv, intro, qs, after


LAB4_STATUSES = ("ok", "done", "sent", "paid", "pass", "ready", "clear", "shipped")


def lab4_values(pick):
    """Your status word and an other word. Keys that start with _ are the numbers in your CSV; they are not shown."""
    first = pick("status", len(LAB4_STATUSES))
    other = (first + 1 + pick("other", len(LAB4_STATUSES) - 1)) % len(LAB4_STATUSES)
    return {"status": LAB4_STATUSES[first], "other": LAB4_STATUSES[other],
            "_a": 2 + pick("a", 8), "_b": 2 + pick("b", 8), "_c": 2 + pick("c", 8),
            "_x": 1 + pick("x", 8), "_z": 20 + pick("z", 80), "_turn": pick("turn", 6)}


def lab4_rows(v):
    """The records of data/events.csv: three of your status, two of the other word, one 'late' look-alike."""
    s, o = v["status"], v["other"]
    rows = [(s, v["_a"]), (o, v["_x"]), (s, v["_b"]), (s + "-late", v["_z"]), (s, v["_c"]), (o, v["_x"] + 3)]
    turn = v["_turn"] % len(rows)
    return rows[turn:] + rows[:turn]


def lab4_csv(rows):
    return "status,count\n" + "".join(f"{name},{count}\n" for name, count in rows)


def lab4_total(rows, status):
    return sum(count for name, count in rows if name == status)


def lab4_fixture(v):
    rows = lab4_rows(v)
    return {"data/events.csv": lab4_csv(rows), "data/expected.txt": f"{v['status']} total: {lab4_total(rows, v['status'])}\n"}


def lab4_predict(v):
    s, rows = v["status"], lab4_rows(v)
    first = next(count for name, count in rows if name == s)
    n = sum(1 for name, _ in rows if name == s)
    return [question("first", f"What number does  grep '^{s},' data/events.csv | cut -d, -f2 | head -n 1  print? (Read the file first.)", "int", [first]),
            question("equal", "Is that number the required total of all your records? (yes/no)", "yesno", "n"),
            question("lines", f"How many lines does  grep '^{s},' data/events.csv | wc -l  print?", "int", [n]),
            question("why", "One sentence: what does the number from wc -l measure, and what does the total measure?", "text")]


def lab4_checkpoint(pick, v):
    s, o = v["status"], v["other"]
    word = WORDS[pick("word", len(WORDS))]
    a, b = 2 + pick("p", 15), 2 + pick("q", 15)
    rows = [(o, 4 + pick("o", 6)), (s, a), (s + "-late", 30 + pick("z", 60)), (s, b), ("not-" + s, 40 + pick("n", 50))]
    name = f"{word}.csv"
    cv = {"name": name, "rows": [list(r) for r in rows], "total": a + b}
    intro = [f"New data arrive as a file called data/{name}. These are its records, after the header:"]
    intro += [f"    {n},{c}" for n, c in rows]
    intro += ["Your report.sh will be used on this file. Answer before you create it."]
    qs = [question("total", "What will your report.sh print for this file? Type only the total number.", "int", [a + b]),
          question("lines", f"A friend selects with  grep '^{s},'  and counts with  wc -l.  What number does wc -l print for this file?", "int", [2]),
          question("stream", "If you give report.sh a file that does not exist, your error message goes to a numbered stream. Which number?", "int", [2]),
          question("why", "One sentence: why is the wc -l number not the total?", "text")]
    lines = " ".join(["'status,count'"] + [f"'{n},{c}'" for n, c in rows])
    after = ["Now make the file and run your own script on it, in your lab4 folder:",
             '  cd "$OSLAB_WORKSPACE/lab4"',
             f"  printf '%s\\n' {lines} > data/{name}",
             f"  bash report.sh data/{name} > checkpoint.txt",
             "  cat checkpoint.txt",
             "Then run: oslab check lab4"]
    return cv, intro, qs, after


TWO_WORKERS_C = r'''#define _POSIX_C_SOURCE 200809L
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
struct job { int id; int steps; int result; };
static void *worker(void *arg) {
    struct job *job = arg;
    const struct timespec delay = {0, 20000000};
    for (int i = 0; i < job->steps; ++i) {
        job->result += job->id;
        nanosleep(&delay, NULL); /* teaching delay, not synchronization */
    }
    printf("worker %d finished\n", job->id);
    return NULL;
}
int main(void) {
    struct job a = {@IDA@, @SA@, 0}, b = {@IDB@, @SB@, 0};
    pthread_t ta, tb;
    int rc = pthread_create(&ta, NULL, worker, &a);
    if (rc) { fprintf(stderr, "create A: %s\n", strerror(rc)); return 1; }
    rc = pthread_create(&tb, NULL, worker, &b);
    if (rc) {
        fprintf(stderr, "create B: %s\n", strerror(rc));
        pthread_join(ta, NULL);
        return 1;
    }
    /* The report line must look like:  A result=NUMBER B result=NUMBER */
    /* TODO: join both workers and check each return code. */
    /* TODO: after both joins, print a.result and b.result. */
    puts("main finishing");
    return 0;
}
'''

THREAD_TRACE = "thread,step\nA,read\nB,read\nA,write\nB,write\n"
THREAD_STARTER = ("#include <pthread.h>\n#include <stdio.h>\nstatic void *worker(void *arg) { puts((const char *)arg); return NULL; }\n"
                  "int main(void) { pthread_t a, b;\n  if (pthread_create(&a, NULL, worker, \"A\") || pthread_create(&b, NULL, worker, \"B\")) return 1;\n"
                  "  /* TODO: join both workers before reading results. */\n  return 0;\n}\n")


def lab5_values(pick):
    return {"id_a": 2 + pick("id_a", 4), "id_b": 6 + pick("id_b", 4),
            "steps_a": 2 + pick("steps_a", 4), "steps_b": 2 + pick("steps_b", 4)}


def lab5_source(v):
    return (TWO_WORKERS_C.replace("@IDA@", str(v["id_a"])).replace("@SA@", str(v["steps_a"]))
            .replace("@IDB@", str(v["id_b"])).replace("@SB@", str(v["steps_b"])))


def lab5_fixture(v):
    return {"threads/two_workers.c": lab5_source(v), "threads/starter.c": THREAD_STARTER, "threads/trace.csv": THREAD_TRACE}


def lab5_predict(v):
    ra, rb = v["id_a"] * v["steps_a"], v["id_b"] * v["steps_b"]
    return [question("unjoined", "A program starts two workers and main returns at once, without joining them. Must the line `worker A finished` always appear? (yes/no)", "yesno", "n"),
            question("a", f"Your worker A has id {v['id_a']} and {v['steps_a']} steps; each step adds its id to the result. After main has joined A, what is a.result?", "int", [ra]),
            question("b", f"Your worker B has id {v['id_b']} and {v['steps_b']} steps. After main has joined B, what is b.result?", "int", [rb]),
            question("why", "One sentence: why must main wait for a worker before it reads that worker's result?", "text")]


def lab5_checkpoint(pick, v):
    word = WORDS[pick("word", len(WORDS))]
    steps_a, steps_b = 1 + pick("sa", 6), 1 + pick("sb", 6)
    unjoined, workers = 2 + pick("unjoined", 5), 3 + pick("workers", 4)
    final = v["id_b"] * unjoined
    cv = {"name": word, "steps_a": steps_a, "steps_b": steps_b,
          "ra": v["id_a"] * steps_a, "rb": v["id_b"] * steps_b}
    intro = [f"Case 1. A program starts workers A and B like yours. Main joins A but NOT B, and then prints b.result.",
             f"Worker B has id {v['id_b']} and needs {unjoined} steps of 20 ms each, so its final result is {final}.",
             "Case 2 is a file task, printed after the questions."]
    qs = [question("sure", f"Case 1: is it guaranteed that main prints {final}? (yes/no)", "yesno", "n"),
          question("low", "Case 1: what is the smallest number main could print for b.result?", "int", [0]),
          question("joins", f"A program creates {workers} workers and all creations succeed. How many pthread_join calls does it need?", "int", [workers]),
          question("why", "One sentence: what does main still not know when it reads b.result without joining B?", "text")]
    after = ["Case 2: make a copy of your program with new step counts, and run it.",
             '  cd "$OSLAB_WORKSPACE/lab5"',
             f"  cp threads/two_workers.c threads/{word}.c",
             f"  Edit threads/{word}.c: in the line  struct job a = ...  give worker A {steps_a} steps and worker B {steps_b} steps (keep the ids).",
             f"  gcc -Wall -Wextra -pthread threads/{word}.c -o threads/{word}",
             f"  timeout 5 threads/{word} > checkpoint.txt",
             "  cat checkpoint.txt",
             "Then run: oslab check lab5"]
    return cv, intro, qs, after


LAB5_JOB_LINE = re.compile(r"struct job a = \{\s*(\d+)\s*,\s*(\d+)\s*,\s*0\s*\}\s*,\s*b = \{\s*(\d+)\s*,\s*(\d+)\s*,\s*0\s*\}\s*;")
LAB5_REPORT = re.compile(r"^A result=(-?\d+) B result=(-?\d+)$", re.M)
LAB5_CHECKED_JOIN = re.compile(r"(=\s*pthread_join\s*\(|if\s*\(\s*(\w+\s*=\s*)?pthread_join\s*\()")


def lab5_build(source_text, directory, name):
    """Compile the student's program in a disposable folder. Returns (built, problems, binary)."""
    source = directory / f"{name}.c"
    source.write_text(source_text, encoding="utf-8")
    binary = directory / name
    try:
        done = subprocess.run(["gcc", "-Wall", "-Wextra", "-pthread", str(source), "-o", str(binary)], cwd=str(directory),
                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except FileNotFoundError:
        return False, ["gcc is not installed on this machine: tell the instructor (the lab has a trace fallback)"], binary
    except subprocess.TimeoutExpired:
        return False, ["the compiler took more than 60 seconds"], binary
    lines = [line.strip() for line in done.stderr.decode("utf-8", "replace").splitlines() if line.strip()]
    lines = [line.replace(str(directory) + "/", "") for line in lines]
    if done.returncode:
        return False, ["it does not compile: " + " | ".join(lines[:3])[:240]], binary
    if lines:
        return False, ["the compiler printed a warning (the lab asks for none): " + " | ".join(lines[:2])[:240]], binary
    return True, [], binary


def lab5_run(binary, directory):
    try:
        done = subprocess.run([str(binary)], cwd=str(directory), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=5)
    except subprocess.TimeoutExpired:
        return 124, ""
    return done.returncode, done.stdout.decode("utf-8", "replace")


def lab5_trial(source_text, directory, name, ra, rb):
    """Build and run one version of the program. Returns the problems with its report line."""
    built, problems, binary = lab5_build(source_text, directory, name)
    if not built:
        return problems
    code, out = lab5_run(binary, directory)
    lines = out.splitlines()
    if code:
        return [f"the program ended with status {code} (124 means it ran for more than 5 seconds)"]
    reports = LAB5_REPORT.findall(out)
    if len(reports) != 1:
        return ["main must print one line  A result=NUMBER B result=NUMBER  (after both joins)"]
    got = tuple(int(x) for x in reports[0])
    finished = [i for i, line in enumerate(lines) if re.match(r"^worker \d+ finished$", line)]
    where = next(i for i, line in enumerate(lines) if LAB5_REPORT.match(line))
    if got != (ra, rb):
        hint = "; main read the results before the workers finished: join each worker first" if 0 in got and (ra, rb) != (0, 0) else ""
        return [f"expected A result={ra} B result={rb}, got A result={got[0]} B result={got[1]}{hint}"]
    if len(finished) < 2 or where < max(finished):
        return ["the results are right, but main printed them before both `worker ... finished` lines: it read them too early (by luck)"]
    return []


def check_lab5(target, values, extra):
    ida, idb, sa, sb = values["id_a"], values["id_b"], values["steps_a"], values["steps_b"]
    names = [f"two_workers.c builds with -Wall -Wextra -pthread and no warning",
             f"both workers finish first: main prints `A result={ida * sa} B result={idb * sb}`",
             "the return code of every pthread_join is checked",
             f"changed case (A 0 steps, B 1 step): main prints `A result=0 B result={idb}`"]
    if extra:
        names.append("checkpoint: your copy builds, prints the right results, and checkpoint.txt holds them")
    source = target / "threads/two_workers.c"
    if not source.is_file() or source.is_symlink():
        return [(name, ["threads/two_workers.c does not exist (or is a link): run `oslab start lab5` to get it back"]) for name in names]
    text = read_text(source)
    line = LAB5_JOB_LINE.search(text)
    if line and tuple(int(x) for x in line.groups()) != (ida, sa, idb, sb):
        print(f"NOTE: your program has the numbers a = {{{line.group(1)}, {line.group(2)}}} and b = {{{line.group(3)}, {line.group(4)}}}, "
              f"but your own values are a = {{{ida}, {sa}}} and b = {{{idb}, {sb}}} (oslab values lab5). Put your own numbers in the line "
              "`struct job a = ...`.")
    sandbox = Path(tempfile.mkdtemp(prefix=".check-", dir=str(target)))
    try:
        built, build_problems, _ = lab5_build(text, sandbox, "w")
        results = [(names[0], build_problems)]
        results.append((names[1], build_problems if not built else lab5_trial(text, sandbox, "w", ida * sa, idb * sb)))
        joins = len(LAB5_CHECKED_JOIN.findall(text))
        results.append((names[2], [] if joins >= 2 else [f"found {joins} checked pthread_join call(s); each of the two workers needs one, "
                                                         "written as  rc = pthread_join(...)  or  if (pthread_join(...))"]))
        match = LAB5_JOB_LINE.search(text)
        if not match:
            results.append((names[3], ["keep the line  struct job a = {ID, STEPS, 0}, b = {ID, STEPS, 0};  on one line, as it was"]))
        else:
            changed = text[:match.start()] + f"struct job a = {{{match.group(1)}, 0, 0}}, b = {{{match.group(3)}, 1, 0}};" + text[match.end():]
            results.append((names[3], build_problems if not built else lab5_trial(changed, sandbox, "c", 0, idb)))
        if extra:
            ra, rb = extra["ra"], extra["rb"]
            mine = target / "threads" / f"{extra['name']}.c"
            problems = []
            if not mine.is_file():
                problems.append(f"threads/{extra['name']}.c does not exist: copy your program to that name (Case 2)")
            else:
                problems = lab5_trial(read_text(mine), sandbox, "k", ra, rb)
            line = f"A result={ra} B result={rb}"
            if line not in read_text(target / "checkpoint.txt"):
                problems.append(f"checkpoint.txt does not hold the line `{line}`: save the output of your copy there")
            results.append((names[4], problems))
    finally:
        shutil.rmtree(str(sandbox), ignore_errors=True)
    return results


# (file mode, folder mode, can the owner's group list the folder, the policy as a sentence)
LAB6_POLICIES = (
    (0o640, 0o750, True, "The owner may change the file. The owner's group may read it and list the folder. Others have no access."),
    (0o644, 0o711, False, "Everyone may read the file if they know its name, but only the owner may list the folder. Only the owner may change anything."),
    (0o660, 0o770, True, "The owner and the owner's group may read and change the file and the folder. Others have no access."),
    (0o600, 0o700, False, "Only the owner may use the file and the folder. Nobody else may read, change, list or enter."),
)
LAB6_OWN = 3  # the first three policies are given to students for shared/; the fourth is a checkpoint-only policy


def lab6_values(pick):
    index = pick("policy", LAB6_OWN)
    return {"notice": LAB6_POLICIES[index][3], "box": "sealed-" + WORDS[pick("box", len(WORDS))], "_policy": index}


def lab6_fixture(v):
    return {"private/record.txt": "student-owned record\n", "shared/notice.txt": "Read-only public notice\n"}


def lab6_predict(v):
    group_list = LAB6_POLICIES[v["_policy"]][2]
    return [question("list", "A directory has mode 600 (rw-------) and holds a file with mode 600 that you own. Can you list the NAMES in the directory? (yes/no)", "yesno", "y"),
            question("open", "Can you open that file through the directory? (yes/no)", "yesno", "n"),
            question("mode", "Type the octal mode (three digits) of a file with the permissions rw-r-----.", "word", "640"),
            question("group", f"Your notice policy for shared/ is: {v['notice']}  Can the owner's group list the names in shared/? (yes/no)", "yesno", "y" if group_list else "n"),
            question("why", "One sentence: which permission bit of a directory decides whether you can open a file inside it?", "text")]


def lab6_checkpoint(pick, v):
    others = [i for i in range(len(LAB6_POLICIES)) if i != v["_policy"]]
    index = others[pick("policy", len(others))]
    file_mode, dir_mode, group_list, sentence = LAB6_POLICIES[index]
    folder = "checkpoint-" + WORDS[pick("word", len(WORDS))]
    cv = {"folder": folder, "file_mode": f"{file_mode:03o}", "dir_mode": f"{dir_mode:03o}"}
    intro = [f"A new folder {folder}/ will hold one file, data.txt. The policy for both is:", f"    {sentence}",
             "Answer before you create anything."]
    qs = [question("file", "Type the octal mode (three digits) of data.txt.", "word", cv["file_mode"]),
          question("dir", f"Type the octal mode (three digits) of the folder {folder}.", "word", cv["dir_mode"]),
          question("group", "Can the owner's group list the names in the folder? (yes/no)", "yesno", "y" if group_list else "n"),
          question("why", "One sentence: why must the folder have an x (search) bit for someone to read data.txt inside it?", "text")]
    after = ["Now make it for real, with your two answers:",
             '  cd "$OSLAB_WORKSPACE/lab6"',
             f"  mkdir {folder}",
             f"  printf 'checkpoint text\\n' > {folder}/data.txt",
             f"  chmod YOUR_FILE_MODE {folder}/data.txt     # replace YOUR_FILE_MODE with your answer",
             f"  chmod YOUR_DIR_MODE {folder}     # replace YOUR_DIR_MODE with your answer",
             f"  stat -c '%A %a %n' {folder} {folder}/data.txt > checkpoint.txt",
             "  cat checkpoint.txt",
             "Then run: oslab check lab6"]
    return cv, intro, qs, after


def lab6_mode_problem(target, rel, want, is_dir, role):
    """A problem line when `rel` does not have mode `want`, else None."""
    path = target / rel
    try:
        info = os.lstat(str(path))
    except OSError:
        return f"{rel} does not exist"
    if stat.S_ISLNK(info.st_mode):
        return f"{rel} is a link: use the real file"
    if stat.S_ISDIR(info.st_mode) != is_dir:
        return f"{rel} must be a {'folder' if is_dir else 'file'}"
    mode = stat.S_IMODE(info.st_mode)
    if mode == want:
        return None
    kind = stat.S_IFDIR if is_dir else stat.S_IFREG
    return (f"{rel} has mode {mode:03o} ({stat.filemode(mode | kind)}) but {role} needs {want:03o} "
            f"({stat.filemode(want | kind)})")


def lab6_listed_modes(text):
    """From lines in the form of  stat -c '%A %a %U:%G %n'  : {name: octal mode text}."""
    found = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and re.match(r"^[0-7]{3,4}$", parts[1]):
            skip = 3 if len(parts) >= 4 and re.match(r"^[\w.-]+:[\w.-]+$", parts[2]) else 2  # owner:group is optional
            found[" ".join(parts[skip:])] = parts[1]
    return found


def check_lab6(target, values, extra):
    file_mode, dir_mode, _, _ = LAB6_POLICIES[values["_policy"]]
    box = values["box"]
    private = [lab6_mode_problem(target, "private", 0o700, True, "a private folder"),
               lab6_mode_problem(target, "private/record.txt", 0o600, False, "a private record")]
    notice = [lab6_mode_problem(target, "shared", dir_mode, True, "your notice policy"),
              lab6_mode_problem(target, "shared/notice.txt", file_mode, False, "your notice policy")]
    trace = read_text(target / "evidence/traversal.txt")
    sealed = [p for p in [lab6_mode_problem(target, f"demo/{box}", 0o700, True, "the restored demo folder")] if p]
    inside = read_text(target / "demo" / box / "item.txt")
    if "inside" not in inside:
        sealed.append(f"demo/{box}/item.txt must hold the line `inside` (see Core 2, step 2)")
    if "permission denied" not in trace.lower():
        sealed.append("evidence/traversal.txt has no `Permission denied` line: save the failed read, too (Core 2, step 2)")
    elif "inside" not in trace:
        sealed.append("evidence/traversal.txt has no successful read (`inside`) after you restored the mode")
    listed = lab6_listed_modes(read_text(target / "evidence/policy.txt"))
    record = []
    for rel in ("private", "private/record.txt", "shared", "shared/notice.txt"):
        try:
            actual = f"{stat.S_IMODE(os.lstat(str(target / rel)).st_mode):03o}"
        except OSError:
            continue
        if listed.get(rel) != actual:
            record.append(f"evidence/policy.txt must list {rel} with its mode {actual}: run the stat line again after the last chmod (Core 1)"
                          if rel not in listed else f"evidence/policy.txt shows {listed[rel]} for {rel} but it is {actual} now: run the stat line again")
    text = read_text(target / "private/record.txt")
    if not text.startswith("student-owned record"):
        record.append("private/record.txt lost its first line `student-owned record`; only append to it")
    if "owner update" not in text:
        record.append("private/record.txt has no line `owner update`: append it as its owner (Core 2, step 1)")
    results = [("private/ is 700 and private/record.txt is 600", [p for p in private if p]),
               (f"shared/ and shared/notice.txt follow your notice policy ({dir_mode:03o} and {file_mode:03o})", [p for p in notice if p]),
               (f"demo/{box}: the read failed, the mode is back to 700 and the file is read again", sealed),
               ("evidence/policy.txt lists the four modes as they are now, and the record has your update", record)]
    if extra:
        folder = extra["folder"]
        problems = [p for p in (lab6_mode_problem(target, folder, int(extra["dir_mode"], 8), True, "the checkpoint policy"),
                                lab6_mode_problem(target, f"{folder}/data.txt", int(extra["file_mode"], 8), False, "the checkpoint policy")) if p]
        if "checkpoint text" not in read_text(target / folder / "data.txt"):
            problems.append(f"{folder}/data.txt must hold the line `checkpoint text`")
        listed = lab6_listed_modes(read_text(target / "checkpoint.txt"))
        if listed.get(folder) != extra["dir_mode"] or listed.get(f"{folder}/data.txt") != extra["file_mode"]:
            problems.append("checkpoint.txt must hold the stat line of the folder and of data.txt (run it after the last chmod)")
        results.append(("checkpoint: the new folder and data.txt have the modes of the policy, and checkpoint.txt shows them", problems))
    return results


LAB7_WORDS = ("alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta")
LAB7_SKELETON = "#!/usr/bin/env bash\nset -u\n# TODO: loop over quoted arguments, reject missing files, and count words.\n"


def lab7_values(pick):
    """file1 has spaces in its name, file2 starts with a dash. Keys that start with _ are the word counts."""
    a = pick("a", len(WORDS))
    b = (a + 1 + pick("b", len(WORDS) - 1)) % len(WORDS)
    c = (b + 1 + pick("c", len(WORDS) - 1)) % len(WORDS)
    d = (c + 1 + pick("d", len(WORDS) - 1)) % len(WORDS)
    parts = 2 + pick("parts", 2)
    first = " ".join([WORDS[a], WORDS[b], WORDS[c]][:parts]) + ".txt"
    return {"file1": first, "file2": f"-{WORDS[d]}.txt", "_n1": 2 + pick("n1", 5), "_n2": 1 + pick("n2", 4), "_parts": parts}


def lab7_texts(v):
    return " ".join(LAB7_WORDS[:v["_n1"]]) + "\n", " ".join(LAB7_WORDS[:v["_n2"]]) + "\n"


def lab7_fixture(v):
    first, second = lab7_texts(v)
    return {f"input/{v['file1']}": first, f"input/{v['file2']}": second, "count_words.sh": LAB7_SKELETON}


def lab7_predict(v):
    return [question("pieces", f"A script receives the file name '{v['file1']}' as ONE argument, but loops over an unquoted $@. Into how many pieces does the loop split that name?", "int", [v["_parts"]]),
            question("dash", f"You are inside input/ and run  wc -w {v['file2']}  (no --). Does wc count the words of that file? (yes/no)", "yesno", "n"),
            question("status", "One input file is missing and the next one is fine. Should the script end with status 0? (yes/no)", "yesno", "n"),
            question("why", "One sentence: why does a leading dash in a file name need  --  before it?", "text")]


def lab7_checkpoint(pick, v):
    word = WORDS[pick("w1", len(WORDS))]
    other = WORDS[(WORDS.index(word) + 1 + pick("w2", len(WORDS) - 1)) % len(WORDS)]
    third = WORDS[(WORDS.index(other) + 1 + pick("w3", len(WORDS) - 1)) % len(WORDS)]
    kinds = ((f"{word}  {other}.txt", 2), (f"-{word} {other}.txt", 2), (f"{word} {other} {third}.txt", 3))
    name, tokens = kinds[pick("kind", len(kinds))]
    words = 2 + pick("words", 5)
    text = " ".join(LAB7_WORDS[:words])
    cv = {"name": name, "words": words, "text": text}
    intro = [f"A new input file will be called  '{name}'  (the name is between single quotes; it has no quote in it).",
             f"Its content is {words} words. Answer before you create it."]
    qs = [question("tokens", f"You forget the quotes and type  bash count_words.sh input/{name}.  How many arguments does the shell give your script?", "int", [tokens]),
          question("words", "How many words should your script report for the new file?", "int", [words]),
          question("status", "Two files are given: the first is missing and the second is fine. Should the final status be 0? (yes/no)", "yesno", "n"),
          question("why", "One sentence: why do you write \"$file\" with double quotes in the script, and not $file?", "text")]
    after = ["Now make the file and run your own script on it, in your lab7 folder:",
             '  cd "$OSLAB_WORKSPACE/lab7"',
             f"  printf '%s\\n' '{text}' > 'input/{name}'",
             f"  bash count_words.sh 'input/{name}' > checkpoint.txt",
             "  cat checkpoint.txt",
             "Then run: oslab check lab7"]
    return cv, intro, qs, after


def lab7_run(script, arguments, cwd, direct=False):
    """Run the student's script on test files. Returns (status, stdout, stderr)."""
    command = ([str(script)] if direct else ["bash", str(script)]) + list(arguments)
    try:
        done = subprocess.run(command, cwd=str(cwd), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=10)
    except subprocess.TimeoutExpired:
        return 124, "", "the script ran for more than 10 seconds"
    except OSError as exc:
        return 126, "", str(exc)
    return done.returncode, done.stdout.decode("utf-8", "replace"), done.stderr.decode("utf-8", "replace")


def lab7_line_problem(out, name, count):
    """A problem line unless some output line holds the file name and its word count."""
    lines = [line for line in out.splitlines() if name in line]
    if not lines:
        return f"no output line holds the file name `{name}`: print the name, intact, with its count"
    if not any(re.search(rf"(?<!\d){count}(?!\d)", line) for line in lines):
        return f"the line for `{name}` must show {count} words; it says: {lines[0][:60]!r}"
    return None


def check_lab7(target, values, extra):
    first, second = values["file1"], values["file2"]
    n1, n2 = values["_n1"], values["_n2"]
    names = [f"count_words.sh runs directly (./count_words.sh) on `{first}` and reports {n1} words",
             f"two files at once: `{first}` ({n1}) and `{second}` ({n2}), names intact",
             f"run inside input/: `{second}` (a leading dash) is counted, not read as an option",
             "no argument: usage on stderr; a missing file: message on stderr, the next file is still counted, final status not 0"]
    if extra:
        names.append("checkpoint: the new file is counted by your script, and checkpoint.txt holds the line")
    script = target / "count_words.sh"
    if not script.is_file() or script.is_symlink():
        return [(name, ["count_words.sh does not exist (or is a link): write it in Core 1"]) for name in names]
    sandbox = Path(tempfile.mkdtemp(prefix=".check-", dir=str(target)))
    try:
        shutil.copy2(str(script), str(sandbox / "count_words.sh"))
        (sandbox / "input").mkdir()
        text1, text2 = lab7_texts(values)
        (sandbox / "input" / first).write_text(text1, encoding="utf-8")
        (sandbox / "input" / second).write_text(text2, encoding="utf-8")
        mine = sandbox / "count_words.sh"
        results = []
        problems = []
        if not os.access(str(mine), os.X_OK):
            problems.append("the script is not executable by its owner: run `chmod u+x count_words.sh`")
        else:
            code, out, err = lab7_run("./count_words.sh", [f"input/{first}"], sandbox, direct=True)
            problems += [f"status {code}, expected 0" + (f"; message: {err.strip()[:80]}" if err.strip() else "")] if code else []
            problems += [p for p in [lab7_line_problem(out, first, n1)] if p]
        results.append((names[0], problems))
        code, out, err = lab7_run(mine, [f"input/{first}", f"input/{second}"], sandbox)
        problems = ([f"status {code}, expected 0" + (f"; message: {err.strip()[:80]}" if err.strip() else "")] if code else [])
        problems += [p for p in [lab7_line_problem(out, first, n1), lab7_line_problem(out, second, n2)] if p]
        results.append((names[1], problems))
        code, out, err = lab7_run("../count_words.sh", [second], sandbox / "input")
        problems = ([f"status {code}, expected 0: put `--` before the file operand of wc, and quote it" + (f" ({err.strip()[:70]})" if err.strip() else "")] if code else [])
        problems += [p for p in [lab7_line_problem(out, second, n2)] if p]
        results.append((names[2], problems))
        problems = []
        code, out, err = lab7_run(mine, [], sandbox)
        if code == 0:
            problems.append("with no argument the script must end with a status other than 0")
        if not err.strip():
            problems.append("with no argument, print a usage message to stderr (>&2)")
        code, out, err = lab7_run(mine, ["missing.txt", f"input/{first}"], sandbox)
        if code == 0:
            problems.append("a missing file must make the final status other than 0")
        if not err.strip():
            problems.append("a missing file needs a message on stderr (>&2)")
        problem = lab7_line_problem(out, first, n1)
        if problem:
            problems.append("after the missing file, the next file must still be counted: " + problem)
        results.append((names[3], problems))
        if extra:
            (sandbox / "input" / extra["name"]).write_text(extra["text"] + "\n", encoding="utf-8")
            code, out, err = lab7_run(mine, [f"input/{extra['name']}"], sandbox)
            problems = ([f"status {code}, expected 0" + (f"; message: {err.strip()[:80]}" if err.strip() else "")] if code else [])
            problems += [p for p in [lab7_line_problem(out, extra["name"], extra["words"])] if p]
            if read_text(target / "input" / extra["name"]).split() != extra["text"].split():
                problems.append(f"input/{extra['name']} must hold the {extra['words']} words printed by oslab checkpoint lab7")
            problem = lab7_line_problem(read_text(target / "checkpoint.txt"), extra["name"], extra["words"])
            if problem:
                problems.append("checkpoint.txt: " + problem)
            results.append((names[4], problems))
    finally:
        shutil.rmtree(str(sandbox), ignore_errors=True)
    return results


LAB9_RESOURCES = ("amber", "birch", "cedar", "dune", "ember", "frost", "grove", "haze")
LAB9_WORKER = r'''#!/usr/bin/env bash
set -euo pipefail
[[ $# -eq 2 && "$1" =~ ^(A|B)$ && "$2" =~ ^(opposite|ordered)$ ]] || { echo 'usage: worker.sh A|B opposite|ordered' >&2; exit 2; }
role=$1
mode=$2
vault=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
res1=@R1@
res2=@R2@
mkdir -p "$vault/coord"
# Worker A takes @AF@ first and @AS@ second. Worker B takes them the other way round.
first=@FIRST@; second=@SECOND@
# TODO: in ordered mode, every worker must use one global order.
if [[ "$role" = B ]]; then tmp=$first; first=$second; second=$tmp; fi
exec 8>"$vault/$first.lock"
flock -x -w 2 8 || { echo "$role first lock timeout"; exit 3; }
printf '%s holds %s\n' "$role" "$first"
sleep "${HOLD:-0}"   # teaching delay after the first lock; keep this line
if [[ "$mode" = opposite ]]; then
    touch "$vault/coord/$role.ready"
    other=B
    [[ "$role" = B ]] && other=A
    for step in {1..30}; do
        [[ -f "$vault/coord/$other.ready" ]] && break
        sleep 0.1
    done
    [[ -f "$vault/coord/$other.ready" ]] || { echo 'barrier timeout'; exit 4; }
fi
exec 9>"$vault/$second.lock"
printf '%s requests %s\n' "$role" "$second"
flock -x -w 2 9 || { echo "$role second lock timeout"; exit 5; }
printf '%s holds both\n' "$role"
'''
LAB9_OLD_WORKER = "#!/usr/bin/env bash\nset -euo pipefail\n# TODO: acquire two owned lock files with flock -w 2; log each acquisition.\n"


def lab9_values(pick):
    one = pick("res1", len(LAB9_RESOURCES))
    two = (one + 1 + pick("res2", len(LAB9_RESOURCES) - 1)) % len(LAB9_RESOURCES)
    return {"res1": LAB9_RESOURCES[one], "res2": LAB9_RESOURCES[two], "a_first": LAB9_RESOURCES[(one, two)[pick("a_first", 2)]]}


def lab9_worker(v):
    first, second = ("$res1", "$res2") if v["a_first"] == v["res1"] else ("$res2", "$res1")
    second_name = v["res2"] if v["a_first"] == v["res1"] else v["res1"]
    return (LAB9_WORKER.replace("@R1@", v["res1"]).replace("@R2@", v["res2"]).replace("@AF@", v["a_first"])
            .replace("@AS@", second_name).replace("@FIRST@", first).replace("@SECOND@", second))


def lab9_fixture(v):
    return {f"vault/{v['res1']}.txt": f"{v['res1']}\n", f"vault/{v['res2']}.txt": f"{v['res2']}\n", "vault/worker.sh": lab9_worker(v)}


def lab9_predict(v):
    a_first = v["a_first"]
    a_second = v["res2"] if a_first == v["res1"] else v["res1"]
    return [question("stuck", f"Worker A holds {a_first} and requests {a_second}. Worker B holds {a_second} and requests {a_first}. Can either one get its second lock before the other releases something? (yes/no)", "yesno", "n"),
            question("edges", "How many wait edges (a worker waiting for a lock that the other holds) does this picture have?", "int", [2]),
            question("timeout", "Each worker waits at most 2 seconds (flock -w 2). Does that timeout PREVENT the deadlock? (yes/no)", "yesno", "n"),
            question("order", f"Now both workers always take {v['res1']} first and {v['res2']} second. Can they still wait for each other forever? (yes/no)", "yesno", "n"),
            question("why", "One sentence: why does one global lock order remove the circular wait?", "text")]


def lab9_checkpoint(pick, v):
    names = list(LAB9_RESOURCES)
    x = names.pop(pick("x", len(names)))
    y = names.pop(pick("y", len(names)))
    z = names.pop(pick("z", len(names)))
    cv = {"x": x, "y": y, "z": z}
    intro = [f"A third worker C joins. Three workers each need two of the locks {x}, {y} and {z}:",
             f"    A holds {x} and requests {y}",
             f"    B holds {y} and requests {z}",
             f"    C holds {z} and requests {x}",
             "Answer before you do the file task."]
    qs = [question("cycle", "Can all three workers be stuck at the same time? (yes/no)", "yesno", "y"),
          question("wrong", f"You choose the global order {x}, then {y}, then {z}. Which worker (type A, B or C) lists its two locks in the wrong order?", "word", "C"),
          question("after", "If all three workers follow that global order, how many of them can wait forever in a cycle?", "int", [0]),
          question("why", "One sentence: does your order rule still work when a third worker joins? Why?", "text")]
    after = ["Now test that your ordering rule does not depend on the names. Use YOUR worker script with two new names:",
             '  cd "$OSLAB_WORKSPACE/lab9"',
             "  cp vault/worker.sh vault/third.sh",
             f"  Edit vault/third.sh: change ONLY the two lines at its top to  res1={x}  and  res2={y}",
             "  timeout 6 bash vault/third.sh A ordered > evidence/cp-a.txt 2>&1 &",
             "  timeout 6 bash vault/third.sh B ordered > evidence/cp-b.txt 2>&1 &",
             "  wait",
             "  cat evidence/cp-a.txt evidence/cp-b.txt | tee checkpoint.txt",
             "Then run: oslab check lab9"]
    return cv, intro, qs, after


def lab9_pair(script, mode, hold, cwd):
    """Start worker A and worker B of the student's script together. Returns {role: (status, output)}."""
    folder = Path(cwd)
    for marker_file in (folder / "coord").glob("*.ready") if (folder / "coord").is_dir() else ():
        marker_file.unlink()
    env = dict(os.environ, HOLD=str(hold))
    processes = {role: subprocess.Popen(["bash", str(script), role, mode], cwd=str(folder), env=env,
                                        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                 for role in ("A", "B")}
    result = {}
    for role, process in processes.items():
        try:
            out, _ = process.communicate(timeout=8)
            code = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            out, _ = process.communicate()
            code = 124
        result[role] = (code, out.decode("utf-8", "replace"))
    return result


def lab9_ordered_problems(result):
    """Problems when the two workers did not both finish in ordered mode."""
    problems = []
    for role, (code, out) in result.items():
        if code == 5:
            problems.append(f"worker {role} timed out on its second lock: the workers still take the two locks in different orders")
        elif code == 124:
            problems.append(f"worker {role} ran for more than 8 seconds")
        elif code:
            problems.append(f"worker {role} ended with status {code}: {out.strip()[:80]!r}")
        elif f"{role} holds both" not in out:
            problems.append(f"worker {role} did not print `{role} holds both`")
    return problems


def check_lab9(target, values, extra):
    res1, res2 = values["res1"], values["res2"]
    names = ["opposite mode: both workers hold their first lock and at least one times out on the second (status 5)",
             "ordered mode: both workers finish with status 0 and print `holds both`",
             "your ordering rule does not depend on the names: it also works with two other resource names",
             "evidence/opposite.txt shows the conflict and evidence/ordered.txt shows both workers finishing"]
    if extra:
        names.append("checkpoint: your script works with the checkpoint's names, and checkpoint.txt shows both workers")
    script = target / "vault/worker.sh"
    if not script.is_file() or script.is_symlink():
        return [(name, ["vault/worker.sh does not exist (or is a link): run `oslab start lab9` or `oslab reset lab9`"]) for name in names]
    text = read_text(script)
    sandbox = Path(tempfile.mkdtemp(prefix=".check-", dir=str(target)))
    try:
        def fresh(name, content):
            folder = sandbox / name
            folder.mkdir()
            (folder / "worker.sh").write_text(content, encoding="utf-8")
            return folder / "worker.sh", folder
        mine, folder = fresh("v1", text)
        result = lab9_pair(mine, "opposite", 0, folder)
        problems = []
        if not any(code == 5 for code, _ in result.values()):
            problems.append("no worker timed out on its second lock: in opposite mode worker A and worker B must take the two locks "
                            "in opposite orders (and the barrier must stay)")
        for role, (code, out) in result.items():
            if "holds" not in out and code not in (0, 5):
                problems.append(f"worker {role} ended with status {code} before it held a lock: {out.strip()[:80]!r}")
        results = [(names[0], problems)]
        mine, folder = fresh("v2", text)
        ordered_problems = lab9_ordered_problems(lab9_pair(mine, "ordered", 0.6, folder))
        results.append((names[1], ordered_problems))
        one, two = re.search(r"^res1=\S*$", text, re.M), re.search(r"^res2=\S*$", text, re.M)
        if ordered_problems:
            results.append((names[2], ["fix the ordered mode first (the milestone above)"]))
        elif not one or not two:
            results.append((names[2], ["keep the two lines  res1=...  and  res2=...  at the top of the script, as they were (oslab reset lab9 restores them)"]))
        else:
            renamed = re.sub(r"^res1=\S*$", "res1=quartz", re.sub(r"^res2=\S*$", "res2=rubble", text, flags=re.M), flags=re.M)
            mine, folder = fresh("v3", renamed)
            problems = lab9_ordered_problems(lab9_pair(mine, "ordered", 0.6, folder))
            if problems:
                problems.append(f"with other lock names the workers wait for each other again: your rule must not depend on the names {res1} and {res2}")
            results.append((names[2], problems))
        opposite, ordered = read_text(target / "evidence/opposite.txt"), read_text(target / "evidence/ordered.txt")
        problems = []
        if not re.search(r"^opposite A=\d+ B=\d+", opposite, re.M) or ("second lock timeout" not in opposite and not re.search(r"=5\b", opposite)):
            problems.append("evidence/opposite.txt must start with `opposite A=.. B=..` and show the timeout of a worker (Levels 2-3, step 3)")
        if not re.search(r"^ordered A=0 B=0", ordered, re.M) or ordered.count("holds both") < 2:
            problems.append("evidence/ordered.txt must start with `ordered A=0 B=0` and show `holds both` twice (Levels 5-6, step 2)")
        results.append((names[3], problems))
        if extra:
            third = read_text(target / "vault/third.sh")
            problems = []
            if not third:
                problems.append("vault/third.sh does not exist: copy your worker.sh to that name (checkpoint task)")
            elif not re.search(rf"^res1={extra['x']}$", third, re.M) or not re.search(rf"^res2={extra['y']}$", third, re.M):
                problems.append(f"in vault/third.sh the two lines must read  res1={extra['x']}  and  res2={extra['y']}")
            else:
                mine, folder = fresh("v5", third)
                problems += lab9_ordered_problems(lab9_pair(mine, "ordered", 0.6, folder))
            saved = read_text(target / "checkpoint.txt")
            if saved.count("holds both") < 2 or extra["x"] not in saved:
                problems.append(f"checkpoint.txt must show both workers with `holds both` and the new lock names ({extra['x']}, {extra['y']})")
            results.append((names[4], problems))
    finally:
        shutil.rmtree(str(sandbox), ignore_errors=True)
    return results


LAB10_NAMES = ("nightly", "daily", "weekly", "vault", "records", "report", "archive", "memo")
LAB10_SCRIPT = r'''#!/usr/bin/env bash
set -euo pipefail
keep=@KEEP@
name=@NAME@
work=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
mkdir -p "$work/backups"
stamp=$(date -u +%Y%m%dT%H%M%S%N)
final="$work/backups/$name-$stamp-$$.tar.gz"
pending=$(mktemp "$work/backups/.pending-XXXXXX")
trap 'rm -f -- "$pending"' EXIT
tar -czf "$pending" -C "$work" project
tar -tzf "$pending" >/dev/null
mv -- "$pending" "$final"
# TODO: retain only the newest $keep completed $name-*.tar.gz files.
printf 'created %s\n' "$final"
'''
LAB10_OLD_SCRIPT = "#!/usr/bin/env bash\nset -euo pipefail\n# TODO: archive project with absolute paths, verify it, retain newest three owned archives.\n"
LAB10_PROJECT = {"project/report.txt": "report v1\n", "project/config.ini": "mode=practice\n"}


def lab10_values(pick):
    return {"keep": 2 + pick("keep", 4), "name": LAB10_NAMES[pick("name", len(LAB10_NAMES))]}


def lab10_fixture(v):
    return dict(LAB10_PROJECT, **{"backup.sh": LAB10_SCRIPT.replace("@KEEP@", str(v["keep"])).replace("@NAME@", v["name"])})


def lab10_pattern(name):
    return re.compile(rf"^{re.escape(name)}-[0-9]{{8}}T[0-9]{{15}}-[0-9]+\.tar\.gz$")


def lab10_predict(v):
    keep, name = v["keep"], v["name"]
    return [question("assume", "A cron entry runs backup.sh with its full path, from another directory and with almost no environment. Must it work just because it worked in your shell? (yes/no)", "yesno", "n"),
            question("count", f"Your finished script keeps {keep} archives. You run it {keep + 3} times in a row. How many archives named {name}-... remain in backups/?", "int", [keep]),
            question("which", "Which ones remain: the oldest or the newest? (type oldest or newest)", "word", "newest"),
            question("unrelated", f"backups/ also holds keep-me.txt and a file called {name}-notes.tar.gz. Does your script delete either of them? (yes/no)", "yesno", "n"),
            question("why", "One sentence: why do the names of the archives let you find the oldest one?", "text")]


def lab10_checkpoint(pick, v):
    keep = 2 + pick("keep", 4)
    if keep == v["keep"]:
        keep = 2 + (keep - 1) % 4
    runs = keep + 2
    cv = {"keep": keep, "runs": runs}
    name = v["name"]
    intro = [f"New rule: keep only the newest {keep} archives. You run the script {runs} times in a row.",
             "Answer before you change anything."]
    qs = [question("left", f"How many archives named {name}-... remain after the {runs} runs?", "int", [keep]),
          question("gone", "Which archive is removed first: the oldest or the newest? (type oldest or newest)", "word", "oldest"),
          question("notes", f"backups/ holds a file called {name}-notes.tar.gz. Must the script delete it? (yes/no)", "yesno", "n"),
          question("why", "One sentence: what must your script contain so that this rule needs a change in only one place?", "text")]
    after = ["Now test it on a copy of YOUR script, in your lab10 folder:",
             '  cd "$OSLAB_WORKSPACE/lab10"',
             "  cp backup.sh backup-cp.sh",
             f"  Edit backup-cp.sh: change only the line  keep=...  to  keep={keep}",
             f"  for i in $(seq 1 {runs}); do bash backup-cp.sh; done",
             "  ls backups > checkpoint.txt",
             "  cat checkpoint.txt",
             "Then run: oslab check lab10"]
    return cv, intro, qs, after


def lab10_sandbox(parent, script_text, mode, script_name="backup.sh"):
    """A disposable lab folder: the student's script, the project, and files in backups/ that must survive."""
    folder = Path(tempfile.mkdtemp(prefix="run-", dir=str(parent)))
    (folder / script_name).write_text(script_text, encoding="utf-8")
    os.chmod(str(folder / script_name), mode)
    for rel, text in LAB10_PROJECT.items():
        (folder / rel).parent.mkdir(exist_ok=True)
        (folder / rel).write_text(text, encoding="utf-8")
    (folder / "backups").mkdir()
    return folder


def lab10_run(command, cwd, env=None):
    try:
        done = subprocess.run(command, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=20)
    except subprocess.TimeoutExpired:
        return 124, "the script ran for more than 20 seconds"
    return done.returncode, done.stderr.decode("utf-8", "replace").strip()[:100]


def lab10_archives(folder, name):
    pattern = lab10_pattern(name)
    return sorted(p.name for p in (folder / "backups").iterdir() if p.is_file() and not p.is_symlink() and pattern.match(p.name))


def lab10_series(script_name, folder, name, keep, runs):
    """Run the script `runs` times. Returns (problems, archives still there)."""
    seen, problems = set(), []
    for number in range(runs):
        code, err = lab10_run(["bash", str(folder / script_name)], folder)
        if code:
            return [f"run {number + 1} ended with status {code}" + (f": {err}" if err else "")], []
        seen |= set(lab10_archives(folder, name))
    left = lab10_archives(folder, name)
    wanted = sorted(seen)[-keep:]
    if len(left) != keep:
        problems.append(f"{len(left)} archive(s) named {name}-... remain after {runs} runs, expected {keep}"
                        + (f" (does your pattern also match {name}-notes.tar.gz?)" if len(left) < keep else " (is anything deleted?)"))
    elif left != wanted:
        problems.append("the archives that remain are not the newest ones: sort the names and remove from the oldest end")
    return problems, left


def check_lab10(target, values, extra):
    keep, name = values["keep"], values["name"]
    names = [f"one run makes a complete archive {name}-STAMP-PID.tar.gz that restores (file listing and bytes)",
             f"retention: after {keep + 2} runs exactly the {keep} newest {name}-... archives remain",
             f"files that are not yours stay: keep-me.txt and {name}-notes.tar.gz are untouched",
             "restricted environment: run from another folder with env -i and PATH=/usr/bin:/bin, the script still works"]
    if extra:
        names.append(f"checkpoint: your copy with keep={extra['keep']} leaves {extra['keep']} archives, and checkpoint.txt lists them")
    script = target / "backup.sh"
    if not script.is_file() or script.is_symlink():
        return [(n, ["backup.sh does not exist (or is a link): run `oslab start lab10` or write it in Core 1"]) for n in names]
    text = read_text(script)
    mode = stat.S_IMODE(os.lstat(str(script)).st_mode) | stat.S_IRUSR
    sandbox = Path(tempfile.mkdtemp(prefix=".check-", dir=str(target)))
    try:
        # 1: one run, then restore
        folder = lab10_sandbox(sandbox, text, mode)
        code, err = lab10_run(["bash", str(folder / "backup.sh")], folder)
        problems = []
        archives = lab10_archives(folder, name)
        if code:
            problems.append(f"the first run ended with status {code}" + (f": {err}" if err else ""))
        elif len(archives) != 1:
            problems.append(f"expected one archive named {name}-STAMP-PID.tar.gz in backups/, found {len(archives)}"
                            + (" (the old name `backup-` is not yours: use `name` from oslab values lab10)" if list((folder / "backups").glob("backup-*")) and not archives else ""))
        else:
            archive = folder / "backups" / archives[0]
            listed = subprocess.run(["tar", "-tzf", str(archive)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            code, listing = listed.returncode, listed.stdout.decode("utf-8", "replace")
            if code or "project/report.txt" not in listing or "project/config.ini" not in listing:
                problems.append("the archive must list project/report.txt and project/config.ini (use tar -C so the member names start with project/)")
            else:
                restore = folder / "restored"
                restore.mkdir()
                subprocess.run(["tar", "-xzf", str(archive), "-C", str(restore)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for rel, text_ in LAB10_PROJECT.items():
                    if read_text(restore / rel) != text_:
                        problems.append(f"{rel} does not come back with the same bytes after restoring")
            if list((folder / "backups").glob(".pending-*")):
                problems.append("a .pending-... file is left in backups/: only complete archives may stay")
        results = [(names[0], problems)]
        # 2 and 3: retention and files that are not yours
        folder = lab10_sandbox(sandbox, text, mode)
        (folder / "backups" / "keep-me.txt").write_text("unrelated; preserve me\n", encoding="utf-8")
        (folder / "backups" / f"{name}-notes.tar.gz").write_text("not an archive made by the script\n", encoding="utf-8")
        problems, _ = lab10_series("backup.sh", folder, name, keep, keep + 2)
        results.append((names[1], problems))
        survivors = ["write the retention first (the milestone above): files that are not yours can only be tested "
                     "when your script really deletes old archives"] if problems else []
        for fixed, expected in (("keep-me.txt", "unrelated; preserve me\n"), (f"{name}-notes.tar.gz", "not an archive made by the script\n")):
            if read_text(folder / "backups" / fixed) != expected:
                survivors.append(f"backups/{fixed} was deleted or changed: remove only files that match the exact names made by this script")
        results.append((names[2], survivors))
        # 4: restricted environment, other working directory
        folder = lab10_sandbox(sandbox, text, mode)
        elsewhere = sandbox / "elsewhere"
        elsewhere.mkdir(exist_ok=True)
        code, err = lab10_run(["env", "-i", f"HOME={target}", "PATH=/usr/bin:/bin", "/bin/bash", str(folder / "backup.sh")], elsewhere)
        problems = []
        if code:
            problems.append(f"with env -i the script ended with status {code}" + (f": {err}" if err else "") + ". Find the program or the folder it expects")
        elif len(lab10_archives(folder, name)) != 1:
            problems.append("with env -i no archive appeared in the script's own backups/ folder")
        results.append((names[3], problems))
        if extra:
            wanted = extra["keep"]
            mine = target / "backup-cp.sh"
            problems = []
            if not mine.is_file():
                problems.append("backup-cp.sh does not exist: copy backup.sh to that name (checkpoint task)")
            else:
                copy_text = read_text(mine)
                if not re.search(rf"^keep={wanted}\s*$", copy_text, re.M):
                    problems.append(f"in backup-cp.sh the line must read  keep={wanted}")
                folder = lab10_sandbox(sandbox, copy_text, mode, "backup-cp.sh")
                (folder / "backups" / f"{name}-notes.tar.gz").write_text("not an archive made by the script\n", encoding="utf-8")
                found, _ = lab10_series("backup-cp.sh", folder, name, wanted, extra["runs"])
                problems += found
            listed = [line for line in read_text(target / "checkpoint.txt").splitlines() if lab10_pattern(name).match(line.strip())]
            if len(listed) != wanted:
                problems.append(f"checkpoint.txt must list the {wanted} archives that remain in backups/ (found {len(listed)})")
            results.append((names[4], problems))
    finally:
        shutil.rmtree(str(sandbox), ignore_errors=True)
    return results


def lab8_values(pick):
    # Each buyer alone fits in the stock; together they never do (stock >= 7, each wants stock-3 or more).
    stock = 7 + pick("stock", 8)
    return {"stock": stock, "buyer_a": stock - 1 - pick("a", 3), "buyer_b": stock - 1 - pick("b", 3)}


def lab8_predict(v):
    s, a, b = v["stock"], v["buyer_a"], v["buyer_b"]
    return [question("accepted", f"Stock is {s}. Buyer A wants {a} and buyer B wants {b}. They run the unsafe buy.sh at the same time and both read the stock before either writes. How many purchases are accepted?", "int", [2]),
            question("sold", "How many units does sales.log show as sold in total?", "int", [a + b]),
            question("stock", "Give one value that stock.txt can hold at the end.", "int", sorted({s - a, s - b})),
            question("why", f"One sentence: is `units sold + units left = {s}` still true? Why?", "text")]


def lab8_checkpoint(pick, v):
    q = 2 + pick("q", 3)
    stock = 6 + pick("stock", 8)
    limit = 20 + pick("limit", 5)  # above every quantity the other checks use
    accepted = min(3, stock // q)
    cv = {"stock": stock, "quantity": q, "limit": limit}
    intro = [f"Stock is {stock}. THREE buyers run YOUR repaired buy.sh at the same time. Each wants {q} units."]
    qs = [question("accepted", "How many purchases are accepted?", "int", [accepted]),
          question("stock", "What is in stock.txt at the end?", "int", [stock - accepted * q]),
          question("sold", "How many units does sales.log show in total?", "int", [accepted * q]),
          question("why", "One sentence: which line of your script makes a later buyer see the earlier buyer's update?", "text")]
    after = [f"Now change your store/buy.sh: one purchase may be at most {limit} units.",
             f"A larger quantity must print a message, exit with status 4 and change nothing. Quantity {limit} is still allowed.",
             "Then run: oslab check lab8"]
    return cv, intro, qs, after


VALUES = {"lab1": lab1_values, "lab2": lab2_values, "lab3": lab3_values, "lab4": lab4_values, "lab5": lab5_values, "lab6": lab6_values, "lab7": lab7_values, "lab9": lab9_values, "lab10": lab10_values, "lab8": lab8_values}
PREDICT = {"lab1": lab1_predict, "lab2": lab2_predict, "lab3": lab3_predict, "lab4": lab4_predict, "lab5": lab5_predict, "lab6": lab6_predict, "lab7": lab7_predict, "lab9": lab9_predict, "lab10": lab10_predict, "lab8": lab8_predict}
CHECKPOINT = {"lab1": lab1_checkpoint, "lab2": lab2_checkpoint, "lab3": lab3_checkpoint, "lab4": lab4_checkpoint,
              "lab5": lab5_checkpoint, "lab6": lab6_checkpoint, "lab7": lab7_checkpoint, "lab9": lab9_checkpoint, "lab10": lab10_checkpoint, "lab8": lab8_checkpoint}


def lab_values(lab, user):
    return VALUES[lab](picker(user, lab)) if lab in VALUES else {}


def checkpoint_task(lab, user, nonce):
    return CHECKPOINT[lab](picker(user, lab, nonce), lab_values(lab, user))


def mark(kind, expect, answer):
    """True/False for a marked answer, None when a person must read it."""
    if expect is None:
        return None
    if kind == "int":
        return bool(re.match(r"^-?\d{1,6}$", str(answer))) and int(answer) in expect
    if kind == "yesno":
        return str(answer).lower()[:1] == expect
    if kind == "word":
        return str(answer).strip().lower() == str(expect).strip().lower()
    if kind == "path":
        text = (shell_words(str(answer), {}, split=False) or [""])[0]
        return bool(text) and not text.startswith("/") and posixpath.normpath(posixpath.join(expect[0], text)) == expect[1]
    if kind == "dir":
        text = (shell_words(str(answer), {}, split=False) or [""])[0].strip()
        return bool(text) and posixpath.normpath(text) == expect
    return None


# Arrow and function keys send ESC sequences; without readline they would end up in the answer as "[D".
ESCAPES = re.compile(r"\x1b(\[[0-?]*[ -/]*[@-~]|O.|.)?")
VARIABLE = re.compile(r"\$(\{(\w+)\}|(\w+))")
PROMPTS = {"int": "number", "yesno": "yes/no", "path": "path", "dir": "folder", "word": "word", "text": "sentence"}


def clean(raw):
    return "".join(ch for ch in ESCAPES.sub("", raw) if ch.isprintable()).strip()[:300]


def interactive():
    return sys.stdin.isatty() and sys.stdout.isatty()


def bold(text):
    return f"\033[1m{text}\033[0m" if sys.stdout.isatty() else text


def shell_words(text, env, split=True):
    """Read text the way bash would: quotes removed, $NAME and ${NAME} filled in from env outside single
    quotes, ~ at the start of a word replaced by HOME. A variable env does not know stays as typed.
    With split=False the whole text is one word, so an unquoted name with a space stays together."""
    text = text.strip()
    words, word, started, quote, i = [], "", False, None, 0
    while i < len(text):
        ch = text[i]
        if quote == "'":
            if ch == "'":
                quote = None
            else:
                word += ch
        elif ch == "$" and VARIABLE.match(text, i):
            found = VARIABLE.match(text, i)
            word += str(env.get(found.group(2) or found.group(3), found.group(0)))
            started, i = True, found.end()
            continue
        elif quote == '"':
            if ch == '"':
                quote = None
            else:
                word += ch
        elif ch == "\\" and i + 1 < len(text):
            i += 1
            word += text[i]
        elif ch in "'\"":
            quote = ch
        elif ch.isspace() and split:
            if started:
                words.append(word)
            word, started, i = "", False, i + 1
            continue
        elif ch == "~" and not started and text[i + 1:i + 2] in ("", "/", " "):
            word += str(env.get("HOME", "~"))
        else:
            word += ch
        started, i = True, i + 1
    if started:
        words.append(word)
    return words


def read_path(answer, env):
    """(path, problem) for a path answer, with the student's own variables filled in."""
    path = (shell_words(answer, env, split=False) or [""])[0]
    unknown = VARIABLE.search(path)
    if unknown:
        return path, f"oslab does not know the variable {unknown.group(0)}. Type the path itself."
    if path.startswith("/"):
        return path, "This is an absolute path: it starts at /. Type a relative path, from your current directory."
    return path, None


def ask(item, label="", env=None):
    kind = item["kind"]
    if sys.stdout.isatty():
        sys.stdout.write("\033[?25h")  # show the cursor, in case an earlier program hid it
    print(f"\n{bold(label + item['text'])}")
    while True:
        try:
            answer = clean(input(f"{PROMPTS[kind]} > "))
        except EOFError:
            fail("no answer was given; run the command again")
        if kind == "int" and re.match(r"^-?\d{1,6}$", answer):
            return answer
        if kind == "yesno" and answer.lower() in ("y", "n", "yes", "no"):
            return answer.lower()[:1]
        if kind in ("path", "dir") and answer:
            if env is None:
                return answer
            path, problem = read_path(answer, env)
            if kind == "dir" and path.startswith("/"):
                problem = "Type the folder's path from the lab folder, not from /."
            if not problem:
                if path != answer:
                    print(f"Read as: {path}")
                return path
            print(problem)
            continue
        if kind == "word" and answer and " " not in answer:
            return answer
        if kind == "text" and len(answer) >= 3:
            return answer
        print({"int": "Type a whole number.", "yesno": "Type yes or no.", "path": "Type a path.", "dir": "Type a folder path.",
               "word": "Type one word or number, without spaces.", "text": "Write a short sentence."}[kind])


def ask_all(items, env=None):
    """Ask every question, then, in a terminal, show the answers and let the student change any before saving."""
    answers = {}
    for number, item in enumerate(items, 1):
        answers[item["key"]] = ask(item, f"[{number}/{len(items)}] ", env)
    if not interactive():
        return answers
    while True:
        print(f"\n{bold('Your answers:')}")
        for number, item in enumerate(items, 1):
            question = item["text"].splitlines()[0]
            print(f"  {number}. {question[:70] + '...' if len(question) > 70 else question}\n     {answers[item['key']]}")
        try:
            choice = clean(input(f"Press Enter to save, or type a number (1-{len(items)}) to change that answer > "))
        except EOFError:
            fail("no answer was given; run the command again")
        if not choice:
            return answers
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            item = items[int(choice) - 1]
            answers[item["key"]] = ask(item, f"[{choice}/{len(items)}] ", env)
        else:
            print(f"Type a number from 1 to {len(items)}, or press Enter to save.")


def shell_env(base, values):
    """The variables a student may type in an answer or an evidence file."""
    return dict({k: str(v) for k, v in values.items()}, OSLAB_WORKSPACE=base.as_posix(), HOME=Path.home().as_posix())


def workspace():
    home = Path.home().resolve(strict=True)
    base = Path(os.environ.get("OSLAB_WORKSPACE", str(home / "oslab-work"))).expanduser()
    if ".." in base.parts or "." in base.parts:
        fail("workspace path must not contain dot components")
    if not base.is_absolute() or base == home or home not in base.parents:
        fail("workspace must be an absolute directory below your home")
    if base.exists() and (base.is_symlink() or not base.is_dir()):
        fail("workspace is not a real directory")
    for part in [base, *list(base.parents)[:-1]]:
        if part == home:
            break
        if part.exists() and part.is_symlink():
            fail("symlink in workspace path")
    return base


def safe_tree(path, root=None):
    if root is None:
        if path.is_symlink():
            fail(f"managed root is a symlink: {path}")
        root = path.resolve()
    if path.is_symlink():
        try:
            resolved = path.resolve(strict=False)
        except RuntimeError:
            fail(f"symbolic-link cycle: {path}")
        if resolved != root and root not in resolved.parents:
            fail(f"symbolic link escapes workspace: {path}")
        return  # inspect the link destination; never traverse it during cleanup
    if path.is_dir():
        if os.path.ismount(path):
            fail(f"unmount before managing this directory: {path}")
        try:
            children = list(path.iterdir())
        except PermissionError:
            return  # a folder the student made unreadable on purpose (Lab 6); nothing there can be followed
        for child in children:
            try:
                safe_tree(child, root)
            except PermissionError:
                continue  # inside a folder without search permission
    elif path.exists() and not path.is_file():
        fail(f"special file is not managed: {path}")


def marker(path, lab):
    file = path / MARKER
    if not file.is_file() or file.is_symlink():
        fail("missing managed marker; refusing to change files")
    data = json.loads(file.read_text(encoding="utf-8"))
    if data != {"tool": "oslab", "lab": lab, "version": 1}:
        fail("managed marker mismatch")


def ensure_base(base):
    if not base.exists():
        base.mkdir(mode=0o700)
    if base.is_symlink():
        fail("workspace symlink")


def inbox():
    path = Path(os.environ.get("OSLAB_INBOX", DEFAULT_INBOX))
    return path if path.is_dir() and not path.is_symlink() else None


def submit(lab, kind, data):
    """Drop one record for the instructor. Returns False when no inbox exists (local practice)."""
    box = inbox()
    user = current_user()
    payload = dict(data, v=1, lab=lab, kind=kind, user=user, epoch=int(time.time()),
                   time=time.strftime("%Y-%m-%d %H:%M:%S %z"))
    if box is None:
        return False
    name = f"{lab}.{kind}.{user}.{int(time.time())}-{secrets.token_hex(8)}.json"
    try:
        fd = os.open(str(box / name), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    except OSError:
        return False
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        os.fchmod(fd, 0o644)
        json.dump(payload, handle, sort_keys=True)
    return True


def record_path(base, lab, kind):
    folder = base / RECORDS
    if folder.is_symlink():
        fail("records folder is a symlink")
    folder.mkdir(mode=0o700, exist_ok=True)
    return folder / f"{lab}-{kind}.json"


def read_record(base, lab, kind):
    path = base / RECORDS / f"{lab}-{kind}.json"
    if not path.is_file() or path.is_symlink():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_record(base, lab, kind, data):
    path = record_path(base, lab, kind)
    path.write_text(json.dumps(data, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    sent = submit(lab, kind, data)
    print("Saved and sent to the instructor." if sent else "Saved in your workspace only (no class inbox here: practice mode).")


def show_values(lab):
    values = lab_values(lab, current_user())
    if not values:
        print(f"{lab}: no personal values; everyone uses the values in the instruction")
        return
    print(f"Your personal values for {lab} ({current_user()}):")
    for key, value in values.items():
        if not key.startswith("_"):  # keys that start with _ build your files; they are not for you to read
            print(f"  {key:8} = {value}")


# Fixture files whose content changed when a lab got personal values. A workspace started before the change
# still holds the old content; `oslab start` replaces such a file only while it is exactly the old content.
LEGACY_FIXTURES = {
    "lab3": {"links/source.txt": "version 1\n", "links/target-name.txt": "A symlink target for diagnosis.\n"},
    "lab4": {"data/events.csv": "status,count\nok,3\nfail,2\nok,5\n", "data/expected.txt": "ok total: 8\n"},
    "lab7": {"input/one file.txt": "alpha beta\n", "input/-dash.txt": "gamma\n"},
    "lab9": {"vault/alpha.txt": "alpha\n", "vault/beta.txt": "beta\n", "vault/worker.sh": LAB9_OLD_WORKER},
    "lab10": {"backup.sh": LAB10_OLD_SCRIPT},
}
# Fixture files that workspaces started before the change do not have at all (names, or a function of the new files).
NEW_FIXTURES = {"lab3": lambda files: [name for name in files if name.startswith("notes/")],
                "lab5": lambda files: ("threads/two_workers.c",),
                "lab7": lambda files: [name for name in files if name.startswith("input/")],
                "lab9": lambda files: [name for name in files if name.startswith("vault/")]}


def refresh_fixtures(target, lab):
    """Bring an older workspace up to date without touching anything the student changed."""
    files = FIXTURES[lab]
    if callable(files):
        files = files(lab_values(lab, current_user()))
    for name, old in LEGACY_FIXTURES.get(lab, {}).items():
        dest = target / name
        if not (dest.is_file() and not dest.is_symlink() and read_text(dest) == old):
            continue  # missing, or the student changed it: leave it alone
        if name not in files:
            dest.unlink()
            print(f"{lab}: {name} was an old shared file and is removed; your own files are added")
        elif files[name] != old:
            dest.write_text(files[name], encoding="utf-8")
            print(f"{lab}: {name} was the old shared file; it is now your own version")
    links = target / "links"
    if lab == "lab3" and links.is_dir() and not any(links.iterdir()):  # the old unchanged report was just removed
        for name in files:
            if name.startswith("links/"):
                (target / name).write_text(files[name], encoding="utf-8")
                print(f"{lab}: added {name}")
    for name in NEW_FIXTURES.get(lab, lambda files: ())(files):
        dest = target / name
        if not dest.exists() and not dest.is_symlink():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(files[name], encoding="utf-8")
            print(f"{lab}: added {name}")


def start(base, lab):
    ensure_base(base)
    target = base / lab
    if target.exists():
        safe_tree(target)
        marker(target, lab)
        refresh_fixtures(target, lab)
        print(f"{lab}: existing work preserved at {target}")
        submit(lab, "start", {})
        return
    target.mkdir(mode=0o700)
    (target / MARKER).write_text(json.dumps({"tool": "oslab", "lab": lab, "version": 1}) + "\n", encoding="utf-8")
    files = FIXTURES[lab]
    if callable(files):
        files = files(lab_values(lab, current_user()))
    for name, value in files.items():
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(value, encoding="utf-8")
    print(f"{lab}: ready at {target}")
    submit(lab, "start", {})


def archive(base, lab):
    target = base / lab
    safe_tree(target)
    marker(target, lab)
    size = sum(p.lstat().st_size for p in target.rglob("*") if p.is_file() or p.is_symlink())
    if size > MAX_BYTES:
        fail("work exceeds 2 MB archive limit; save it yourself before reset")
    parent = base / ".attempts"
    if parent.exists() and parent.is_symlink():
        fail("attempt archive symlink")
    parent.mkdir(mode=0o700, exist_ok=True)
    attempts = sorted(parent.glob(f"{lab}-*"))
    if len(attempts) >= MAX_ARCHIVES:
        fail("three saved attempts already exist; remove an old attempt manually")
    dest = parent / f"{lab}-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
    shutil.move(str(target), str(dest))
    print(f"saved previous attempt: {dest}")


def prelab(base, lab):
    if lab not in PRELAB:
        print(f"{lab}: no pre-lab questions; read the instruction before class")
        return
    print(f"Pre-lab for {lab}: {len(PRELAB[lab])} questions. Wrong answers cost nothing; read the explanation.")
    first_try = 0
    for number, (text, options, correct, why) in enumerate(PRELAB[lab], 1):
        print(f"\n{number}. {text}")
        for letter, option in zip("abc", options):
            print(f"   {letter}) {option}")
        tries = 0
        while True:
            try:
                answer = clean(input("> ")).lower()[:1]
            except EOFError:
                fail("no answer was given; run the command again")
            tries += 1
            if answer == correct:
                break
            print("Not this one. Try again.")
        first_try += tries == 1
        print(f"   Correct. {why}")
    ensure_base(base)
    save_record(base, lab, "prelab", {"first_try": first_try, "questions": len(PRELAB[lab])})


def predict(base, lab):
    if lab not in PREDICT:
        fail(f"{lab} collects its prediction on paper; see the instruction")
    ensure_base(base)
    if read_record(base, lab, "predict"):
        fail("your prediction is already saved; the first answer is the one that counts")
    values = lab_values(lab, current_user())
    print("Prediction: answer BEFORE you run the experiment. No AI, no neighbour.")
    print("A wrong prediction costs nothing. You will compare it with the real result later.")
    answers = ask_all(PREDICT[lab](values), shell_env(base, values))
    save_record(base, lab, "predict", {"values": values, "answers": answers})


def debrief(base, lab):
    """After the lab: give the right answer to each marked prediction question. The prediction stays as it
    was; comparing the two shows which answers were confirmed and which corrected."""
    if lab not in PREDICT:
        fail(f"{lab} has no prediction to debrief")
    ensure_base(base)
    first = read_record(base, lab, "predict")
    if not first:
        fail(f"save your prediction first: oslab predict {lab}")
    values = lab_values(lab, current_user())
    print("Debrief: now that you have done the lab, give the right answer to each prediction question.")
    print("If your prediction was right, type it again. Your prediction itself stays saved as it was.")
    items = [dict(item, text=f"{item['text']}\n(Your prediction was: {first['answers'].get(item['key'], '')})")
             for item in PREDICT[lab](values) if item["expect"] is not None]
    answers = ask_all(items, shell_env(base, values))
    save_record(base, lab, "debrief", {"values": values, "answers": answers})


def release_nonce(lab):
    folder = Path(os.environ.get("OSLAB_RELEASE_DIR", DEFAULT_RELEASE))
    if not folder.is_dir():
        return "practice", True
    path = folder / f"{lab}.checkpoint"
    if not path.is_file() or path.is_symlink():
        fail("the checkpoint is not open yet; wait for the instructor")
    nonce = path.read_text(encoding="utf-8").strip()
    if not TOKEN.match(nonce):
        fail("the checkpoint release file is damaged; tell the instructor")
    return nonce, False


def checkpoint(base, lab):
    if lab not in CHECKPOINT:
        fail(f"{lab} collects its checkpoint on paper; see the instruction")
    ensure_base(base)
    nonce, practice = release_nonce(lab)
    earlier = read_record(base, lab, "checkpoint")
    if not practice and earlier and not earlier.get("practice"):
        fail("your checkpoint is already saved; the first answer is the one that counts")
    values, intro, items, after = checkpoint_task(lab, current_user(), nonce)
    print("Checkpoint: your own work. Close AI tools; do not ask a neighbour." + (" (practice values)" if practice else ""))
    print("\n" + "\n".join(intro))
    if interactive():
        print("Use the arrow keys and Backspace to correct an answer. You can review all answers before they are saved.")
    answers = ask_all(items, shell_env(base, lab_values(lab, current_user())))
    save_record(base, lab, "checkpoint", {"values": values, "answers": answers, "practice": practice})
    print("\n" + "\n".join(after))


def run_buy(script, arguments, delay="0"):
    env = dict(os.environ, BUY_DELAY=delay)
    return subprocess.Popen(["bash", str(script), *arguments], env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def finish(process):
    try:
        return process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return 124


def store_state(store):
    try:
        stock = int((store / "stock.txt").read_text().strip())
    except (OSError, ValueError):
        stock = None
    try:
        lines = (store / "sales.log").read_text().splitlines()
    except OSError:
        lines = []
    sold = sum(int(line.split()[1]) for line in lines if re.match(r"^sold \d+$", line))
    return stock, sold


def reset_store(store, stock):
    (store / "stock.txt").write_text(f"{stock}\n")
    (store / "sales.log").write_text("")


def check_lab8(target, values, extra):
    source = target / "store/buy.sh"
    if not source.is_file() or source.is_symlink():
        return [("store/buy.sh exists", ["store/buy.sh does not exist or is a link: run `oslab reset lab8` to get it back"])]
    stock, a, b = values["stock"], values["buyer_a"], values["buyer_b"]
    results = []
    sandbox = Path(tempfile.mkdtemp(prefix=".check-", dir=str(target)))

    def state(expected_left, expected_sold):
        left, sold = store_state(sandbox)
        problems = []
        if left != expected_left:
            problems.append(f"stock.txt holds {'no number' if left is None else left}, expected {expected_left}")
        if sold != expected_sold:
            problems.append(f"sales.log shows {sold} sold, expected {expected_sold}")
        return problems
    try:
        script = sandbox / "buy.sh"
        shutil.copyfile(str(source), str(script))
        reset_store(sandbox, stock)
        code = finish(run_buy(script, ["2"]))
        problems = ([f"`buy.sh 2` with stock {stock} ended with exit status {code}, expected 0"] if code else []) + state(stock - 2, 2)
        results.append(("one buyer of 2 is accepted and recorded", problems))
        reset_store(sandbox, stock)
        bad_inputs = (["0"], ["abc"], [], [str(stock + 1)])
        codes = [finish(run_buy(script, bad)) for bad in bad_inputs]
        problems = [f"`buy.sh {' '.join(bad)}` was accepted (exit status 0)" for bad, code in zip(bad_inputs, codes) if code == 0]
        results.append(("bad or too large quantities change nothing", problems + state(stock, 0)))
        reset_store(sandbox, stock)
        buyers = [run_buy(script, [str(a)], "1"), run_buy(script, [str(b)], "1")]
        accepted = [finish(buyer) for buyer in buyers].count(0)
        left, sold = store_state(sandbox)
        problems = [f"{accepted} purchases were accepted, expected 1"] if accepted != 1 else []
        if left is None or left + sold != stock or sold not in (a, b):
            problems.append(f"sold {sold} + left {'?' if left is None else left} should be {stock} with one buyer's units sold: "
                            "the second buyer still read the stock before the first one wrote it")
        results.append((f"two buyers at once ({a} and {b} of {stock}): sold + left = {stock}", problems))
        if extra:
            limit = extra["limit"]
            reset_store(sandbox, limit + 5)
            over = finish(run_buy(script, [str(limit + 1)]))
            problems = [f"`buy.sh {limit + 1}` ended with exit status {over}, expected 4"] if over != 4 else []
            problems += [f"after `buy.sh {limit + 1}`: {p}" for p in state(limit + 5, 0)]
            exact = finish(run_buy(script, [str(limit)]))
            if exact != 0:
                problems.append(f"`buy.sh {limit}` ended with exit status {exact}, expected 0: {limit} units are still allowed")
            elif not problems:
                problems += [f"after `buy.sh {limit}`: {p}" for p in state(5, limit)]
            results.append((f"checkpoint: more than {limit} units exits 4 and changes nothing; {limit} is allowed", problems))
    finally:
        shutil.rmtree(str(sandbox), ignore_errors=True)
    if PAY_DELAY.split("#")[0].strip() not in source.read_text(encoding="utf-8", errors="replace"):
        print('NOTE: keep the line  sleep "${BUY_DELAY:-0}"  so the two-buyer test can slow the payment down.')
    return results


def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    except OSError:
        return ""


def sleep_rows(text):
    """Lines of `ps` output whose command is sleep."""
    return re.findall(r"^\s*\d+\s+\S+\s+\S+\s+sleep\s*$", text, re.M)


def missing(target, name):
    """A problem line when lab file `name` does not exist, else None."""
    return None if (target / name).is_file() else f"{name} does not exist (run `ls` in the lab folder)"


def found(text):
    """How a file's content is shown in a problem line."""
    text = text.strip()
    return "it is empty" if not text else f"it holds: {text[:60] + '...' if len(text) > 60 else text}"


def check_lab1(target, values, extra):
    """Each result is (milestone, problems): the milestone passes when the list of problems is empty."""
    info = read_text(target / "task1_os_info.txt")
    problems = [p for p in [missing(target, "task1_os_info.txt")] if p] or [
        p for p, bad in (("no kernel line: the word Linux is not in the file", "Linux" not in info),
                         ("no distribution description: Distributor ID or Ubuntu is not in the file",
                          "Distributor ID" not in info and "Ubuntu" not in info)) if bad]
    results = [("task1_os_info.txt has the kernel line and the distribution description", problems)]
    folder = target / "task2_files"
    first, second = values["file1"], values["file2"]
    problems = []
    if not folder.is_dir():
        problems.append("the folder task2_files does not exist")
    else:
        if not (folder / f"{first}.txt").is_file():
            problems.append(f"task2_files/{first}.txt does not exist")
        elif read_text(folder / f"{first}.txt") != f"This is file {first}\n":
            problems.append(f"task2_files/{first}.txt must hold the line: This is file {first}; {found(read_text(folder / f'{first}.txt'))}")
        if not (folder / f"{second}_renamed.txt").is_file():
            problems.append(f"task2_files/{second}_renamed.txt does not exist")
        for name, step in ((f"{first}_copy.txt", "delete it"), (f"{second}.txt", "rename it")):
            if (folder / name).exists():
                problems.append(f"task2_files/{name} is still there: {step}")
    commands = read_text(target / "task2_file_commands.txt")
    if not commands:
        problems.append("task2_file_commands.txt does not exist or is empty")
    elif folder.name not in commands:
        problems.append("task2_file_commands.txt does not name the folder task2_files")
    results.append((f"task2_files holds {first}.txt and {second}_renamed.txt (no copy left), and task2_file_commands.txt names the folder", problems))
    count = values["count"]
    one = len(sleep_rows(read_text(target / "task4_process_list.txt")))
    many = len(sleep_rows(read_text(target / "task5_multitasking.txt")))
    problems = [p for p in (missing(target, "task4_process_list.txt"), missing(target, "task5_multitasking.txt")) if p]
    if not problems and one < 1:
        problems.append("task4_process_list.txt has no line of `ps` output for sleep")
    if not problems and many < count:
        problems.append(f"task5_multitasking.txt shows {many} sleep line(s); start {count} copies in the background, "
                        "then run `ps` while they all still run")
    results.append((f"task4_process_list.txt shows a sleep process and task5_multitasking.txt shows {count} at the same time", problems))
    virt = [line for line in read_text(target / "task6_virtualization_check.txt").splitlines() if line.strip()]
    problems = [p for p in [missing(target, "task6_virtualization_check.txt")] if p] or (
        [f"the file has {len(virt)} line(s) with text; it needs 3: the detection result, the kernel release and the host name"] if len(virt) < 3 else [])
    results.append(("task6_virtualization_check.txt has the detection result, kernel release and host name", problems))
    if extra:
        box = target / extra["folder"]
        text = f"{extra['text']}\n"
        listing = read_text(target / "checkpoint.txt")
        problems = []
        if not box.is_dir():
            problems.append(f"the folder {extra['folder']} does not exist in the lab1 folder")
        else:
            for name in (extra["old"], extra["copy"]):
                if not (box / name).is_file():
                    problems.append(f"{extra['folder']}/{name} does not exist")
                elif read_text(box / name) != text:
                    problems.append(f"{extra['folder']}/{name} must hold the line: {extra['text']}; {found(read_text(box / name))}")
            if (box / extra["note"]).exists():
                problems.append(f"{extra['folder']}/{extra['note']} is still there: rename it to {extra['old']}")
        if not listing:
            problems.append("checkpoint.txt does not exist or is empty: save the list of files there (step 5)")
        elif extra["old"] not in listing or extra["copy"] not in listing:
            problems.append(f"checkpoint.txt does not list both {extra['old']} and {extra['copy']}")
        results.append(("checkpoint: the folder holds the renamed file and the copy with the right text, and the listing is saved", problems))
    return results


def same_bytes(first, second):
    try:
        return first.is_file() and second.is_file() and first.read_bytes() == second.read_bytes()
    except OSError:
        return False


def lab2_error_fix(target, values):
    """Core 3, step 2: an Error: line with a real "No such file or directory", and a Fix: line holding a
    relative path that reaches one of the two reports from the reader department. The path is read as bash
    would read it, so "$file1", quotes and backslashes work. Returns (error, fix, problems)."""
    error = fix = False
    errors, fixes = [], []
    reader = f"TechCorp/{values['reader']}"
    start = (target / reader).as_posix()
    reports = {(target / "reports" / values[n]).as_posix() for n in ("file1", "file2")}
    env = shell_env(target.parent, values)
    for line in read_text(target / "evidence/paths.txt").splitlines():
        head, _, rest = line.partition(":")
        head, rest = head.strip().lower(), rest.strip()
        if head == "error":
            errors.append(rest)
            error = error or "no such file or directory" in rest.lower()
        if head == "fix":
            if rest.lower().startswith("cat "):
                rest = rest[4:].strip()
            if rest.startswith("-- "):
                rest = rest[3:]
            path, problem = read_path(rest, env)
            if not rest:
                problem = "the Fix: line has no path after it"
            elif problem:
                problem = f"Fix: {rest} -> {problem}"
            elif posixpath.normpath(posixpath.join(start, path)) in reports:
                fix = True
            else:
                reached = posixpath.relpath(posixpath.normpath(posixpath.join(start, path)), target.as_posix())
                problem = (f"Fix: {rest} -> from {reader} this path leads to {reached}, not to reports/<your file>. "
                           f"Count the folders you must go up from {reader} to reach the lab folder")
            fixes.append(problem)
    problems = []
    if not errors:
        problems.append("no line starts with Error: (Core 3, step 2)")
    elif not error:
        problems.append("the Error: line must hold the message that cat printed, with: No such file or directory")
    if not fixes:
        problems.append("no line starts with Fix: (Core 3, step 2)")
    elif not fix:
        problems.append(fixes[-1])
    return error, fix, problems


def lab2_path_error(target, values):
    error, fix, _ = lab2_error_fix(target, values)
    return {"error": error, "fix": fix}


def lab2_path_kinds(target, values):
    """Problems with milestone 4: paths.txt needs a relative path that goes up with .. and an absolute path.
    "$OSLAB_WORKSPACE/lab2/..." and ~/... count as absolute, because bash makes them start with /."""
    text = read_text(target / "evidence/paths.txt")
    if not text.strip():
        return ["evidence/paths.txt does not exist or is empty: write the commands that worked into it (Core 2)"]
    env = shell_env(target.parent, values)
    words = [word for line in text.splitlines() for word in shell_words(line, env)]
    relative = "../" in text or any(not w.startswith("/") and ".." in w.split("/") for w in words)
    absolute = re.search(r"(^|[\s'\"])/", text) is not None or any(w.startswith("/") for w in words)
    problems = []
    if not relative:
        problems.append("no relative path that goes up with .. was found, such as ../reports/ (Core 2, step 1)")
    if not absolute:
        problems.append('no absolute path was found: one that starts with / or with "$OSLAB_WORKSPACE/lab2/" (Core 2, step 2)')
    return problems


def check_lab2(target, values, extra):
    """Each result is (milestone, problems): the milestone passes when the list of problems is empty."""
    names = (values["file1"], values["file2"])
    wanted = (f"amount,{values['amount1']}\n", f"amount,{values['amount2']}\n")
    owner = f"TechCorp/{values['owner']}"
    moved, copies = [], []
    for name, content in zip(names, wanted):
        report = target / "reports" / name
        if (target / "incoming" / name).exists():
            moved.append(f"incoming/{name} is still there: move it with mv, do not copy it")
        if not report.is_file():
            moved.append(f"reports/{name} does not exist")
            copies.append(f"reports/{name} does not exist, so there is nothing to compare with")
        elif read_text(report) != content:
            moved.append(f"reports/{name} must hold {content.strip()}; {found(read_text(report))}")
        if report.is_file() and not (target / owner / name).is_file():
            copies.append(f"{owner}/{name} does not exist")
        elif report.is_file() and not same_bytes(report, target / owner / name):
            copies.append(f"{owner}/{name} is not the same as reports/{name}: copy it again")
    archive = target / owner / "archive/first-original.txt"
    if not archive.is_file():
        archived = [f"{owner}/archive/first-original.txt does not exist"]
    elif read_text(archive) != wanted[0]:
        archived = [f"it must be a copy of your first file, {names[0]} ({wanted[0].strip()}); {found(read_text(archive))}"]
    else:
        archived = []
    results = [("both files were moved into reports/ with their contents", moved),
               (f"{owner}/ holds identical copies", copies),
               ("archive/first-original.txt is a copy of your first file", archived),
               ("evidence/paths.txt records a relative and an absolute path", lab2_path_kinds(target, values)),
               ("evidence/paths.txt has your Error: line and a Fix: path that works from your reader department",
                lab2_error_fix(target, values)[2])]
    if extra:
        saved = target / "evidence/checkpoint.txt"
        if not saved.is_file():
            problems = ["evidence/checkpoint.txt does not exist: run the cat ... | tee line that oslab checkpoint printed"]
        elif not read_text(saved).strip():
            problems = [f"evidence/checkpoint.txt is empty: cat did not find the file, so the path does not lead from "
                        f"{extra['cwd']} to {extra['target']}. Read the error cat printed"]
        elif extra["content"] not in read_text(saved):
            problems = [f"evidence/checkpoint.txt does not hold {extra['content']}, so the file you read is not {extra['target']}; "
                        f"{found(read_text(saved))}"]
        else:
            problems = []
        results.append(("checkpoint: evidence/checkpoint.txt holds the content of the target file", problems))
    return results


def lab3_sections(text):
    """evidence/links.txt: the lines under each `=== LABEL ===` header, as {first words of the label: lines}."""
    sections, current = {}, None
    for line in text.splitlines():
        header = re.match(r"^\s*=+\s*(.*?)\s*=+\s*$", line)
        if header:
            label = header.group(1).upper()
            current = next((key for key in ("BEFORE RENAME", "AFTER RENAME", "AFTER REPAIR") if label.startswith(key)), None)
            if current:
                sections.setdefault(current, [])
        elif current:
            sections[current].append(line)
    return sections


def lab3_evidence(target, values):
    """Core 3: evidence/links.txt records the failure after the rename and the repaired link, with your own values.
    Returns (failure, repair, problems)."""
    name, tag, v1 = values["name"], values["tag"], values["v1"]
    path = "evidence/links.txt"
    if not read_text(target / path).strip():
        return False, False, [f"{path} does not exist or is empty: save the labelled states with the tee commands (Core 2 and Core 3)"]
    sections = lab3_sections(read_text(target / path))
    problems = []
    for key, step in (("BEFORE RENAME", "Core 2, step 1"), ("AFTER RENAME", "Core 2, step 2"), ("AFTER REPAIR", "Core 3, step 2")):
        if key not in sections:
            problems.append(f"{path} has no `=== {key} ... ===` section ({step})")
    failure = repair = False
    after = "\n".join(sections.get("AFTER RENAME", []))
    if "AFTER RENAME" in sections:
        if "no such file or directory" not in after.lower():
            problems.append("the AFTER RENAME section must hold the error that cat printed: No such file or directory (Core 2, step 2)")
        elif not re.search(rf"^\s*stored target:\s*{re.escape(name)}\.txt\s*$", after, re.M):
            problems.append(f"the AFTER RENAME section must show `stored target: {name}.txt`, the old name that is now missing")
        else:
            failure = True
    fixed = "\n".join(sections.get("AFTER REPAIR", []))
    if "AFTER REPAIR" in sections:
        stored = re.search(r"^\s*stored target:\s*(\S+)\s*$", fixed, re.M)
        if not stored:
            problems.append("the AFTER REPAIR section has no `stored target:` line (Core 3, step 2)")
        elif posixpath.normpath(posixpath.join("links", stored.group(1))) != f"links/{name}-{tag}.txt":
            problems.append(f"the AFTER REPAIR section shows the target {stored.group(1)}, which does not lead to {name}-{tag}.txt from links/")
        elif f"version {v1}" not in fixed:
            problems.append(f"the AFTER REPAIR section must show the link reading version {v1}")
        else:
            repair = True
    return failure, repair, problems


def lab3_path_error(target, values):
    failure, repair, _ = lab3_evidence(target, values)
    return {"error": failure, "fix": repair}


def check_lab3(target, values, extra=None):
    """Check real file identity and stored targets on the files, not a transcript. Each result is (milestone, problems)."""
    name, tag, v1, v2 = values["name"], values["tag"], values["v1"], values["v2"]
    links = target / "links"
    original, hard, renamed, soft = links / f"{name}.txt", links / f"{name}-hard.txt", links / f"{name}-{tag}.txt", links / f"{name}-soft.txt"
    results = []
    # 1. wildcards: three blocks of printf output, in the order of the instruction (the order inside a block is not checked)
    notes = sorted(p for p in lab3_notes(values))
    visible = sorted(f"<{p}>" for p in notes if p.endswith(".txt") and not Path(p).name.startswith("."))
    one = sorted(f"<notes/{name}{d}.txt>" for d in "12")
    lines = [line for line in read_text(target / "evidence/wildcards.txt").splitlines() if line.strip()]
    problems = []
    if not lines:
        problems.append("evidence/wildcards.txt does not exist or is empty: save the three printf commands with tee (Core 1)")
    else:
        parts = (("notes/*.txt", visible, lines[:3]), (f"notes/{name}?.txt", one, lines[3:5]), ("'notes/*.txt'", ["<notes/*.txt>"], lines[5:]))
        for label, wanted, got in parts:
            if sorted(got) != wanted:
                problems.append(f"the lines for {label} must be {', '.join(wanted)}; {found(chr(10).join(got))}")
        if len(lines) != 6:
            problems.append(f"the file must hold 6 lines (3, 2 and 1 from the three commands); it holds {len(lines)}")
    results.append(("wildcards: evidence/wildcards.txt holds your three expansions", problems[:3]))
    # 2. hard link
    problems = []
    if not hard.is_file() or hard.is_symlink():
        problems.append(f"links/{name}-hard.txt does not exist or is not a hard link: ln {name}.txt {name}-hard.txt, before the rename")
    elif not renamed.is_file() or renamed.is_symlink():
        problems.append(f"links/{name}-{tag}.txt does not exist: rename the original with mv")
    elif not os.path.samefile(hard, renamed):
        problems.append(f"{name}-hard.txt and {name}-{tag}.txt are not the same file (a copy, or a hard link made after the rename): compare ls -li")
    elif read_text(hard) != f"version {v1}\n":
        problems.append(f"the hard-linked file must still hold version {v1}; {found(read_text(hard))}")
    results.append((f"hard link: {name}-hard.txt and {name}-{tag}.txt are the same file (version {v1})", problems))
    # 3. repaired symbolic link
    problems = []
    if not soft.is_symlink():
        problems.append(f"links/{name}-soft.txt is not a symbolic link: repair it with rm -- then ln -s")
    else:
        stored = os.readlink(soft)
        if stored.startswith("/"):
            problems.append(f"the stored target {stored} is an absolute path; store a relative one, read from the folder that holds the link")
        elif not renamed.is_file():
            problems.append(f"links/{name}-{tag}.txt does not exist")
        elif not os.path.exists(soft):
            problems.append(f"the link stores {stored}, and no file has that name here: it is still dangling")
        elif not os.path.samefile(soft, renamed):
            if original.is_file() and os.path.samefile(soft, original):
                problems.append(f"the link stores {stored}: it reads the NEW file, not your renamed original. Point it at {name}-{tag}.txt")
            else:
                problems.append(f"the link stores {stored}, which does not lead to {name}-{tag}.txt")
    results.append((f"symbolic link: {name}-soft.txt stores a relative target that reaches {name}-{tag}.txt", problems))
    # 4. the new file with the old name
    problems = []
    if not original.is_file() or original.is_symlink():
        problems.append(f"links/{name}.txt does not exist: create a NEW file under the old name (Core 2, step 3)")
    elif read_text(original) != f"version {v2}\n":
        problems.append(f"the new {name}.txt must hold version {v2}; {found(read_text(original))}")
    elif hard.is_file() and os.path.samefile(original, hard):
        problems.append(f"{name}.txt is the same file as {name}-hard.txt: create it with printf and >, after the rename")
    replacement = read_text(target / "evidence/replacement.txt")
    if not problems and (f"version {v1}" not in replacement or f"version {v2}" not in replacement):
        problems.append(f"evidence/replacement.txt must show both versions, {v1} and {v2}: save the Core 2, step 3 listing")
    results.append((f"new file: {name}.txt holds version {v2} and is separate from the version {v1} file", problems))
    # 5. the evidence of failure and repair
    results.append(("evidence/links.txt records the failure after the rename and the repaired link", lab3_evidence(target, values)[2]))
    if extra:
        box = target / extra["folder"]
        data, moved = box / extra["data"], box / extra["moved"]
        first, second, hard_link = box / "links/first.txt", box / "links/second.txt", box / "links/hard.txt"
        problems = []
        if data.exists() or data.is_symlink():
            problems.append(f"{extra['folder']}/{extra['data']} is still there: the data file was renamed to {extra['moved']}")
        elif not moved.is_file() or moved.is_symlink() or read_text(moved) != extra["content"] + "\n":
            problems.append(f"{extra['folder']}/{extra['moved']} must hold {extra['content']}: follow the commands printed by oslab checkpoint lab3")
        elif not (hard_link.is_file() and not hard_link.is_symlink() and os.path.samefile(hard_link, moved)):
            problems.append("links/hard.txt must be a hard link made before the rename (ls -li shows the same inode as the data file)")
        elif not first.is_symlink() or os.readlink(first).startswith("/") or first.resolve() != moved.resolve():
            problems.append(f"links/first.txt must store a relative target that reaches {extra['moved']}: it stores {os.readlink(first) if first.is_symlink() else 'nothing (not a link)'}")
        elif not second.is_symlink() or os.readlink(second) != "first.txt":
            problems.append("links/second.txt must still be a symbolic link that stores first.txt: repair only first.txt")
        elif read_text(target / "evidence/checkpoint.txt").count(extra["content"]) < 2:
            problems.append("evidence/checkpoint.txt must show the data read through hard.txt and through second.txt: use the tee line that oslab checkpoint printed")
        results.append(("checkpoint: first.txt is repaired, second.txt follows it, hard.txt still reads, and the output is saved", problems))
    return results


def run_report(script, arguments, cwd):
    """Run the student's own script on a small input, with a time limit. Returns (status, stdout, stderr)."""
    try:
        done = subprocess.run(["bash", str(script), *arguments], cwd=str(cwd), stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    except subprocess.TimeoutExpired:
        return 124, "", "the script ran for more than 10 seconds"
    except OSError as exc:
        return 127, "", str(exc)
    return done.returncode, done.stdout.decode("utf-8", "replace"), done.stderr.decode("utf-8", "replace")


def check_lab4(target, values, extra):
    if read_text(target / "data/events.csv") == LEGACY_FIXTURES["lab4"]["data/events.csv"]:
        print("NOTE: data/events.csv is the old shared file from before the update. Run `oslab start lab4` to get your own, "
              "then use your status word (oslab values lab4) in report.sh.")
    source = target / "report.sh"
    if not source.is_file() or source.is_symlink():
        problem = ["report.sh does not exist in the lab4 folder (or is a link): write it in Core 1"]
        status = values["status"]
        names = [f"report.sh prints `{status} total: TOTAL` for your own events.csv", f"no row has your status: it prints `{status} total: 0`",
                 f"extra records and a look-alike ({status}-late): the total is still right",
                 "a missing input: a message on standard error and a status other than 0"]
        if extra:
            names.append("checkpoint: report.sh is right on the new file and checkpoint.txt holds its output")
        return [(name, problem) for name in names]
    status, other = values["status"], values["other"]
    label = f"{status} total: "
    sandbox = Path(tempfile.mkdtemp(prefix=".check-", dir=str(target)))

    def trial(rows, name="in.csv"):
        (sandbox / name).write_text(lab4_csv(rows), encoding="utf-8")
        code, out, err = run_report(sandbox / "report.sh", [name], sandbox)
        total = lab4_total(rows, status)
        selected = [count for n, count in rows if n == status]
        if code:
            return [f"exit status {code}, expected 0" + (f"; message: {err.strip()[:100]}" if err.strip() else "")]
        if out == f"{label}{total}\n":
            return []
        if len(out.splitlines()) != 1:
            return [f"it must print exactly one line, `{label}{total}`; it printed {len(out.splitlines())} line(s): {out.strip()[:60]!r}"]
        problems = [f"expected `{label}{total}`, got `{out.strip()[:60]}`"]
        if out.strip() == f"{label}{len(selected)}":
            problems.append("that is the number of matching rows; add up field 2 instead")
        elif selected and out.strip() == f"{label}{selected[0]}":
            problems.append("that is only the first matching record; add up every one")
        elif out.strip() == f"{label}{total + sum(count for n, count in rows if n.startswith(status) and n != status)}":
            problems.append(f"a look-alike such as {status}-late was counted; the first field must be exactly `{status}`")
        return problems
    try:
        shutil.copyfile(str(source), str(sandbox / "report.sh"))
        results = [(f"report.sh prints `{label}TOTAL` for your own events.csv", trial(lab4_rows(values))),
                   (f"no row has your status: it prints `{label}0`", trial([(other, 5), (other, 2)])),
                   (f"extra records and a look-alike ({status}-late): the total is still right",
                    trial([(status, 7), (status + "-late", 50), (other, 9), (status, 8), ("not-" + status, 99)]))]
        (sandbox / "in.csv").unlink()
        code, out, err = run_report(sandbox / "report.sh", ["missing.csv"], sandbox)
        problems = []
        if code == 0:
            problems.append("a missing input file must end with a status other than 0")
        if out.strip():
            problems.append(f"the message must go to standard error (>&2), not to the screen output; stdout held {out.strip()[:50]!r}")
        if code != 0 and not err.strip():
            problems.append("print a message with echo ... >&2 so the user knows what went wrong")
        results.append(("a missing input: a message on standard error and a status other than 0", problems))
        if extra:
            rows = [tuple(r) for r in extra["rows"]]
            problems = trial(rows, extra["name"])
            expected = lab4_csv(rows)
            if read_text(target / "data" / extra["name"]) != expected:
                problems.append(f"data/{extra['name']} does not hold the records of the checkpoint: use the printf line printed by oslab checkpoint lab4")
            if read_text(target / "checkpoint.txt").strip() != f"{label}{extra['total']}":
                problems.append(f"checkpoint.txt must hold `{label}{extra['total']}`, the output of your report.sh on data/{extra['name']}")
            results.append(("checkpoint: report.sh is right on the new file and checkpoint.txt holds its output", problems))
    finally:
        shutil.rmtree(str(sandbox), ignore_errors=True)
    return results


CHECKS = {"lab1": check_lab1, "lab2": check_lab2, "lab3": check_lab3, "lab4": check_lab4, "lab5": check_lab5, "lab6": check_lab6, "lab7": check_lab7, "lab9": check_lab9, "lab10": check_lab10, "lab8": check_lab8}
# Details a check sends with its milestones, so the marking screen can give part of a row's points.
CHECK_DETAILS = {"lab3": lambda target, values: {"path_error": lab3_path_error(target, values)},
                 "lab2": lambda target, values: {"path_error": lab2_path_error(target, values)}}
EVIDENCE_BUDGET = 8000  # bytes of file entries per record; oslab_teach drops records over 16 KB
HASH_LIMIT = 5_000_000


def evidence_files(target):
    """Hash, size and time of the top-level files and everything under evidence/,
    so the instructor can compare the submitted copies with what was checked here.
    Returns (entries, skipped): entries stop at the byte budget; dotfiles and links are left out."""
    paths = [p for p in sorted(target.iterdir()) if not p.name.startswith(".")]
    folder = target / "evidence"
    if folder.is_dir() and not folder.is_symlink():
        for root, dirs, files in os.walk(folder):
            dirs[:] = sorted(d for d in dirs if not d.startswith("."))
            paths += [Path(root) / f for f in sorted(files) if not f.startswith(".")]
    entries, used, skipped = [], 0, 0
    for path in paths:
        if path.is_symlink() or not path.is_file():
            continue
        if used >= EVIDENCE_BUDGET:
            skipped += 1
            continue
        info = path.lstat()
        digest = None
        if info.st_size <= HASH_LIMIT:
            sha = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(65536), b""):
                    sha.update(block)
            digest = sha.hexdigest()
        entry = {"path": path.relative_to(target).as_posix(), "size": info.st_size,
                 "mtime": int(info.st_mtime), "sha256": digest}
        used += len(json.dumps(entry))
        entries.append(entry)
    return entries, skipped


def check(base, lab):
    target = base / lab
    safe_tree(target)
    marker(target, lab)
    files, skipped = evidence_files(target)
    evidence = {"files": files, "files_skipped": skipped}
    if lab in CHECKS:
        record = read_record(base, lab, "checkpoint")
        values = lab_values(lab, current_user())
        results = CHECKS[lab](target, values, record["values"] if record else None)
        for text, problems in results:
            print(f"{'TRY ' if problems else 'PASS'}: {text}")
            for problem in problems:
                print(f"      why: {problem}")
        failed = [(text, problems) for text, problems in results if problems]
        print(f"milestones: {len(results) - len(failed)}/{len(results)}")
        if lab in CHECK_DETAILS:
            evidence.update(CHECK_DETAILS[lab](target, values))
        submit(lab, "check", dict(evidence, passed=len(results) - len(failed), total=len(results),
                                  failed=[text for text, _ in failed],
                                  reasons={text: [p[:200] for p in problems[:4]] for text, problems in failed},
                                  checkpoint=not results[-1][1] if record else None))
        return
    if lab == "lab10":
        print("Inspect archive contents and retention manually; public checks cannot grade cron behaviour.")
    else:
        print("Fixture integrity OK. Submit your test evidence and explanation for human review.")
    submit(lab, "check", evidence)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor", "list", "start", "status", "values", "prelab", "predict",
                                            "hint", "check", "checkpoint", "debrief", "reset", "clean"])
    parser.add_argument("lab", nargs="?")
    parser.add_argument("level", nargs="?", type=int)
    args = parser.parse_args()
    base = workspace()
    if args.command == "doctor":
        print(f"user={os.getuid()} name={current_user()} workspace={base} python={sys.version.split()[0]}")
        print(f"class inbox: {'connected' if inbox() else 'not found (practice mode: answers stay in your workspace)'}")
        print("Required: Python 3.8+, Bash, coreutils; topic-specific tools are listed in each lab.")
        return
    if args.command == "list":
        print(" ".join(LABS))
        return
    if args.lab not in LABS:
        fail("choose lab1 through lab11")
    target = base / args.lab
    if args.command in ("start", "reset", "clean"):
        ensure_base(base)
        lock_path = base / ".oslab.lock"
        if lock_path.is_symlink():
            fail("workspace lock symlink")
        with lock_path.open("a+") as lock:
            until = time.monotonic() + 3
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= until:
                        fail("workspace busy; retry shortly")
                    time.sleep(0.05)
            if args.command == "start":
                start(base, args.lab)
            elif args.command == "reset":
                if target.exists():
                    archive(base, args.lab)
                start(base, args.lab)
            elif target.exists():
                safe_tree(target)
                marker(target, args.lab)
                shutil.rmtree(target)
                print(f"removed managed {args.lab} workspace; saved attempts untouched")
    elif args.command == "status":
        print(f"{args.lab}: {'ready' if target.exists() else 'not started'}")
        if target.exists():
            safe_tree(target)
            marker(target, args.lab)
        for kind in ("prelab", "predict", "checkpoint", "debrief"):
            print(f"  {kind}: {'saved' if read_record(base, args.lab, kind) else 'not yet'}")
    elif args.command == "values":
        show_values(args.lab)
    elif args.command == "prelab":
        prelab(base, args.lab)
    elif args.command == "predict":
        predict(base, args.lab)
    elif args.command == "checkpoint":
        checkpoint(base, args.lab)
    elif args.command == "debrief":
        debrief(base, args.lab)
    elif args.command == "hint":
        if args.level not in (1, 2, 3):
            fail("hint level must be 1, 2, or 3")
        print(HINTS.get(args.lab, GENERIC_HINTS)[args.level - 1])
        submit(args.lab, "hint", {"level": args.level})
    elif args.command == "check":
        check(base, args.lab)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"oslab: {exc}", file=sys.stderr)
        sys.exit(2)
