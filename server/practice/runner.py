#!/usr/bin/env python3
"""Practice room runner: sets up and checks scenarios for the API. Runs as root (systemd: itc-os-practice.service).

It listens on a Unix socket that only the itc-exam group can reach (the API runs in that group), one JSON request per
connection:

    {"op": "setup", "user": .., "sid": .., "attempt": n}            the starting files, made again from scratch
    {"op": "check", "user": .., "sid": .., "attempt": n, "info": {..}}  the checks, one {id, label, ok, why} each

It refuses root, staff, the gateway and system accounts, accounts not on the roster, unknown scenarios, and a second
check by the same student within 10 seconds. For the work in the student's home it starts collect.py AS THE STUDENT
(runuser, env -i, python3 -I -S, inside a systemd scope: 256 MB, half a CPU, 64 tasks, 40 s), and judges what comes
back itself: scenario code (and a Super challenge's hidden inputs, which students cannot read) only ever runs here.

    sudo python3 runner.py                      # the service
    python3 runner.py --dev --socket PATH       # development: no root, only your own account
"""
import argparse
import grp
import json
import logging
import os
import pwd
import re
import shutil
import signal
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True  # no .pyc of a private scenario with looser permissions than its source

import practice  # noqa: E402

log = logging.getLogger("practice-runner")
COLLECT = HERE / "collect.py"
SAFE_PATH = "/usr/local/bin:/usr/bin:/bin"
# runuser lives in /usr/sbin on Ubuntu, which SAFE_PATH (the clean PATH of the student's process, and of systemd-run) does not have:
# find it here by its full path, or the collector never starts ("collector did not start").
RUNUSER = shutil.which("runuser", path="/usr/sbin:/sbin:/usr/bin:/bin") or "/usr/sbin/runuser"
JOBS = threading.Semaphore(4)
STAFF_GROUP, GW_USER = "itc-exam", "examgw"
USER_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")


class Refused(Exception):
    pass


class Runner:
    def __init__(self, args):
        self.args = args
        self.dev = args.dev
        self.me = pwd.getpwuid(os.getuid()).pw_name
        self.last_check = {}
        self.mu = threading.Lock()
        self.key = self.load_key()

    def etc(self):
        return Path(os.environ.get("ITC_EXAM_ETC", "/etc/itc-os-exam"))

    def load_key(self):
        path = self.etc() / "practice.key"
        try:
            key = path.read_bytes().strip()
            if len(key) >= 32:
                return key
        except OSError:
            pass
        if self.dev:
            return b"dev-practice-key-" + b"0" * 32
        raise SystemExit("runner: %s is missing (examctl install makes it)" % path)

    def roster(self):
        base = practice.read_json(self.etc() / "practice.json", {})
        path = base.get("roster") or practice.read_json(self.etc() / "agent.json", {}).get("roster")
        users = set()
        if path:
            try:
                data = json.loads(Path(path).read_text(encoding="utf-8"))
                users = {str(v.get("user")) for v in data.values() if isinstance(v, dict)}
            except (OSError, ValueError):
                pass
        return users

    def staff(self):
        try:
            return set(grp.getgrnam(STAFF_GROUP).gr_mem)
        except KeyError:
            return set()

    def check_user(self, user):
        if not USER_RE.match(user):
            raise Refused("bad user")
        try:
            pw = pwd.getpwnam(user)
        except KeyError:
            raise Refused("no such account")
        if self.dev:
            if user != self.me:
                raise Refused("development runner: only %s" % self.me)
            return pw
        if user in ("root", GW_USER) or pw.pw_uid < 1000 or user in self.staff():
            raise Refused("refusing a staff, service or system account")
        if user not in self.roster():
            raise Refused("not on the roster")
        return pw

    # the student's side
    def child(self, pw, req, timeout=40):
        py = sys.executable or "/usr/bin/python3"
        env_list = ["PATH=" + SAFE_PATH, "HOME=" + pw.pw_dir, "USER=" + pw.pw_name, "LOGNAME=" + pw.pw_name,
                    "LANG=C.UTF-8", "LC_ALL=C.UTF-8"]
        if self.dev:
            cmd = [py, "-I", "-S", str(COLLECT)]
            env = dict(e.split("=", 1) for e in env_list)
        else:
            cmd = [RUNUSER, "-u", pw.pw_name, "--", "/usr/bin/env", "-i"] + env_list + [py, "-I", "-S", str(COLLECT)]
            if shutil.which("systemd-run") and not self.args.no_scope:
                cmd = ["systemd-run", "--quiet", "--scope", "--collect", "-p", "MemoryMax=256M", "-p", "CPUQuota=50%",
                       "-p", "TasksMax=64", "-p", "RuntimeMaxSec=%d" % (timeout + 5)] + cmd
            env = {"PATH": SAFE_PATH, "LANG": "C.UTF-8"}
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                             cwd="/", start_new_session=True)
        try:
            # The request (with any hidden inputs) is written only after the child made itself non-dumpable.
            first = p.stdout.readline()
            if first.strip() != b"ready":
                raise Refused("collector did not start")
            out, err = p.communicate((json.dumps(req) + "\n").encode("utf-8"), timeout=timeout)
        except subprocess.TimeoutExpired:
            self.kill(p)
            raise Refused("the check took too long (over %d s)" % timeout)
        finally:
            self.kill(p)
        try:
            data = json.loads(out.decode("utf-8").strip().splitlines()[-1])
        except (ValueError, IndexError):
            log.warning("collector for %s said: %s", pw.pw_name, err.decode("utf-8", "replace")[-300:])
            raise Refused("the collector failed")
        if not isinstance(data, dict):
            raise Refused("the collector failed")
        if data.get("error"):
            raise Refused(str(data["error"])[:200])
        return data

    @staticmethod
    def kill(p):
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass

    def handle(self, req):
        if not isinstance(req, dict):
            raise Refused("bad request")
        if req.get("op") == "ping":
            return {"ok": True, "scenarios": len(practice.catalog()), "drills": len(practice.drills())}
        op, user, sid = req.get("op"), str(req.get("user", "")), str(req.get("sid", ""))
        try:
            attempt = int(req.get("attempt", 1))
        except (TypeError, ValueError):
            raise Refused("bad attempt")
        if op not in ("setup", "check") or not practice.SCENARIO_RE.match(sid) or not 1 <= attempt <= 10 ** 6:
            raise Refused("bad request")
        pw = self.check_user(user)
        mod = practice.exercise(sid)   # a scenario or a drill
        if not mod:
            raise Refused("unknown scenario")
        v = practice.values(mod, user, attempt)
        if op == "setup":
            spec = mod.fixture(v)
            staff = sorted(self.staff()) if not self.dev else []
            data = self.child(pw, {"op": "setup", "sid": sid, "dirs": spec.get("dirs", []), "files": spec.get("files", {}),
                                   "staff": staff})
            return {"ok": True, "info": {"inodes": data.get("inodes", {}), "root": data.get("root", "")}}
        with self.mu:
            last = self.last_check.get(user, 0)
            gap = self.args.min_gap if self.dev and self.args.min_gap is not None else practice.CHECK_EVERY_S
            if time.time() - last < gap:
                return {"error": "wait", "retry_s": round(gap - (time.time() - last), 1)}
            self.last_check[user] = time.time()
        hidden = None
        if hasattr(mod, "hidden"):
            hidden = mod.hidden(v, practice.hidden_picker(self.key, user, sid, attempt))
        creq = mod.collect(v, hidden) if hasattr(mod, "collect") else {"tree": True}
        creq = dict(creq, op="collect", sid=sid)
        data = self.child(pw, creq)
        info = req.get("info") if isinstance(req.get("info"), dict) else {}
        try:
            results = mod.checks(data, v, hidden, info)
        except Exception as e:
            log.exception("checks of %s for %s", sid, user)
            raise Refused("the checker failed (%s); tell the instructor" % type(e).__name__)
        clean = []
        for r in results:
            clean.append({"id": str(r.get("id", ""))[:40], "label": str(r.get("label", ""))[:200], "ok": bool(r.get("ok")),
                          "why": str(r.get("why", ""))[:400] if not r.get("ok") else ""})
        return {"ok": bool(clean) and all(r["ok"] for r in clean), "checks": clean}


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        runner = self.server.runner
        try:
            line = self.rfile.readline(65536)
            req = json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.reply({"error": "bad request"})
            return
        if isinstance(req, dict) and req.get("op") == "ping":  # the board asks every 5 s: no job slot, no log line
            self.reply({"ok": True})
            return
        with JOBS:
            try:
                out = runner.handle(req)
            except Refused as e:
                out = {"error": str(e)}
            except Exception as e:  # pragma: no cover
                log.exception("request")
                out = {"error": "runner: %s" % type(e).__name__}
        if isinstance(req, dict):
            log.info("%s %s %s: %s", req.get("op"), req.get("user"), req.get("sid"),
                     "ok" if out.get("ok") else out.get("error", "not yet"))
        self.reply(out)

    def reply(self, obj):
        try:
            self.wfile.write((json.dumps(obj) + "\n").encode("utf-8"))
        except OSError:
            pass


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


def main(argv=None):
    p = argparse.ArgumentParser(description="Practice room runner")
    p.add_argument("--socket", default=practice.runner_socket())
    p.add_argument("--group", default=STAFF_GROUP, help="group allowed to use the socket (the API's)")
    p.add_argument("--dev", action="store_true", help="development: no root, only your own account")
    p.add_argument("--no-scope", action="store_true", help="do not use systemd-run (containers)")
    p.add_argument("--min-gap", type=float, default=None, help="tests only (with --dev): seconds between two checks")
    a = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    if not a.dev and os.geteuid() != 0:
        sys.exit("runner: run as root (or --dev for development)")
    sock = Path(a.socket)
    sock.parent.mkdir(parents=True, exist_ok=True)
    if sock.exists() or sock.is_symlink():
        sock.unlink()
    old = os.umask(0o117)
    srv = Server(str(sock), Handler)
    os.umask(old)
    if not a.dev:
        try:
            shutil.chown(str(sock), "root", a.group)
            os.chmod(str(sock), 0o660)
        except (KeyError, LookupError, OSError) as e:
            sys.exit("runner: cannot give the socket to group %s: %s" % (a.group, e))
    else:
        os.chmod(str(sock), 0o600)
    srv.runner = Runner(a)
    errors = practice.catalog_errors()
    log.info("runner on %s, %d scenarios, %d drills%s", sock, len(practice.catalog()), len(practice.drills()),
             (", errors: %s" % errors) if errors else "")

    def stop(*_):
        threading.Thread(target=srv.shutdown, daemon=True).start()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        srv.serve_forever()
    finally:
        try:
            sock.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
