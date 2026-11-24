#!/usr/bin/env python3
"""Exam room terminal gateway: browser websocket -> SSH to localhost as the student -> tmux.

One asyncio process for every student. For each connection it:

- checks the signed, single-use ticket the API gave the page (no password ever reaches the gateway),
- opens SSH to 127.0.0.1 as that student with the gateway key, and attaches `tmux new -A -s exam`, so a reload or a
  dropped connection comes back to the same shell; a second connection for the same student replaces the first,
- records what the student types and sees as asciicast v2 in rec/<user>/<start>.cast (stopped at a size cap and
  marked "output truncated"),
- appends the page's proctoring events (left the page, came back, paste, fullscreen, screens, side panel) to rec/<user>/events.jsonl,
- keeps rec/<user>/status.json up to date for the instructor board,
- throttles output to the browser, so `yes` cannot flood the page or the tunnel,
- closes every terminal when the exam is no longer open.

Protocol (one websocket per terminal):
    page -> gateway, text JSON: {"t":"auth","ticket":..,"cols":..,"rows":..} first, then
        {"t":"i","d":"typed text"}  {"t":"r","cols":..,"rows":..}  {"t":"e","k":"leave"|...}  {"t":"ping"}
        {"t":"unlock","code":"482913"}
    gateway -> page: binary frames = terminal output; text JSON {"t":"hello"|"bye"|"pong"|"note", ...}
        {"t":"lock","why":..,"bad":"wrong"|"wait"}  {"t":"unlocked"}

Exam lock: with "lock": {"on": ["fs_exit"]} in the config, leaving fullscreen (or starting the exam a second time)
locks the student. Typed input is dropped until the page sends the unlock code shown on the instructor board.

Practice room (Practice Linux Commands): a ticket with x = "practice" opens the shell in ~/practice/<scenario>/, in its
own tmux session (practice-<scenario>), with its recordings, events, status and lock under rec/<user>/practice/. It
is open whenever no exam is running; an exam that opens ends every practice session. Its lock is always the wait.
At most max_sessions practice shells run at once; the others wait in a queue ({"t":"queue","pos":n}).

Quiz session (Linux skill roadmap): a practice ticket with k = "quiz" opens no shell, no recording and no queue place:
only the lock, the page's events and the status (kind "quiz", the quiz id and the attempt). A quiz has no typed input to
drop, so the API is the gate: it refuses hint and submit unless the status shows this attempt's socket alive and the
lock is off (app.py `_quiz_gate`). The lock is the practice room's, shared with the shell: the same wait that doubles.

Run (see server/examroom/README.md):
    python3 gateway.py --port 5010                      # SSH backend, the real setup
    python3 gateway.py --backend local --dev --port 5010  # development only: a local shell as yourself
"""
import argparse
import asyncio
import codecs
import json
import logging
import hmac
import os
import re
import shlex
import signal
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import common  # noqa: E402

try:
    import websockets
    from websockets.asyncio.server import serve
    from websockets.exceptions import ConnectionClosed
except ImportError:  # pragma: no cover
    sys.exit("gateway: the websockets package (13 or later) is missing: apt install python3-websockets")

log = logging.getLogger("examgw")

EVENT_KINDS = {"start", "leave", "back", "paste", "fs_exit", "fs_enter", "reload", "note",
               "screens", "panel_open", "panel_close", "kb_lock", "stop"}
MAX_EVENTS_PER_MIN = 120
STATUS_EVERY = 5.0
STATE_EVERY = 10.0


def append_event(user, kind, folder=None, **fields):
    ev = {"ts": round(time.time(), 3), "k": kind}
    ev.update(fields)
    folder = folder or common.rec_dir(user)
    try:
        with open(folder / "events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        os.chmod(folder / "events.jsonl", 0o640)
    except OSError as e:
        log.warning("events %s: %s", user, e)


# ── Backends ──────────────────────────────────────────────────

class SSHBackend:
    """SSH to localhost as the student with the gateway key, then tmux."""

    def __init__(self, args):
        self.args = args
        self.conn = None
        self.proc = None

    async def open(self, user, cols, rows, folder, session="exam"):
        import asyncssh  # imported here so the local development backend needs no asyncssh
        kh = self.args.known_hosts if self.args.known_hosts and os.path.exists(self.args.known_hosts) else None
        self.conn = await asyncssh.connect(
            self.args.ssh_host, port=self.args.ssh_port, username=user, client_keys=[self.args.key],
            known_hosts=kh, agent_path=None, password=None, kbdint_auth=False, gss_auth=False,
            keepalive_interval=30)
        self.proc = await self.conn.create_process(
            remote_command(self.args.tmux_conf, folder, session=session), term_type="xterm-256color",
            term_size=(cols, rows), encoding=None)

    async def read(self):
        data = await self.proc.stdout.read(65536)
        return data or b""

    def write(self, data):
        self.proc.stdin.write(data)

    def resize(self, cols, rows):
        self.proc.change_terminal_size(cols, rows)

    async def close(self):
        try:
            if self.proc:
                self.proc.close()
            if self.conn:
                self.conn.close()
                await asyncio.wait_for(self.conn.wait_closed(), 5)
        except Exception:
            pass


class LocalBackend:
    """Development only: a pty running tmux as the gateway's own account. Never used on the server."""

    def __init__(self, args):
        self.args = args
        self.master = None
        self.proc = None
        self.queue = asyncio.Queue()

    async def open(self, user, cols, rows, folder, session="exam"):
        import fcntl
        import pty
        import termios
        self.master, slave = pty.openpty()
        set_winsize(self.master, cols, rows)
        env = dict(os.environ, TERM="xterm-256color")
        env.pop("TMUX", None)

        def ctty():
            fcntl.ioctl(0, termios.TIOCSCTTY, 0)
        self.proc = await asyncio.create_subprocess_exec(
            "/bin/sh", "-c", remote_command(self.args.tmux_conf, folder, socket=self.args.tmux_socket, session=session),
            stdin=slave, stdout=slave, stderr=slave, start_new_session=True, preexec_fn=ctty, env=env,
            cwd=os.path.expanduser("~"))
        os.close(slave)
        loop = asyncio.get_running_loop()
        loop.add_reader(self.master, self._readable)

    def _readable(self):
        try:
            data = os.read(self.master, 65536)
        except OSError:
            data = b""
        if not data:
            asyncio.get_running_loop().remove_reader(self.master)
        self.queue.put_nowait(data)

    async def read(self):
        return await self.queue.get()

    def write(self, data):
        os.write(self.master, data)

    def resize(self, cols, rows):
        set_winsize(self.master, cols, rows)

    async def close(self):
        try:
            asyncio.get_running_loop().remove_reader(self.master)
        except Exception:
            pass
        try:
            if self.proc and self.proc.returncode is None:
                self.proc.terminate()  # tmux client only; the tmux server and the shell keep running
                await asyncio.wait_for(self.proc.wait(), 3)
        except Exception:
            pass
        try:
            os.close(self.master)
        except Exception:
            pass


def set_winsize(fd, cols, rows):
    import fcntl
    import struct
    import termios
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


PRACTICE_MAX_S = 7200   # a practice tmux session is ended 2 hours after it was created


def remote_command(tmux_conf, folder, socket="itcexam", session="exam"):
    conf = "-f %s " % shlex.quote(tmux_conf) if tmux_conf and os.path.exists(tmux_conf) else ""
    if session == "exam":
        return ("cd ~/%s 2>/dev/null || cd ~; unset TMUX; exec tmux %s-L %s new-session -A -s exam"
                % (shlex.quote(folder), conf, shlex.quote(socket)))
    # Practice: its own tmux server (<socket>-practice), so nothing of it lives in the exam's server; `examctl open`
    # ends that server and the student's practice processes before an exam. The session is created once, with a
    # timer that ends it after 2 hours; reconnecting attaches to it. "=name" matches the name exactly.
    socket = socket + "-practice"
    t = "%s-L %s" % (conf, shlex.quote(socket))
    name = shlex.quote(session)
    kill = shlex.quote("sleep %d; tmux -L %s kill-session -t =%s" % (PRACTICE_MAX_S, shlex.quote(socket), session))
    return ("cd ~/%s 2>/dev/null || cd ~; unset TMUX; tmux %s has-session -t =%s 2>/dev/null || "
            "tmux %s new-session -d -s %s \\; run-shell -b %s; exec tmux %s attach-session -t =%s"
            % (shlex.quote(folder), t, name, t, name, kill, t, name))


# ── Recording ─────────────────────────────────────────────────

class Recorder:
    """asciicast v2: a JSON header line, then [seconds, "o"|"i"|"r"|"m", data] lines."""

    def __init__(self, user, cols, rows, cap, folder=None):
        folder = folder or common.rec_dir(user)
        folder.mkdir(parents=True, exist_ok=True, mode=0o750)
        self.t0 = time.time()
        name = "%d.cast" % int(self.t0)
        n = 1
        while (folder / name).exists():
            n += 1
            name = "%d-%d.cast" % (int(self.t0), n)
        self.name = name
        self.path = folder / name
        self.f = open(self.path, "w", encoding="utf-8")
        os.chmod(self.path, 0o640)
        self.cap = cap
        self.size = 0
        self.truncated = False
        self._line(json.dumps({"version": 2, "width": cols, "height": rows, "timestamp": int(self.t0),
                               "env": {"TERM": "xterm-256color"}, "title": user}))

    def _line(self, text):
        self.f.write(text + "\n")
        self.size += len(text) + 1

    def event(self, kind, data):
        if self.truncated or self.f is None:
            return
        line = json.dumps([round(time.time() - self.t0, 3), kind, data], ensure_ascii=False)
        if self.size + len(line) > self.cap:
            self._line(json.dumps([round(time.time() - self.t0, 3), "m", "output truncated"]))
            self.truncated = True
            self.f.flush()
            return
        self._line(line)

    def flush(self):
        if self.f:
            self.f.flush()

    def close(self):
        if self.f:
            self.f.close()
            self.f = None


class LineTracker:
    """An approximation of the last command line typed, for the board. Line editing and Tab make it approximate."""

    def __init__(self):
        self.buf = ""
        self.esc = False
        self.last = ""

    def feed(self, text):
        for ch in text:
            if self.esc:
                if ch.isalpha() or ch == "~":
                    self.esc = False
                continue
            if ch == "\x1b":
                self.esc = True
            elif ch in "\r\n":
                if self.buf.strip():
                    self.last = self.buf.strip()[:200]
                self.buf = ""
            elif ch in "\x7f\x08":
                self.buf = self.buf[:-1]
            elif ch in "\x03\x15":
                self.buf = ""
            elif ch >= " ":
                self.buf += ch
                if len(self.buf) > 400:
                    self.buf = self.buf[-400:]


# ── Sessions ──────────────────────────────────────────────────

class Gateway:
    def __init__(self, args):
        self.args = args
        self.sessions = {}      # (user, room) -> Session; room is "exam" or "practice"
        self.used = {}          # ticket nonce -> expiry
        self.lock = asyncio.Lock()
        self.locks = {}         # (user, room) -> lock state, shared by every connection of that student (lock.json)
        self.queue = []         # practice connections waiting for a free place, in order of arrival

    def backend(self):
        return LocalBackend(self.args) if self.args.backend == "local" else SSHBackend(self.args)

    def lock_of(self, user, exam_id, room="exam"):
        d = self.locks.get((user, room))
        if not d or d.get("exam") != exam_id:
            d = self.locks[(user, room)] = common.read_lock(user, exam_id, room)
        return d

    def save_lock(self, user, room="exam"):
        try:
            common.room_dir(user, room).mkdir(parents=True, exist_ok=True, mode=0o750)
            common.write_json_atomic(common.lock_path(user, room), self.locks[(user, room)], mode=0o640)
        except OSError as e:
            log.warning("lock %s: %s", user, e)

    def practice_count(self, but=None):
        """Practice shells (a quiz socket costs next to nothing and takes no place)."""
        return sum(1 for (u, room), s in self.sessions.items() if room == "practice" and u != but and not s.quiz)

    def take_ticket(self, ticket):
        try:
            data = common.read_ticket(ticket, key=self.args.ticket_key_bytes)
        except OSError:
            return None
        now = time.time()
        for nonce in [n for n, e in self.used.items() if e < now]:
            self.used.pop(nonce, None)
        if not data or data.get("n") in self.used:
            return None
        self.used[data["n"]] = float(data["e"]) + 1
        return data


class Session:
    def __init__(self, gw, ws, user, cfg, cols, rows, room="exam", scenario="", attempt=0, quiz=False):
        self.gw, self.ws, self.user, self.cfg = gw, ws, user, cfg
        self.cols, self.rows = cols, rows
        self.room, self.scenario, self.attempt = room, scenario, attempt
        self.quiz = bool(quiz)   # a practice session with no shell: lock, events and status only
        self.dir = common.room_dir(user, room)
        self.last_input = time.monotonic()
        self.backend = gw.backend()
        self.rec = None
        self.lines = LineTracker()
        self.decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.closing = None
        self.out_bytes = 0
        self.events_minute = []
        self.status_dirty = True
        self.bucket = float(gw.args.rate)
        self.bucket_t = time.monotonic()
        self.lockst = gw.lock_of(user, cfg["id"], room)

    def practice(self):
        return self.room == "practice"

    def room_open(self):
        if self.practice():
            return not common.exam_blocks_practice()
        return common.load_state(self.cfg)["phase"] == "open"

    def save_lock(self):
        self.gw.save_lock(self.user, self.room)

    # status.json and events.jsonl
    def status_path(self):
        return self.dir / "status.json"

    def write_status(self, connected):
        old = common.read_json(self.status_path(), {}) or {}
        now = time.time()
        st = {"user": self.user, "connected": connected, "last_seen": now,
              "since": old.get("since") if old.get("connected") and connected else (now if connected else old.get("since")),
              "connects": int(old.get("connects", 0)) + (1 if connected and not old.get("connected") else 0),
              "last_cmd": self.lines.last or old.get("last_cmd", ""),
              "cast": self.rec.name if self.rec else old.get("cast"),
              "truncated": bool(self.rec and self.rec.truncated) or bool(old.get("truncated")),
              "out_bytes": self.out_bytes, "exam": self.cfg["id"]}
        if self.practice():
            st.update(scenario=self.scenario, attempt=self.attempt)
            if self.quiz:
                st.update(kind="quiz")
        try:
            common.write_json_atomic(self.status_path(), st, mode=0o640)
        except OSError as e:
            log.warning("status %s: %s", self.user, e)
        self.status_dirty = False

    def event(self, kind, **fields):
        if self.practice():
            fields.setdefault("s", self.scenario)
        append_event(self.user, kind, folder=self.dir, **fields)

    async def send_json(self, obj):
        try:
            await self.ws.send(json.dumps(obj))
        except ConnectionClosed:
            pass

    async def bye(self, why, code=4000):
        if self.closing:
            return
        self.closing = why
        await self.send_json({"t": "bye", "why": why})
        try:
            await self.ws.close(code, why)
        except Exception:
            pass

    async def throttle(self, n):
        rate = float(self.gw.args.rate)
        now = time.monotonic()
        self.bucket = min(rate, self.bucket + (now - self.bucket_t) * rate)
        self.bucket_t = now
        self.bucket -= n
        if self.bucket < 0:
            await asyncio.sleep(-self.bucket / rate)

    async def pump_out(self):
        while True:
            data = await self.backend.read()
            if not data:
                self.event("shell_end")
                await self.send_json({"t": "note", "what": "shell_end"})
                return "shell_end"
            self.out_bytes += len(data)
            self.rec.event("o", self.decoder.decode(data))
            await self.throttle(len(data))
            await self.ws.send(data)

    async def pump_in(self):
        flags = self.cfg["flags"]
        async for msg in self.ws:
            if isinstance(msg, bytes):
                continue
            try:
                m = json.loads(msg)
            except ValueError:
                continue
            t = m.get("t") if isinstance(m, dict) else None
            if self.quiz and t in ("i", "r"):
                continue   # no shell behind a quiz socket
            if t == "i":
                d = m.get("d")
                if not isinstance(d, str) or not d or self.lockst["locked"]:
                    continue
                d = d[:65536]
                self.last_input = time.monotonic()
                self.rec.event("i", d)
                self.lines.feed(d)
                self.status_dirty = True
                if len(d) > flags["large_paste_chars"]:
                    self.event("big_input", n=len(d))
                self.backend.write(d.encode("utf-8", "replace"))
            elif t == "r":
                try:
                    cols = max(20, min(400, int(m.get("cols"))))
                    rows = max(5, min(200, int(m.get("rows"))))
                except (TypeError, ValueError):
                    continue
                if (cols, rows) != (self.cols, self.rows):
                    self.cols, self.rows = cols, rows
                    self.backend.resize(cols, rows)
                    self.rec.event("r", "%dx%d" % (cols, rows))
            elif t == "e":
                await self.page_event(m)
            elif t == "unlock":
                await self.try_unlock(m.get("code"))
            elif t == "ping":
                await self.send_json({"t": "pong", "now": time.time()})
        return "closed"

    async def page_event(self, m):
        kind = m.get("k")
        if kind not in EVENT_KINDS:
            return
        now = time.time()
        self.events_minute = [x for x in self.events_minute if x > now - 60]
        if len(self.events_minute) >= MAX_EVENTS_PER_MIN:
            return
        self.events_minute.append(now)
        fields = {}
        for key in ("n", "away_ms", "queued_ms"):
            if isinstance(m.get(key), (int, float)):
                fields[key] = int(max(0, min(m[key], 10 ** 9)))
        for key in ("why", "detail"):
            if isinstance(m.get(key), str):
                fields[key] = m[key][:60]
        if isinstance(m.get("cts"), (int, float)):
            fields["cts"] = round(float(m["cts"]) / 1000.0, 3)  # the page's clock, for events sent late
        self.event(kind, **fields)
        on = self.cfg["lock"]["on"]
        if kind == "start":
            st = {"start": "%s@%d" % (self.scenario, self.attempt)} if self.practice() else common.load_state(self.cfg)
            self.sync_opening(st)
            d = self.lockst
            # A reload after the time was up (the exam was then extended) is expected, not a way around the lock: the
            # end the student saw at their last start has passed.
            try:
                time_was_up = bool(d.get("end_seen")) and time.time() >= common.parse_iso(d["end_seen"])
            except ValueError:
                time_was_up = False
            restart = d["started"] and "fs_exit" in on and not time_was_up
            d.update(started=True, end_seen=st.get("end"))
            self.save_lock()
            if restart:
                await self.set_lock("restart")  # a reload or a second tab: the page left fullscreen without saying so
        elif kind == "stop" and self.practice():
            # Practice: the student left through "back to the map", a proper exit, so their next start is not a reload.
            self.lockst.update(started=False)
            self.save_lock()
        elif kind == "fs_exit" and "fs_exit" in on:
            await self.set_lock("fs_refused" if fields.get("why") == "refused" else "fs_exit")
        elif kind == "panel_open" and "panel" in on:
            await self.set_lock("panel")
        elif kind == "leave" and "leave" in on:
            await self.set_lock("leave")

    # exam lock
    def sync_opening(self, st):
        """Opened again after a close: a new opening starts with no lock and not started (the code count goes on).
        Practice: an opening is one attempt of one scenario. Moving to another one keeps a running wait, so opening
        another scenario is no way around it."""
        d = self.lockst
        if self.practice():
            if d.get("opening") != st.get("start"):
                d.update(opening=st.get("start"), started=False, end_seen=None)
                self.save_lock()
            return
        if d.get("opening") != st.get("start"):
            d.update(opening=st.get("start"), started=False, locked=False, since=None, why="", total_s=0.0, bad=[], end_seen=None,
                     until=None)
            self.save_lock()

    def lock_msg(self, bad=None):
        d = self.lockst
        m = {"t": "lock", "why": d["why"], "mode": d.get("mode") or "code"}
        if m["mode"] == "wait":
            m["left"] = common.lock_left(d)
        if bad:
            m["bad"] = bad
        return m

    async def set_lock(self, why):
        d = self.lockst
        if d["locked"] or not self.room_open():
            return
        now = time.time()
        mode = self.cfg["lock"].get("mode") or "code"
        d.update(locked=True, n=int(d["n"]) + 1, since=now, why=why, bad=[], mode=mode, until=None)
        fields = {"why": why}
        if mode == "wait":
            today = time.strftime("%Y-%m-%d", time.localtime(now))
            if d.get("day") != today:
                d.update(day=today, day_n=0)
            d["day_n"] = int(d.get("day_n") or 0) + 1
            wait = common.wait_seconds(self.cfg, d["day_n"])
            d["until"] = now + wait
            fields.update(mode="wait", wait_s=wait)
        self.save_lock()
        self.event("lock", **fields)
        await self.send_json(self.lock_msg())

    async def release(self, how=None):
        d = self.lockst
        now = time.time()
        d.update(locked=False, total_s=round(float(d["total_s"] or 0) + now - float(d["since"] or now), 1), since=None, bad=[],
                 until=None)
        self.save_lock()
        if how:
            self.event("unlock", how=how)
        else:
            self.event("unlock")
        await self.send_json({"t": "unlocked"})

    async def try_unlock(self, code):
        d = self.lockst
        if not d["locked"]:
            await self.send_json({"t": "unlocked"})
            return
        if d.get("mode") == "wait":
            # No code: the page asks when its countdown ends, from the click that goes back to fullscreen.
            if common.lock_left(d) <= 0:
                await self.release("wait")
            else:
                await self.send_json(self.lock_msg("early"))
            return
        now = time.time()
        d["bad"] = [x for x in d.get("bad") or [] if x > now - 60]
        if len(d["bad"]) >= int(self.cfg["lock"]["max_attempts"]):
            await self.send_json(self.lock_msg("wait"))
            return
        code = re.sub(r"\D", "", str(code or ""))[:12]  # "48 27" works too; the code is never written anywhere
        want = common.unlock_code(self.user, self.cfg["id"], d["n"], key=self.gw.args.ticket_key_bytes)
        if code and hmac.compare_digest(code, want):
            await self.release()
        else:
            d["bad"].append(now)
            self.save_lock()
            self.event("unlock_bad")
            await self.send_json(self.lock_msg("wrong"))

    async def tick(self):
        last_state = last_status = time.time()
        while True:
            await asyncio.sleep(1.0)
            if time.time() - last_status >= STATUS_EVERY:  # also refreshes last_seen when nothing was typed
                last_status = time.time()
                if self.rec:
                    self.rec.flush()
                self.write_status(True)
            if self.practice() and not self.quiz:   # a quiz is read and clicked, not typed: no idle limit
                idle = time.monotonic() - self.last_input
                if idle > 60 * int(self.cfg.get("idle_min") or 15):
                    return "idle"
            if time.time() - last_state >= STATE_EVERY:
                last_state = time.time()
                if self.practice():
                    cfg = common.load_practice()
                    if not cfg or common.exam_blocks_practice():
                        return "exam"
                    self.cfg = cfg
                    continue
                cfg = common.load_config()
                if not cfg or cfg["id"] != self.cfg["id"] or common.load_state(cfg)["phase"] != "open":
                    return "ended"
                self.cfg = cfg  # settings changed on the instructor board (lock, flags) apply within 10 s

    async def run(self):
        if self.quiz:
            folder = tmux_name = ""   # no shell, no recording (so nothing else makes the folder for status and events)
            try:
                self.dir.mkdir(parents=True, exist_ok=True, mode=0o750)
            except OSError as e:
                log.warning("quiz folder %s: %s", self.user, e)
        elif self.practice():
            folder, tmux_name = "practice/" + self.scenario, "practice-" + self.scenario
            self.rec = Recorder(self.user, self.cols, self.rows, self.gw.args.rec_cap, folder=self.dir / self.scenario)
        else:
            folder, tmux_name = self.cfg.get("folder", "midterm"), "exam"
            self.rec = Recorder(self.user, self.cols, self.rows, self.gw.args.rec_cap)
        if not self.quiz:
            try:
                await self.backend.open(self.user, self.cols, self.rows, folder, tmux_name)
            except Exception as e:  # SSH refused, key missing, account locked
                log.warning("open %s: %s", self.user, e)
                self.event("open_failed", detail=str(e)[:60])
                self.rec.close()
                await self.bye("unavailable", 4002)
                return
        self.event("connect", cols=self.cols, rows=self.rows)
        self.write_status(True)
        await self.send_json({"t": "hello", "user": self.user, "cast": self.rec.name if self.rec else ""})
        if not self.practice():
            self.sync_opening(common.load_state(self.cfg))
        if self.lockst["locked"]:
            await self.send_json(self.lock_msg())
        coros = (self.pump_in(), self.tick()) if self.quiz else (self.pump_out(), self.pump_in(), self.tick())
        tasks = [asyncio.ensure_future(c) for c in coros]
        why = "closed"
        try:
            done, _pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for t in done:
                try:
                    why = t.result() or why
                except ConnectionClosed:
                    why = "closed"
                except Exception as e:
                    log.warning("session %s: %r", self.user, e)
                    why = "error"
        finally:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if why == "ended":
                await self.bye("ended", 4003)
            elif why in ("exam", "idle"):
                await self.bye(why, 4003)
            elif why == "shell_end":
                await self.bye("shell_end", 4004)
            if not self.quiz:
                await self.backend.close()
            if self.rec:
                self.rec.close()
            if self.closing != "replaced":
                self.event("disconnect", why=why)
                self.write_status(False)


async def handler(gw, ws):
    peer = getattr(ws, "remote_address", None)
    try:
        first = await asyncio.wait_for(ws.recv(), 10)
        m = json.loads(first)
        if not isinstance(m, dict) or m.get("t") != "auth":
            raise ValueError("auth first")
    except (asyncio.TimeoutError, ValueError, ConnectionClosed):
        await ws.close(4400, "auth required")
        return
    data = gw.take_ticket(str(m.get("ticket", "")))
    if data and data.get("x") == common.PRACTICE_ID:
        await practice_handler(gw, ws, m, data, peer)
        return
    cfg = common.load_config()
    if not data or not cfg or data.get("x") != cfg["id"]:
        log.info("refused ticket from %s", peer)
        await ws.send(json.dumps({"t": "bye", "why": "ticket"}))
        await ws.close(4401, "ticket")
        return
    if common.load_state(cfg)["phase"] != "open":
        await ws.send(json.dumps({"t": "bye", "why": "ended"}))
        await ws.close(4003, "not open")
        return
    user = data["u"]
    cols, rows = term_size(m)
    await run_session(gw, Session(gw, ws, user, cfg, cols, rows), peer)


def term_size(m):
    try:
        return max(20, min(400, int(m.get("cols", 100)))), max(5, min(200, int(m.get("rows", 30))))
    except (TypeError, ValueError):
        return 100, 30


async def run_session(gw, sess, peer):
    key = (sess.user, sess.room)
    async with gw.lock:
        old = gw.sessions.get(key)
        gw.sessions[key] = sess
    if old:
        old.event("replaced")
        await old.bye("replaced", 4001)
    log.info("open %s %s from %s (%dx%d)", sess.user, sess.room + (":" + sess.scenario if sess.scenario else ""),
             peer, sess.cols, sess.rows)
    try:
        await sess.run()
    finally:
        async with gw.lock:
            if gw.sessions.get(key) is sess:
                gw.sessions.pop(key, None)
        log.info("close %s (%s)", sess.user, sess.closing or "closed")


async def practice_handler(gw, ws, m, data, peer):
    """A practice ticket: open while no exam runs, at most max_sessions at once (the others queue)."""
    cfg = common.load_practice()
    scenario = str(data.get("s", ""))
    try:
        attempt = max(0, min(10 ** 6, int(data.get("a", 0))))
    except (TypeError, ValueError):
        attempt = 0
    if not cfg or not common.SCENARIO_RE.match(scenario):
        await ws.send(json.dumps({"t": "bye", "why": "ticket"}))
        await ws.close(4401, "ticket")
        return
    if common.exam_blocks_practice():
        await ws.send(json.dumps({"t": "bye", "why": "exam"}))
        await ws.close(4003, "exam")
        return
    user = data["u"]
    cols, rows = term_size(m)
    if data.get("k") == "quiz":   # no shell: no place in the queue either
        await run_session(gw, Session(gw, ws, user, cfg, cols, rows, "practice", scenario, attempt, quiz=True), peer)
        return
    cap = int(cfg.get("max_sessions") or 20)
    gw.queue.append(ws)
    try:
        while True:
            ahead = gw.queue.index(ws)
            if (user, "practice") in gw.sessions or gw.practice_count(but=user) + ahead < cap:
                break  # a reconnect takes its own place back; otherwise wait for the ones ahead
            await ws.send(json.dumps({"t": "queue", "pos": ahead + 1, "cap": cap}))
            try:
                await asyncio.wait_for(ws.recv(), 3)  # anything the page sends while waiting is ignored
            except asyncio.TimeoutError:
                pass
            if common.exam_blocks_practice():
                await ws.send(json.dumps({"t": "bye", "why": "exam"}))
                await ws.close(4003, "exam")
                return
    except ConnectionClosed:
        return
    finally:
        if ws in gw.queue:
            gw.queue.remove(ws)
    await run_session(gw, Session(gw, ws, user, cfg, cols, rows, "practice", scenario, attempt), peer)


def health(connection, request):
    if request.path.rstrip("/").endswith("/health"):
        return connection.respond(200, "ok\n")
    return None


async def control_loop(gw):
    """Unlock requests from the instructor board: the API drops control/<user>.json (no network endpoint needed)."""
    while True:
        await asyncio.sleep(1.0)
        try:
            names = os.listdir(common.control_dir())
        except OSError:
            continue
        for name in names:
            path = common.control_dir() / name
            user = name[:-5] if name.endswith(".json") else ""
            req = None
            if common.USER_RE.match(user) and os.path.isfile(path) and not os.path.islink(path) and os.path.getsize(path) < 4096:
                req = common.read_json(path)
            if not name.startswith("."):
                try:
                    os.unlink(path)
                except OSError:
                    continue
            if not isinstance(req, dict) or req.get("action") != "unlock":
                continue
            room = "practice" if req.get("room") == "practice" else "exam"
            cfg = common.load_practice() if room == "practice" else common.load_config()
            if not cfg:
                continue
            d = gw.lock_of(user, cfg["id"], room)
            if not d["locked"]:
                continue
            now = time.time()
            d.update(locked=False, total_s=round(float(d["total_s"] or 0) + now - float(d["since"] or now), 1), since=None, bad=[],
                     until=None)
            gw.save_lock(user, room)
            append_event(user, "unlock", folder=common.room_dir(user, room), how="instructor", by=str(req.get("by", ""))[:40])
            sess = gw.sessions.get((user, room))
            if sess:
                await sess.send_json({"t": "unlocked"})
            log.info("unlocked %s by %s", user, req.get("by"))


PRACTICE_KEEP_DAYS = 14


def prune_practice(days=PRACTICE_KEEP_DAYS):
    """Practice recordings are kept 14 days (the exam's are never removed here)."""
    cutoff = time.time() - days * 86400
    n = 0
    for cast in common.rec_dir().glob("*/practice/*/*.cast"):
        try:
            if cast.stat().st_mtime < cutoff and not cast.is_symlink():
                cast.unlink()
                n += 1
        except OSError:
            continue
    if n:
        log.info("removed %d practice recordings older than %d days", n, days)
    return n


async def prune_loop():
    while True:
        try:
            prune_practice()
        except Exception as e:  # pragma: no cover
            log.warning("prune: %r", e)
        await asyncio.sleep(3600)


async def main_async(args):
    gw = Gateway(args)
    asyncio.ensure_future(control_loop(gw))
    asyncio.ensure_future(prune_loop())
    stop = asyncio.get_running_loop().create_future()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            asyncio.get_running_loop().add_signal_handler(sig, stop.set_result, None)
        except (NotImplementedError, RuntimeError):
            pass
    origins = args.origin or None
    async with serve(lambda ws: handler(gw, ws), args.host, args.port, ping_interval=20, ping_timeout=30,
                     max_size=1 << 20, origins=origins, process_request=health):
        log.info("gateway on %s:%d, backend %s", args.host, args.port, args.backend)
        await stop


def parse_args(argv=None):
    etc = common.etc_dir()
    p = argparse.ArgumentParser(description="Exam room terminal gateway")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5010)
    p.add_argument("--backend", choices=("ssh", "local"), default="ssh")
    p.add_argument("--dev", action="store_true", help="required with --backend local")
    p.add_argument("--ssh-host", default="127.0.0.1")
    p.add_argument("--ssh-port", type=int, default=22)
    p.add_argument("--key", default=str(etc / "gateway_ed25519"))
    p.add_argument("--known-hosts", default=str(etc / "known_hosts"))
    p.add_argument("--tmux-conf", default=str(_HERE / "tmux.conf"))
    p.add_argument("--tmux-socket", default="itcexam")
    p.add_argument("--rec-cap", type=int, default=20 * 1024 * 1024, help="bytes per recording")
    p.add_argument("--rate", type=int, default=256 * 1024, help="output bytes per second to one browser")
    p.add_argument("--origin", action="append", default=[], help="allowed page origin (repeat); default any")
    args = p.parse_args(argv)
    if args.backend == "local" and not (args.dev and args.host in ("127.0.0.1", "localhost", "::1")):
        p.error("--backend local needs --dev and a localhost --host")
    return args


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    args = parse_args(argv)
    args.ticket_key_bytes = common.ticket_key()
    os.umask(0o027)
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
