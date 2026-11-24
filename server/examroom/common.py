"""Shared pieces of the exam room: paths, the exam config and state, and the signed terminal tickets.

Used by the API (app/server/app.py), the gateway (gateway.py) and the admin tool (examctl.py).
Python 3.8 or later, standard library only.

Layout on the server (both roots can be moved with environment variables, which the tests do):

    /etc/itc-os-exam/                ITC_EXAM_ETC
        exam.json                    the exam config (root, 0644), see exam.example.json
        ticket.key                   HMAC key for terminal tickets (root:itc-exam, 0640)
        gateway_ed25519[.pub]        the gateway's SSH key (examgw, 0600)
        known_hosts                  this server's host keys, as 127.0.0.1
    /srv/exam/                       ITC_EXAM_VAR
        <exam id>/state.json         phase, start and end (written by examctl only)
        <exam id>/collect/<user>/    the snapshot taken at close: the submission
        rec/<user>/<start>.cast      asciicast v2 recordings (gateway)
        rec/<user>/events.jsonl      proctoring events (gateway)
        rec/<user>/status.json       live connection status (gateway)
        rec/<user>/lock.json         the exam lock of one student (gateway)
        rec/<user>/practice/         the practice room: events.jsonl, status.json, lock.json, <scenario>/<start>.cast
        requests/, control/          the control panel's requests (see the end of this file)
    /srv/practice/                   ITC_PRACTICE_VAR, the practice room's data (the API; see server/practice/)
        settings.json                the instructor's practice settings (lock, waits, session cap)

The practice room ("Practice Linux Commands") uses the same gateway and tickets. Its tickets name the room
(x = "practice", s = the scenario, a = the attempt); it is open whenever no exam is running.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PPH = timezone(timedelta(hours=7))
USER_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
EXAM_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
CAST_RE = re.compile(r"^\d{10}(-\d+)?\.cast$")
TICKET_TTL = 60  # seconds; the page asks for a new ticket for every connection

DEFAULT_FLAGS = {
    "review_away_s": 60,       # more than this in total away from the page: review
    "high_away_s": 300,        # more than this: high
    "large_paste_chars": 200,  # a paste longer than this is a "large paste"
    "high_pastes": 3,          # this many large pastes: high
    "high_offline_s": 120,     # offline this long while the exam is open: high
    "second_screen": "review", # a second screen connected (Chrome and Edge report it): "review", "high" or ""
    "side_panel": "review",    # the page got narrower inside the same window (a side panel or developer tools)
}


def etc_dir():
    return Path(os.environ.get("ITC_EXAM_ETC", "/etc/itc-os-exam"))


def var_dir():
    return Path(os.environ.get("ITC_EXAM_VAR", "/srv/exam"))


def rec_dir(user=None):
    base = var_dir() / "rec"
    return base / user if user else base


def room_dir(user, room="exam"):
    """Where the gateway keeps one student's events, status and lock for a room. The exam's stay where they always
    were; practice has its own folder, so practice never shows up on the exam board."""
    return rec_dir(user) if room == "exam" else rec_dir(user) / "practice"


def now_ts():
    return time.time()


def iso(ts):
    return datetime.fromtimestamp(ts, PPH).isoformat(timespec="seconds")


def parse_iso(text):
    return datetime.fromisoformat(text).timestamp()


def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json_atomic(path, data, mode=0o644):
    path = Path(path)
    tmp = path.with_name(".%s.%s.tmp" % (path.name, secrets.token_hex(4)))
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")
    os.chmod(tmp, mode)
    os.replace(tmp, path)


# ── Exam config and state ─────────────────────────────────────

def load_config():
    """The exam config, with defaults filled in, or None when no exam is configured."""
    cfg = read_json(etc_dir() / "exam.json")
    if not isinstance(cfg, dict) or not EXAM_ID_RE.match(str(cfg.get("id", ""))) or cfg.get("id") == "practice":
        return None  # "practice" is the practice room's ticket id
    cfg.setdefault("kind", "midterm")
    cfg.setdefault("title", "Exam")
    cfg.setdefault("duration_min", 60)
    cfg.setdefault("parts", ["A", "B", "C", "D"])
    cfg.setdefault("folder", "midterm")
    cfg.setdefault("show_progress", "presence")
    cfg.setdefault("rain", False)
    cfg.setdefault("gateway_url", "")
    seb = cfg.setdefault("seb", {})
    seb.setdefault("required", False)
    seb.setdefault("config_keys", [])
    seb.setdefault("public_api", "")
    flags = dict(DEFAULT_FLAGS)
    flags.update(cfg.get("flags") or {})
    cfg["flags"] = flags
    lock = cfg.get("lock") if isinstance(cfg.get("lock"), dict) else {}
    lock["on"] = [x for x in (lock.get("on") or []) if x in LOCK_TRIGGERS]
    lock.setdefault("max_attempts", 3)  # wrong codes per minute; with 4 digits, guessing stays under 2% in an hour
    if lock.get("mode") not in LOCK_MODES:
        lock["mode"] = "code"
    lock.setdefault("wait_s", 30)       # wait mode: the first wait; it doubles each time that day, up to wait_max_s
    lock.setdefault("wait_max_s", 300)
    cfg["lock"] = lock
    if cfg.get("profile") not in PROFILES:
        cfg["profile"] = "custom" if cfg.get("profile") else "exam"
    return cfg


def state_path(cfg):
    return var_dir() / cfg["id"] / "state.json"


def load_state(cfg):
    """Phase is sealed, open or closed. An open exam whose end has passed counts as closed for students."""
    st = read_json(state_path(cfg), {}) or {}
    phase = st.get("phase", "sealed")
    if phase not in ("sealed", "open", "closed"):
        phase = "sealed"
    out = {"phase": phase, "start": st.get("start"), "end": st.get("end"),
           "extended_min": st.get("extended_min", 0), "closed_at": st.get("closed_at")}
    if phase == "open" and out["end"]:
        try:
            if now_ts() >= parse_iso(out["end"]):
                out["phase"] = "ended"  # time is up; examctl close takes the snapshot
        except ValueError:
            pass
    return out


# ── Tickets ───────────────────────────────────────────────────

def _b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def ticket_key():
    with open(etc_dir() / "ticket.key", "rb") as f:
        key = f.read().strip()
    if len(key) < 32:
        raise ValueError("ticket.key is too short")
    return key


def make_ticket(user, exam_id, key=None, ttl=TICKET_TTL, extra=None):
    """extra: more signed fields; a practice ticket has x = "practice", s = the scenario and a = the attempt."""
    if not USER_RE.match(user):
        raise ValueError("bad user")
    data = {"u": user, "x": exam_id, "e": int(now_ts()) + ttl, "n": secrets.token_urlsafe(12)}
    data.update({k: v for k, v in (extra or {}).items() if k not in data})
    payload = json.dumps(data, separators=(",", ":")).encode()
    body = _b64(payload)
    sig = hmac.new(key or ticket_key(), body.encode("ascii"), hashlib.sha256).digest()
    return body + "." + _b64(sig)


def read_ticket(ticket, key=None):
    """The ticket's fields if the signature is good and it has not expired, else None. Single use is the caller's job."""
    try:
        body, sig = ticket.split(".", 1)
        want = hmac.new(key or ticket_key(), body.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(want, _unb64(sig)):
            return None
        data = json.loads(_unb64(body))
        if not isinstance(data, dict) or not USER_RE.match(str(data.get("u", ""))):
            return None
        if int(data.get("e", 0)) < now_ts():
            return None
        return data
    except (ValueError, TypeError, OSError):
        return None


# ── Exam lock (unlock code from the invigilator) ─────────────
#
# When the page reports a trigger (by default none; the example config locks on leaving fullscreen), the gateway locks
# the student: typed input is dropped and the page hides the paper and the terminal until the student types the
# unlock code the instructor board shows. The state is one small file per student, written only by the gateway.

LOCK_TRIGGERS = {"fs_exit", "panel", "leave"}  # with fs_exit, starting the exam a second time (reload) locks too
# code: the invigilator gives a 4-digit code (exams). wait: the room unlocks by itself after a countdown that doubles
# each time the student leaves again that day (practice, where nobody hands out codes).
LOCK_MODES = ("code", "wait")


def lock_path(user, room="exam"):
    return room_dir(user, room) / "lock.json"


def read_lock(user, exam_id, room="exam"):
    d = read_json(lock_path(user, room), {}) or {}
    if not isinstance(d, dict) or d.get("exam") != exam_id:
        d = {}
    out = {"exam": exam_id, "locked": False, "n": 0, "since": None, "why": "", "total_s": 0.0, "bad": [], "started": False,
           "opening": None, "end_seen": None, "mode": "code", "until": None, "day": "", "day_n": 0}
    out.update({k: d[k] for k in out if k in d and k != "exam"})
    return out


def current_lock(user, cfg, state):
    """The student's lock for this opening of the exam: a lock left from an earlier opening (closed, then opened
    again) does not count; the gateway clears it when the student comes back."""
    d = read_lock(user, cfg["id"])
    if d.get("opening") and d["opening"] != state.get("start"):
        d.update(locked=False, since=None, why="", total_s=0.0, bad=[], started=False, until=None)
    return d


def wait_seconds(cfg, day_n):
    """How long the day_n-th lock of the day lasts in wait mode: the first wait, doubled each time, up to the cap."""
    first = max(1, int(cfg["lock"].get("wait_s") or 30))
    cap = max(first, int(cfg["lock"].get("wait_max_s") or 300))
    return min(cap, first * 2 ** max(0, min(int(day_n) - 1, 20)))


def lock_left(lock):
    """Seconds left before a wait-mode lock lets the student continue (0 for a code lock or no lock)."""
    if not lock.get("locked") or lock.get("mode") != "wait" or not lock.get("until"):
        return 0
    return max(0, int(round(float(lock["until"]) - now_ts())))


def lock_seconds(lock):
    """Time spent locked so far, including a lock that is still on."""
    s = float(lock.get("total_s") or 0)
    if lock.get("locked") and lock.get("since"):
        s += max(0.0, now_ts() - float(lock["since"]))
    return s


def unlock_code(user, exam_id, n, key=None):
    """Four digits, different for every student and every lock, known only to holders of the ticket key."""
    msg = ("unlock|%s|%s|%d" % (exam_id, user, int(n))).encode("utf-8")
    digest = hmac.new(key or ticket_key(), msg, hashlib.sha256).digest()
    return "%04d" % (int.from_bytes(digest[:8], "big") % 10000)


# ── Safe Exam Browser ─────────────────────────────────────────

def seb_ok(cfg, url, header_value):
    """True when SEB is not required, or the Config Key hash header matches one of the configured keys.

    SEB sends X-SafeExamBrowser-ConfigKeyHash = SHA-256 of (the absolute request URL + the Config Key).
    `url` must be the URL as the browser asked for it (the public address, not the tunnel's local one).
    """
    seb = cfg.get("seb") or {}
    if not seb.get("required"):
        return True
    if not header_value:
        return False
    for key in seb.get("config_keys") or []:
        want = hashlib.sha256((url + key).encode("utf-8")).hexdigest()
        if hmac.compare_digest(want, header_value.strip().lower()):
            return True
    return False


# ── Proctoring summary (used by the API board) ────────────────

def read_events(user, limit_bytes=2_000_000):
    path = rec_dir(user) / "events.jsonl"
    out = []
    try:
        with open(path, "rb") as f:
            data = f.read(limit_bytes)
    except OSError:
        return out
    for line in data.splitlines():
        try:
            ev = json.loads(line)
            if isinstance(ev, dict):
                out.append(ev)
        except ValueError:
            continue
    return out


def summarize(events, status, cfg, state):
    """Counts and the flag for one student. The flag is a reason to look at the replay, never a mark."""
    flags = cfg["flags"]
    away_n, away_ms, pastes, big_paste, big_input, fs_exits = 0, 0, 0, 0, 0, 0
    away_since = None
    screens = "unknown"  # "extended" once the page has seen a second screen, "single" if it saw only one
    panel_n, panel_ms, panel_since = 0, 0, None
    wrong_codes = 0
    for ev in events:
        k = ev.get("k")
        if k == "screens":
            d = ev.get("detail")
            if d == "extended" or (d == "single" and screens == "unknown"):
                screens = d
        elif k == "panel_open":
            panel_n += 1
            panel_since = ev.get("ts")
        elif k == "panel_close":
            panel_ms += max(0, int(ev.get("away_ms") or 0))
            panel_since = None
        elif k == "unlock_bad":
            wrong_codes += 1
        if k == "leave":
            away_since = ev.get("ts")
        elif k == "back":
            away_n += 1
            away_ms += max(0, int(ev.get("away_ms") or 0))
            away_since = None
        elif k == "paste":
            pastes += 1
            if int(ev.get("n") or 0) > flags["large_paste_chars"]:
                big_paste += 1
        elif k == "big_input":
            big_input += 1
        elif k == "fs_exit":
            fs_exits += 1
    # One paste is usually seen twice: by the page (paste) and by the gateway (a long input). Count the larger.
    big = max(big_paste, big_input)
    now = now_ts()
    away_now = 0
    if away_since and status.get("connected"):
        away_now = max(0, now - float(away_since))
    total_away = away_ms / 1000.0 + away_now
    panel_s = panel_ms / 1000.0 + (max(0, now - float(panel_since)) if panel_since and status.get("connected") else 0)
    offline_s = 0
    if state.get("phase") == "open" and not status.get("connected") and status.get("last_seen"):
        offline_s = max(0, now - float(status["last_seen"]))
    extra = [flags.get("second_screen") if screens == "extended" else "", flags.get("side_panel") if panel_n else ""]
    level = ""
    if total_away > flags["high_away_s"] or big >= flags["high_pastes"] or offline_s > flags["high_offline_s"] or "high" in extra:
        level = "high"
    elif total_away > flags["review_away_s"] or big >= 1 or "review" in extra:
        level = "review"
    return {"away_n": away_n, "away_s": round(total_away), "away_now": bool(away_since), "pastes": pastes,
            "large_pastes": big, "fs_exits": fs_exits, "offline_s": round(offline_s), "screens": screens,
            "panel_n": panel_n, "panel_s": round(panel_s), "panel_now": bool(panel_since), "wrong_codes": wrong_codes,
            "flag": level}


# ── Control panel: settings, requests to the root helper, unlock requests to the gateway ─────
#
# The instructor board can change settings and ask for open / extend / close / harden. The API (not root) only
# validates a request and drops it in requests/queue/; `examctl agent` (root, started by a systemd path unit, and only
# when installed with --web-control) validates it again, runs it, and writes the result in requests/done/.
# Unlocking a student does not need root: the API drops control/<user>.json and the gateway picks it up.
#
#     /etc/itc-os-exam/agent.json      {"roster": "<path>"} (root, 0640): web control is on when this file exists
#     /srv/exam/requests/{tmp,queue,work,done}/<id>.json   (root:itc-exam, 2770)
#     /srv/exam/control/<user>.json    {"action": "unlock", "by": ..} (root:itc-exam, 2770)

LEVELS = ("review", "high", "")
PROFILES = ("exam", "practice", "custom")  # custom: a preset was applied, then a setting changed by hand

# setting -> (kind, bounds or choices, may change while the exam is open)
SETTINGS = {
    "lock.on": ("subset", tuple(sorted(LOCK_TRIGGERS)), True),
    "lock.max_attempts": ("int", (1, 10), True),
    "lock.mode": ("choice", LOCK_MODES, True),
    "lock.wait_s": ("int", (5, 600), True),
    "lock.wait_max_s": ("int", (10, 1800), True),
    "profile": ("choice", PROFILES, True),
    "flags.second_screen": ("choice", LEVELS, True),
    "flags.side_panel": ("choice", LEVELS, True),
    "flags.review_away_s": ("int", (10, 3600), True),
    "flags.high_away_s": ("int", (30, 7200), True),
    "flags.large_paste_chars": ("int", (50, 5000), True),
    "flags.high_pastes": ("int", (1, 20), True),
    "flags.high_offline_s": ("int", (30, 3600), True),
    "rain": ("bool", None, True),
    "seb.required": ("bool", None, False),   # on while students are in: everyone would be cut off
    "title": ("text", 80, False),
    "duration_min": ("int", (10, 300), False),  # once open, use extend
    # the scenario bank (the instructor's exam bank plan): none of these can change once the exam has drawn (checked in clean_request)
    "bank.mode": ("choice", ("balanced", "random"), False),
    "bank.seed": ("text", 40, False),
    "bank.disabled": ("ids", 40, False),
    "bank.pins": ("pins", 400, False),
}

# The two presets on the board's Settings tab. Exam is the strict room as built for the midterm; practice keeps the
# room locked (no AI) but a student who leaves waits instead of asking for a code.
PRESETS = {
    "exam": {"profile": "exam", "lock.on": ["fs_exit"], "lock.mode": "code", "lock.max_attempts": 3,
             "lock.wait_s": 30, "lock.wait_max_s": 300,
             "flags.second_screen": "review", "flags.side_panel": "review"},
    "practice": {"profile": "practice", "lock.on": ["fs_exit", "panel"], "lock.mode": "wait", "lock.max_attempts": 3,
                 "lock.wait_s": 30, "lock.wait_max_s": 300,
                 "flags.second_screen": "review", "flags.side_panel": "review"},
}

ACTIONS = {
    "open": {"minutes": (5, 300)},
    "extend": {"minutes": (1, 120)},
    "close": {},
    "harden_on": {"kick": "bool"},
    "harden_off": {},
    "prepare": {},
    "settings": {"changes": "settings"},
    # the scenario bank: write every student's draw now (what Open does anyway), take the draw back before the exam was ever
    # opened, and a regrade of one slot of one scenario
    "draw": {},
    "undraw": {},
    "correct": {"scenario": "ident", "slot": "slot", "mode": ("give", "ignore", "clear"), "reason": "reason"},
}
IDENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,40}$")
SLOT_RE = re.compile(r"^[A-Z][1-9]$")
PART_RE = re.compile(r"^[A-Z]$")
REQ_FILE_RE = re.compile(r"^[0-9a-f]{16}\.json$")
REQ_MAX_BYTES = 16384


def _get(d, dotted):
    for part in dotted.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(part)
    return d


def settings_view(cfg):
    return {k: _get(cfg, k) for k in SETTINGS}


def exam_running(state):
    return state.get("phase") in ("open", "ended")


def clean_settings(changes, running, table=None):
    """The validated changes, or ValueError naming the first bad one."""
    table = SETTINGS if table is None else table
    if not isinstance(changes, dict) or not changes or len(changes) > len(table):
        raise ValueError("no settings to change")
    out = {}
    for key, value in changes.items():
        if key not in table:
            raise ValueError("unknown setting %s" % key)
        kind, extra, live = table[key]
        if running and not live:
            raise ValueError("%s cannot change while the exam is open" % key)
        if kind == "bool":
            ok = isinstance(value, bool)
        elif kind == "int":
            ok = isinstance(value, int) and not isinstance(value, bool) and extra[0] <= value <= extra[1]
        elif kind == "choice":
            ok = value in extra
        elif kind == "ids":
            ok = (isinstance(value, list) and len(value) <= extra and all(isinstance(x, str) and IDENT_RE.match(x) for x in value))
            value = sorted(set(value)) if ok else value
        elif kind == "pins":
            ok = isinstance(value, dict) and len(value) <= extra and all(
                USER_RE.match(str(u)) and isinstance(per, dict) and len(per) <= 8 and
                all(PART_RE.match(str(pt)) and isinstance(sid, str) and IDENT_RE.match(sid) for pt, sid in per.items())
                for u, per in value.items())
        elif kind == "subset":
            ok = isinstance(value, list) and all(isinstance(x, str) and x in extra for x in value)
            value = sorted(set(value)) if ok else value
        else:  # text
            ok = isinstance(value, str) and 0 < len(value.strip()) <= extra and "\n" not in value
            value = value.strip() if ok else value
        if not ok:
            raise ValueError("bad value for %s" % key)
        out[key] = value
    return out


def apply_settings(raw, changes):
    for key, value in changes.items():
        d = raw
        parts = key.split(".")
        for part in parts[:-1]:
            if not isinstance(d.get(part), dict):
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
    return raw


def clean_request(action, params, running):
    """Validated parameters for one control action, or ValueError. Only names and small numbers get through."""
    if action not in ACTIONS:
        raise ValueError("unknown action")
    params = params if params is not None else {}
    if not isinstance(params, dict):
        raise ValueError("bad parameters")
    spec = ACTIONS[action]
    extra = set(params) - set(spec)
    if extra:
        raise ValueError("unexpected field %s" % sorted(extra)[0])
    out = {}
    for key, rule in spec.items():
        value = params.get(key)
        if rule == "bool":
            if value is None:
                value = False
            if not isinstance(value, bool):
                raise ValueError("bad value for %s" % key)
        elif rule == "settings":
            value = clean_settings(value, running)
            if running and any(k.startswith("bank.") for k in value):
                raise ValueError("the scenario settings cannot change while the exam is open")
        elif rule == "ident":
            if not isinstance(value, str) or not IDENT_RE.match(value):
                raise ValueError("bad value for %s" % key)
        elif rule == "slot":
            if not isinstance(value, str) or not SLOT_RE.match(value):
                raise ValueError("bad value for %s" % key)
        elif rule == "reason":
            value = value.strip() if isinstance(value, str) else value
            if not isinstance(value, str) or not 3 <= len(value) <= 120 or "\n" in value:
                raise ValueError("give a reason (3 to 120 characters, one line)")
        elif isinstance(rule, tuple) and rule and isinstance(rule[0], str):
            if value not in rule:
                raise ValueError("%s must be one of %s" % (key, ", ".join(rule)))
        else:
            lo, hi = rule
            if value is None and action == "open":
                out[key] = None  # the config's duration
                continue
            if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
                raise ValueError("%s must be %d to %d" % (key, lo, hi))
        out[key] = value
    return out


def agent_config():
    """The web control settings, or None when web control is off (not installed with --web-control)."""
    d = read_json(etc_dir() / "agent.json")
    return d if isinstance(d, dict) and d.get("roster") else None


def req_dir(name=""):
    base = var_dir() / "requests"
    return base / name if name else base


def submit_request(action, params, by):
    """Queue a validated request for the root helper. Returns its id."""
    rid = secrets.token_hex(8)
    body = {"id": rid, "action": action, "params": params, "by": str(by)[:40], "at": round(now_ts(), 3)}
    tmp = req_dir("tmp") / (rid + ".json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(body, f)
    os.chmod(tmp, 0o660)
    os.replace(tmp, req_dir("queue") / (rid + ".json"))  # appears in the queue complete, never half-written
    return rid


def request_status(rid):
    if not re.match(r"^[0-9a-f]{16}$", str(rid)):
        return None
    done = read_json(req_dir("done") / (rid + ".json"))
    if isinstance(done, dict):
        done["status"] = "done"
        return done
    for name, status in (("work", "running"), ("queue", "queued")):
        p = req_dir(name) / (rid + ".json")
        try:
            age = now_ts() - p.stat().st_mtime
            return {"id": rid, "status": status, "age_s": round(age, 1)}
        except OSError:
            continue
    return None


def request_history(n=20):
    items = []
    try:
        paths = sorted((p for p in req_dir("done").iterdir() if REQ_FILE_RE.match(p.name)),
                       key=lambda p: p.stat().st_mtime, reverse=True)[:n]
    except OSError:
        return items
    for p in paths:
        d = read_json(p)
        if isinstance(d, dict):
            items.append({k: d.get(k) for k in ("id", "action", "params", "by", "at", "done_at", "ok", "output")})
    return items


def control_dir():
    return var_dir() / "control"


def request_unlock(user, by, room="exam"):
    """Ask the gateway to unlock one student (it checks every second). Needs no root."""
    if not USER_RE.match(user):
        raise ValueError("bad user")
    tmp = control_dir() / (".%s.%s.tmp" % (user, secrets.token_hex(4)))
    body = {"action": "unlock", "by": str(by)[:40], "at": round(now_ts(), 3)}
    if room != "exam":
        body["room"] = "practice"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(body, f)
    os.chmod(tmp, 0o660)
    os.replace(tmp, control_dir() / (user + ".json"))


# ── Practice room (Practice Linux Commands, server/practice/) ─────────
#
# The practice room runs in the same gateway, all term. Its base config is /etc/itc-os-exam/practice.json (root,
# written by `examctl install`: the gateway address and whether practice is on); the instructor's practice page writes
# /srv/practice/settings.json (the lock triggers, the waits, the session cap). It never reads exam.json's lock, so
# making the exam strict does not change practice, and the reverse.

PRACTICE_ID = "practice"           # the "x" of a practice ticket; examctl config refuses an exam with this id
SCENARIO_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
PRACTICE_SETTINGS = {
    "lock.on": ("subset", tuple(sorted(LOCK_TRIGGERS)), True),
    "lock.wait_s": ("int", (5, 600), True),
    "lock.wait_max_s": ("int", (10, 1800), True),
    "max_sessions": ("int", (1, 60), True),
    "idle_min": ("int", (5, 120), True),
}


def practice_var():
    return Path(os.environ.get("ITC_PRACTICE_VAR", "/srv/practice"))


def load_practice():
    """The practice room's config, shaped like an exam config for the gateway, or None when practice is off."""
    base = read_json(etc_dir() / "practice.json")
    if not isinstance(base, dict) or base.get("enabled") is False:
        return None
    pre = PRESETS["practice"]
    cfg = {"id": PRACTICE_ID, "profile": "practice", "gateway_url": str(base.get("gateway_url", "")),
           "max_sessions": 20, "idle_min": 15, "flags": dict(DEFAULT_FLAGS),
           "lock": {"on": list(pre["lock.on"]), "mode": "wait", "max_attempts": 3,
                    "wait_s": pre["lock.wait_s"], "wait_max_s": pre["lock.wait_max_s"]}}
    over = read_json(practice_var() / "settings.json", {}) or {}
    if isinstance(over, dict):
        for k in PRACTICE_SETTINGS:  # one at a time: a bad value drops only that setting
            if k in over:
                try:
                    apply_settings(cfg, clean_settings({k: over[k]}, False, PRACTICE_SETTINGS))
                except ValueError:
                    pass
    cfg["lock"]["mode"] = "wait"   # practice never hands out codes
    cfg["lock"]["wait_max_s"] = max(cfg["lock"]["wait_max_s"], cfg["lock"]["wait_s"])
    return cfg


def exam_blocks_practice():
    """An exam that is open (or whose time is up but is not closed yet) closes the practice room: the gateway reaches
    the shell over 127.0.0.1, which hardening leaves open, so a practice shell would be a second shell in the exam."""
    cfg = load_config()
    return bool(cfg) and load_state(cfg).get("phase") in ("open", "ended")
