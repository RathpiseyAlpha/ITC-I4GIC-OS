#!/usr/bin/env python3
"""Local preview of the exam room: a throwaway copy of the API, the gateway with a local shell, and the site.

Linux or WSL only (tmux needed). Nothing here touches a real server. Logins on this copy accept the password `test`
for any account on its made-up roster (your own account and five invented students with sample board data).

    python3 server/examroom/devstack.py            # then open the URLs it prints
    python3 server/examroom/devstack.py --phase sealed
    python3 server/examroom/devstack.py --no-lock      # leaving fullscreen does not lock (the lock is on by default)
    python3 server/examroom/devstack.py --phase sealed # practice is open (an open exam closes it)

The site is served with its own env.js, so the portal (http://localhost:8080/) logs in against this local API and
shows the exam room and practice links; no ?api= is needed.

Stop it with Ctrl+C; it removes its temporary folder and the exam folder it made in your home.
"""
import argparse
import functools
import http.server
import json
import os
import pwd
import random
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
ME = pwd.getpwuid(os.getuid()).pw_name
FAKE = [("e20990101", "fake01", "CHAN Dara"), ("e20990102", "fake02", "KEO Sina"), ("e20990103", "fake03", "LIM Sophea"),
        ("e20990104", "fake04", "TEP Malis"), ("e20990105", "fake05", "PHAN Chenda")]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api-port", type=int, default=5001)
    p.add_argument("--gw-port", type=int, default=5011)
    p.add_argument("--web-port", type=int, default=8080)
    p.add_argument("--phase", default="open", choices=("sealed", "open", "closed"))
    p.add_argument("--minutes", type=int, default=60)
    p.add_argument("--no-lock", action="store_true", help="do not lock the exam when a student leaves fullscreen")
    a = p.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="examroom-dev-"))
    etc, var = tmp / "etc", tmp / "var"
    etc.mkdir()
    (var / "rec").mkdir(parents=True)
    (etc / "ticket.key").write_text(os.urandom(32).hex())
    folder = "midterm-devstack"
    (etc / "exam.json").write_text(json.dumps({
        "id": "midterm-dev", "kind": "midterm", "title": "Midterm: Labs 1 to 4", "duration_min": a.minutes,
        "parts": ["A", "B", "C", "D"], "folder": folder, "gateway_url": "ws://localhost:%d/term" % a.gw_port,
        "lock": {"on": [] if a.no_lock else ["fs_exit"]}}))
    pvar = tmp / "practice"
    pvar.mkdir()
    (etc / "practice.json").write_text(json.dumps({"gateway_url": "ws://localhost:%d/term" % a.gw_port}))
    sock = str(tmp / "runner.sock")
    os.environ.update(ITC_EXAM_ETC=str(etc), ITC_EXAM_VAR=str(var), OSLAB_TERM_FILE="/nonexistent",
                      ITC_PRACTICE_VAR=str(pvar), ITC_PRACTICE_SOCK=sock)
    sys.path.insert(0, str(HERE))
    import common
    now = time.time()
    (var / "midterm-dev").mkdir()
    (var / "midterm-dev" / "state.json").write_text(json.dumps(
        {"phase": a.phase, "start": common.iso(now - 23 * 60), "end": common.iso(now - 23 * 60 + a.minutes * 60)}))

    # sample board data for the invented students
    rnd = random.Random(4)
    samples = [dict(away=[(41, "tab"), (75, "window"), (230, "tab")], pastes=[540, 312, 228], conn=False, cmd="awk -F, '{print $2}' auth.csv"),
               dict(away=[(72, "tab")], pastes=[], conn=True, cmd="sort -rn | head -3", screens="extended"),
               dict(away=[], pastes=[260], conn=True, cmd="mkdir -p b/office", panel=45, screens="single"),
               dict(away=[], pastes=[], conn=True, cmd="grep '^paid,' data/panda.csv | wc -l", screens="single"),
               dict(away=[(8, "window")], pastes=[40], conn=True, cmd="ln -s candle-old.txt candle-soft.txt", locked=True)]
    for (sid, user, _name), s in zip(FAKE, samples):
        d = var / "rec" / user
        d.mkdir()
        t = now - 20 * 60
        with open(d / "events.jsonl", "w") as f:
            f.write(json.dumps({"ts": t, "k": "connect"}) + "\n")
            f.write(json.dumps({"ts": t + 2, "k": "start"}) + "\n")
            for secs, why in s["away"]:
                t += rnd.randint(60, 200)
                f.write(json.dumps({"ts": t, "k": "leave", "why": why}) + "\n")
                t += secs
                f.write(json.dumps({"ts": t, "k": "back", "away_ms": secs * 1000, "why": why}) + "\n")
            if s.get("screens"):
                f.write(json.dumps({"ts": t + 3, "k": "screens", "detail": s["screens"]}) + "\n")
            if s.get("panel"):
                t += 90
                f.write(json.dumps({"ts": t, "k": "panel_open", "n": 28}) + "\n")
                t += s["panel"]
                f.write(json.dumps({"ts": t, "k": "panel_close", "away_ms": s["panel"] * 1000}) + "\n")
            for n in s["pastes"]:
                t += rnd.randint(30, 120)
                f.write(json.dumps({"ts": t, "k": "paste", "n": n}) + "\n")
                if n > 200:
                    f.write(json.dumps({"ts": t, "k": "big_input", "n": n}) + "\n")
        if s.get("locked"):
            (d / "lock.json").write_text(json.dumps({"exam": "midterm-dev", "locked": True, "n": 1, "since": now - 40,
                                                     "why": "fs_exit", "total_s": 0, "bad": [], "started": True}))
            with open(d / "events.jsonl", "a") as f:
                f.write(json.dumps({"ts": now - 40, "k": "fs_exit"}) + "\n")
                f.write(json.dumps({"ts": now - 40, "k": "lock", "why": "fs_exit"}) + "\n")
        (d / "status.json").write_text(json.dumps({"user": user, "connected": s["conn"], "last_seen": now - (0 if s["conn"] else 190),
                                                  "connects": 1, "last_cmd": s["cmd"], "since": now - 1200}))
        cast = d / ("%d.cast" % int(now - 1200))
        lines = [json.dumps({"version": 2, "width": 100, "height": 30, "timestamp": int(now - 1200)})]
        tt = 0.5
        for cmd in ("ls", "cat values.txt", s["cmd"]):
            lines.append(json.dumps([tt, "o", "%s@itc-os:~/midterm$ " % user]))
            for ch in cmd:
                tt += 0.15
                lines.append(json.dumps([tt, "i", ch]))
                lines.append(json.dumps([tt, "o", ch]))
            tt += 0.4
            lines.append(json.dumps([tt, "o", "\r\n(output of %s)\r\n" % cmd.split()[0]]))
            tt += 20
        cast.write_text("\n".join(lines) + "\n")

    # sample practice data: XP and nicknames for the invented students, so the leaderboard is not empty
    led = []
    plan = [("fake01", ["paths-easy", "pipes-easy", "links-easy", "processes-easy", "paths-medium"], "Root Beer"),
            ("fake02", ["paths-easy", "pipes-easy", "pipes-medium", "pipes-hard"], ""),
            ("fake03", ["links-easy"], "ln -s life"),
            ("fake04", ["processes-easy", "processes-medium", "processes-hard", "paths-easy"], "Zombie Hunter")]
    for i, (user, sids, _n) in enumerate(plan):
        for j, sid in enumerate(sids):
            lvl = sid.split("-")[1]
            led.append({"ts": now - 86400 * (3 - i % 3) - 600 * j, "user": user, "kind": "clear", "sid": sid, "attempt": 1,
                        "hints": (i + j) % 3, "checks": 1 + j, "secs": 300 + 120 * j, "level": lvl,
                        "base": {"easy": 50, "medium": 100, "hard": 200}[lvl], "track": sid.split("-")[0]})
    (pvar / "ledger.jsonl").write_text("".join(json.dumps(e) + chr(10) for e in led))
    (pvar / "profiles.json").write_text(json.dumps({u: {"nick": n} for u, _s, n in plan if n}))

    site = tmp / "site"
    (site / "app" / "server").mkdir(parents=True)
    src = (REPO / "app" / "server" / "app.py").read_text(encoding="utf-8")
    src = src.replace("\ndef create_session(username):",
                      "\ndef verify_password(username, password):  # devstack only: every roster account, password 'test'\n"
                      "    return password == 'test'\n\n\ndef create_session(username):", 1)
    (site / "app" / "server" / "app.py").write_text(src, encoding="utf-8")
    shutil.copytree(REPO / "server", site / "server", ignore=shutil.ignore_patterns("__pycache__"))
    roster = {"e20990100": {"user": ME, "name": "YOU Test"}}
    roster.update({sid: {"user": u, "name": n} for sid, u, n in FAKE})
    (site / "app" / "server" / "roster.json").write_text(json.dumps(roster))
    home_folder = Path.home() / folder
    import exambank
    import midterm
    midterm.set_roster_source(lambda: [ME])
    if a.phase == "sealed":
        # Open (the board's button, or examctl) draws the roster and makes the starting files; a folder left from an earlier
        # run would be kept by it and could belong to another scenario
        shutil.rmtree(home_folder, ignore_errors=True)
    else:
        exambank.write_draws("midterm-dev", midterm.plan([ME]))   # what Open would have written
        dirs, files = midterm.fixture(ME)
        subprocess.run([sys.executable, str(HERE / "examctl.py"), "_fixture", "--folder", folder], check=True,
                       input=json.dumps({"dirs": dirs, "files": files}), text=True)

    # web control in preview mode: the root helper runs as you; hardening and account changes are refused
    (etc / "agent.json").write_text(json.dumps({"roster": str(site / "app" / "server" / "roster.json"), "dev": True}))
    for name in ("tmp", "queue", "work", "done"):
        common.req_dir(name).mkdir(parents=True)
    common.control_dir().mkdir()
    env = dict(os.environ, ITC_OS_ADMINS="instructor", ITC_OS_ROSTER=str(site / "app" / "server" / "roster.json"),
               ITC_EXAM_GW_HEALTH="http://127.0.0.1:%d/term/health" % a.gw_port)
    procs = [
        subprocess.Popen([sys.executable, str(site / "app" / "server" / "app.py"), "--host", "127.0.0.1", "--port", str(a.api_port)], env=env),
        subprocess.Popen([sys.executable, str(HERE / "gateway.py"), "--backend", "local", "--dev", "--host", "127.0.0.1",
                          "--port", str(a.gw_port), "--tmux-socket", "itcexam-dev", "--tmux-conf", str(HERE / "tmux.conf")], env=env),
        subprocess.Popen([sys.executable, str(HERE / "examctl.py"), "agent", "--dev", "--loop"], env=env),
        subprocess.Popen([sys.executable, str(REPO / "server" / "practice" / "runner.py"), "--dev", "--socket", sock], env=env),
    ]
    api = "http://localhost:%d" % a.api_port
    env_js = ("window.__ENV = { serverUrl: %s, examRoom: true, practice: true };  // devstack, local only\n"
              % json.dumps(api)).encode("utf-8")

    class Web(http.server.SimpleHTTPRequestHandler):
        """The repository as the website, except env.js, which points the pages at this local API."""
        def do_GET(self):
            if self.path.split("?", 1)[0] == "/app/js/env.js":
                self.send_response(200)
                self.send_header("Content-Type", "text/javascript; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(env_js)))
                self.end_headers()
                self.wfile.write(env_js)
                return
            super().do_GET()

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")  # edits show on reload
            super().end_headers()

        def log_message(self, *args):
            pass
    web = http.server.ThreadingHTTPServer(("127.0.0.1", a.web_port), functools.partial(Web, directory=str(REPO)))
    import threading
    threading.Thread(target=web.serve_forever, daemon=True).start()
    print("\nportal:      http://localhost:%d/   (log in as %s or as instructor, password test)" % (a.web_port, ME))
    print("exam room:   http://localhost:%d/exam.html" % a.web_port)
    print("exam board:  http://localhost:%d/exam-board.html   (instructor)" % a.web_port)
    print("practice:    http://localhost:%d/practice.html   (closed while the exam is open: start with --phase sealed)" % a.web_port)
    print("practice board: http://localhost:%d/practice-board.html   (instructor)" % a.web_port)
    print("phase %s; change it by editing %s\n" % (a.phase, var / "midterm-dev" / "state.json"), flush=True)

    def stop(*_):
        for pr in procs:
            pr.terminate()
        subprocess.run(["tmux", "-L", "itcexam-dev", "kill-server"], capture_output=True)
        shutil.rmtree(home_folder, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while True:
        time.sleep(1)
        for pr in procs:
            if pr.poll() is not None:
                print("a process stopped; shutting down", flush=True)
                stop()


if __name__ == "__main__":
    main()
