#!/usr/bin/env python3
"""Per-user OS lab fixtures. No privileged operations or student code execution."""
import argparse
import fcntl
import json
import os
import shutil
import sys
import time
from pathlib import Path

LABS = tuple(f"lab{n}" for n in range(1, 12))
MARKER = ".oslab-managed.json"
MAX_ARCHIVES = 3
MAX_BYTES = 2_000_000

FIXTURES = {
    "lab1": {"process.txt": "Observe a process you started with sleep 30. Record PID and state.\n"},
    "lab2": {"incoming/quarter 1.txt": "revenue,120\n", "incoming/quarter 2.txt": "revenue,130\n", "reports/README.txt": "Move the quarterly files here; preserve names.\n"},
    "lab3": {"links/source.txt": "version 1\n", "links/target-name.txt": "A symlink target for diagnosis.\n"},
    "lab4": {"data/events.csv": "status,count\nok,3\nfail,2\nok,5\n", "data/expected.txt": "ok total: 8\n"},
    "lab5": {"threads/trace.csv": "thread,step\nA,read\nB,read\nA,write\nB,write\n",
             "threads/starter.c": "#include <pthread.h>\n#include <stdio.h>\nstatic void *worker(void *arg) { puts((const char *)arg); return NULL; }\nint main(void) { pthread_t a, b;\n  if (pthread_create(&a, NULL, worker, \"A\") || pthread_create(&b, NULL, worker, \"B\")) return 1;\n  /* TODO: join both workers before reading results. */\n  return 0;\n}\n"},
    "lab6": {"private/record.txt": "student-owned record\n", "shared/notice.txt": "Read-only public notice\n"},
    "lab7": {"input/one file.txt": "alpha beta\n", "input/-dash.txt": "gamma\n",
             "count_words.sh": "#!/usr/bin/env bash\nset -u\n# TODO: loop over quoted arguments, reject missing files, and count words.\n"},
    "lab8": {"store/stock.txt": "5\n", "store/sales.log": "",
             "store/buy.sh": "#!/usr/bin/env bash\nset -euo pipefail\n# TODO: validate quantity; lock before reading stock; check, update and log while locked.\n"},
    "lab9": {"vault/alpha.txt": "alpha\n", "vault/beta.txt": "beta\n",
             "vault/worker.sh": "#!/usr/bin/env bash\nset -euo pipefail\n# TODO: acquire two owned lock files with flock -w 2; log each acquisition.\n"},
    "lab10": {"project/report.txt": "report v1\n", "project/config.ini": "mode=practice\n",
              "backup.sh": "#!/usr/bin/env bash\nset -euo pipefail\n# TODO: archive project with absolute paths, verify it, retain newest three owned archives.\n"},
    "lab11": {"images/README.txt": "Create regular image files here. Never use a device path.\n"},
}


def fail(message):
    raise ValueError(message)


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


def start(base, lab):
    ensure_base(base)
    target = base / lab
    if target.exists():
        safe_tree(target)
        marker(target, lab)
        print(f"{lab}: existing work preserved at {target}")
        return
    target.mkdir(mode=0o700)
    (target / MARKER).write_text(json.dumps({"tool": "oslab", "lab": lab, "version": 1}) + "\n", encoding="utf-8")
    for name, value in FIXTURES[lab].items():
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(value, encoding="utf-8")
    print(f"{lab}: ready at {target}")


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


def check(base, lab):
    target = base / lab
    safe_tree(target)
    marker(target, lab)
    if lab == "lab2":
        names = ["quarter 1.txt", "quarter 2.txt"]
        ok = all((target / "reports" / n).is_file() for n in names)
        print("PASS: both reports present" if ok else "TRY: reports directory is incomplete")
    elif lab == "lab8":
        try:
            count = int((target / "store/stock.txt").read_text().strip())
            print("PASS: stock is a nonnegative integer" if count >= 0 else "TRY: stock is negative")
        except (ValueError, FileNotFoundError):
            print("TRY: stock must be an integer")
    elif lab == "lab10":
        print("Inspect archive contents and retention manually; public checks cannot grade cron behaviour.")
    else:
        print("Fixture integrity OK. Submit your test evidence and explanation for human review.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor", "list", "start", "status", "hint", "check", "reset", "clean"])
    parser.add_argument("lab", nargs="?")
    parser.add_argument("level", nargs="?", type=int)
    args = parser.parse_args()
    base = workspace()
    if args.command == "doctor":
        print(f"user={os.getuid()} workspace={base} python={sys.version.split()[0]}")
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
    elif args.command == "hint":
        if args.level not in (1, 2, 3):
            fail("hint level must be 1, 2, or 3")
        print({1: "Identify the resource and expected invariant.", 2: "Inspect the fixture and the command's exit status.", 3: "Try one controlled change, then compare before and after."}[args.level])
    elif args.command == "check":
        check(base, args.lab)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"oslab: {exc}", file=sys.stderr)
        sys.exit(2)
