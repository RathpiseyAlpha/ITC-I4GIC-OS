#!/usr/bin/env python3
"""Install/remove only the one-minute Lab 10 practice entry in a user's crontab."""
import argparse
import fcntl
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from oslab import marker, workspace

TAG = "# OSLAB-LAB10"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "install", "remove"))
    args = parser.parse_args()
    home = Path.home().resolve(strict=True)
    work = workspace() / "lab10"
    if not work.is_dir() or work.is_symlink():
        parser.error("start lab10 with oslab first")
    marker(work, "lab10")
    log = work / "cron.log"
    command = f"* * * * * /usr/bin/date -Is >> {shlex.quote(str(log))} 2>&1 {TAG}"
    lock_path = home / ".oslab-lab10-cron.lock"
    if lock_path.is_symlink():
        parser.error("lock path is a symlink")
    with lock_path.open("a+") as lock:
        until = time.monotonic() + 3
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= until:
                    parser.error("cron helper busy; retry shortly")
                time.sleep(0.05)
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if current.returncode and "no crontab" not in current.stderr.lower():
            parser.error("cannot read personal crontab: " + current.stderr.strip())
        lines = current.stdout.splitlines()
        marked = [line for line in lines if line.rstrip().endswith(TAG)]
        if any(line != command for line in marked):
            parser.error("another Lab 10 marker exists; inspect it manually")
        if args.action == "status":
            print("installed" if marked else "absent")
            return
        if args.action == "install" and not marked:
            lines.append(command)
        if args.action == "remove":
            lines = [line for line in lines if line != command]
        if args.action == "install" and marked or args.action == "remove" and not marked:
            print("already in requested state")
            return
        result = subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, capture_output=True, timeout=5)
        if result.returncode:
            parser.error("cannot update personal crontab: " + result.stderr.strip())
        print("practice entry installed" if args.action == "install" else "practice entry removed")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"lab10-cron: {exc}", file=sys.stderr)
        sys.exit(2)
