#!/usr/bin/env python3
"""Instructor view of the class inbox: live board, checkpoint release, keys and CSV export.

Reads the records that `oslab` drops in the inbox. A record is attributed to the
account that owns the file, never to the name written inside it. This is class
feedback and marking support, not tamper-proof grading.
"""
import argparse
import csv
import hashlib
import json
import os
import pwd
import re
import secrets
import stat
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oslab  # noqa: E402  (installed next to this file)

MAX_RECORD = 16384
USER = re.compile(r"^[a-z_][a-z0-9_-]*[$]?$")


def inbox_dir():
    return Path(os.environ.get("OSLAB_INBOX", oslab.DEFAULT_INBOX))


def release_dir():
    return Path(os.environ.get("OSLAB_RELEASE_DIR", oslab.DEFAULT_RELEASE))


def state_dir():
    folder = Path(os.environ.get("OSLAB_TEACH_STATE", str(Path.home() / ".oslab-teach")))
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    return folder


def roster(path):
    if not path:
        return []
    names = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            if not USER.match(line):
                oslab.fail(f"invalid username in roster: {line}")
            names.append(line)
    return names


def owner_name(uid, data):
    # Only the test suite sets this: all its "students" share one uid.
    if os.environ.get("OSLAB_TEACH_TRUST_NAME") == "1":
        return str(data.get("user", uid))
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def scan(lab):
    """Return {user: {kind: [records, oldest first]}} and the names of users with rewritten or removed answers."""
    box = inbox_dir()
    if not box.is_dir():
        oslab.fail(f"inbox not found: {box}")
    seen_path = state_dir() / f"seen-{lab}.json"
    try:
        seen = json.loads(seen_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        seen = {}
    present = set()
    users = {}
    for entry in os.scandir(str(box)):
        if not entry.name.startswith(lab + ".") or not entry.name.endswith(".json"):
            continue
        try:
            fd = os.open(entry.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except OSError:
            continue
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_RECORD:
                continue
            raw = os.read(fd, MAX_RECORD)
        finally:
            os.close(fd)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict) or data.get("lab") != lab or not isinstance(data.get("kind"), str):
            continue
        user = owner_name(info.st_uid, data)
        present.add(entry.name)
        first = seen.setdefault(entry.name, {"user": user, "kind": data["kind"], "first_seen": int(time.time()),
                                             "sha": hashlib.sha256(raw).hexdigest()})
        data["_when"] = min(first["first_seen"], int(info.st_mtime))
        users.setdefault(user, {}).setdefault(data["kind"], []).append(data)
    tmp = seen_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(seen), encoding="utf-8")
    os.replace(str(tmp), str(seen_path))
    counts = Counter((item["user"], item["kind"]) for item in seen.values() if item["kind"] in ("predict", "checkpoint"))
    removed = {item["user"] for name, item in seen.items() if name not in present and item["kind"] in ("predict", "checkpoint")}
    flagged = {user for (user, _), count in counts.items() if count > 1} | removed
    for kinds in users.values():
        for records in kinds.values():
            records.sort(key=lambda record: record["_when"])
    return users, flagged


def released(lab):
    path = release_dir() / f"{lab}.checkpoint"
    try:
        nonce = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return nonce if oslab.TOKEN.match(nonce) else None


def marks(items, answers):
    """(correct, marked) over the questions that have an expected answer."""
    results = [oslab.mark(item["kind"], item["expect"], answers.get(item["key"], "")) for item in items]
    results = [result for result in results if result is not None]
    return sum(results), len(results)


def summary(lab, user, kinds, nonce):
    row = {"user": user, "prelab": "", "started": "", "predict": "", "checks": "", "hints": "", "checkpoint": "", "task": "",
           "predict_answers": {}, "checkpoint_answers": {}, "auto_points": ""}
    if kinds.get("prelab"):
        first = kinds["prelab"][0]
        row["prelab"] = f"{first.get('first_try', '?')}/{first.get('questions', '?')}"
    if kinds.get("start"):
        row["started"] = "yes"
    if kinds.get("predict") and lab in oslab.PREDICT:
        answers = kinds["predict"][0].get("answers", {})
        good, total = marks(oslab.PREDICT[lab](oslab.lab_values(lab, user)), answers)
        row["predict"] = f"{good}/{total}"
        row["predict_answers"] = answers
    if kinds.get("check"):
        best = max(kinds["check"], key=lambda record: (record.get("passed", 0), record["_when"]))
        row["checks"] = f"{best.get('passed', 0)}/{best.get('total', 0)} x{len(kinds['check'])}"
        outcome = [record.get("checkpoint") for record in kinds["check"] if record.get("checkpoint") is not None]
        row["task"] = "" if not outcome else ("done" if any(outcome) else "no")
    if kinds.get("hint"):
        row["hints"] = f"{len(kinds['hint'])} (to {max(record.get('level', 0) for record in kinds['hint'])})"
    if kinds.get("checkpoint") and lab in oslab.CHECKPOINT:
        first = kinds["checkpoint"][0]
        answers = first.get("answers", {})
        row["checkpoint_answers"] = answers
        if first.get("practice") or not nonce:
            row["checkpoint"] = "practice"
        else:
            good, total = marks(oslab.checkpoint_task(lab, user, nonce)[2], answers)
            row["checkpoint"] = f"{good}/{total}"
            # 1 point for the answers (half if at least half are right), 1 for the task; the sentence point is read by a person.
            row["auto_points"] = (1 if good == total else 0.5 if good * 2 >= total else 0) + (1 if row["task"] == "done" else 0)
    return row


def rows(lab, names):
    users, flagged = scan(lab)
    nonce = released(lab)
    order = names or sorted(users)
    result = [summary(lab, user, users.get(user, {}), nonce) for user in order]
    for row in result:
        row["flag"] = "rewritten" if row["user"] in flagged else ""
    return result, nonce


def board(lab, names):
    table, nonce = rows(lab, names)
    columns = ("user", "prelab", "started", "predict", "checks", "hints", "checkpoint", "task", "flag")
    widths = {name: max(len(name), *(len(str(row[name])) for row in table)) if table else len(name) for name in columns}
    print(f"{lab} at {time.strftime('%H:%M:%S')}   checkpoint: {'RELEASED' if nonce else 'closed'}   students: {len(table)}")
    print("  ".join(name.ljust(widths[name]) for name in columns))
    for row in table:
        print("  ".join(str(row[name]).ljust(widths[name]) for name in columns))
    waiting = [row["user"] for row in table if not row["predict"]]
    if waiting:
        print(f"\nNo prediction yet ({len(waiting)}): " + " ".join(waiting))
    if lab in oslab.PREDICT:
        print("\nPrediction spread (answer: how many students)")
        for item in oslab.PREDICT[lab](oslab.lab_values(lab, "x")):
            if item["kind"] == "text":
                continue
            spread = Counter(str(row["predict_answers"].get(item["key"])) for row in table if row["predict_answers"])
            print(f"  {item['key']:9} " + "  ".join(f"{answer}: {count}" for answer, count in spread.most_common()))
    sentences = [(row["user"], row["checkpoint_answers"].get("why", "")) for row in table if row["checkpoint_answers"]]
    if sentences:
        print("\nCheckpoint sentences")
        for user, text in sentences:
            print(f"  {user}: {text}")


def release(lab):
    folder = release_dir()
    if not folder.is_dir():
        oslab.fail(f"release directory not found: {folder}")
    path = folder / f"{lab}.checkpoint"
    if path.exists():
        oslab.fail(f"{lab} checkpoint was already released at {time.strftime('%H:%M:%S', time.localtime(path.stat().st_mtime))}; "
                   "remove that file by hand only if no student has answered yet")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        os.fchmod(fd, 0o644)
        handle.write(secrets.token_hex(6) + "\n")
    print(f"{lab} checkpoint released. Students run: oslab checkpoint {lab}")


def key(lab, names):
    if lab not in oslab.VALUES:
        oslab.fail(f"{lab} has no personal values")
    if not names:
        names = sorted(scan(lab)[0])
    nonce = released(lab)
    for user in names:
        values = oslab.lab_values(lab, user)
        print(f"\n{user}: {values}")
        for item in oslab.PREDICT[lab](values):
            if item["expect"] is not None:
                print(f"  predict {item['key']:9} {item['expect']}")
        if nonce:
            task_values, _, items, _ = oslab.checkpoint_task(lab, user, nonce)
            print(f"  checkpoint values {task_values}")
            for item in items:
                if item["expect"] is not None:
                    print(f"  checkpoint {item['key']:9} {item['expect']}")
    if not nonce:
        print("\nCheckpoint keys appear after `release`.")


def export(lab, names):
    table, _ = rows(lab, names)
    writer = csv.writer(sys.stdout)
    writer.writerow(["user", "prelab_first_try", "started", "predict_correct", "milestones", "hints", "checkpoint_answers",
                     "checkpoint_task", "checkpoint_auto_points_of_2", "flag", "predict_sentence", "checkpoint_sentence"])
    for row in table:
        writer.writerow([row["user"], row["prelab"], row["started"], row["predict"], row["checks"], row["hints"], row["checkpoint"],
                         row["task"], row["auto_points"], row["flag"], row["predict_answers"].get("why", ""),
                         row["checkpoint_answers"].get("why", "")])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["board", "release", "key", "export"])
    parser.add_argument("lab")
    parser.add_argument("--roster", help="file with one student account per line; default: accounts seen in the inbox")
    parser.add_argument("--watch", type=int, default=0, help="redraw the board every N seconds")
    args = parser.parse_args()
    if args.lab not in oslab.LABS:
        oslab.fail("choose lab1 through lab11")
    names = roster(args.roster)
    if args.command == "release":
        release(args.lab)
    elif args.command == "key":
        key(args.lab, names)
    elif args.command == "export":
        export(args.lab, names)
    elif args.watch > 0:
        while True:
            print("\033[2J\033[H", end="")
            board(args.lab, names)
            time.sleep(max(args.watch, 2))
    else:
        board(args.lab, names)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as exc:
        print(f"oslab-teach: {exc}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        pass
