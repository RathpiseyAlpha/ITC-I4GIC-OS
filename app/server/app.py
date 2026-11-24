#!/usr/bin/env python3
"""
ITC-OS 2026 — Presence Server (Flask)
Tracks Linux users currently logged into the server via `who` and `last`.
Exposes a REST API for the frontend to poll.
Provides authentication against Linux user accounts and admin statistics.

Usage:
    python3 app.py                    # runs on 0.0.0.0:5000
    python3 app.py --port 8080        # custom port
    python3 app.py --host 127.0.0.1   # localhost only
"""

import argparse
import ctypes
import ctypes.util
import json
import math
import os
import re
import secrets
import struct
import subprocess
import threading
import time
import warnings
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

warnings.filterwarnings("ignore", category=DeprecationWarning, module="crypt")

# Python 3.13 removed the `crypt` module; call the system libcrypt directly.
# It understands every hash scheme in /etc/shadow, including yescrypt.
try:
    import crypt as _crypt_module  # type: ignore[deprecated]
    _crypt_hash = _crypt_module.crypt
except ImportError:
    _libcrypt = ctypes.CDLL(ctypes.util.find_library("crypt") or "libcrypt.so.1")
    _libcrypt.crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    _libcrypt.crypt.restype = ctypes.c_char_p
    _crypt_lock = threading.Lock()  # crypt(3) returns a static buffer

    def _crypt_hash(password, stored):
        with _crypt_lock:
            result = _libcrypt.crypt(
                password.encode("utf-8"), stored.encode("utf-8")
            )
            return result.decode("utf-8") if result else None

# Phnom Penh is UTC+7
_PPH = timezone(timedelta(hours=7))

# ── Configuration ──────────────────────────────────────────────

CORS_ORIGIN = "*"
POLL_CACHE_SEC = 5
WEB_STALE_SEC = 20
# Comma-separated Linux accounts that see the admin tabs.
ADMIN_USERS = [
    name.strip()
    for name in os.environ.get("ITC_OS_ADMINS", "rathpisey").split(",")
    if name.strip()
]
MAX_LOGIN_ATTEMPTS = 5          # failed attempts per address and account in the window
MAX_LOGIN_FAILS_PER_IP = 60     # failed attempts per address (a computer room shares one)
LOGIN_WINDOW_SEC = 60
SESSION_TIMEOUT_SEC = 3600  # 1 hour

# ── Deadline Storage ───────────────────────────────────────────

_DEADLINES_FILE = Path(__file__).resolve().parent / "deadlines.json"


def _load_deadlines():
    """Load deadlines from JSON file."""
    if _DEADLINES_FILE.exists():
        try:
            with open(_DEADLINES_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_deadlines(data):
    """Save deadlines to JSON file."""
    with open(_DEADLINES_FILE, "w") as f:
        json.dump(data, f, indent=2)


# In-memory cache refreshed from disk on every read
_deadlines = _load_deadlines()


def _debug_enabled():
    return os.environ.get("ITC_OS_DEBUG", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _debug_log(*parts):
    if not _debug_enabled():
        return
    ts = datetime.now().isoformat(timespec="seconds")
    print("[DEBUG " + ts + "]", *parts, flush=True)


# ── Student Roster ─────────────────────────────────────────────

# The roster holds student names, so it lives in a file that is not in git.
# Copy roster.example.json to roster.json on the server and fill it in.
_ROSTER_FILE = Path(
    os.environ.get(
        "ITC_OS_ROSTER", str(Path(__file__).resolve().parent / "roster.json")
    )
)


def _load_roster():
    """Return {student id: {"name": ..., "user": linux account}}; empty if missing."""
    try:
        with open(_ROSTER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print("[roster] not loaded from", _ROSTER_FILE, "-", exc, flush=True)
        return {}
    roster = {}
    for sid, info in data.items() if isinstance(data, dict) else []:
        if isinstance(info, dict) and info.get("user") and info.get("name"):
            roster[str(sid)] = {"name": str(info["name"]), "user": str(info["user"])}
    print("[roster]", len(roster), "students from", _ROSTER_FILE, flush=True)
    return roster


STUDENTS = _load_roster()

_USER_TO_SID = {v["user"]: k for k, v in STUDENTS.items()}

# ── Cache ──────────────────────────────────────────────────────

_cache = {"data": None, "ts": 0}

# ── Web Presence (in-memory) ───────────────────────────────────

_web_users = {}


def _prune_web_users():
    now = time.time()
    stale = [k for k, v in _web_users.items()
             if now - v.get("lastSeen", 0) > WEB_STALE_SEC]
    for k in stale:
        del _web_users[k]


# ── Authentication ─────────────────────────────────────────────

_sessions = {}
_login_attempts = {}
_session_lock = threading.Lock()
_SESSIONS_FILE = Path(__file__).resolve().parent / "sessions.json"
_SESSION_SAVE_INTERVAL = 30  # persist at most every 30s during activity
_last_session_save = 0.0


def _load_sessions():
    """Load sessions from disk (survives server restarts)."""
    global _sessions
    if _SESSIONS_FILE.exists():
        try:
            with open(_SESSIONS_FILE, "r") as f:
                data = json.load(f)
            now = time.time()
            # Only restore sessions that haven't expired
            _sessions = {
                t: s for t, s in data.items()
                if now - s.get("last_active", s.get("created", 0)) < SESSION_TIMEOUT_SEC
            }
        except (json.JSONDecodeError, OSError, TypeError):
            _sessions = {}


def _save_sessions():
    """Persist sessions to disk. Must be called with _session_lock held."""
    try:
        with open(_SESSIONS_FILE, "w") as f:
            json.dump(_sessions, f)
    except OSError:
        pass


# Load sessions from previous run on startup
_load_sessions()


def _rate_limited(key):
    now = time.time()
    attempts = [t for t in _login_attempts.get(key, [])
                if now - t < LOGIN_WINDOW_SEC]
    _login_attempts[key] = attempts
    limit = MAX_LOGIN_ATTEMPTS if "|" in key else MAX_LOGIN_FAILS_PER_IP
    return len(attempts) >= limit


def _record_attempt(ip):
    _login_attempts.setdefault(ip, []).append(time.time())


def _prune_sessions():
    """Remove expired sessions. Must be called with _session_lock held."""
    now = time.time()
    expired = [t for t, s in _sessions.items()
               if now - s.get("last_active", s.get("created", 0)) > SESSION_TIMEOUT_SEC]
    for t in expired:
        _sessions.pop(t, None)
    if expired:
        _save_sessions()


def verify_password(username, password):
    try:
        result = subprocess.run(
            ["getent", "shadow", username],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return False
        fields = result.stdout.strip().split(":")
        if len(fields) < 2:
            return False
        stored = fields[1]
        if stored in ("!", "*", "!!", "", "x"):
            return False
        computed = _crypt_hash(password, stored)
        return bool(computed) and secrets.compare_digest(computed, stored)
    except Exception:
        return False


def create_session(username):
    with _session_lock:
        _prune_sessions()
        token = secrets.token_urlsafe(32)
        role = "admin" if username in ADMIN_USERS else "user"
        now = time.time()
        _sessions[token] = {
            "username": username, "role": role,
            "created": now, "last_active": now,
        }
        _save_sessions()
    return token, role


def validate_token(token):
    global _last_session_save
    with _session_lock:
        _prune_sessions()
        s = _sessions.get(token)
        if s and time.time() - s.get("last_active", s["created"]) < SESSION_TIMEOUT_SEC:
            now = time.time()
            s["last_active"] = now
            # Throttle disk writes — persist activity updates periodically
            if now - _last_session_save > _SESSION_SAVE_INTERVAL:
                _save_sessions()
                _last_session_save = now
            return s
    return None


# ── Flask Helpers ──────────────────────────────────────────────

def _get_token():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def _get_client_ip():
    forwarded = (request.headers.get("CF-Connecting-IP")
                 or request.headers.get("X-Forwarded-For"))
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


# ── Auth Decorators ────────────────────────────────────────────

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_token()
        session = validate_token(token)
        if not session:
            return jsonify({"error": "Unauthorized"}), 403
        request._session = session # type: ignore
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_token()
        session = validate_token(token)
        if not session or session["role"] != "admin":
            return jsonify({"error": "Unauthorized"}), 403
        request._session = session # type: ignore
        return f(*args, **kwargs)
    return decorated


# ── Admin Statistics ───────────────────────────────────────────

def get_user_stats():
    stats = {}

    try:
        with open("/etc/passwd", "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) < 7:
                    continue
                username, uid_str, shell = parts[0], parts[2], parts[6]
                try:
                    uid = int(uid_str)
                except ValueError:
                    continue
                if uid < 1000 or shell in (
                    "/usr/sbin/nologin", "/bin/false", "/sbin/nologin",
                ):
                    continue
                stats[username] = {
                    "username": username,
                    "loginCount": 0,
                    "lastLogin": "",
                    "totalSeconds": 0,
                }
    except OSError:
        pass

    ended = set()
    for username, start, end in _wtmp_sessions():
        if username not in stats:
            stats[username] = {
                "username": username,
                "loginCount": 0,
                "lastLogin": "",
                "totalSeconds": 0,
            }
        stats[username]["loginCount"] += 1
        stats[username]["lastLogin"] = datetime.fromtimestamp(start, _PPH).isoformat()
        if end is not None:
            stats[username]["totalSeconds"] += max(0, end - start)
            ended.add(username)

    current = get_logged_in_users()
    online = {u["username"] for u in current}
    result_list = []
    for u in sorted(stats.values(), key=lambda x: x["loginCount"], reverse=True):
        secs = u["totalSeconds"]
        h, rem = divmod(secs, 3600)
        m = rem // 60
        # Logins without any recorded logout have no known length.
        known = u["username"] in ended or not u["loginCount"]
        u["totalDuration"] = f"{h}h {m}m" if known else "—"
        u["isOnline"] = u["username"] in online
        result_list.append(u)
    return result_list


_WTMP_FILE = os.environ.get("ITC_OS_WTMP", "/var/log/wtmp")
_UTMP_RECORD = struct.Struct("<hxxi32s4s32s256shhiii4i20s")  # struct utmp, x86_64 Linux
_USER_PROCESS, _DEAD_PROCESS, _BOOT_TIME = 7, 8, 2


def _wtmp_sessions(path=None):
    """Logins in the wtmp file as (user, start, end), oldest first; end is None
    when no logout was recorded. Ubuntu 26.04 has no `last`, so the file is read
    here. A session ends at the next logout on its terminal or at a reboot."""
    path = path or _WTMP_FILE
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as exc:
        print("[stats] cannot read", path, "-", exc, flush=True)
        return []
    sessions, open_on = [], {}
    usable = len(data) - len(data) % _UTMP_RECORD.size
    for rec in _UTMP_RECORD.iter_unpack(data[:usable]):
        kind, line, user, when = rec[0], rec[2], rec[4], rec[9]
        line = line.split(b"\0", 1)[0].decode("utf-8", "replace")
        user = user.split(b"\0", 1)[0].decode("utf-8", "replace")
        if kind == _USER_PROCESS and user:
            open_on[line] = len(sessions)
            sessions.append([user, when, None])
        elif kind == _DEAD_PROCESS and line in open_on:
            sessions[open_on.pop(line)][2] = when
        elif kind == _BOOT_TIME:
            for index in open_on.values():
                sessions[index][2] = when
            open_on.clear()
    return [tuple(s) for s in sessions]


def _loginctl_users():
    """Logged-in users from systemd-logind, in the same shape as the `who` list."""
    users = []
    try:
        listing = subprocess.run(
            ["loginctl", "list-sessions", "--no-legend", "--no-pager"],
            capture_output=True, text=True, timeout=5,
        )
        ids = [ln.split()[0] for ln in listing.stdout.splitlines() if ln.split()]
        if not ids:
            return []
        shown = subprocess.run(
            ["loginctl", "show-session", *ids, "--no-pager",
             "-p", "Id", "-p", "Name", "-p", "Class", "-p", "State",
             "-p", "TTY", "-p", "RemoteHost", "-p", "Timestamp"],
            capture_output=True, text=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []

    for block in shown.stdout.split("\n\n"):
        props = dict(
            ln.split("=", 1) for ln in block.splitlines() if "=" in ln
        )
        if props.get("Class") != "user" or props.get("State") == "closing":
            continue
        if not props.get("Name"):
            continue
        # Timestamp looks like "Thu 2026-10-08 07:24:23 +07"
        stamp = props.get("Timestamp", "").split()
        login_time = (
            f"{stamp[1]} {stamp[2][:5]}" if len(stamp) >= 3
            else " ".join(stamp)
        )
        users.append({
            "username": props["Name"],
            "terminal": props.get("TTY", ""),
            "loginTime": login_time,
            "host": props.get("RemoteHost", ""),
        })
    return users


def get_logged_in_users():
    now = time.time()
    if _cache["data"] is not None and (now - _cache["ts"]) < POLL_CACHE_SEC:
        return _cache["data"]

    users = []
    seen = set()
    try:
        result = subprocess.run(
            ["who"], capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            username = parts[0]
            terminal = parts[1]
            login_time = (
                " ".join(parts[2:4]) if len(parts) >= 4 else parts[2]
            )
            host = ""
            if "(" in line and ")" in line:
                host = line[line.rindex("(") + 1 : line.rindex(")")]
            key = f"{username}@{terminal}"
            if key not in seen:
                seen.add(key)
                users.append({
                    "username": username,
                    "terminal": terminal,
                    "loginTime": login_time,
                    "host": host,
                })
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        users = []

    # Newer Ubuntu has no /run/utmp, so `who` prints nothing there.
    if not users:
        users = _loginctl_users()

    users.sort(key=lambda u: u["username"])
    _cache["data"] = users
    _cache["ts"] = now
    return users


def get_recent_logins(count=20):
    entries = []
    try:
        result = subprocess.run(
            ["last", "-n", str(count), "-w"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if (
                not line
                or line.startswith("wtmp")
                or line.startswith("reboot")
            ):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            entries.append({
                "username": parts[0],
                "terminal": parts[1],
                "info": " ".join(parts[2:]),
            })
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        entries = []
    return entries


# ── Lab Grading Engine ─────────────────────────────────────────

# Required files of each lab's submission tree (see the lab instruction's Submit section).
# This measures what was handed in, not whether it is correct.
LAB_SPECS = {
    "lab1": {
        "total_points": 100,
        "files": [
            "README.md",
            "task1_os_info.txt",
            "task2_file_commands.txt",
            "task3_apt.txt",
            "task4_process_list.txt",
            "task5_multitasking.txt",
            "task6_virtualization_check.txt",
        ],
        "dirs": ["task2_files", "images"],
    },
    "lab2": {
        "total_points": 100,
        "files": [
            "README.md",
            "evidence/paths.txt",
            "evidence/tree.txt",
        ],
        "dirs": ["evidence"],
    },
    "lab3": {
        "total_points": 100,
        "files": [
            "README.md",
            "evidence/wildcards.txt",
            "evidence/links.txt",
            "evidence/replacement.txt",
        ],
        "dirs": ["evidence"],
    },
    "lab4": {
        "total_points": 100,
        "files": [
            "README.md", "checkpoint.txt", "evidence/commands.txt",
            "evidence/selected.txt", "evidence/fields.txt", "evidence/normal.txt",
            "evidence/edge.txt", "evidence/stdout.txt", "evidence/stderr.txt",
            "evidence/status.txt", "evidence/checkpoint-selected.txt",
        ],
        "dirs": ["evidence"],
    },
    "lab5": {
        "total_points": 100,
        "files": [
            "README.md",
            "two_workers.c",
            "evidence/normal.txt",
            "evidence/changed.txt",
        ],
        "dirs": ["evidence"],
    },
    "lab6": {
        "total_points": 100,
        "files": [
            "README.md",
            "evidence/policy.txt",
            "evidence/traversal.txt",
        ],
        "dirs": ["evidence"],
    },
    "lab7": {
        "total_points": 100,
        "files": [
            "README.md",
            "count_words.sh",
            "evidence/normal.txt",
            "evidence/edge.txt",
        ],
        "dirs": ["evidence"],
    },
    "lab8": {
        "total_points": 100,
        "files": [
            "README.md",
            "buy.sh",
            "evidence/trace.txt",
            "evidence/race.txt",
            "evidence/locked.txt",
        ],
        "dirs": ["evidence"],
    },
    "lab9": {
        "total_points": 100,
        "files": [
            "README.md",
            "worker.sh",
            "evidence/opposite.txt",
            "evidence/ordered.txt",
        ],
        "dirs": ["evidence"],
    },
    "lab10": {
        "total_points": 100,
        "files": [
            "README.md",
            "backup.sh",
            "evidence/restore.txt",
            "evidence/automation.txt",
        ],
        "dirs": ["evidence"],
    },
}

# ── Class Activity Specs ───────────────────────────────────────

_ACTIVITY_MD_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "lectures"
    / "class-activity"
)
_SKIP_CONTENT_DIRS = frozenset(("screenshots", "images"))


def _parse_activity_spec(md_path, activity_name):
    try:
        text = Path(md_path).read_text(encoding="utf-8")
    except OSError:
        return None

    tree_block = None
    in_code = False
    buf = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            if in_code:
                block = "\n".join(buf)
                if (
                    f"{activity_name}/" in block
                    and ("├" in block or "└" in block)
                ):
                    tree_block = block
                    break
                buf = []
            in_code = not in_code
            continue
        if in_code:
            buf.append(line)

    if not tree_block:
        return None

    files, dirs = [], []
    root_found = False
    base_indent = None
    stack = []

    for raw in tree_block.splitlines():
        m = re.search(r"([├└])── (.+)", raw)
        if not m:
            continue
        marker_pos = raw.index(m.group(1))
        entry_raw = m.group(2)

        if not root_found:
            if entry_raw.strip().rstrip("/") == activity_name:
                root_found = True
            continue

        if base_indent is None:
            base_indent = marker_pos
        depth = (marker_pos - base_indent) // 4
        if depth < 0:
            break

        entry = re.sub(r"\s{2,}#.*$", "", entry_raw).strip()
        entry = re.sub(r"\s+←.*$", "", entry).strip()
        if not entry or "..." in entry:
            continue

        is_dir = entry.endswith("/")
        name = entry.rstrip("/")
        stack = stack[:depth]

        if is_dir:
            rel = "/".join(stack + [name]) if stack else name
            dirs.append(rel)
            stack.append(name)
        else:
            cm = re.search(r"\s{2,}#\s*(.+)$", entry_raw)
            if cm and re.search(r"optional|bonus", cm.group(1), re.I):
                continue
            if stack and stack[0] in _SKIP_CONTENT_DIRS:
                continue
            rel = "/".join(stack + [name]) if stack else name
            files.append(rel)

    if not root_found or (not files and not dirs):
        return None

    total = 100
    for line in text.splitlines():
        if "total" in line.lower() and "|" in line:
            pts = re.search(r"\*\*(\d+)(?:\s*\(\+\d+[^)]*\))?\*\*", line)
            if pts:
                total = int(pts.group(1))
                break

    return {"total_points": total, "files": files, "dirs": dirs}


def _build_activity_specs():
    specs = {}
    for i in range(1, 100):
        md = _ACTIVITY_MD_DIR / f"class-activity{i}.md"
        if not md.exists():
            break
        spec = _parse_activity_spec(md, f"activity{i}")
        if spec:
            specs[f"activity{i}"] = spec
    return specs


ACTIVITY_SPECS = _build_activity_specs()

# Hard-coded override for activity1 (its markdown tree is complex)
ACTIVITY_SPECS["activity1"] = {
    "total_points": 100,
    "files": [
        "README.md",
        "task1/file_creator_lib.c",
        "task1/file_creator_sys.c",
        "task1/file_reader_lib.c",
        "task1/file_reader_sys.c",
        "task2/dir_list_lib.c",
        "task2/dir_list_sys.c",
        "task3_strace/strace_lib_task1.txt",
        "task3_strace/strace_sys_task1.txt",
        "task3_strace/strace_lib_reader.txt",
        "task3_strace/strace_sys_reader.txt",
        "task3_strace/strace_summary_lib.txt",
        "task3_strace/strace_summary_sys.txt",
        "screenshots/task4_system_info.png",
        "screenshots/task4_process_info.png",
        "screenshots/task4_modules.png",
        "screenshots/task4_os_layers_diagram.png",
    ],
    "dirs": ["screenshots", "task1", "task2", "task3_strace"],
}

# Activity 5 permits any programming language, so source filenames vary.
ACTIVITY_SPECS["activity5"] = {
    "total_points": 100,
    "files": [
        "README.md",
        "screenshots/task1_before_semaphore.png",
        "screenshots/task1_after_semaphore.png",
        "screenshots/task2_before_semaphore.png",
        "screenshots/task2_after_semaphore.png",
    ],
    "dirs": ["screenshots", "task1_particles", "task2_hello"],
}

# Activity 6 permits any programming language, so source filenames vary.
ACTIVITY_SPECS["activity6"] = {
    "total_points": 100,
    "files": [
        "README.md",
        "screenshots/task1_deadlock.png",
        "screenshots/task2_prevention.png",
    ],
    "dirs": ["screenshots", "task1_deadlock", "task2_prevention"],
}

_SCREENSHOT_KEYWORDS = {
    "screenshots/task4_system_info.png": [
        ["system", "info"], ["cpuinfo"], ["meminfo"], ["cpu"], ["mem"],
    ],
    "screenshots/task4_process_info.png": [
        ["process", "info"], ["process"], ["proc"],
    ],
    "screenshots/task4_modules.png": [["mod"]],
    "screenshots/task4_os_layers_diagram.png": [["layer"]],
}

_DIR_ALIASES = {"task3_strace": ["task3"]}


def _try_alias(expected_lower, existing):
    for spec_dir, alts in _DIR_ALIASES.items():
        sd = spec_dir.lower()
        if expected_lower == sd or expected_lower.startswith(sd + "/"):
            for alt in alts:
                p = alt + expected_lower[len(sd):]
                if p in existing:
                    return existing[p]
        for alt in alts:
            al = alt.lower()
            if expected_lower == al or expected_lower.startswith(al + "/"):
                p = sd + expected_lower[len(al):]
                if p in existing:
                    return existing[p]
    return None


# ── File-System Helpers ────────────────────────────────────────


# A student's course repository folder: the new name first, then the name used before 2026.
REPO_PREFIXES = ("os-gic-", "os-se-")


def _find_lab_root(username, lab_name):
    home = Path(f"/home/{username}")
    if not home.is_dir():
        return None
    try:
        for d in home.iterdir():
            if d.is_dir() and d.name.lower().startswith(REPO_PREFIXES):
                for sub in d.iterdir():
                    if sub.is_dir() and sub.name.lower().startswith("os-lab-"):
                        lab_dir = sub / lab_name
                        if lab_dir.is_dir():
                            return lab_dir
        for d in home.iterdir():
            if d.is_dir() and d.name.lower().startswith("os-lab-"):
                lab_dir = d / lab_name
                if lab_dir.is_dir():
                    return lab_dir
        lab_dir = home / lab_name
        if lab_dir.is_dir():
            return lab_dir
    except PermissionError:
        return None
    return None


def _find_activity_root(username, activity_name):
    home = Path(f"/home/{username}")
    if not home.is_dir():
        return None
    try:
        for d in home.iterdir():
            if d.is_dir() and d.name.lower().startswith(REPO_PREFIXES):
                for sub in d.iterdir():
                    if sub.is_dir() and sub.name.lower().startswith(
                        "os-class-activit"
                    ):
                        act_dir = sub / activity_name
                        if act_dir.is_dir():
                            return act_dir
        for d in home.iterdir():
            if d.is_dir() and d.name.lower().startswith("os-class-activit"):
                act_dir = d / activity_name
                if act_dir.is_dir():
                    return act_dir
        act_dir = home / activity_name
        if act_dir.is_dir():
            return act_dir
    except PermissionError:
        return None
    return None


def _get_file_submission_dates(root):
    if not root or not Path(root).is_dir():
        _debug_log("git-dates: skipped; invalid root:", root)
        return {}
    try:
        repo_prefix = ""
        prefix_result = subprocess.run(
            ["git", "rev-parse", "--show-prefix"],
            capture_output=True, text=True, timeout=5,
            cwd=str(root),
        )
        if prefix_result.returncode == 0:
            repo_prefix = (prefix_result.stdout or "").strip().replace(
                "\\", "/"
            )
            if repo_prefix and not repo_prefix.endswith("/"):
                repo_prefix += "/"
        _debug_log(
            "git-dates: repo prefix", repr(repo_prefix), "for", str(root)
        )

        _debug_log("git-dates: running git log in", str(root))
        result = subprocess.run(
            [
                "git", "log", "--diff-filter=A", "--format=DATE:%aI",
                "--name-only", "--", ".",
            ],
            capture_output=True, text=True, timeout=10,
            cwd=str(root),
        )
        if result.returncode != 0 or not result.stdout.strip():
            _debug_log(
                "git-dates: empty or failed",
                "cwd=" + str(root),
                "returncode=" + str(result.returncode),
                "stderr=" + repr((result.stderr or "").strip()[:400]),
                "stdout=" + repr((result.stdout or "").strip()[:400]),
                "service_user=" + os.environ.get("USER", "?"),
                "path=" + os.environ.get("PATH", ""),
            )
            return {}

        file_dates = {}
        current_date = None
        for line in result.stdout.strip().splitlines():
            if line.startswith("DATE:"):
                current_date = line[5:]
            elif line.strip() and current_date:
                fname = line.strip().replace("\\", "/")
                if repo_prefix and fname.startswith(repo_prefix):
                    fname = fname[len(repo_prefix):]
                if fname.startswith("./"):
                    fname = fname[2:]
                if not fname:
                    continue
                file_dates[fname] = current_date
        _debug_log(
            "git-dates: parsed", len(file_dates), "entries from", str(root),
        )
        return file_dates
    except subprocess.TimeoutExpired as exc:
        _debug_log(
            "git-dates: timeout",
            "cwd=" + str(root),
            "timeout=" + str(exc.timeout),
        )
        return {}
    except FileNotFoundError as exc:
        _debug_log("git-dates: git not found", "cwd=" + str(root), repr(exc))
        return {}
    except OSError as exc:
        _debug_log("git-dates: os error", "cwd=" + str(root), repr(exc))
        return {}


def _calc_late_penalty(file_dates, deadline_iso, penalty_per_day):
    if not file_dates or not deadline_iso:
        return None
    try:
        deadline_dt = datetime.fromisoformat(deadline_iso)
        if deadline_dt.tzinfo is None:
            deadline_dt = deadline_dt.replace(tzinfo=_PPH)
    except (ValueError, TypeError):
        return None

    total_files = len(file_dates)
    late_files = 0
    max_days_late = 0

    for _fname, date_iso in file_dates.items():
        try:
            fdt = datetime.fromisoformat(date_iso)
            if fdt.tzinfo is None:
                fdt = fdt.replace(tzinfo=_PPH)
            if fdt > deadline_dt:
                late_files += 1
                days = math.ceil(
                    (fdt - deadline_dt).total_seconds() / 86400
                )
                if days > max_days_late:
                    max_days_late = days
        except (ValueError, TypeError):
            continue

    if late_files == 0:
        return {
            "late": False, "lateFiles": 0, "totalFiles": total_files,
            "weight": 0, "daysLate": 0, "penalty": 0,
        }

    weight = round(late_files / total_files, 4)
    penalty = round(weight * max_days_late * penalty_per_day, 2)
    return {
        "late": True,
        "lateFiles": late_files,
        "totalFiles": total_files,
        "weight": weight,
        "daysLate": max_days_late,
        "penalty": penalty,
    }


def _list_recursive(root):
    result = {}
    root = Path(root)
    try:
        for item in root.rglob("*"):
            rel = str(item.relative_to(root)).replace("\\", "/")
            result[rel.lower()] = rel
    except PermissionError:
        pass
    return result


# ── Grading Functions ──────────────────────────────────────────


def grade_student_lab(username, lab_name):
    spec = LAB_SPECS.get(lab_name)
    if not spec:
        return {"error": f"Unknown lab: {lab_name}"}

    lab_root = _find_lab_root(username, lab_name)
    if not lab_root:
        return {
            "username": username, "lab": lab_name, "score": 0,
            "finalScore": 0, "total": spec["total_points"],
            "percentage": 0, "finalPercentage": 0,
            "found": False, "labPath": None, "items": [],
            "feedback": [
                f"Lab directory not found. Expected "
                f"~/os-gic-<ID>/os-lab-<ID>/{lab_name}/"
            ],
        }

    all_items = spec.get("files", []) + spec.get("dirs", [])
    total_items = len(all_items)
    if total_items == 0:
        return {"error": "No items defined for this lab."}

    points_per_item = spec["total_points"] / total_items
    existing = _list_recursive(lab_root)

    score = 0.0
    items = []
    feedback = []

    for expected in all_items:
        expected_lower = expected.lower()
        is_dir = expected in spec.get("dirs", [])
        item_type = "dir" if is_dir else "file"

        if expected_lower in existing:
            actual_path = existing[expected_lower]
            full_path = lab_root / actual_path
            type_ok = (
                full_path.is_dir() if is_dir else full_path.is_file()
            )
            if not type_ok:
                items.append({
                    "expected": expected, "status": "wrong_type",
                    "points": 0, "maxPoints": round(points_per_item, 2),
                    "type": item_type,
                })
                feedback.append(
                    f"'{expected}' exists but is "
                    f"{'a file' if is_dir else 'a directory'} "
                    f"(expected {item_type})."
                )
                continue

            if actual_path != expected:
                penalty = min(1.0, points_per_item)
                earned = max(0, points_per_item - penalty)
                score += earned
                items.append({
                    "expected": expected, "actual": actual_path,
                    "status": "case_mismatch",
                    "points": round(earned, 2),
                    "maxPoints": round(points_per_item, 2),
                    "type": item_type,
                })
                feedback.append(
                    f"'{actual_path}' should be '{expected}' "
                    f"(naming convention: all lowercase with underscores). "
                    f"-1 point."
                )
            else:
                score += points_per_item
                items.append({
                    "expected": expected, "status": "ok",
                    "points": round(points_per_item, 2),
                    "maxPoints": round(points_per_item, 2),
                    "type": item_type,
                })
        else:
            items.append({
                "expected": expected, "status": "missing",
                "points": 0, "maxPoints": round(points_per_item, 2),
                "type": item_type,
            })
            feedback.append(f"Missing {item_type}: '{expected}'")

    score = round(min(score, spec["total_points"]), 2)
    file_dates = _get_file_submission_dates(lab_root)
    sub_date = max(file_dates.values()) if file_dates else None

    dl = _deadlines.get(lab_name, {})
    late_info = _calc_late_penalty(
        file_dates, dl.get("due"), dl.get("penalty", 5),
    )
    final_score = score
    if late_info and late_info["late"]:
        final_score = round(max(0, score - late_info["penalty"]), 2)
        feedback.append(
            f"Late penalty: {late_info['lateFiles']}/{late_info['totalFiles']}"
            f" files submitted late (max {late_info['daysLate']}d) — "
            f"-{late_info['penalty']} pts "
            f"(weight {late_info['weight']:.0%})"
        )

    return {
        "username": username, "lab": lab_name,
        "score": score, "finalScore": final_score,
        "total": spec["total_points"],
        "percentage": round(score / spec["total_points"] * 100, 1),
        "finalPercentage": round(final_score / spec["total_points"] * 100, 1),
        "found": True, "labPath": str(lab_root),
        "submissionDate": sub_date, "lateInfo": late_info,
        "fileDates": file_dates,
        "deadline": dl if dl else None,
        "items": items, "feedback": feedback,
    }


def grade_all_students(lab_name=None):
    labs = [lab_name] if lab_name else list(LAB_SPECS.keys())
    results = []
    for sid in sorted(STUDENTS.keys()):
        info = STUDENTS[sid]
        linux_user = info["user"]
        for lab in labs:
            try:
                g = grade_student_lab(linux_user, lab)
                g["id"] = sid
                g["name"] = info["name"]
                results.append(g)
            except (PermissionError, OSError):
                results.append({
                    "username": linux_user, "id": sid,
                    "name": info["name"], "lab": lab, "score": 0,
                    "finalScore": 0,
                    "total": LAB_SPECS.get(lab, {}).get("total_points", 0),
                    "percentage": 0, "finalPercentage": 0,
                    "found": False, "labPath": None,
                    "items": [],
                    "feedback": [
                        "Permission denied: cannot access home directory."
                    ],
                })
    return results


def grade_student_activity(username, activity_name):
    spec = ACTIVITY_SPECS.get(activity_name)
    if not spec:
        return {"error": f"Unknown activity: {activity_name}"}

    act_root = _find_activity_root(username, activity_name)
    if not act_root:
        return {
            "username": username, "activity": activity_name,
            "score": 0, "finalScore": 0, "total": spec["total_points"],
            "percentage": 0, "finalPercentage": 0,
            "found": False, "activityPath": None,
            "items": [],
            "feedback": [
                f"Activity directory not found. Expected "
                f"~/os-gic-<ID>/os-class-activities-<ID>/{activity_name}/"
            ],
        }

    all_items = spec.get("files", []) + spec.get("dirs", [])
    total_items = len(all_items)
    if total_items == 0:
        return {"error": "No items defined for this activity."}

    points_per_item = spec["total_points"] / total_items
    existing = _list_recursive(act_root)

    score = 0.0
    items = []
    feedback = []

    for expected in all_items:
        expected_lower = expected.lower()
        is_dir = expected in spec.get("dirs", [])
        item_type = "dir" if is_dir else "file"

        if expected_lower in existing:
            actual_path = existing[expected_lower]
            full_path = act_root / actual_path
            type_ok = (
                full_path.is_dir() if is_dir else full_path.is_file()
            )
            if not type_ok:
                items.append({
                    "expected": expected, "status": "wrong_type",
                    "points": 0, "maxPoints": round(points_per_item, 2),
                    "type": item_type,
                })
                feedback.append(
                    f"'{expected}' exists but is "
                    f"{'a file' if is_dir else 'a directory'} "
                    f"(expected {item_type})."
                )
                continue

            if actual_path != expected:
                penalty = min(1.0, points_per_item)
                earned = max(0, points_per_item - penalty)
                score += earned
                items.append({
                    "expected": expected, "actual": actual_path,
                    "status": "case_mismatch",
                    "points": round(earned, 2),
                    "maxPoints": round(points_per_item, 2),
                    "type": item_type,
                })
                feedback.append(
                    f"'{actual_path}' should be '{expected}' "
                    f"(naming convention). -1 point."
                )
            else:
                score += points_per_item
                items.append({
                    "expected": expected, "status": "ok",
                    "points": round(points_per_item, 2),
                    "maxPoints": round(points_per_item, 2),
                    "type": item_type,
                })
        elif (
            alias_path := _try_alias(expected_lower, existing)
        ) is not None:
            actual_path = alias_path
            full_path = act_root / actual_path
            type_ok = (
                full_path.is_dir() if is_dir else full_path.is_file()
            )
            if not type_ok:
                items.append({
                    "expected": expected, "status": "wrong_type",
                    "points": 0, "maxPoints": round(points_per_item, 2),
                    "type": item_type,
                })
                feedback.append(
                    f"'{expected}' exists but is "
                    f"{'a file' if is_dir else 'a directory'} "
                    f"(expected {item_type})."
                )
                continue
            score += points_per_item
            items.append({
                "expected": expected, "actual": actual_path,
                "status": "ok",
                "points": round(points_per_item, 2),
                "maxPoints": round(points_per_item, 2),
                "type": item_type,
            })
        else:
            # Screenshot keyword matching for activity1
            matched_path = None
            if expected in _SCREENSHOT_KEYWORDS:
                keyword_groups = _SCREENSHOT_KEYWORDS[expected]
                for ex_lower, ex_actual in existing.items():
                    if not ex_lower.startswith("screenshots/"):
                        continue
                    base = ex_lower.rsplit("/", 1)[-1]
                    base = base.rsplit(".", 1)[0] if "." in base else base
                    if any(
                        all(kw in base for kw in grp)
                        for grp in keyword_groups
                    ):
                        full = act_root / ex_actual
                        if full.is_file():
                            matched_path = ex_actual
                            break

            if matched_path is not None:
                score += points_per_item
                items.append({
                    "expected": expected, "actual": matched_path,
                    "status": "ok",
                    "points": round(points_per_item, 2),
                    "maxPoints": round(points_per_item, 2),
                    "type": "file",
                })
            else:
                items.append({
                    "expected": expected, "status": "missing",
                    "points": 0, "maxPoints": round(points_per_item, 2),
                    "type": item_type,
                })
                feedback.append(f"Missing {item_type}: '{expected}'")

    score = round(min(score, spec["total_points"]), 2)
    file_dates = _get_file_submission_dates(act_root)
    sub_date = max(file_dates.values()) if file_dates else None

    dl = _deadlines.get(activity_name, {})
    late_info = _calc_late_penalty(
        file_dates, dl.get("due"), dl.get("penalty", 5),
    )
    final_score = score
    if late_info and late_info["late"]:
        final_score = round(max(0, score - late_info["penalty"]), 2)
        feedback.append(
            f"Late penalty: {late_info['lateFiles']}/{late_info['totalFiles']}"
            f" files submitted late (max {late_info['daysLate']}d) — "
            f"-{late_info['penalty']} pts "
            f"(weight {late_info['weight']:.0%})"
        )

    return {
        "username": username, "activity": activity_name,
        "score": score, "finalScore": final_score,
        "total": spec["total_points"],
        "percentage": round(score / spec["total_points"] * 100, 1),
        "finalPercentage": round(final_score / spec["total_points"] * 100, 1),
        "found": True, "activityPath": str(act_root),
        "submissionDate": sub_date, "lateInfo": late_info,
        "fileDates": file_dates,
        "deadline": dl if dl else None,
        "items": items, "feedback": feedback,
    }


def grade_all_activities(activity_name=None):
    acts = [activity_name] if activity_name else list(ACTIVITY_SPECS.keys())
    results = []
    for sid in sorted(STUDENTS.keys()):
        info = STUDENTS[sid]
        linux_user = info["user"]
        for act in acts:
            try:
                g = grade_student_activity(linux_user, act)
                g["id"] = sid
                g["name"] = info["name"]
                results.append(g)
            except (PermissionError, OSError):
                results.append({
                    "username": linux_user, "id": sid,
                    "name": info["name"], "activity": act, "score": 0,
                    "finalScore": 0,
                    "total": ACTIVITY_SPECS.get(act, {}).get(
                        "total_points", 0
                    ),
                    "percentage": 0, "finalPercentage": 0,
                    "found": False, "activityPath": None,
                    "items": [],
                    "feedback": [
                        "Permission denied: cannot access home directory."
                    ],
                })
    return results


def get_leaderboard():
    all_grades = grade_all_students()
    all_acts = grade_all_activities()
    per_student = {}

    def add_grade(target, category, key, grade):
        score = grade.get("score", 0) or 0
        final_score = grade.get("finalScore", score)
        total = grade.get("total", 0) or 0
        late_info = grade.get("lateInfo") or {}
        is_late = bool(late_info.get("late"))
        penalty = round(max(0, score - final_score), 2)
        percentage = round(final_score / total * 100, 1) if total else 0

        target[category][key] = {
            "score": final_score,
            "rawScore": score,
            "finalScore": final_score,
            "total": total,
            "percentage": percentage,
            "rawPercentage": grade.get("percentage", percentage),
            "finalPercentage": percentage,
            "found": grade.get("found", False),
            "late": is_late,
            "lateInfo": late_info if late_info else None,
            "penalty": penalty,
        }
        target["totalRawScore"] += score
        target["totalScore"] += final_score
        target["totalPossible"] += total
        if is_late:
            target["lateCount"] += 1
            target["totalPenalty"] = round(target["totalPenalty"] + penalty, 2)

    for g in all_grades:
        sid = g.get("id", g["username"])
        if sid not in per_student:
            per_student[sid] = {
                "id": sid, "username": g["username"],
                "name": g.get("name", sid),
                "labs": {}, "activities": {},
                "totalRawScore": 0, "totalScore": 0,
                "totalPossible": 0, "lateCount": 0,
                "totalPenalty": 0,
            }
        add_grade(per_student[sid], "labs", g["lab"], g)

    for g in all_acts:
        sid = g.get("id", g["username"])
        if sid not in per_student:
            per_student[sid] = {
                "id": sid, "username": g["username"],
                "name": g.get("name", sid),
                "labs": {}, "activities": {},
                "totalRawScore": 0, "totalScore": 0,
                "totalPossible": 0, "lateCount": 0,
                "totalPenalty": 0,
            }
        add_grade(per_student[sid], "activities", g["activity"], g)

    board = []
    for s in per_student.values():
        s["totalPercentage"] = (
            round(s["totalScore"] / s["totalPossible"] * 100, 1)
            if s["totalPossible"] > 0
            else 0
        )
        s["totalRawPercentage"] = (
            round(s["totalRawScore"] / s["totalPossible"] * 100, 1)
            if s["totalPossible"] > 0
            else 0
        )
        board.append(s)

    board.sort(key=lambda x: x["totalScore"], reverse=True)
    for i, entry in enumerate(board):
        entry["rank"] = i + 1
    return board


def get_marks_board():
    """The course leaderboard: students ranked by their PUBLISHED instructor
    marks (labs and class activities).

    A work counts once at least one roster student has a published mark for
    it. Inside a counted work a student with no published mark scores 0, so
    every row is measured against the same set of works. Labs are out of 10
    and activities out of 100, so the score is the mean of points/max over
    the counted works (each work weighs the same), as a percentage; raw
    points would let the activities swamp the labs. Equal scores share a
    rank. A student with no published mark is not listed. Entries carry id,
    username and name; callers decide what a student may see (see
    route_my_leaderboard)."""
    marks = _load_marks()
    rubrics = {}
    given = {}   # work -> {sid: (points, max)} for published marks only
    for work in list(LAB_SPECS.keys()) + list(ACTIVITY_SPECS.keys()):
        for user, entry in (marks.get(work) or {}).items():
            sid = _USER_TO_SID.get(user)
            if not sid or not isinstance(entry, dict) or not entry.get("published"):
                continue
            if work not in rubrics:
                rubrics[work] = _rubric(work)
            view = _mark_view(work, entry, rubrics[work])
            if view["total"] is None or not view["max"]:
                continue
            given.setdefault(work, {})[sid] = (view["total"], view["max"])
    works = list(given.keys())
    sids = {sid for per_work in given.values() for sid in per_work}
    board = []
    for sid in sids:
        ratios = [(given[w][sid][0] / given[w][sid][1]) if sid in given[w] else 0.0 for w in works]
        score = sum(ratios) / len(works) if works else 0.0
        board.append({
            "id": sid, "username": STUDENTS.get(sid, {}).get("user", ""),
            "name": STUDENTS.get(sid, {}).get("name", sid),
            "works": {w: {"total": given[w][sid][0], "max": given[w][sid][1]} for w in works if sid in given[w]},
            "marked": sum(1 for w in works if sid in given[w]),
            "of": len(works),
            "percentage": round(score * 100, 1),
            "_score": round(score, 6),
        })
    board.sort(key=lambda r: (-r["_score"], r["id"]))
    prev, rank = None, 0
    for i, row in enumerate(board):
        if row["_score"] != prev:
            prev, rank = row["_score"], i + 1
        row["rank"] = rank
        del row["_score"]
    return board


def get_student_tree(username, lab_name):
    lab_root = _find_lab_root(username, lab_name)
    if not lab_root:
        return None

    def build_tree(path, depth=0, max_depth=5):
        if depth > max_depth:
            return []
        items = []
        try:
            entries = sorted(
                path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except PermissionError:
            return items
        for entry in entries:
            if entry.name.startswith("."):
                continue
            node = {
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
            }
            if entry.is_dir():
                node["children"] = build_tree(entry, depth + 1, max_depth)
            else:
                try:
                    node["size"] = entry.stat().st_size
                except OSError:
                    node["size"] = 0
            items.append(node)
        return items

    return {
        "username": username, "lab": lab_name,
        "path": str(lab_root), "tree": build_tree(lab_root),
    }


def get_student_activity_tree(username, activity_name):
    act_root = _find_activity_root(username, activity_name)
    if not act_root:
        return None

    def build_tree(path, depth=0, max_depth=5):
        if depth > max_depth:
            return []
        items = []
        try:
            entries = sorted(
                path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except PermissionError:
            return items
        for entry in entries:
            if entry.name.startswith("."):
                continue
            node = {
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
            }
            if entry.is_dir():
                node["children"] = build_tree(entry, depth + 1, max_depth)
            else:
                try:
                    node["size"] = entry.stat().st_size
                except OSError:
                    node["size"] = 0
            items.append(node)
        return items

    return {
        "username": username, "activity": activity_name,
        "path": str(act_root), "tree": build_tree(act_root),
    }


# ══════════════════════════════════════════════════════════════
#  Instructor marks — rubric, lab records, file viewer
# ══════════════════════════════════════════════════════════════

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MARKS_FILE = Path(__file__).resolve().parent / "marks.json"
_marks_lock = threading.Lock()
_TEXT_LIMIT = 200_000
_IMAGE_LIMIT = 4_000_000
_IMAGE_TYPES = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp",
}


def _lab_rubric(lab):
    """Rows of the Grading Criteria table in the lab's instruction."""
    path = _REPO_ROOT / "labs" / lab / f"{lab}-instruction.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        text = ""
    rows = []
    parts = text.split("## Grading Criteria", 1)
    if len(parts) == 2:
        section = parts[1].split("\n## ", 1)[0]
        found = re.findall(
            r"^\|\s*([^|\n]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*$", section, re.M
        )
        for label, points in found:
            rows.append({
                "key": f"r{len(rows) + 1}",
                "label": label.replace("`", ""),
                "max": float(points),
            })
    return rows or [{"key": "r1", "label": "Lab mark", "max": 10.0}]


def _activity_rubric(activity):
    """Rows of the Grading Criteria table in the class activity. Its rows
    may have a description column after the points, and a Total row."""
    path = _ACTIVITY_MD_DIR / f"class-{activity}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        text = ""
    rows = []
    parts = text.split("## Grading Criteria", 1)
    if len(parts) == 2:
        section = parts[1].split("\n## ", 1)[0]
        found = re.findall(
            r"^\|\s*([^|\n]+?)\s*\|\s*\**\s*(\d+(?:\.\d+)?)\s*\**\s*\|", section, re.M
        )
        for label, points in found:
            label = label.replace("`", "").replace("**", "").strip()
            if label.lower() == "total":
                continue
            rows.append({
                "key": f"r{len(rows) + 1}",
                "label": label,
                "max": float(points),
            })
    return rows or [{"key": "r1", "label": "Activity mark", "max": 100.0}]


def _rubric(work):
    """The rubric of a lab (labN) or a class activity (activityN)."""
    return _activity_rubric(work) if work in ACTIVITY_SPECS else _lab_rubric(work)


def _load_marks():
    try:
        with open(_MARKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_marks(data):
    """Write the marks file. Must be called with _marks_lock held."""
    tmp = _MARKS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    os.chmod(tmp, 0o600)  # marks are private to the service account
    os.replace(tmp, _MARKS_FILE)


def _mark_view(lab, entry, rubric=None):
    """A stored mark with its rubric rows and totals. entry may be None."""
    rubric = rubric or _rubric(lab)
    entry = entry or {}
    given = entry.get("rows", {})
    rows, total, marked = [], 0.0, 0
    for r in rubric:
        points = given.get(r["key"])
        if points is not None:
            total += points
            marked += 1
        rows.append({"key": r["key"], "label": r["label"],
                     "max": r["max"], "points": points})
    return {
        "rows": rows,
        "total": round(total, 2) if marked else None,
        "max": sum(r["max"] for r in rubric),
        "complete": marked == len(rubric),
        "comment": entry.get("comment", ""),
        "published": bool(entry.get("published")),
        "updated": entry.get("updated", ""),
    }


def _mark_summary(lab, username, marks):
    """The short form shown in tables, or None when nothing is marked."""
    entry = marks.get(lab, {}).get(username)
    if not entry:
        return None
    view = _mark_view(lab, entry)
    return {k: view[k] for k in ("total", "max", "complete", "published")}


def _oslab_modules():
    """The lab helper and its instructor module from this repository."""
    import sys
    folder = str(_REPO_ROOT / "server")
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        import oslab
        import oslab_teach
        return oslab, oslab_teach
    except Exception:
        return None


def _expected_text(item):
    kind, expect = item["kind"], item["expect"]
    if expect is None:
        return ""
    if kind == "int":
        return " or ".join(str(x) for x in expect)
    if kind == "yesno":
        return "yes" if expect == "y" else "no"
    if kind == "path":
        return os.path.relpath(expect[1], expect[0]).replace(os.sep, "/")
    return str(expect)


def _oslab_activity(username, lab):
    """What the student did with oslab in this lab: pre-lab, prediction,
    hints, checks and checkpoint, with the answers marked."""
    mods = _oslab_modules()
    if not mods:
        return {"available": False,
                "reason": "The lab helper is not installed with this site."}
    oslab, teach = mods
    if lab not in oslab.PREDICT:
        return {"available": False,
                "reason": "This lab collects its prediction and checkpoint on paper."}
    try:
        users, flagged = teach.scan(lab)
    except (ValueError, OSError) as exc:
        return {"available": False,
                "reason": f"The class inbox cannot be read: {exc}"}
    kinds = users.get(username, {})
    nonce = teach.released(lab)
    values = oslab.lab_values(lab, username)

    def marked(items, given):
        out = []
        for item in items:
            answer = given.get(item["key"], "")
            out.append({
                "key": item["key"], "question": item["text"], "answer": answer,
                "expected": _expected_text(item),
                "ok": oslab.mark(item["kind"], item["expect"], answer),
            })
        return out

    checks = [{"passed": c.get("passed", 0), "total": c.get("total", 0),
               "failed": c.get("failed", []), "reasons": c.get("reasons", {}), "time": c.get("time", ""),
               "checkpoint": c.get("checkpoint"), "pathError": c.get("path_error")}
              for c in kinds.get("check", [])]
    out = {
        "available": True, "values": values, "released": bool(nonce),
        "flag": username in flagged,
        "started": bool(kinds.get("start")),
        "prelab": None, "prediction": None, "debrief": None, "checkpoint": None,
        "hints": [{"level": h.get("level"), "time": h.get("time", "")}
                  for h in kinds.get("hint", [])],
        "checks": checks,
    }
    if kinds.get("prelab"):
        first = kinds["prelab"][0]
        out["prelab"] = {"firstTry": first.get("first_try"),
                         "questions": first.get("questions"),
                         "time": first.get("time", "")}
    if kinds.get("predict"):
        first = kinds["predict"][0]
        out["prediction"] = {
            "time": first.get("time", ""),
            "answers": marked(oslab.PREDICT[lab](values), first.get("answers", {})),
        }
    if kinds.get("debrief"):
        last = kinds["debrief"][-1]  # a student may run the debrief again; the last one counts
        items = [item for item in oslab.PREDICT[lab](values) if item["expect"] is not None]
        out["debrief"] = {"time": last.get("time", ""),
                          "answers": marked(items, last.get("answers", {}))}
    if kinds.get("checkpoint"):
        first = kinds["checkpoint"][0]
        practice = bool(first.get("practice")) or not nonce
        entry = {"time": first.get("time", ""), "practice": practice,
                 "values": first.get("values", {}), "answers": [],
                 "taskDone": any(c["checkpoint"] for c in checks)}
        if not practice:
            items = oslab.checkpoint_task(lab, username, nonce)[2]
            entry["answers"] = marked(items, first.get("answers", {}))
        out["checkpoint"] = entry
    return out


def _share(right, total):
    """1 point when all are right, half when at least half are, else 0."""
    if not total:
        return 0.0
    return 1.0 if right == total else 0.5 if right * 2 >= total else 0.0


def _mark_suggestions(rubric, activity, grade=None, lab=None):
    """Provisional points from lab records, for the pilot rubric.
    grade is the file check of the submitted folder, for the last row."""
    if not activity.get("available"):
        return {}
    if [r["max"] for r in rubric] != [2.0, 2.0, 2.0, 3.0, 1.0]:
        return {}
    out = {}
    best = max(activity["checks"], key=lambda c: c["passed"], default=None)
    if best:
        extra = 0 if best["checkpoint"] is None else 1
        core_total = best["total"] - extra
        core_passed = best["passed"] - (1 if best["checkpoint"] else 0)
        error = best.get("pathError")
        if error is not None:
            # Labs 2 and 3: the path-error / failure-and-repair milestone belongs to the tests row, not to the files row.
            found, fixed = bool(error.get("error")), bool(error.get("fix"))
            core_total -= 1
            core_passed -= 1 if found and fixed else 0
            out["r2"] = {
                "points": float(found) + float(fixed),
                "note": (f"links.txt: failure after the rename {'recorded' if found else 'missing'}, "
                         f"repair {'recorded' if fixed else 'missing or wrong'}" if lab == "lab3" else
                         f"paths.txt: Error line {'found' if found else 'missing'}, "
                         f"Fix path {'works' if fixed else 'missing or wrong'}"),
            }
        if core_total > 0:
            out["r1"] = {
                "points": round(2 * core_passed / core_total * 2) / 2,
                "note": f"{core_passed} of {core_total} milestones passed",
            }
    if activity.get("prediction"):
        debrief = activity.get("debrief")
        if debrief:
            marks = [a["ok"] for a in debrief["answers"] if a["ok"] is not None]
            out["r3"] = {"points": 1.0 + _share(sum(marks), len(marks)),
                         "note": f"saved in time; debrief: {sum(marks)} of {len(marks)} answers right"}
        else:
            out["r3"] = {"points": 1.0,
                         "note": "saved in time; no debrief yet (add 1 for the correction in the report)"}
    cp = activity.get("checkpoint")
    if cp and not cp["practice"]:
        parent = [a["ok"] for a in cp["answers"] if a.get("key") == "parent" and a["ok"] is not None]
        marks = [a["ok"] for a in cp["answers"] if a.get("key") != "parent" and a["ok"] is not None]
        task = 1.0 if cp["taskDone"] else 0.0
        note = (f"{sum(marks)} of {len(marks)} answers right, file task "
                f"{'done' if cp['taskDone'] else 'not done'}")
        if parent:
            note += f", .. question {'right' if parent[0] else 'wrong'}"
        else:
            note += "; add up to 1 for the sentence"
        out["r4"] = {"points": _share(sum(marks), len(marks)) + task + (1.0 if parent and parent[0] else 0.0),
                     "note": note}
    if grade and grade.get("found"):
        missing = [i["expected"] for i in grade.get("items", []) if i.get("status") != "ok"]
        percent = grade.get("finalPercentage", 0)
        out["r5"] = {"points": 1.0 if percent >= 100 else 0.5 if percent >= 50 else 0.0,
                     "note": "every required file submitted on time" if not missing and percent >= 100
                             else f"file check {percent:g}%" + (f"; missing or misnamed: {', '.join(missing)}" if missing else "; late")}
    return out


def _student_file(username, lab, rel):
    """Read one file of a student's lab folder. Returns (data, error).
    Refuses anything that leaves the lab folder or the student's home,
    because the service account can read more than a student may show."""
    if lab in ACTIVITY_SPECS:
        root = _find_activity_root(username, lab)
    else:
        root = _find_lab_root(username, lab)
    if not root:
        return None, "Lab directory not found."
    if not rel or rel.startswith(("/", "\\")) or ".." in Path(rel).parts:
        return None, "Not a path inside the lab folder."
    try:
        home_real = Path(f"/home/{username}").resolve(strict=True)
        root_real = root.resolve(strict=True)
        real = (root / rel).resolve(strict=True)
    except (OSError, RuntimeError):
        return None, "File not found."
    if home_real not in root_real.parents or root_real not in real.parents:
        return None, "Not a file inside this lab folder."
    if not real.is_file():
        return None, "Not a regular file."
    size = real.stat().st_size
    kind = _IMAGE_TYPES.get(real.suffix.lower())
    try:
        if kind:
            if size > _IMAGE_LIMIT:
                return None, "The picture is larger than 4 MB."
            import base64
            data = base64.b64encode(real.read_bytes()).decode("ascii")
            return {"path": rel, "kind": "image", "size": size,
                    "dataUrl": f"data:{kind};base64,{data}"}, None
        with open(real, "rb") as f:
            raw = f.read(_TEXT_LIMIT + 1)
    except OSError:
        return None, "The file cannot be read."
    if b"\0" in raw:
        return {"path": rel, "kind": "binary", "size": size}, None
    return {"path": rel, "kind": "text", "size": size,
            "truncated": len(raw) > _TEXT_LIMIT,
            "content": raw[:_TEXT_LIMIT].decode("utf-8", "replace")}, None

# ══════════════════════════════════════════════════════════════
#  Flask Application & Routes
# ══════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder=None)
CORS(app)


# ── Auth Routes ────────────────────────────────────────────────


@app.route("/api/auth/login", methods=["POST"])
def route_auth_login():
    body = request.get_json(silent=True) or {}
    ip = _get_client_ip()
    if _rate_limited(ip):
        return jsonify({"error": "Too many attempts. Try again later."}), 429
    username = str(body.get("username", "")).strip()[:32]
    password = body.get("password", "")
    if not username or not password:
        return jsonify({"error": "Username and password required."}), 400
    # Count failed attempts per address and account: a whole computer room shares one public address, so a
    # per-address limit that also counted good logins locked students out when the class logged in together.
    if _rate_limited(ip + "|" + username):
        return jsonify({"error": "Too many attempts. Try again later."}), 429
    if not verify_password(username, password):
        _record_attempt(ip + "|" + username)
        _record_attempt(ip)
        return jsonify({"error": "Invalid credentials."}), 401
    token, role = create_session(username)
    return jsonify({
        "ok": True, "token": token, "user": username, "role": role,
    })


@app.route("/api/auth/verify", methods=["POST"])
def route_auth_verify():
    body = request.get_json(silent=True) or {}
    token = _get_token() or str(body.get("token", ""))
    session = validate_token(token)
    if session:
        return jsonify({
            "valid": True, "user": session["username"],
            "role": session["role"],
        })
    return jsonify({"valid": False}), 401


@app.route("/api/auth/logout", methods=["POST"])
def route_auth_logout():
    body = request.get_json(silent=True) or {}
    token = _get_token() or str(body.get("token", ""))
    with _session_lock:
        _sessions.pop(token, None)
        _save_sessions()
    return jsonify({"ok": True})


# ── Web Presence Routes ────────────────────────────────────────


@app.route("/api/web/login", methods=["POST"])
def route_web_login():
    body = request.get_json(silent=True) or {}
    name = str(body.get("name", "")).strip()[:50]
    sid = str(body.get("sessionId", "")).strip()[:64]
    if not name or not sid:
        return jsonify({"error": "name and sessionId required"}), 400
    _prune_web_users()
    _web_users[sid] = {
        "name": name, "loginTime": time.time(), "lastSeen": time.time(),
    }
    return jsonify({"ok": True, "count": len(_web_users)})


@app.route("/api/web/heartbeat", methods=["POST"])
def route_web_heartbeat():
    body = request.get_json(silent=True) or {}
    sid = str(body.get("sessionId", "")).strip()[:64]
    if sid in _web_users:
        _web_users[sid]["lastSeen"] = time.time()
    _prune_web_users()
    return jsonify({"ok": True, "count": len(_web_users)})


@app.route("/api/web/logout", methods=["POST"])
def route_web_logout():
    body = request.get_json(silent=True) or {}
    sid = str(body.get("sessionId", "")).strip()[:64]
    _web_users.pop(sid, None)
    _prune_web_users()
    return jsonify({"ok": True, "count": len(_web_users)})


@app.route("/api/web/users")
@auth_required
def route_web_users():
    _prune_web_users()
    users = [
        {"name": v["name"], "loginTime": v["loginTime"], "sessionId": k}
        for k, v in _web_users.items()
    ]
    users.sort(key=lambda u: u["loginTime"])
    return jsonify({
        "users": users, "count": len(users),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


# ── Server Presence Routes ─────────────────────────────────────


@app.route("/api/users")
@auth_required
def route_api_users():
    users = get_logged_in_users()
    return jsonify({
        "users": users, "count": len(users),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/api/who")
def route_api_who():
    try:
        result = subprocess.run(
            ["who"], capture_output=True, text=True, timeout=5,
        )
        return jsonify({
            "output": result.stdout,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return jsonify({"output": "", "error": "who command not available"})


@app.route("/api/last")
def route_api_last():
    count = request.args.get("n", 20, type=int)
    count = max(1, min(count, 100))
    return jsonify({
        "entries": get_recent_logins(count),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/api/health")
def route_api_health():
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat() + "Z",
    })


# ── Admin Routes ───────────────────────────────────────────────


@app.route("/api/admin/stats")
@admin_required
def route_admin_stats():
    return jsonify({
        "users": get_user_stats(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/api/admin/grades")
@admin_required
def route_admin_grades():
    lab = request.args.get("lab")
    user = request.args.get("user")
    marks = _load_marks()
    if user and lab:
        grade = grade_student_lab(user, lab)
        grade["mark"] = _mark_summary(lab, user, marks)
        return jsonify(grade)
    results = grade_all_students(lab)
    for g in results:
        g["mark"] = _mark_summary(g.get("lab"), g.get("username"), marks)
    return jsonify({"grades": results, "labs": list(LAB_SPECS.keys())})


@app.route("/api/admin/leaderboard")
@admin_required
def route_admin_leaderboard():
    # "leaderboard" (file scores) feeds the Total tab; "marks" is the
    # leaderboard proper, ranked by published instructor marks.
    return jsonify({
        "leaderboard": get_leaderboard(),
        "marks": get_marks_board(),
        "labs": list(LAB_SPECS.keys()),
        "activities": list(ACTIVITY_SPECS.keys()),
    })


@app.route("/api/admin/tree")
@admin_required
def route_admin_tree():
    user = request.args.get("user")
    lab = request.args.get("lab")
    if not user or not lab:
        return jsonify({"error": "user and lab params required"}), 400
    tree = get_student_tree(user, lab)
    if tree is None:
        return jsonify({"error": "Lab directory not found"}), 404
    return jsonify(tree)


@app.route("/api/admin/deadlines", methods=["POST"])
@admin_required
def route_admin_deadlines_post():
    body = request.get_json(silent=True) or {}
    deadlines = body if isinstance(body, dict) else {}
    clean = {}
    for lab_key, val in deadlines.items():
        lab_key = str(lab_key).strip()[:20]
        if not lab_key or not isinstance(val, dict):
            continue
        due = str(val.get("due", "")).strip()[:30]
        penalty = val.get("penalty", 5)
        if isinstance(penalty, (int, float)):
            penalty = max(0, min(100, int(penalty)))
        else:
            penalty = 5
        if due:
            clean[lab_key] = {"due": due, "penalty": penalty}
    global _deadlines
    _deadlines = clean
    _save_deadlines(clean)
    return jsonify({"ok": True, "deadlines": clean})


@app.route("/api/admin/activities")
@admin_required
def route_admin_activities():
    activity = request.args.get("activity")
    user = request.args.get("user")
    marks = _load_marks()
    if user and activity:
        grade = grade_student_activity(user, activity)
        grade["mark"] = _mark_summary(activity, user, marks)
        return jsonify(grade)
    grades = grade_all_activities(activity)
    for g in grades:
        g["mark"] = _mark_summary(g.get("activity"), g.get("username"), marks)
    return jsonify({
        "grades": grades, "activities": list(ACTIVITY_SPECS.keys()),
    })


@app.route("/api/admin/activity-tree")
@admin_required
def route_admin_activity_tree():
    user = request.args.get("user")
    activity = request.args.get("activity")
    if not user or not activity:
        return jsonify({"error": "user and activity params required"}), 400
    tree = get_student_activity_tree(user, activity)
    if tree is None:
        return jsonify({"error": "Activity directory not found"}), 404
    return jsonify(tree)


# ── Instructor marks (admin) ───────────────────────────────────


def _mark_target():
    """(user, lab, error response) from the query string or JSON body."""
    body = request.get_json(silent=True) or {}
    user = request.args.get("user") or body.get("user")
    lab = request.args.get("lab") or body.get("lab")
    if lab not in LAB_SPECS and lab not in ACTIVITY_SPECS:
        return None, None, (jsonify({"error": "Unknown lab or activity."}), 400)
    if user not in _USER_TO_SID:
        return None, None, (jsonify({"error": "Student not found in roster."}), 404)
    return user, lab, None


@app.route("/api/admin/mark")
@admin_required
def route_admin_mark():
    user, lab, error = _mark_target()
    if error:
        return error
    rubric = _rubric(lab)
    # Class activities have no oslab records, so nothing to suggest from.
    activity = None if lab in ACTIVITY_SPECS else _oslab_activity(user, lab)
    sid = _USER_TO_SID[user]
    return jsonify({
        "user": user, "lab": lab, "id": sid, "name": STUDENTS[sid]["name"],
        "mark": _mark_view(lab, _load_marks().get(lab, {}).get(user), rubric),
        "suggested": _mark_suggestions(rubric, activity, grade_student_lab(user, lab), lab=lab) if activity else {},
        "activity": activity,
    })


@app.route("/api/admin/mark", methods=["POST"])
@admin_required
def route_admin_mark_post():
    user, lab, error = _mark_target()
    if error:
        return error
    body = request.get_json(silent=True) or {}
    given = body.get("rows") if isinstance(body.get("rows"), dict) else {}
    rows = {}
    for r in _rubric(lab):
        value = given.get(r["key"])
        if value is None or value == "":
            continue
        try:
            points = round(float(value) * 2) / 2
        except (TypeError, ValueError):
            return jsonify({"error": f"Points for '{r['label']}' must be a number."}), 400
        if not 0 <= points <= r["max"]:
            return jsonify({"error": f"Points for '{r['label']}' must be between 0 and {r['max']:g}."}), 400
        rows[r["key"]] = points
    entry = {
        "rows": rows,
        "comment": str(body.get("comment", ""))[:2000],
        "published": bool(body.get("published")),
        "updated": datetime.now(_PPH).isoformat(timespec="seconds"),
        "by": request._session["username"],  # type: ignore
    }
    with _marks_lock:
        marks = _load_marks()
        marks.setdefault(lab, {})[user] = entry
        _save_marks(marks)
    return jsonify({"ok": True, "mark": _mark_view(lab, entry)})


@app.route("/api/admin/marks/publish", methods=["POST"])
@admin_required
def route_admin_marks_publish():
    body = request.get_json(silent=True) or {}
    lab = body.get("lab")
    if lab not in LAB_SPECS and lab not in ACTIVITY_SPECS:
        return jsonify({"error": "Unknown lab or activity."}), 400
    published = bool(body.get("published"))
    with _marks_lock:
        marks = _load_marks()
        entries = marks.get(lab, {})
        for entry in entries.values():
            entry["published"] = published
        _save_marks(marks)
    return jsonify({"ok": True, "lab": lab, "published": published, "count": len(entries)})


@app.route("/api/admin/file")
@admin_required
def route_admin_file():
    user, lab, error = _mark_target()
    if error:
        return error
    data, problem = _student_file(user, lab, request.args.get("path", ""))
    if problem:
        return jsonify({"error": problem}), 404
    return jsonify(data)


# ── Deadlines (any authenticated user) ────────────────────────


@app.route("/api/deadlines")
@auth_required
def route_api_deadlines():
    return jsonify({"deadlines": _load_deadlines()})


# ── Student Self-Service Routes ────────────────────────────────


def _get_student_info():
    """Look up student from current session. Returns (sid, info)."""
    username = request._session["username"] # type: ignore
    sid = _USER_TO_SID.get(username)
    info = STUDENTS.get(sid) if sid else None
    return sid, info


@app.route("/api/my/profile")
@auth_required
def route_my_profile():
    """The logged-in account for the portal's profile page: account, role, the student's own ID and name, and
    their practice rank when the practice room is installed."""
    s = request._session  # type: ignore
    user = s["username"]
    sid = _USER_TO_SID.get(user)
    out = {"user": user, "role": s["role"], "id": sid or "", "name": STUDENTS.get(sid, {}).get("name", "") if sid else ""}
    if sid:
        _common, prac = _practice_mods()
        if prac:
            try:
                entries, metas, profs = prac.ledger(), prac.all_metas(), prac.profiles()
                profile, _st = _practice_profile(prac, user, entries, metas, profs)
                out["practice"] = {"xp": profile["xp"], "rank": profile["rank"], "clears": profile["clears"],
                                   "nick": (profs.get(user) or {}).get("nick", "")}
            except Exception as exc:  # practice data unreadable: the profile still works
                print("[profile] practice:", exc, flush=True)
    return jsonify(out)


@app.route("/api/my/grades")
@auth_required
def route_my_grades():
    sid, info = _get_student_info()
    if not info:
        return jsonify({"error": "Student not found in roster"}), 404
    linux_user = info["user"]
    labs = list(LAB_SPECS.keys())
    grades = []
    for lab in labs:
        try:
            g = grade_student_lab(linux_user, lab)
            g["id"] = sid or ""
            g["name"] = info["name"]
            grades.append(g)
        except (PermissionError, OSError):
            grades.append({
                "username": linux_user, "id": sid, "name": info["name"],
                "lab": lab, "score": 0, "finalScore": 0,
                "total": LAB_SPECS[lab]["total_points"],
                "percentage": 0, "finalPercentage": 0,
                "found": False, "labPath": None,
                "items": [],
                "feedback": ["Cannot access lab directory."],
            })
    marks = _load_marks()
    for g in grades:
        entry = marks.get(g.get("lab"), {}).get(linux_user)
        g["mark"] = _mark_view(g["lab"], entry) if entry and entry.get("published") else None
    return jsonify({"grades": grades, "labs": labs})


@app.route("/api/my/tree")
@auth_required
def route_my_tree():
    sid, info = _get_student_info()
    if not info:
        return jsonify({"error": "Student not found in roster"}), 404
    lab = request.args.get("lab")
    if not lab:
        return jsonify({"error": "lab param required"}), 400
    tree = get_student_tree(info["user"], lab)
    if tree is None:
        return jsonify({"error": "Lab directory not found"}), 404
    return jsonify(tree)


@app.route("/api/my/leaderboard")
@auth_required
def route_my_leaderboard():
    """Ranked by published marks. A student sees only the rank, the student
    ID (as before), the score and whether the row is their own: no names, account names, file scores or
    per-lab marks of other students."""
    me = request._session["username"]  # type: ignore
    full = get_marks_board()
    board = [{
        "rank": r["rank"], "id": r["id"], "percentage": r["percentage"],
        "me": r["username"] == me,
    } for r in full]
    return jsonify({"leaderboard": board, "works": full[0]["of"] if full else 0})


@app.route("/api/my/activities")
@auth_required
def route_my_activities():
    sid, info = _get_student_info()
    if not info:
        return jsonify({"error": "Student not found in roster"}), 404
    linux_user = info["user"]
    acts = list(ACTIVITY_SPECS.keys())
    grades = []
    for act in acts:
        try:
            g = grade_student_activity(linux_user, act)
            g["id"] = sid or ""
            g["name"] = info["name"]
            grades.append(g)
        except (PermissionError, OSError):
            grades.append({
                "username": linux_user, "id": sid or "",
                "name": info["name"], "activity": act, "score": 0,
                "finalScore": 0,
                "total": ACTIVITY_SPECS[act]["total_points"],
                "percentage": 0, "finalPercentage": 0,
                "found": False, "activityPath": None,
                "items": [],
                "feedback": ["Cannot access activity directory."],
            })
    marks = _load_marks()
    for g in grades:
        entry = marks.get(g.get("activity"), {}).get(linux_user)
        g["mark"] = _mark_view(g["activity"], entry) if entry and entry.get("published") else None
    return jsonify({"grades": grades, "activities": acts})


@app.route("/api/my/activity-tree")
@auth_required
def route_my_activity_tree():
    sid, info = _get_student_info()
    if not info:
        return jsonify({"error": "Student not found in roster"}), 404
    activity = request.args.get("activity")
    if not activity:
        return jsonify({"error": "activity param required"}), 400
    tree = get_student_activity_tree(info["user"], activity)
    if tree is None:
        return jsonify({"error": "Activity directory not found"}), 404
    return jsonify(tree)


# ── Exam room (see server/examroom/README.md) ─────────────────
# The paper, the terminal ticket and the progress for students; the board and the replay for the instructor.
# The exam config and state are written by `sudo examctl`; this service only reads them.

_EXAM_CACHE = {"board": None, "ts": 0.0}


def _has_account(user):
    """`examctl open` leaves out roster names that have no account on the server, so the preview does the same."""
    import pwd
    try:
        pwd.getpwnam(user)
        return True
    except KeyError:
        return False


def _exam_modules():
    """The exam modules: the installed copy in /opt/itc-os-exam first (it has the paper, which is not in git), else
    the repository's server/examroom."""
    import sys
    for folder in (os.environ.get("ITC_EXAM_OPT", "/opt/itc-os-exam"), str(_REPO_ROOT / "server" / "examroom")):
        if os.path.exists(os.path.join(folder, "midterm.py")):
            break
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        import common as exam_common
        import midterm as exam_midterm
        # before the exam has drawn, the preview and "view as student" show the draw `examctl open` will write: the balanced
        # deal over this roster
        exam_midterm.set_roster_source(lambda: [i["user"] for i in STUDENTS.values() if _has_account(i["user"])])
        return exam_common, exam_midterm
    except Exception as exc:  # oslab or the exam files missing
        print("[exam] modules not loaded:", exc, flush=True)
        return None, None


def _exam_parts(cfg, midterm):
    return [p for p in cfg.get("parts", []) if p in midterm.PART_TITLES]


def _exam_folder(cfg, username):
    return Path(os.path.expanduser("~" + username)) / cfg.get("folder", "midterm")


def _exam_seb(cfg, common):
    public = (cfg.get("seb") or {}).get("public_api", "").rstrip("/")
    url = (public + request.full_path.rstrip("?")) if public else request.url
    return common.seb_ok(cfg, url, request.headers.get("X-SafeExamBrowser-ConfigKeyHash", ""))


def _exam_checks(cfg, midterm, username, parts):
    try:
        return midterm.checks(_exam_folder(cfg, username), username, parts)
    except (PermissionError, OSError, midterm.eb.BankError):
        return None


@app.route("/api/exam/state")
@auth_required
def route_exam_state():
    common, midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"exam": None})
    session = request._session  # type: ignore
    is_admin = session["role"] == "admin"
    username = session["username"]
    preview = request.args.get("user", "") if is_admin else ""
    target = preview or username
    state = common.load_state(cfg)
    parts = _exam_parts(cfg, midterm)
    sid = _USER_TO_SID.get(target)
    participant = bool(sid)
    seb = _exam_seb(cfg, common)
    out = {
        "exam": {"id": cfg["id"], "title": cfg["title"], "duration_min": cfg["duration_min"],
                 "parts": [{"id": p, "title": midterm.PART_TITLES[p][0], "lab": midterm.PART_TITLES[p][1], "marks": 10}
                           for p in parts],
                 "total": 10 * len(parts), "rain": bool(cfg.get("rain")),
                 "large_paste_chars": cfg["flags"]["large_paste_chars"], "folder": cfg["folder"],
                 "lock_on": cfg["lock"]["on"], "lock_mode": cfg["lock"]["mode"]},
        "phase": state["phase"], "start": state["start"], "end": state["end"], "now": common.iso(time.time()),
        "me": {"user": target, "id": sid or "", "name": STUDENTS.get(sid, {}).get("name", "") if sid else "",
               "admin": is_admin, "participant": participant},
        "seb_ok": seb, "seb_required": bool(cfg["seb"].get("required")),
    }
    show = (state["phase"] in ("open", "ended") and participant and seb) or (preview and participant)
    if show:
        try:
            out["paper"] = midterm.paper(target, parts, cfg["folder"])
        except midterm.eb.BankError as e:
            print("[exam] paper of %s: %s" % (target, e), flush=True)
            out["paper"] = None
            out["paper_error"] = "Your paper is not available. Tell the invigilator."
        result = _exam_checks(cfg, midterm, target, parts)
        if result is None:
            out["progress"] = None
        elif preview:
            out["checks"] = result
            out["progress"] = midterm.progress(result)
        else:
            out["progress"] = {p: {"present": v["present"], "of": v["of"]} for p, v in midterm.progress(result).items()}
        if state["phase"] == "open" and not preview:
            out["gateway_url"] = cfg.get("gateway_url", "")
    return jsonify(out)


@app.route("/api/exam/ticket", methods=["POST"])
@auth_required
def route_exam_ticket():
    common, _midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"error": "No exam is set up."}), 404
    username = request._session["username"]  # type: ignore
    if username not in _USER_TO_SID:
        return jsonify({"error": "This account is not on the exam roster."}), 403
    if common.load_state(cfg)["phase"] != "open":
        return jsonify({"error": "The exam is not open."}), 409
    if not _exam_seb(cfg, common):
        return jsonify({"error": "Open the exam in Safe Exam Browser."}), 403
    try:
        ticket = common.make_ticket(username, cfg["id"])
    except (OSError, ValueError) as exc:
        print("[exam] ticket:", exc, flush=True)
        return jsonify({"error": "The exam server is not ready (ticket key)."}), 503
    return jsonify({"ticket": ticket, "url": cfg.get("gateway_url", ""), "ttl": common.TICKET_TTL})


def _exam_board(common, midterm, cfg):
    state = common.load_state(cfg)
    parts = _exam_parts(cfg, midterm)
    rows = []
    for sid, info in sorted(STUDENTS.items()):
        user = info["user"]
        status = common.read_json(common.rec_dir(user) / "status.json", {}) or {}
        events = common.read_events(user)
        summary = common.summarize(events, status, cfg, state)
        result = _exam_checks(cfg, midterm, user, parts)
        prog = midterm.progress(result) if result is not None else None
        now = time.time()
        if status.get("connected") and now - float(status.get("last_seen", 0)) < 20:
            conn, conn_s = "connected", 0
        elif status.get("last_seen"):
            conn_s = now - float(status["last_seen"])
            conn = "reconnecting" if conn_s < 60 else "offline"  # a gateway that stopped leaves connected=true behind
        else:
            conn, conn_s = "never", 0
        lock = common.current_lock(user, cfg, state)
        wait = lock.get("mode") == "wait"
        try:
            code = common.unlock_code(user, cfg["id"], lock["n"]) if lock["locked"] and not wait else ""
        except (OSError, ValueError):
            code = ""
        summary.update(locked=bool(lock["locked"]), lock_why=lock["why"] if lock["locked"] else "", lock_n=int(lock["n"]),
                       lock_s=round(common.lock_seconds(lock)), unlock_code=code,
                       lock_mode="wait" if wait else "code", lock_left=common.lock_left(lock))
        rows.append({"id": sid, "name": info["name"], "user": user, "connection": conn,
                     "connection_s": round(conn_s), "connects": status.get("connects", 0),
                     "last_cmd": status.get("last_cmd", ""), "truncated": bool(status.get("truncated")),
                     "progress": prog, "points": sum(p["points"] for p in prog.values()) if prog else None,
                     **summary})
    order = {"high": 0, "review": 1, "": 2}
    rows.sort(key=lambda r: (not r["locked"], order.get(r["flag"], 2), r["id"]))  # locked students waiting for a code first
    end_ts = None
    if state.get("end"):
        try:
            end_ts = common.parse_iso(state["end"])
        except ValueError:
            pass
    return {"exam": {"id": cfg["id"], "title": cfg["title"], "parts": parts, "total": 10 * len(parts),
                     "large_paste_chars": cfg["flags"]["large_paste_chars"], "lock_on": cfg["lock"]["on"],
                     "lock_mode": cfg["lock"]["mode"], "profile": cfg["profile"]},
            "phase": state["phase"], "start": state["start"], "end": state["end"], "now": common.iso(time.time()),
            "left_s": max(0, round(end_ts - time.time())) if end_ts else None,
            "connected": sum(1 for r in rows if r["connection"] == "connected"),
            "students": len(rows), "high": sum(1 for r in rows if r["flag"] == "high"),
            "review": sum(1 for r in rows if r["flag"] == "review"),
            "locked": sum(1 for r in rows if r["locked"]),
            "rows": rows}


@app.route("/api/admin/exam/board")
@admin_required
def route_admin_exam_board():
    common, midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"exam": None, "rows": []})
    if _EXAM_CACHE["board"] is None or time.time() - _EXAM_CACHE["ts"] > 3:
        _EXAM_CACHE["board"] = _exam_board(common, midterm, cfg)
        _EXAM_CACHE["ts"] = time.time()
    return jsonify(_EXAM_CACHE["board"])


def _exam_target_user(common):
    user = request.args.get("user", "")
    if not common.USER_RE.match(user) or user not in _USER_TO_SID:
        return None
    return user


@app.route("/api/admin/exam/replay")
@admin_required
def route_admin_exam_replay():
    common, midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"error": "No exam is set up."}), 404
    user = _exam_target_user(common)
    if not user:
        return jsonify({"error": "Unknown student."}), 404
    folder = common.rec_dir(user)
    casts = []
    try:
        for p in sorted(folder.iterdir()):
            if common.CAST_RE.match(p.name):
                casts.append({"name": p.name, "size": p.stat().st_size, "start": int(p.name.split(".")[0].split("-")[0])})
    except OSError:
        pass
    sid = _USER_TO_SID[user]
    state = common.load_state(cfg)
    status = common.read_json(folder / "status.json", {}) or {}
    events = common.read_events(user)
    return jsonify({"user": user, "id": sid, "name": STUDENTS[sid]["name"], "casts": casts, "events": events,
                    "status": status, "summary": common.summarize(events, status, cfg, state),
                    "start": state["start"], "end": state["end"],
                    "checks": _exam_checks(cfg, midterm, user, _exam_parts(cfg, midterm))})


@app.route("/api/admin/exam/cast")
@admin_required
def route_admin_exam_cast():
    common, _midterm = _exam_modules()
    if not common:
        return jsonify({"error": "No exam is set up."}), 404
    user = _exam_target_user(common)
    name = request.args.get("name", "")
    if not user or not common.CAST_RE.match(name):
        return jsonify({"error": "Unknown recording."}), 404
    path = common.rec_dir(user) / name
    try:
        with open(path, "rb") as f:
            data = f.read(25 * 1024 * 1024)
    except OSError:
        return jsonify({"error": "Unknown recording."}), 404
    return app.response_class(data, mimetype="application/x-asciicast")


# ── Exam control panel (instructor board tabs) ────────────────
# Settings and open / extend / close / harden go to the root helper as queued requests (only when the server was
# installed with `examctl install --web-control`); unlocking a student goes to the gateway. See common.py.

def _exam_gateway_ok():
    import urllib.request
    url = os.environ.get("ITC_EXAM_GW_HEALTH", "http://127.0.0.1:5010/term/health")
    try:
        with urllib.request.urlopen(url, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


@app.route("/api/admin/exam/control")
@admin_required
def route_admin_exam_control():
    common, _midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"exam": None})
    state = common.load_state(cfg)
    agent = common.agent_config()
    harden = common.read_json(common.var_dir() / "harden.json", None)
    locked = []
    for sid, info in sorted(STUDENTS.items()):
        lk = common.current_lock(info["user"], cfg, state)
        if lk["locked"]:
            locked.append(info["user"])
    return jsonify({
        "exam": {"id": cfg["id"], "title": cfg["title"], "duration_min": cfg["duration_min"], "folder": cfg["folder"],
                 "parts": cfg["parts"]},
        "state": state, "running": common.exam_running(state), "now": common.iso(time.time()),
        "settings": common.settings_view(cfg), "presets": common.PRESETS,
        "fixed_while_open": sorted(k for k, v in common.SETTINGS.items() if not v[2]),
        "seb_keys": bool((cfg.get("seb") or {}).get("config_keys")),
        "web_control": bool(agent), "preview": bool(agent and agent.get("dev")),
        "harden": harden if isinstance(harden, dict) else None,
        "gateway_ok": _exam_gateway_ok(),
        "students": len(STUDENTS), "locked": locked,
        "history": common.request_history(25),
    })


@app.route("/api/admin/exam/request", methods=["POST", "GET"])
@admin_required
def route_admin_exam_request():
    common, midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"error": "No exam is set up."}), 404
    if request.method == "GET":
        st = common.request_status(request.args.get("id", ""))
        return (jsonify(st), 200) if st else (jsonify({"error": "Unknown request."}), 404)
    if not common.agent_config():
        return jsonify({"error": "Web control is off on this server. Use examctl, or install with --web-control."}), 409
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify({"error": "Bad request."}), 400
    try:
        params = common.clean_request(body.get("action"), body.get("params"), common.exam_running(common.load_state(cfg)))
        _exam_check_bank_request(common, midterm, cfg, body["action"], params)
        rid = common.submit_request(body["action"], params, request._session["username"])  # type: ignore
    except (ValueError, midterm.eb.BankError) as e:
        return jsonify({"error": str(e)}), 400
    except OSError:
        return jsonify({"error": "The request folder is missing; reinstall with --web-control."}), 500
    return jsonify({"id": rid})


@app.route("/api/admin/exam/unlock", methods=["POST"])
@admin_required
def route_admin_exam_unlock():
    common, _midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"error": "No exam is set up."}), 404
    body = request.get_json(silent=True) or {}
    if body.get("all") is True:
        users = [info["user"] for info in STUDENTS.values()]
    else:
        user = str(body.get("user", ""))
        if not common.USER_RE.match(user) or user not in _USER_TO_SID:
            return jsonify({"error": "Unknown student."}), 404
        users = [user]
    state = common.load_state(cfg)
    users = [u for u in users if common.current_lock(u, cfg, state)["locked"]]
    try:
        for u in users:
            common.request_unlock(u, request._session["username"])  # type: ignore
    except OSError:
        return jsonify({"error": "The control folder is missing; run examctl install again."}), 500
    _EXAM_CACHE["board"] = None
    return jsonify({"sent": len(users)})


def _exam_check_bank_request(common, midterm, cfg, action, params):
    """The checks the API can make before it queues a request that touches the scenario bank (the root helper makes them again)."""
    state = common.load_state(cfg)
    if action == "settings" and any(k.startswith("bank.") for k in params["changes"]):
        if midterm.drawn():
            raise ValueError("The scenarios are already drawn: discard the draw first (only possible before the exam was opened).")
        midterm.check_bank_settings(params["changes"], [i["user"] for i in STUDENTS.values()], cfg)
    elif action == "correct":
        midterm.check_correction(params["scenario"], params["slot"])
    elif action in ("draw", "undraw"):
        st = common.read_json(common.state_path(cfg), {}) or {}
        if st.get("phase", "sealed") != "sealed" or st.get("start") or state["phase"] != "sealed":
            raise ValueError("The exam has been opened: its draw is final.")
        if action == "draw" and midterm.drawn():
            raise ValueError("Already drawn: discard the draw first to draw again.")
        if action == "undraw" and not midterm.drawn():
            raise ValueError("Nothing is drawn.")
        midterm.bank()


def _exam_snapshot(common, cfg, user):
    """(folder, source label) of what a student's marks are read from: the latest snapshot, else the live folder."""
    base = common.var_dir() / cfg["id"] / "collect"
    try:
        snaps = sorted((base / user).iterdir()) if (base / user).is_dir() else []
    except OSError:
        snaps = []
    return (snaps[-1], "snapshot " + snaps[-1].name) if snaps else (_exam_folder(cfg, user), "live folder")


@app.route("/api/admin/exam/report.csv")
@admin_required
def route_admin_exam_report():
    """Automatic points per task, from each student's latest snapshot, or the live folder when there is none. One column per
    part says which scenario the student drew; a regrade (corrections) is applied and the raw points are kept."""
    import csv
    import io
    common, midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"error": "No exam is set up."}), 404
    parts = _exam_parts(cfg, midterm)
    out = io.StringIO()
    w = csv.writer(out)
    try:
        w.writerow(midterm.report_header(parts))
        fixes = midterm.corrections()
        for sid, info in sorted(STUDENTS.items()):
            folder, source = _exam_snapshot(common, cfg, info["user"])
            w.writerow(midterm.report_row(sid, info["name"], info["user"], source, parts, folder, fixes))
    except midterm.eb.BankError as e:
        return jsonify({"error": str(e)}), 500
    resp = app.response_class(out.getvalue(), mimetype="text/csv")
    resp.headers["Content-Disposition"] = 'attachment; filename="%s-auto.csv"' % cfg["id"]
    return resp


@app.route("/api/admin/exam/draw")
@admin_required
def route_admin_exam_draw():
    """The Paper tab: the bank's status, the settings, and every student's drawn scenarios (the recorded draw, or what the draw
    will give). Read-only, needs no web control, and a bad bank or draw is reported as data."""
    common, midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"exam": None})
    state = common.load_state(cfg)
    st = common.read_json(common.state_path(cfg), {}) or {}
    view = midterm.bank_view(cfg)
    out = {"exam": {"id": cfg["id"], "phase": state["phase"], "drawn": midterm.drawn(),
                    "never_opened": st.get("phase", "sealed") == "sealed" and not st.get("start"),
                    "parts": _exam_parts(cfg, midterm)},
           "bank": view, "students": [], "counts": {}, "changed": 0, "web_control": bool(common.agent_config())}
    if not view["ok"]:
        return jsonify(out)
    bank = midterm.bank()
    for sid, info in sorted(STUDENTS.items()):
        user = info["user"]
        row = {"id": sid, "name": info["name"], "user": user, "scenarios": {}, "recorded": False, "error": ""}
        if not _has_account(user):   # `examctl open` leaves these out, so they are not part of the draw either
            row["error"] = "no account on this server: left out of the exam"
            out["students"].append(row)
            continue
        try:
            d = midterm.draw(user)
            row["scenarios"] = d["scenarios"]
            row["recorded"] = midterm.eb.draw_path(cfg["id"], user).exists()
            if row["recorded"] and midterm.eb.bank_changed(d, bank):
                out["changed"] += 1
            for part, scen in d["scenarios"].items():
                out["counts"].setdefault(part, {})
                out["counts"][part][scen] = out["counts"][part].get(scen, 0) + 1
        except midterm.eb.BankError as e:
            row["error"] = str(e)[:160]
        out["students"].append(row)
    return jsonify(out)


@app.route("/api/admin/exam/results")
@admin_required
def route_admin_exam_results():
    """The Results tab's per-scenario numbers: how many students drew each scenario and how they did on each slot, and the
    corrections in force. From the latest snapshots, or the live folders before the exam is closed."""
    common, midterm = _exam_modules()
    cfg = common.load_config() if common else None
    if not cfg:
        return jsonify({"exam": None})
    parts = _exam_parts(cfg, midterm)
    entries, problems = [], 0
    try:
        for sid, info in sorted(STUDENTS.items()):
            try:
                folder, _src = _exam_snapshot(common, cfg, info["user"])
                scen = midterm.draw(info["user"])["scenarios"]
                entries.append((scen, midterm.checks(folder, info["user"], parts)))
            except (PermissionError, OSError, midterm.eb.BankError):
                problems += 1
        bank = midterm.bank()
    except midterm.eb.BankError as e:
        return jsonify({"exam": {"id": cfg["id"]}, "error": str(e)})
    return jsonify({"exam": {"id": cfg["id"], "phase": common.load_state(cfg)["phase"], "parts": parts},
                    "stats": midterm.scenario_stats(entries, parts), "problems": problems,
                    "slots": {p.id: p.slot_ids() for p in midterm.PARTS if p.id in parts},
                    "scenarios": {part: [sc.id for sc in bank.scenarios[part]] for part in parts},
                    "corrections": midterm.corrections()})



# ── Practice Linux Commands (see server/practice/ and teaching/PRACTICE-SCENARIOS-PLAN.md) ─────────
# Students practise in the exam room's terminal, with their own values; checks run in the root runner (a Unix
# socket), and only these routes write the ledger, from a runner result. Real names never reach a student.

_PRACTICE_GAP = float(os.environ.get("ITC_PRACTICE_CHECK_GAP", "10"))
_PRACTICE_LAST = {}
_PRACTICE_MU = threading.Lock()


def _practice_mods():
    """(exam common, practice) from the installed copy in /opt/itc-os-exam, else the repository; (None, None)."""
    import sys
    opt = os.environ.get("ITC_EXAM_OPT", "/opt/itc-os-exam")
    if os.path.exists(os.path.join(opt, "common.py")) and os.path.exists(os.path.join(opt, "practice", "practice.py")):
        exam_dir, prac_dir = opt, os.path.join(opt, "practice")
    else:
        exam_dir, prac_dir = str(_REPO_ROOT / "server" / "examroom"), str(_REPO_ROOT / "server" / "practice")
    for folder in (exam_dir, prac_dir):
        if folder not in sys.path:
            sys.path.insert(0, folder)
    try:
        import common as exam_common
        import practice as prac
        return exam_common, prac
    except Exception as exc:
        print("[practice] modules not loaded:", exc, flush=True)
        return None, None


def _practice_open(common):
    if not common.load_practice():
        return False, "Practice is not set up on this server yet."
    if common.exam_blocks_practice():
        return False, "An exam is running: practice is closed until it ends."
    return True, ""


def _practice_profile(prac, user, entries, metas, profs):
    st = prac.standings(entries, metas).get(user) or prac.empty_standing()
    i = prac.rank_of(st)
    return {"xp": st["xp"], "week": st["week"], "rank": prac.RANKS[i][0], "rank_i": i, "ranks": [r[0] for r in prac.RANKS],
            "rank_xp": prac.RANKS[i][1], "next": prac.next_rank(st), "supers": len(st["supers"]), "clears": len(st["cleared"]),
            "skills": prac.skills_summary(st),
            "badges": prac.badges_of(st, metas, author=bool((profs.get(user) or {}).get("author")))}, st


def _practice_board(prac, entries, metas, profs, me):
    st = prac.standings(entries, metas)
    out = {}
    for key in ("week", "xp"):
        rows = sorted(((u, s[key]) for u, s in st.items() if s[key] > 0 and u in _USER_TO_SID),
                      key=lambda x: (-x[1], _USER_TO_SID[x[0]]))
        top, mine = [], None
        for i, (u, x) in enumerate(rows):
            p = profs.get(u) or {}
            row = {"pos": i + 1, "id": _USER_TO_SID[u], "nick": p.get("nick", ""), "xp": x,
                   "rank": prac.RANKS[prac.rank_of(st[u])][0], "me": u == me}
            if i < 10:
                top.append(row)
            if u == me:
                mine = row
        out["week" if key == "week" else "all"] = top
        out["me_week" if key == "week" else "me_all"] = mine
    return out


def _practice_expired(r, now=None):
    return bool(r) and (now or time.time()) > float(r.get("deadline") or 0)


def _practice_view(prac, mod, user, r, cleared):
    """A scenario or a drill (the roadmap's short exercise) as the page needs it."""
    m = prac.meta_of(mod)
    level = m["level"]
    drill = level in prac.KINDS
    out = {"meta": {k: m[k] for k in ("id", "track", "level", "title", "xp", "minutes", "learn")},
           "level_name": prac.LEVEL_NAME.get(level, "Drill"), "kind": "drill" if drill else "scenario",
           "hints_total": 0 if level == "super" else prac.MAX_HINTS.get(level, 3),
           "hint_share": list(prac.HINT_SHARE), "cleared_before": m["id"] in cleared}
    if m.get("stage") or m.get("skills"):   # a drill has a stage; a scenario only the skills it trains
        out["meta"].update(stage=m.get("stage", ""), skills=m.get("skills", []), readonly=bool(m.get("readonly")),
                           skill_titles=[prac.SKILLS[s]["title"] for s in m.get("skills", []) if s in prac.SKILLS])
    if r:
        v = prac.values(mod, user, r["attempt"])
        out["brief"] = mod.brief(v)
        out["steps"] = prac.steps_of(mod, v, r["attempt"])
        out["hints"] = prac.hints_of(mod, v)[: int(r.get("hints", 0))]
        if getattr(mod, "hint_steps", None):
            out["hint_steps"] = mod.hint_steps(v)[: int(r.get("hints", 0))]
        out["run"] = {k: r.get(k) for k in ("attempt", "started", "deadline", "minutes", "hints", "checks", "cleared", "last")}
        out["run"]["expired"] = _practice_expired(r)
        out["run"]["started_iso"] = datetime.fromtimestamp(r["started"], _PPH).isoformat(timespec="seconds")
        out["run"]["deadline_iso"] = datetime.fromtimestamp(r["deadline"], _PPH).isoformat(timespec="seconds")
    return out


def _practice_target():
    """The student a practice route works for, and why not (a message and a status) when there is none."""
    s = request._session  # type: ignore
    user = s["username"]
    if user not in _USER_TO_SID:
        return None, ("This account is not on the class roster.", 403)
    return user, None


def _practice_scenario(prac, sid):
    """A scenario or a drill (both have a workspace and a check in the runner); a quiz has neither."""
    return prac.exercise(sid) if isinstance(sid, str) and prac.SCENARIO_RE.match(sid) else None


def _practice_quizzes():
    """The quiz engine (server/practice/quizzes.py), or None. Its keys are read here, like the Super challenges' checkers."""
    import importlib
    try:
        return importlib.import_module("quizzes")
    except Exception as exc:
        print("[practice] quizzes not loaded:", exc, flush=True)
        return None


def _practice_roadmap(prac, st, runs, metas):
    """The Roadmap tab: six stages with their drills and quizzes, the skills acquired, and which exercises train each skill."""
    cleared, have = st["cleared"], st["skills"]
    tags = {}
    for sid, m in metas.items():
        kind = m["level"] if m["level"] in prac.KINDS else "scenario"
        for s in m.get("skills") or []:
            tags.setdefault(s, []).append({"id": sid, "kind": kind, "title": m["title"]})
    stages, earned_all = [], True
    for s in prac.STAGES:
        drills, quizzes = [], []
        for sid, m in metas.items():
            if m.get("stage") != s["id"]:
                continue
            c, r = cleared.get(sid), runs.get(sid)
            if m["level"] == "quiz":
                state = "passed" if c else ("progress" if (r or {}).get("attempt") else "new")
                quizzes.append({"id": sid, "title": m["title"], "xp": m["xp"], "minutes": m["minutes"], "state": state,
                                "best": int((r or {}).get("best", 0)), "skills": m.get("skills", [])})
            else:
                state = ("cleared_nohint" if c["hints"] == 0 else "cleared") if c else ("progress" if r else "new")
                drills.append({"id": sid, "title": m["title"], "xp": m["xp"], "minutes": m["minutes"], "state": state,
                               "skills": m.get("skills", []), "readonly": bool(m.get("readonly"))})
        skills = [{"id": k, "title": v["title"], "have": k in have} for k, v in prac.SKILLS.items() if v["stage"] == s["id"]]
        total = len(drills) + len(quizzes)
        done = sum(1 for x in drills if x["state"].startswith("cleared")) + sum(1 for x in quizzes if x["state"] == "passed")
        earned = bool(total) and done == total
        earned_all = earned_all and earned
        stages.append({"id": s["id"], "title": s["title"], "badge": s["badge"], "drills": drills, "quizzes": quizzes, "skills": skills,
                       "done": done, "total": total, "earned": earned, "skills_have": sum(1 for k in skills if k["have"])})
    return {"stages": stages, "skills": prac.skills_summary(st), "journeyman": earned_all and bool(stages), "tags": tags}


def _super_locked(prac, mod, cleared, metas):
    m = mod.META
    if m["level"] != "super":
        return False
    hard = [s for s, x in metas.items() if x["track"] == m["track"] and x["level"] == "hard"]
    return bool(hard) and not any(s in cleared for s in hard)


@app.route("/api/practice/home")
@auth_required
def route_practice_home():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    s = request._session  # type: ignore
    preview = request.args.get("user", "") if s["role"] == "admin" else ""  # "view as student" on the practice board
    if preview:
        if preview not in _USER_TO_SID:
            return jsonify({"error": "Unknown student."}), 404
        user = preview
    else:
        user, err = _practice_target()
        if err:
            return jsonify({"error": err[0]}), err[1]
    open_, why = _practice_open(common)
    entries, metas, profs = prac.ledger(), prac.metas(), prac.profiles()   # metas: the scenarios' map
    allm = prac.all_metas()                                                # XP, ranks, skills, badges: everything
    profile, st = _practice_profile(prac, user, entries, allm, profs)
    runs = prac.runs(user)
    tracks = []
    for t in prac.TRACKS:
        tiles = []
        for level in prac.LEVELS:
            sid = next((s for s, m in metas.items() if m["track"] == t["id"] and m["level"] == level), None)
            if not sid:
                tiles.append(None)
                continue
            m, r = metas[sid], runs.get(sid)
            c = st["cleared"].get(sid)
            state = ("cleared_nohint" if c["hints"] == 0 else "cleared") if c else ("progress" if r else "new")
            tiles.append({"id": sid, "title": m["title"], "level": level, "xp": m["xp"], "minutes": m["minutes"], "state": state,
                          "skills": [prac.SKILLS[k]["title"] for k in m.get("skills", []) if k in prac.SKILLS],
                          "guided": hasattr(prac.catalog()[sid], "steps"),
                          "locked": _super_locked(prac, prac.catalog()[sid], st["cleared"], metas),
                          "attempt": (r or {}).get("attempt", 0), "remixes": st["remix"].get(sid, 0)})
        tracks.append(dict(t, tiles=tiles))
    p = profs.get(user) or {}
    out = {"open": open_, "closed_why": why, "levels": prac.LEVEL_NAME, "tracks": tracks, "profile": profile,
           "preview": bool(preview),
           "me": {"user": user, "id": _USER_TO_SID[user], "nick": p.get("nick", ""), "nick_cleared": bool(p.get("nick_cleared"))},
           "leaderboard": _practice_board(prac, entries, allm, profs, user), "now": time.time(),
           "roadmap": _practice_roadmap(prac, st, runs, allm)}
    b = prac.bonus_settings()
    if b.get("published"):
        out["bonus"] = prac.bonus_for(user, entries, allm, b)
    return jsonify(out)


@app.route("/api/practice/scenario")
@auth_required
def route_practice_scenario():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    s = request._session  # type: ignore
    preview = request.args.get("user", "") if s["role"] == "admin" else ""
    if preview:
        if preview not in _USER_TO_SID:
            return jsonify({"error": "Unknown student."}), 404
        user = preview
    else:
        user, err = _practice_target()
        if err:
            return jsonify({"error": err[0]}), err[1]
    mod = _practice_scenario(prac, request.args.get("id"))
    if not mod:
        return jsonify({"error": "Unknown scenario."}), 404
    st = prac.standings(prac.ledger(), prac.all_metas()).get(user) or prac.empty_standing()
    r = prac.runs(user).get(mod.META["id"])
    if preview and not r:
        r = {"attempt": 1, "started": time.time(), "deadline": time.time() + 60 * int(mod.META["minutes"]),
             "minutes": mod.META["minutes"], "hints": 3, "checks": 0, "cleared": False}
    out = _practice_view(prac, mod, user, r, st["cleared"])
    out["open"], out["closed_why"] = _practice_open(common)
    out["locked"] = _super_locked(prac, mod, st["cleared"], prac.metas())
    return jsonify(out)


def _practice_setup(prac, user, sid, attempt):
    res = prac.runner_call({"op": "setup", "user": user, "sid": sid, "attempt": attempt})
    if res.get("error"):
        msg = "The practice runner is not running; tell the instructor." if res.get("unavailable") else res["error"]
        return None, msg
    return res.get("info") or {}, None


def _practice_workspace_gone(user, sid):
    """True only when the student's home can be read and ~/practice/<id> is not there (the API reads homes through
    the u:pisey:rx ACL; when it cannot, it assumes the workspace is there)."""
    home = Path(os.path.expanduser("~" + user))
    try:
        return home.is_dir() and os.access(str(home), os.R_OK | os.X_OK) and not (home / "practice" / sid).is_dir()
    except OSError:
        return False


def _practice_body():
    body = request.get_json(silent=True) or {}
    return body if isinstance(body, dict) else {}


@app.route("/api/practice/start", methods=["POST"])
@auth_required
def route_practice_start():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    user, err = _practice_target()
    if err:
        return jsonify({"error": err[0]}), err[1]
    open_, why = _practice_open(common)
    if not open_:
        return jsonify({"error": why}), 409
    mod = _practice_scenario(prac, _practice_body().get("id"))
    if not mod:
        return jsonify({"error": "Unknown scenario."}), 404
    sid, metas = mod.META["id"], prac.metas()
    st = prac.standings(prac.ledger(), prac.all_metas()).get(user) or prac.empty_standing()
    if _super_locked(prac, mod, st["cleared"], metas):
        return jsonify({"error": "Clear the Hard scenario of this track first."}), 403
    r = prac.runs(user).get(sid)
    if r and _practice_workspace_gone(user, sid):  # the student removed ~/practice/<id>: make it again
        info, e = _practice_setup(prac, user, sid, int(r["attempt"]))
        if e:
            return jsonify({"error": e}), 503
        with prac.locked():
            runs = prac.runs(user)
            runs[sid]["info"] = info
            prac.save_runs(user, runs)
    if not r:
        info, e = _practice_setup(prac, user, sid, 1)
        if e:
            return jsonify({"error": e}), 503
        now = time.time()
        minutes = int(mod.META["minutes"])
        with prac.locked():
            runs = prac.runs(user)
            r = runs.get(sid) or {"attempt": 1, "started": now, "deadline": now + 60 * minutes, "minutes": minutes,
                                  "hints": 0, "checks": 0, "cleared": False, "last": None, "info": info}
            runs[sid] = r
            prac.save_runs(user, runs)
    return jsonify(_practice_view(prac, mod, user, r, st["cleared"]))


@app.route("/api/practice/ticket", methods=["POST"])
@auth_required
def route_practice_ticket():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    user, err = _practice_target()
    if err:
        return jsonify({"error": err[0]}), err[1]
    open_, why = _practice_open(common)
    if not open_:
        return jsonify({"error": why}), 409
    mod = _practice_scenario(prac, _practice_body().get("id"))
    r = prac.runs(user).get(mod.META["id"]) if mod else None
    if not r:
        return jsonify({"error": "Start the scenario first."}), 409
    try:
        ticket = common.make_ticket(user, common.PRACTICE_ID, extra={"s": mod.META["id"], "a": int(r["attempt"])})
    except (OSError, ValueError) as exc:
        print("[practice] ticket:", exc, flush=True)
        return jsonify({"error": "The practice room is not ready (ticket key)."}), 503
    return jsonify({"ticket": ticket, "url": common.load_practice().get("gateway_url", ""), "ttl": common.TICKET_TTL})


def _award_reasons(prac, meta, e, xp, first):
    if not first:
        if meta["level"] in prac.KINDS:
            return ["played again: a %s earns XP once, and your first clear already counted" % meta["level"]]
        return ["remix cleared: %d%% of %d XP" % (round(prac.REMIX_SHARE * 100), meta["xp"])] if xp else \
            ["remix cleared (the first three remixes earn XP)"]
    out = ["%s %s: %d XP" % (prac.LEVEL_NAME.get(meta["level"], meta["level"].capitalize()),
                             "passed" if meta["level"] == "quiz" else "cleared", meta["xp"])]
    if e["hints"]:
        out.append("%d hint%s: %d%%" % (e["hints"], "s" if e["hints"] > 1 else "", round(prac.HINT_SHARE[e["hints"]] * 100)))
    elif meta["level"] != "quiz":
        out.append("no hints: +%d%%" % round(prac.NO_HINT_BONUS * 100))
    if e.get("fast"):
        out.append("under half the countdown: +%d%%" % round(prac.FAST_BONUS * 100))
    if e.get("late"):
        out.append("after the countdown: half")
    return out


@app.route("/api/practice/check", methods=["POST"])
@auth_required
def route_practice_check():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    user, err = _practice_target()
    if err:
        return jsonify({"error": err[0]}), err[1]
    open_, why = _practice_open(common)
    if not open_:
        return jsonify({"error": why}), 409
    mod = _practice_scenario(prac, _practice_body().get("id"))
    if not mod:
        return jsonify({"error": "Unknown scenario."}), 404
    sid = mod.META["id"]
    r = prac.runs(user).get(sid)
    if not r:
        return jsonify({"error": "Start the scenario first."}), 409
    if mod.META["level"] == "super" and _practice_expired(r) and not r.get("cleared"):
        return jsonify({"error": "Time is up for this attempt. Remix to try again with new values.", "expired": True}), 409
    with _PRACTICE_MU:
        left = _PRACTICE_GAP - (time.time() - _PRACTICE_LAST.get(user, 0))
        if left > 0:
            return jsonify({"error": "Wait %d s before the next check." % math.ceil(left), "retry_s": math.ceil(left)}), 429
        _PRACTICE_LAST[user] = time.time()
    attempt = int(r["attempt"])
    res = prac.runner_call({"op": "check", "user": user, "sid": sid, "attempt": attempt, "info": r.get("info") or {}})
    if res.get("error") == "wait":
        return jsonify({"error": "Wait a few seconds before the next check.", "retry_s": res.get("retry_s", 5)}), 429
    if res.get("error"):
        msg = "The practice runner is not running; tell the instructor." if res.get("unavailable") else res["error"]
        return jsonify({"error": msg}), 503
    now = time.time()
    metas = prac.all_metas()
    meta = metas[sid]
    award = None
    steps = []
    with prac.locked():
        runs = prac.runs(user)
        r = runs.get(sid)
        if not r or int(r["attempt"]) != attempt:
            return jsonify({"error": "The scenario changed (a remix) during the check; check again."}), 409
        r["checks"] = int(r.get("checks", 0)) + 1
        r["last"] = {"at": now, "ok": bool(res.get("ok")), "checks": res.get("checks", [])}
        if res.get("ok") and not r.get("cleared"):
            entries = prac.ledger()
            before_st = prac.standings(entries, metas).get(user) or prac.empty_standing()
            first = sid not in before_st["cleared"]
            secs = now - float(r["started"])
            e = {"user": user, "kind": "clear", "sid": sid, "attempt": attempt, "hints": int(r.get("hints", 0)),
                 "checks": r["checks"], "secs": round(secs, 1), "minutes": meta["minutes"],
                 "late": meta["level"] != "super" and now > float(r["deadline"]),
                 "fast": meta["level"] == "super" and secs < meta["minutes"] * 30,
                 "level": meta["level"], "base": meta["xp"], "track": meta["track"], "ts": now}
            prac.append_ledger(e)
            after = prac.standings(prac.ledger(), metas)[user]
            r["cleared"], r["cleared_at"] = True, now
            old_b = {b["id"] for b in prac.badges_of(before_st, metas) if b["earned"]}
            new_b = [b["name"] for b in prac.badges_of(after, metas) if b["earned"] and b["id"] not in old_b]
            ri0, ri1 = prac.rank_of(before_st), prac.rank_of(after)
            gained = after["xp"] - before_st["xp"]
            award = {"xp": gained, "total": after["xp"], "reasons": _award_reasons(prac, meta, e, gained, first),
                     "rank": prac.RANKS[ri1][0], "rank_up": ri1 > ri0, "badges": new_b,
                     "skills": [prac.SKILLS[k]["title"] for k in sorted(after["skills"] - before_st["skills"]) if k in prac.SKILLS]}
        runs[sid] = r
        prac.save_runs(user, runs)
    out = {"ok": bool(res.get("ok")), "checks": res.get("checks", []), "cleared": bool(r.get("cleared")), "award": award,
           "run": {k: r.get(k) for k in ("attempt", "hints", "checks", "cleared")}}
    if getattr(mod, "steps", None):
        v = prac.values(mod, user, attempt)
        out["progress"] = prac.step_progress(prac.steps_of(mod, v, attempt), res.get("checks", []))
    return jsonify(out)


@app.route("/api/practice/hint", methods=["POST"])
@auth_required
def route_practice_hint():
    _common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    user, err = _practice_target()
    if err:
        return jsonify({"error": err[0]}), err[1]
    mod = _practice_scenario(prac, _practice_body().get("id"))
    if not mod:
        return jsonify({"error": "Unknown scenario."}), 404
    if mod.META["level"] == "super":
        return jsonify({"error": "A Super challenge has no hints."}), 400
    sid = mod.META["id"]
    with prac.locked():
        runs = prac.runs(user)
        r = runs.get(sid)
        if not r:
            return jsonify({"error": "Start the scenario first."}), 409
        cap = prac.MAX_HINTS.get(mod.META["level"], 3)
        if not r.get("cleared") and int(r.get("hints", 0)) < cap:
            r["hints"] = int(r.get("hints", 0)) + 1
            prac.save_runs(user, runs)
    v = prac.values(mod, user, r["attempt"])
    out = {"hints": prac.hints_of(mod, v)[: int(r["hints"])], "used": int(r["hints"])}
    if getattr(mod, "hint_steps", None):
        out["hint_steps"] = mod.hint_steps(v)[: int(r["hints"])]
    return jsonify(out)


@app.route("/api/practice/reset", methods=["POST"])
@auth_required
def route_practice_reset():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    user, err = _practice_target()
    if err:
        return jsonify({"error": err[0]}), err[1]
    open_, why = _practice_open(common)
    if not open_:
        return jsonify({"error": why}), 409
    mod = _practice_scenario(prac, _practice_body().get("id"))
    r = prac.runs(user).get(mod.META["id"]) if mod else None
    if not r:
        return jsonify({"error": "Start the scenario first."}), 409
    info, e = _practice_setup(prac, user, mod.META["id"], int(r["attempt"]))
    if e:
        return jsonify({"error": e}), 503
    with prac.locked():
        runs = prac.runs(user)
        runs[mod.META["id"]]["info"] = info
        prac.save_runs(user, runs)
    return jsonify({"ok": True})


@app.route("/api/practice/remix", methods=["POST"])
@auth_required
def route_practice_remix():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    user, err = _practice_target()
    if err:
        return jsonify({"error": err[0]}), err[1]
    open_, why = _practice_open(common)
    if not open_:
        return jsonify({"error": why}), 409
    mod = _practice_scenario(prac, _practice_body().get("id"))
    if not mod:
        return jsonify({"error": "Unknown scenario."}), 404
    sid = mod.META["id"]
    r = prac.runs(user).get(sid)
    if not r or not (r.get("cleared") or (mod.META["level"] == "super" and _practice_expired(r))):
        return jsonify({"error": "Remix opens once this attempt is cleared."}), 409
    attempt = int(r["attempt"]) + 1
    info, e = _practice_setup(prac, user, sid, attempt)
    if e:
        return jsonify({"error": e}), 503
    now, minutes = time.time(), int(mod.META["minutes"])
    with prac.locked():
        runs = prac.runs(user)
        r = {"attempt": attempt, "started": now, "deadline": now + 60 * minutes, "minutes": minutes, "hints": 0, "checks": 0,
             "cleared": False, "last": None, "info": info}
        runs[sid] = r
        prac.save_runs(user, runs)
    st = prac.standings(prac.ledger(), prac.all_metas()).get(user) or prac.empty_standing()
    return jsonify(_practice_view(prac, mod, user, r, st["cleared"]))


# ── Quizzes: multiple choice, no shell (server/practice/quizzes.py) ──────────

def _quiz_target(need_open=True):
    """(common, prac, quizzes, user, quiz, err) for a quiz route; err is a (response, status) pair or None."""
    common, prac = _practice_mods()
    qz = _practice_quizzes() if prac else None
    if not prac or not qz:
        return None, None, None, None, None, (jsonify({"error": "Practice is not installed on this server."}), 503)
    s = request._session  # type: ignore
    preview = request.args.get("user", "") if s["role"] == "admin" and request.method == "GET" else ""
    if preview:
        if preview not in _USER_TO_SID:
            return None, None, None, None, None, (jsonify({"error": "Unknown student."}), 404)
        user = preview
    else:
        user, err = _practice_target()
        if err:
            return None, None, None, None, None, (jsonify({"error": err[0]}), err[1])
    if need_open:
        open_, why = _practice_open(common)
        if not open_:
            return None, None, None, None, None, (jsonify({"error": why}), 409)
    sid = request.args.get("id", "") if request.method == "GET" else _practice_body().get("id", "")
    quiz = qz.catalog().get(sid) if isinstance(sid, str) and prac.SCENARIO_RE.match(sid) else None
    if not quiz:
        return None, None, None, None, None, (jsonify({"error": "Unknown quiz."}), 404)
    return common, prac, qz, user, quiz, None


QUIZ_LIVE_S = 15   # the gateway refreshes a socket's status every 5 s; older than this, the page is not connected


def _quiz_gate(common, user, quiz_id, run, now):
    """The lock on a quiz. A quiz has no typed input for the gateway to drop, so the questions, the hint and the
    submit are held back here, unless both are true: this attempt has a live socket to the gateway (status.json says
    kind "quiz", this quiz, this attempt, seen a moment ago), and the practice lock (the shell's, shared) is off.
    None when the attempt may go on, else {"why": "socket" | "locked", "left": seconds, "message": ...}."""
    if not run.get("open"):
        return None
    st = common.read_json(common.room_dir(user, "practice") / "status.json", {}) or {}
    try:
        fresh = now - float(st.get("last_seen", 0)) <= QUIZ_LIVE_S
        same = st.get("kind") == "quiz" and st.get("scenario") == quiz_id and int(st.get("attempt", -1)) == int(run["attempt"])
    except (TypeError, ValueError):
        fresh = same = False
    if not (st.get("connected") and fresh and same):
        return {"why": "socket", "left": 0, "message": "Not connected to the practice room: the quiz opens only while its page is connected."}
    lock = common.read_lock(user, common.PRACTICE_ID, "practice")
    if lock.get("locked"):
        return {"why": "locked", "left": common.lock_left(lock), "message": "The quiz is locked: you left fullscreen. Wait for the countdown, then return."}
    return None


def _quiz_view(prac, qz, quiz, user, run, cleared, now, show_questions=True, gate=None):
    meta = qz.meta_of(quiz)
    out = {"meta": {k: meta[k] for k in ("id", "title", "xp", "minutes", "learn", "stage", "skills")},
           "stage_title": next((s["title"] for s in prac.STAGES if s["id"] == meta["stage"]), ""),
           "skill_titles": [prac.SKILLS[s]["title"] for s in meta["skills"] if s in prac.SKILLS],
           "rules": {"questions": quiz.n, "pass_mark": qz.pass_mark(quiz.n), "wait_s": qz.WAIT_S, "hint_share": [1.0, prac.HINT_SHARE[1]],
                     "late_share": prac.LATE_SHARE},
           "state": qz.state(run, meta["minutes"], now), "cleared_before": meta["id"] in cleared}
    if run.get("open"):
        out["gate"] = gate   # None, or why the questions are held back (see _quiz_gate)
        out["deadline_iso"] = datetime.fromtimestamp(run["deadline"], _PPH).isoformat(timespec="seconds")
    if run.get("open") and show_questions and not gate:
        d = qz.draw(quiz, user, run["attempt"])
        out["questions"] = qz.public(d)
        h = run.get("hint")
        out["hint"] = {"q": h["q"], "removed": list(h["removed"])} if h else None
    return out


@app.route("/api/practice/quiz")
@auth_required
def route_practice_quiz():
    common, prac, qz, user, quiz, err = _quiz_target(need_open=False)
    if err:
        return err
    s = request._session  # type: ignore
    preview = s["role"] == "admin" and bool(request.args.get("user", ""))
    now = time.time()
    st = prac.standings(prac.ledger(), prac.all_metas()).get(user) or prac.empty_standing()
    run = prac.runs(user).get(quiz.id) or {}
    out = _quiz_view(prac, qz, quiz, user, run, st["cleared"], now, show_questions=not preview,
                     gate=None if preview else _quiz_gate(common, user, quiz.id, run, now))
    out["open"], out["closed_why"] = _practice_open(common)
    out["preview"] = preview
    return jsonify(out)


@app.route("/api/practice/quiz/start", methods=["POST"])
@auth_required
def route_practice_quiz_start():
    common, prac, qz, user, quiz, err = _quiz_target()
    if err:
        return err
    meta = qz.meta_of(quiz)
    now = time.time()
    with prac.locked():
        runs = prac.runs(user)
        run = runs.get(quiz.id) or {}
        e = qz.begin(run, meta["minutes"], now)
        if e:
            return jsonify({"error": "Wait %d s: the next attempt draws new questions." % math.ceil(e["retry_s"]), "retry_s": e["retry_s"]}), 429
        runs[quiz.id] = run
        prac.save_runs(user, runs)
    st = prac.standings(prac.ledger(), prac.all_metas()).get(user) or prac.empty_standing()
    # the questions come with the next GET, once the page has its socket (a fresh start has none yet)
    return jsonify(_quiz_view(prac, qz, quiz, user, run, st["cleared"], now, gate=_quiz_gate(common, user, quiz.id, run, now)))


@app.route("/api/practice/quiz/ticket", methods=["POST"])
@auth_required
def route_practice_quiz_ticket():
    """The gateway ticket of an open quiz attempt: a socket with no shell, which holds the lock and the attempt's
    heartbeat (server/examroom/gateway.py, quiz session)."""
    common, prac, qz, user, quiz, err = _quiz_target()
    if err:
        return err
    run = prac.runs(user).get(quiz.id) or {}
    if not run.get("open"):
        return jsonify({"error": "Start the quiz first."}), 409
    try:
        ticket = common.make_ticket(user, common.PRACTICE_ID, extra={"s": quiz.id, "a": int(run["attempt"]), "k": "quiz"})
    except (OSError, ValueError) as exc:
        print("[practice] quiz ticket:", exc, flush=True)
        return jsonify({"error": "The practice room is not ready (ticket key)."}), 503
    return jsonify({"ticket": ticket, "url": (common.load_practice() or {}).get("gateway_url", ""), "ttl": common.TICKET_TTL})


@app.route("/api/practice/quiz/hint", methods=["POST"])
@auth_required
def route_practice_quiz_hint():
    common, prac, qz, user, quiz, err = _quiz_target()
    if err:
        return err
    try:
        i = int(_practice_body().get("q"))
    except (TypeError, ValueError):
        return jsonify({"error": "Which question?"}), 400
    with prac.locked():
        runs = prac.runs(user)
        run = runs.get(quiz.id) or {}
        if not run.get("open"):
            return jsonify({"error": "Start the quiz first."}), 409
        gate = _quiz_gate(common, user, quiz.id, run, time.time())
        if gate:
            return jsonify({"error": gate["message"], "gate": gate}), 423
        res = qz.use_hint(run, qz.draw(quiz, user, run["attempt"]), i, user, quiz.id)
        if res.get("error"):
            return jsonify(res), 409
        runs[quiz.id] = run
        prac.save_runs(user, runs)
    return jsonify({"q": i, "removed": res["removed"], "hints": int(run.get("hints", 0))})


@app.route("/api/practice/quiz/submit", methods=["POST"])
@auth_required
def route_practice_quiz_submit():
    common, prac, qz, user, quiz, err = _quiz_target()
    if err:
        return err
    body = _practice_body()
    answers = body.get("answers")
    if not isinstance(answers, dict) or len(answers) > 50:
        return jsonify({"error": "Send your answers as {question: choice}."}), 400
    answers = {str(k)[:40]: str(v)[:4] for k, v in answers.items()}
    try:
        leaves = max(0, min(50, int(body.get("leaves", 0))))
    except (TypeError, ValueError):
        leaves = 0
    now = time.time()
    metas = prac.all_metas()
    meta = metas[quiz.id]
    award = None
    with prac.locked():
        runs = prac.runs(user)
        run = runs.get(quiz.id) or {}
        if not run.get("open"):
            return jsonify({"error": "No attempt is open: start the quiz again."}), 409
        gate = _quiz_gate(common, user, quiz.id, run, now)
        if gate:
            return jsonify({"error": gate["message"], "gate": gate}), 423
        res = qz.submit(run, qz.draw(quiz, user, run["attempt"]), answers, now)
        run["leaves"] = int(run.get("leaves", 0)) + leaves   # the page's own count of times it was left; a signal, not a proof
        if res.get("passed"):
            entries = prac.ledger()
            before = prac.standings(entries, metas).get(user) or prac.empty_standing()
            first = quiz.id not in before["cleared"]
            e = qz.clear_entry(user, meta, res, now)
            prac.append_ledger(e)
            after = prac.standings(prac.ledger(), metas)[user]
            old_b = {b["id"] for b in prac.badges_of(before, metas) if b["earned"]}
            new_b = [b["name"] for b in prac.badges_of(after, metas) if b["earned"] and b["id"] not in old_b]
            ri0, ri1 = prac.rank_of(before), prac.rank_of(after)
            gained = after["xp"] - before["xp"]
            award = {"xp": gained, "total": after["xp"], "reasons": _award_reasons(prac, meta, e, gained, first),
                     "rank": prac.RANKS[ri1][0], "rank_up": ri1 > ri0, "badges": new_b, "skills": []}
        runs[quiz.id] = run
        prac.save_runs(user, runs)
    return jsonify({"result": res, "award": award, "state": qz.state(run, meta["minutes"], now)})


@app.route("/api/practice/nick", methods=["POST"])
@auth_required
def route_practice_nick():
    _common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    user, err = _practice_target()
    if err:
        return jsonify({"error": err[0]}), err[1]
    try:
        nick = prac.clean_nick(_practice_body().get("nick", ""))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    with prac.locked():
        profs = prac.profiles()
        p = profs.get(user) or {}
        p.update(nick=nick, nick_cleared=False)
        profs[user] = p
        prac.save_profiles(profs)
    return jsonify({"nick": nick})


def _practice_casts(common, user, sid):
    folder = common.room_dir(user, "practice") / sid
    out = []
    try:
        for p in sorted(folder.iterdir()):
            if common.CAST_RE.match(p.name):
                out.append({"name": p.name, "size": p.stat().st_size, "start": int(p.name.split(".")[0].split("-")[0])})
    except OSError:
        pass
    return out


def _practice_cast_file(common, user, sid, name):
    if not common.SCENARIO_RE.match(str(sid)) or not common.CAST_RE.match(str(name)):
        return None
    try:
        with open(common.room_dir(user, "practice") / sid / name, "rb") as f:
            return f.read(25 * 1024 * 1024)
    except OSError:
        return None


@app.route("/api/practice/replays")
@auth_required
def route_practice_replays():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    user, err = _practice_target()
    if err:
        return jsonify({"error": err[0]}), err[1]
    sid = request.args.get("id", "")
    if not common.SCENARIO_RE.match(sid):
        return jsonify({"error": "Unknown scenario."}), 404
    return jsonify({"casts": _practice_casts(common, user, sid), "keep_days": 14})


@app.route("/api/practice/cast")
@auth_required
def route_practice_cast():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    user, err = _practice_target()
    if err:
        return jsonify({"error": err[0]}), err[1]
    data = _practice_cast_file(common, user, request.args.get("id", ""), request.args.get("name", ""))
    if data is None:
        return jsonify({"error": "Unknown recording."}), 404
    return app.response_class(data, mimetype="application/x-asciicast")


# instructor

def _practice_user_arg(value):
    user = str(value or "")
    return user if user in _USER_TO_SID else None


@app.route("/api/admin/practice/overview")
@admin_required
def route_admin_practice_overview():
    common, prac = _practice_mods()
    if not prac:
        return jsonify({"error": "Practice is not installed on this server."}), 503
    from statistics import median
    entries, metas, profs = prac.ledger(), prac.metas(), prac.profiles()   # metas: the scenarios
    allm = prac.all_metas()                                                # scenarios, drills and quizzes
    st = prac.standings(entries, allm)
    b = prac.bonus_settings()
    firsts = {}
    seen = set()
    for e in sorted(entries, key=lambda x: x.get("ts", 0)):
        if e.get("kind") == "clear" and (e.get("user"), e.get("sid")) not in seen:
            seen.add((e.get("user"), e.get("sid")))
            firsts.setdefault(e.get("sid"), []).append(e)
    started = {}
    stuck = {}          # drill id -> {step number: students whose last check left them on that step}
    drill_mods = prac.exercises()   # drills and scenarios: any guided exercise has steps
    students, live = [], []
    now = time.time()
    for sid_student, info in sorted(STUDENTS.items()):
        user = info["user"]
        runs = prac.runs(user)
        for s in runs:
            started[s] = started.get(s, 0) + 1
        for sid_x, r_x in runs.items():
            mod_x = drill_mods.get(sid_x)
            lastrun = r_x.get("last") if isinstance(r_x, dict) else None   # a quiz's "last" is "pass" or "fail"
            last = lastrun.get("checks") if isinstance(lastrun, dict) else None
            if mod_x is not None and getattr(mod_x, "steps", None) and last and not r_x.get("cleared"):
                att = int(r_x.get("attempt", 1))
                cur_step = prac.step_progress(prac.steps_of(mod_x, prac.values(mod_x, user, att), att), last)["current"] + 1
                stuck.setdefault(sid_x, {})
                stuck[sid_x][cur_step] = stuck[sid_x].get(cur_step, 0) + 1
        s = st.get(user) or prac.empty_standing()
        p = profs.get(user) or {}
        students.append({"id": sid_student, "name": info["name"], "user": user, "xp": s["xp"], "week": s["week"],
                         "rank": prac.RANKS[prac.rank_of(s)][0], "clears": len(s["cleared"]), "supers": len(s["supers"]),
                         "skills": len(s["skills"]),
                         "last": s["last"] or None, "nick": p.get("nick", ""), "nick_cleared": bool(p.get("nick_cleared")),
                         "author": bool(p.get("author")), "bonus": prac.bonus_for(user, entries, allm, b)["amount"],
                         "corrections": s["corrections"]})
        pdir = common.room_dir(user, "practice")
        status = common.read_json(pdir / "status.json", {}) or {}
        if status.get("scenario"):
            lock = common.read_lock(user, common.PRACTICE_ID, "practice")
            connected = bool(status.get("connected")) and now - float(status.get("last_seen", 0)) < 20
            if connected or now - float(status.get("last_seen", 0)) < 3600:
                live.append({"id": sid_student, "name": info["name"], "user": user, "scenario": status.get("scenario"),
                             "attempt": status.get("attempt"), "connected": connected, "last_cmd": status.get("last_cmd", ""),
                             "last_seen": status.get("last_seen"), "locked": bool(lock.get("locked")),
                             "lock_left": common.lock_left(lock), "lock_n_today": lock.get("day_n", 0)})
    scen = []
    for sid, m in sorted(metas.items(), key=lambda x: (prac.TRACK_IDS.index(x[1]["track"]), prac.LEVELS.index(x[1]["level"]))):
        f = firsts.get(sid, [])
        scen.append({"id": sid, "title": m["title"], "track": m["track"], "level": m["level"], "xp": m["xp"],
                     "minutes": m["minutes"], "private": m["private"], "started": started.get(sid, 0), "cleared": len(f),
                     "median_min": round(median(e.get("secs", 0) for e in f) / 60, 1) if f else None,
                     "hints_avg": round(sum(e.get("hints", 0) for e in f) / len(f), 2) if f else None,
                     "hint3": sum(1 for e in f if e.get("hints", 0) >= 3),
                     "checks_avg": round(sum(e.get("checks", 0) for e in f) / len(f), 1) if f else None,
                     "skills": m.get("skills", []), "guided": hasattr(prac.catalog()[sid], "steps"),
                     "stuck": {str(k): v for k, v in sorted((stuck.get(sid) or {}).items())}})
    road = []
    for sid, m in allm.items():
        if not m.get("stage"):
            continue
        f = firsts.get(sid, [])
        road.append({"id": sid, "title": m["title"], "stage": m["stage"], "kind": m["level"], "xp": m["xp"], "minutes": m["minutes"],
                     "started": started.get(sid, 0), "cleared": len(f),
                     "median_min": round(median(e.get("secs", 0) for e in f) / 60, 1) if f and m["level"] != "quiz" else None,
                     "hints_avg": round(sum(e.get("hints", 0) for e in f) / len(f), 2) if f else None,
                     "checks_avg": round(sum(e.get("checks", 0) for e in f) / len(f), 1) if f and m["level"] != "quiz" else None,
                     "stuck": {str(k): v for k, v in sorted((stuck.get(sid) or {}).items())}})
    cfg = common.load_practice()
    ping = prac.runner_call({"op": "ping"}, timeout=3)
    return jsonify({"scenarios": scen, "students": students, "live": live, "errors": prac.catalog_errors(),
                    "roadmap": road, "stages": [{"id": s["id"], "title": s["title"], "badge": s["badge"]} for s in prac.STAGES],
                    "skills_total": len(prac.SKILLS),
                    "settings": ({k: common._get(cfg, k) for k in common.PRACTICE_SETTINGS} if cfg else None),
                    "settings_bounds": {k: list(v[1]) for k, v in common.PRACTICE_SETTINGS.items()},
                    "installed": bool(cfg), "exam_running": common.exam_blocks_practice(),
                    "runner_ok": not ping.get("unavailable"), "bonus": b, "ranks": [r[0] for r in prac.RANKS],
                    "corrections": [e for e in entries if e.get("kind") == "correction"][-30:], "now": now})


@app.route("/api/admin/practice/xp", methods=["POST"])
@admin_required
def route_admin_practice_xp():
    _common, prac = _practice_mods()
    body = _practice_body()
    user = _practice_user_arg(body.get("user"))
    xp, reason = body.get("xp"), str(body.get("reason", "")).strip()
    if not user:
        return jsonify({"error": "Unknown student."}), 404
    if not isinstance(xp, int) or isinstance(xp, bool) or xp == 0 or abs(xp) > 2000:
        return jsonify({"error": "XP must be a whole number from -2000 to 2000, not 0."}), 400
    if not 3 <= len(reason) <= 120 or "\n" in reason:
        return jsonify({"error": "Give a reason (3 to 120 characters)."}), 400
    with prac.locked():
        e = prac.append_ledger({"user": user, "kind": "correction", "xp": xp, "reason": reason,
                                "by": request._session["username"]})  # type: ignore
    return jsonify({"ok": True, "entry": e})


@app.route("/api/admin/practice/nick-clear", methods=["POST"])
@admin_required
def route_admin_practice_nick_clear():
    _common, prac = _practice_mods()
    user = _practice_user_arg(_practice_body().get("user"))
    if not user:
        return jsonify({"error": "Unknown student."}), 404
    with prac.locked():
        profs = prac.profiles()
        p = profs.get(user) or {}
        p.update(nick="", nick_cleared=True)
        profs[user] = p
        prac.save_profiles(profs)
    return jsonify({"ok": True})


@app.route("/api/admin/practice/author", methods=["POST"])
@admin_required
def route_admin_practice_author():
    _common, prac = _practice_mods()
    body = _practice_body()
    user = _practice_user_arg(body.get("user"))
    if not user or not isinstance(body.get("on"), bool):
        return jsonify({"error": "Give a student and on: true or false."}), 400
    with prac.locked():
        profs = prac.profiles()
        p = profs.get(user) or {}
        p["author"] = body["on"]
        profs[user] = p
        prac.save_profiles(profs)
    return jsonify({"ok": True})


@app.route("/api/admin/practice/settings", methods=["POST"])
@admin_required
def route_admin_practice_settings():
    common, prac = _practice_mods()
    try:
        changes = common.clean_settings(_practice_body().get("changes"), False, common.PRACTICE_SETTINGS)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    with prac.locked():
        cur = prac.read_json(prac.var() / "settings.json", {})
        cur.update(changes)
        if int(cur.get("lock.wait_max_s", 300)) < int(cur.get("lock.wait_s", 30)):
            return jsonify({"error": "The longest wait must not be shorter than the first wait."}), 400
        prac.write_json(prac.var() / "settings.json", cur)
    return jsonify({"ok": True, "settings": cur})


@app.route("/api/admin/practice/bonus", methods=["POST"])
@admin_required
def route_admin_practice_bonus():
    _common, prac = _practice_mods()
    body = _practice_body()
    per = body.get("per_rank") if isinstance(body.get("per_rank"), dict) else {}
    clean = {}
    for name, amount in per.items():
        if name not in prac.RANK_NAMES:
            return jsonify({"error": "Unknown rank %s." % str(name)[:30]}), 400
        if amount in (None, ""):
            continue
        if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not 0 <= amount <= 10:
            return jsonify({"error": "A bonus is a number from 0 to 10."}), 400
        clean[name] = round(float(amount), 2)
    cap = body.get("cap", 0)
    if not isinstance(cap, (int, float)) or isinstance(cap, bool) or not 0 <= cap <= 10:
        return jsonify({"error": "The cap is a number from 0 to 10."}), 400
    read_at = str(body.get("read_at") or "")
    if read_at and not re.match(r"^20\d\d-\d\d-\d\d$", read_at):
        return jsonify({"error": "The date is YYYY-MM-DD, or empty for now."}), 400
    with prac.locked():
        b = prac.bonus_settings()
        b.update(per_rank=clean, cap=round(float(cap), 2), read_at=read_at)
        prac.save_bonus(b)
    return jsonify({"ok": True, "bonus": b})


@app.route("/api/admin/practice/bonus/manual", methods=["POST"])
@admin_required
def route_admin_practice_bonus_manual():
    _common, prac = _practice_mods()
    body = _practice_body()
    with prac.locked():
        b = prac.bonus_settings()
        if isinstance(body.get("remove"), int) and not isinstance(body.get("remove"), bool):
            i = body["remove"]
            if not 0 <= i < len(b["manual"]):
                return jsonify({"error": "No such manual bonus."}), 404
            b["manual"].pop(i)
        else:
            user = _practice_user_arg(body.get("user"))
            amount, reason = body.get("amount"), str(body.get("reason", "")).strip()
            if not user:
                return jsonify({"error": "Unknown student."}), 404
            if not isinstance(amount, (int, float)) or isinstance(amount, bool) or not -10 <= amount <= 10 or amount == 0:
                return jsonify({"error": "The amount is a number from -10 to 10, not 0."}), 400
            if not 3 <= len(reason) <= 120 or "\n" in reason:
                return jsonify({"error": "Give a reason (3 to 120 characters)."}), 400
            b["manual"].append({"user": user, "amount": round(float(amount), 2), "reason": reason,
                                "by": request._session["username"], "at": time.time()})  # type: ignore
        prac.save_bonus(b)
    return jsonify({"ok": True, "bonus": b})


@app.route("/api/admin/practice/bonus/publish", methods=["POST"])
@admin_required
def route_admin_practice_bonus_publish():
    _common, prac = _practice_mods()
    on = _practice_body().get("published")
    if not isinstance(on, bool):
        return jsonify({"error": "published: true or false."}), 400
    with prac.locked():
        b = prac.bonus_settings()
        b.update(published=on, published_at=time.time() if on else None)
        prac.save_bonus(b)
    return jsonify({"ok": True, "bonus": b})


@app.route("/api/admin/practice/export.csv")
@admin_required
def route_admin_practice_export():
    import csv
    import io
    _common, prac = _practice_mods()
    entries, metas, profs = prac.ledger(), prac.all_metas(), prac.profiles()
    st = prac.standings(entries, metas)
    b = prac.bonus_settings()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "name", "user", "nickname", "xp", "xp_this_week", "rank", "clears", "super_clears", "bonus",
                "bonus_rank", "bonus_published"])
    for sid_student, info in sorted(STUDENTS.items()):
        s = st.get(info["user"]) or prac.empty_standing()
        bon = prac.bonus_for(info["user"], entries, metas, b)
        w.writerow([sid_student, info["name"], info["user"], (profs.get(info["user"]) or {}).get("nick", ""), s["xp"], s["week"],
                    prac.RANKS[prac.rank_of(s)][0], len(s["cleared"]), len(s["supers"]), bon["amount"], bon["rank"],
                    "yes" if b.get("published") else "no"])
    resp = app.response_class(out.getvalue(), mimetype="text/csv")
    resp.headers["Content-Disposition"] = 'attachment; filename="practice-xp.csv"'
    return resp


@app.route("/api/admin/practice/unlock", methods=["POST"])
@admin_required
def route_admin_practice_unlock():
    common, _prac = _practice_mods()
    user = _practice_user_arg(_practice_body().get("user"))
    if not user:
        return jsonify({"error": "Unknown student."}), 404
    try:
        common.request_unlock(user, request._session["username"], room="practice")  # type: ignore
    except OSError:
        return jsonify({"error": "The control folder is missing; run examctl install again."}), 500
    return jsonify({"sent": 1})


@app.route("/api/admin/practice/replay")
@admin_required
def route_admin_practice_replay():
    common, _prac = _practice_mods()
    user = _practice_user_arg(request.args.get("user"))
    sid = request.args.get("id", "")
    if not user or not common.SCENARIO_RE.match(sid):
        return jsonify({"error": "Unknown student or scenario."}), 404
    events = []
    path = common.room_dir(user, "practice") / "events.jsonl"
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if isinstance(e, dict) and e.get("s") == sid:
                    events.append(e)
    except OSError:
        pass
    sid_student = _USER_TO_SID[user]
    return jsonify({"user": user, "id": sid_student, "name": STUDENTS[sid_student]["name"], "scenario": sid,
                    "casts": _practice_casts(common, user, sid), "events": events[-2000:]})


@app.route("/api/admin/practice/cast")
@admin_required
def route_admin_practice_cast():
    common, _prac = _practice_mods()
    user = _practice_user_arg(request.args.get("user"))
    data = _practice_cast_file(common, user, request.args.get("id", ""), request.args.get("name", "")) if user else None
    if data is None:
        return jsonify({"error": "Unknown recording."}), 404
    return app.response_class(data, mimetype="application/x-asciicast")


# ── Main ───────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="ITC-OS Presence Server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Port (default: 5000)",
    )
    args = parser.parse_args()

    print(f"[Presence Server] http://{args.host}:{args.port}")
    print(f"  API endpoints:")
    print(f"    GET  /api/users              — logged-in Linux users")
    print(f"    GET  /api/web/users          — web visitors")
    print(f"    POST /api/web/login          — register web visitor")
    print(f"    POST /api/web/heartbeat      — keep web session alive")
    print(f"    POST /api/web/logout         — unregister web visitor")
    print(f"    POST /api/auth/login         — authenticate Linux user")
    print(f"    POST /api/auth/verify        — validate session token")
    print(f"    POST /api/auth/logout        — end session")
    print(f"    GET  /api/admin/stats        — user statistics (admin)")
    print(f"    GET  /api/admin/grades       — lab grading (admin)")
    print(f"    GET  /api/admin/leaderboard  — leaderboard (admin)")
    print(f"    GET  /api/admin/tree         — student file tree (admin)")
    print(f"    GET  /api/admin/activities   — activity grading (admin)")
    print(f"    GET  /api/admin/activity-tree — activity tree (admin)")
    print(f"    POST /api/admin/deadlines    — set deadlines (admin)")
    print(f"    GET  /api/deadlines          — read deadlines")
    print(f"    GET  /api/my/*               — student self-service")
    print(f"    GET  /api/who                — raw `who` output")
    print(f"    GET  /api/last               — recent login history")
    print(f"    GET  /api/health             — health check")
    print(f"  Press Ctrl+C to stop.\n")

    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
