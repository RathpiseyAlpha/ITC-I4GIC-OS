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
    "lab3": {"links/source.txt": "version 1\n", "links/target-name.txt": "A symlink target for diagnosis.\n"},
    "lab4": {"data/events.csv": "status,count\nok,3\nfail,2\nok,5\n", "data/expected.txt": "ok total: 8\n"},
    "lab5": {"threads/trace.csv": "thread,step\nA,read\nB,read\nA,write\nB,write\n",
             "threads/starter.c": "#include <pthread.h>\n#include <stdio.h>\nstatic void *worker(void *arg) { puts((const char *)arg); return NULL; }\nint main(void) { pthread_t a, b;\n  if (pthread_create(&a, NULL, worker, \"A\") || pthread_create(&b, NULL, worker, \"B\")) return 1;\n  /* TODO: join both workers before reading results. */\n  return 0;\n}\n"},
    "lab6": {"private/record.txt": "student-owned record\n", "shared/notice.txt": "Read-only public notice\n"},
    "lab7": {"input/one file.txt": "alpha beta\n", "input/-dash.txt": "gamma\n",
             "count_words.sh": "#!/usr/bin/env bash\nset -u\n# TODO: loop over quoted arguments, reject missing files, and count words.\n"},
    "lab8": lambda v: {"store/stock.txt": f"{v['stock']}\n", "store/sales.log": "", "store/buy.sh": BUY_SH,
                       **{f"store/ai-answers/{name}.sh": text for name, text in AI_ANSWERS.items()}},
    "lab9": {"vault/alpha.txt": "alpha\n", "vault/beta.txt": "beta\n",
             "vault/worker.sh": "#!/usr/bin/env bash\nset -euo pipefail\n# TODO: acquire two owned lock files with flock -w 2; log each acquisition.\n"},
    "lab10": {"project/report.txt": "report v1\n", "project/config.ini": "mode=practice\n",
              "backup.sh": "#!/usr/bin/env bash\nset -euo pipefail\n# TODO: archive project with absolute paths, verify it, retain newest three owned archives.\n"},
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


VALUES = {"lab1": lab1_values, "lab2": lab2_values, "lab8": lab8_values}
PREDICT = {"lab1": lab1_predict, "lab2": lab2_predict, "lab8": lab8_predict}
CHECKPOINT = {"lab1": lab1_checkpoint, "lab2": lab2_checkpoint, "lab8": lab8_checkpoint}


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
        for child in path.iterdir():
            safe_tree(child, root)
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
        print(f"  {key:8} = {value}")


def start(base, lab):
    ensure_base(base)
    target = base / lab
    if target.exists():
        safe_tree(target)
        marker(target, lab)
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


CHECKS = {"lab1": check_lab1, "lab2": check_lab2, "lab8": check_lab8}
# Details a check sends with its milestones, so the marking screen can give part of a row's points.
CHECK_DETAILS = {"lab2": lambda target, values: {"path_error": lab2_path_error(target, values)}}
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
