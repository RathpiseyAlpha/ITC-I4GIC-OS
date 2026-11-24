"""Practice Linux Commands: the catalogue, personal values, XP, ranks, badges, the ledger and per-student state.

Used by the API (app/server/app.py) and the runner (runner.py). Standard library only. The rules are in
teaching/PRACTICE-SCENARIOS-PLAN.md; the numbers are here, and every total is computed again from the ledger, so a
change of these numbers applies to every past clear.

Data (the API writes it; students cannot read it):

    /srv/practice/                ITC_PRACTICE_VAR
        ledger.jsonl              append-only: one line per clear, remix clear or XP correction
        runs/<user>.json          per scenario: attempt, start, hints, checks, cleared, setup facts
        profiles.json             nicknames (and whether the instructor cleared one), the Scenario author badge
        bonus.json                the bonus per rank, the cap, the date ranks are read, manual bonuses, published
        settings.json             the room's lock, waits and session cap (also read by the gateway)
"""
import fcntl
import hashlib
import hmac
import importlib.util
import json
import os
import re
import secrets
import socket
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _d in (HERE, HERE.parent):  # kit.py is beside this file; oslab.py one folder up (server/ or /opt/itc-os-exam)
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import oslab  # noqa: E402  personal values are drawn like the pilot labs'

PPH = timezone(timedelta(hours=7))
SCENARIO_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
LEVELS = ("easy", "medium", "hard", "super")
LEVEL_NAME = {"easy": "Easy", "medium": "Medium", "hard": "Hard", "super": "Super challenge"}
BASE_XP = {"easy": 50, "medium": 100, "hard": 200, "super": 400, "drill": 15, "quiz": 10}
MINUTES = {"easy": 10, "medium": 20, "hard": 40, "super": 60, "drill": 5, "quiz": 5}
# The skill roadmap's exercises (drills, quizzes) are not in LEVELS: LEVELS, LEVEL_NAME and TRACK_IDS are the
# scenarios' map, and the API builds its tiles from them.
KINDS = ("drill", "quiz")
MAX_HINTS = {"drill": 2, "quiz": 1}   # a scenario has 3 (none for a Super challenge)
HINT_SHARE = (1.0, 0.9, 0.7, 0.4)     # XP kept after 0, 1, 2 or 3 hints
NO_HINT_BONUS = 0.10
FAST_BONUS = 0.25                     # a Super challenge cleared in less than half its countdown
LATE_SHARE = 0.5                      # Easy to Hard cleared after the countdown ran out
REMIX_SHARE, REMIX_MAX = 0.10, 3
CHECK_EVERY_S = 10

# The tracks follow the labs and lectures. A track's badge needs its Easy, Medium and Hard scenarios.
TRACKS = (
    {"id": "processes", "title": "Files and processes", "from": "Lab 1", "badge": "Reaper"},
    {"id": "paths", "title": "Paths and names", "from": "Lab 2", "badge": "Pathfinder"},
    {"id": "links", "title": "Wildcards and links", "from": "Lab 3", "badge": "Linksmith"},
    {"id": "pipes", "title": "Redirection and pipelines", "from": "Lab 4", "badge": "Plumber"},
    {"id": "threads", "title": "Threads", "from": "Lab 5", "badge": "Threadweaver"},
    {"id": "permissions", "title": "Permissions", "from": "Lab 6", "badge": "Gatekeeper"},
    {"id": "scripting", "title": "Scripting", "from": "Lab 7", "badge": "Scriptwright"},
    {"id": "races", "title": "Race conditions", "from": "Lab 8", "badge": "Lockkeeper"},
    {"id": "deadlock", "title": "Deadlock", "from": "Lab 9", "badge": "Cycle breaker"},
    {"id": "backup", "title": "Backup and cron", "from": "Lab 10", "badge": "Timekeeper"},
    {"id": "scheduling", "title": "Scheduling", "from": "Week 5", "badge": "Dispatcher"},
    {"id": "memory", "title": "Memory", "from": "Weeks 12–13", "badge": "Pager"},
)
TRACK_IDS = tuple(t["id"] for t in TRACKS)

# The Linux skill roadmap (teaching/SKILL-ROADMAP-PLAN.md): 6 stages, 57 skills. A skill is acquired by clearing a
# drill or scenario tagged with it, never by a quiz.
STAGES = (
    {"id": "shell", "title": "Shell basics", "badge": "Navigator"},
    {"id": "text", "title": "Text and pipelines", "badge": "Text Wrangler"},
    {"id": "perms", "title": "Users and permissions", "badge": "Mode Setter"},
    {"id": "procs", "title": "Processes and jobs", "badge": "Signal Caller"},
    {"id": "script", "title": "Scripting and automation", "badge": "Automator"},
    {"id": "insight", "title": "System insight (read-only)", "badge": "Observer"},
)
STAGE_IDS = tuple(s["id"] for s in STAGES)
_SKILL_ROWS = (
    ("shell", (("navigate", "Navigate"), ("mkdir", "Make folders"), ("touch", "Make empty files"), ("copy", "Copy"),
               ("move", "Move and rename"), ("remove", "Remove"), ("view", "View the start and end of a file"),
               ("file-info", "File size and type"), ("help", "Find an option"), ("wildcards", "Wildcards"),
               ("quoting", "Quoting"), ("hidden", "Hidden files"))),
    ("text", (("redirect", "Redirection"), ("stderr", "Error output"), ("grep", "grep"),
              ("grep-options", "grep options"), ("sort-uniq", "sort and uniq"), ("cut", "cut"), ("awk", "awk"),
              ("sed", "sed"), ("tr", "tr"), ("find", "find"), ("xargs", "xargs"), ("links", "Links"))),
    ("perms", (("chmod-octal", "chmod, numbers"), ("chmod-symbolic", "chmod, letters"), ("umask", "umask"),
               ("identity", "Who am I"), ("ownership", "Owner and group"), ("special-bits", "Special bits"),
               ("shared-dir", "Shared folder"), ("find-perm", "Find by permission"))),
    ("procs", (("ps", "Processes"), ("jobs", "Background jobs"), ("signals", "Signals"), ("trap", "trap"),
               ("nice", "Priority"), ("proc-fs", "/proc"), ("nohup", "Surviving a logout"), ("pstree", "Parents"))),
    ("script", (("script-args", "Script arguments"), ("cmd-subst", "Command substitution"), ("tests", "Tests"),
                ("loops", "Loops"), ("while-read", "Reading input"), ("case", "case"), ("functions", "Functions"),
                ("exit-codes", "Exit codes"), ("tar", "Archives"), ("cron", "cron"))),
    ("insight", (("disk", "Disks and mounts"), ("du", "Folder sizes"), ("memory", "Memory"), ("os-info", "The system"),
                 ("ports", "Listening ports"), ("packages", "Packages"), ("env", "The account"))),
)
SKILLS = {sid: {"stage": stage, "title": title} for stage, rows in _SKILL_ROWS for sid, title in rows}

# name, XP, Super challenges cleared, one of them without hints
RANKS = (("Guest", 0, 0, False), ("User", 150, 0, False), ("Power user", 500, 0, False), ("Operator", 1200, 0, False),
         ("Sysadmin", 2500, 0, False), ("Kernel hacker", 4000, 2, False), ("root", 6000, 5, True))
RANK_NAMES = tuple(r[0] for r in RANKS)
JOURNEYMAN = ("journeyman", "Linux Journeyman", "every stage badge of the Linux skill roadmap")
OTHER_BADGES = (("clean-run", "Clean run", "a Hard scenario cleared with no hints, on the first Check"),
                ("beat-the-clock", "Beat the clock", "a Super challenge cleared in less than half its countdown"),
                ("explorer", "Explorer", "one scenario cleared in every track"),
                ("author", "Scenario author", "a project team whose scenarios entered the room"))
NICK_RE = re.compile(r"^[A-Za-z0-9 _-]{3,20}$")


# ── Catalogue ─────────────────────────────────────────────────

def scenario_dirs():
    env = os.environ.get("ITC_PRACTICE_SCENARIOS")
    if env:
        return [Path(x) for x in env.split(os.pathsep) if x]
    return [HERE / "scenarios", HERE / "private"]


_CAT = {"key": None, "mods": {}, "errors": []}


def catalog():
    """Scenario id -> module. Read again when a file changes, so a new scenario needs no restart."""
    files = []
    for d in scenario_dirs():
        try:
            files += sorted(p for p in d.glob("*.py") if not p.name.startswith(("_", "test")))
        except OSError:
            continue
    key = tuple((str(p), p.stat().st_mtime) for p in files)
    if key == _CAT["key"]:
        return _CAT["mods"]
    mods, errors = {}, []
    for p in files:
        try:
            spec = importlib.util.spec_from_file_location("practice_scn_" + p.stem, str(p))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            m = mod.META
            if not SCENARIO_RE.match(m.get("id", "")) or m.get("track") not in TRACK_IDS or m.get("level") not in LEVELS:
                raise ValueError("bad META")
            m.setdefault("xp", BASE_XP[m["level"]])
            m.setdefault("minutes", MINUTES[m["level"]])
            unknown = [s for s in m.get("skills", []) if s not in SKILLS]
            if unknown:
                raise ValueError("unknown skills %s" % unknown)
            m["private"] = p.parent.name == "private"
            if m["id"] in mods:
                raise ValueError("duplicate id %s" % m["id"])
            mods[m["id"]] = mod
        except Exception as e:
            errors.append("%s: %s" % (p.name, e))
    _CAT.update(key=key, mods=mods, errors=errors)
    return mods


def meta_of(mod):
    m = mod.META
    out = {"id": m["id"], "track": m["track"], "level": m["level"], "title": m["title"], "xp": int(m["xp"]),
           "minutes": int(m["minutes"]), "learn": m.get("learn", ""), "private": bool(m.get("private"))}
    if m.get("stage") or m.get("skills"):
        out.update(stage=m.get("stage", ""), skills=list(m.get("skills", [])), readonly=bool(m.get("readonly")))
    return out


def metas():
    """The scenarios only: the API builds the map of tracks and levels from this. See all_metas()."""
    return {sid: meta_of(mod) for sid, mod in catalog().items()}


def drill_dirs():
    env = os.environ.get("ITC_PRACTICE_DRILLS")
    if env:
        return [Path(x) for x in env.split(os.pathsep) if x]
    return [HERE / "drills"]


_DCAT = {"key": None, "mods": {}, "errors": []}


def drills():
    """Drill id -> module, from drills/*.py (each holds DRILLS = [D(...), ...], see drillkit.py). Read again when a
    file changes. A bad drill is left out and named in _DCAT["errors"]; the runner logs it."""
    files = []
    for d in drill_dirs():
        try:
            files += sorted(p for p in d.glob("*.py") if not p.name.startswith(("_", "test")))
        except OSError:
            continue
    scn = catalog()
    key = (_CAT["key"],) + tuple((str(p), p.stat().st_mtime) for p in files)
    if key == _DCAT["key"]:
        return _DCAT["mods"]
    mods, errors = {}, []
    for p in files:
        try:
            spec = importlib.util.spec_from_file_location("practice_drill_" + p.stem, str(p))
            fm = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fm)
            for d in fm.DRILLS:
                try:
                    if not SCENARIO_RE.match(d.id):
                        raise ValueError("bad id")
                    if d.stage not in STAGE_IDS:
                        raise ValueError("unknown stage %r" % d.stage)
                    if not d.skills:
                        raise ValueError("no skill")
                    for s in d.skills:
                        if s not in SKILLS or SKILLS[s]["stage"] != d.stage:
                            raise ValueError("skill %r is not a skill of stage %s" % (s, d.stage))
                    if d.id in mods or d.id in scn:
                        raise ValueError("duplicate id")
                    d.validate()
                    mod = d.module()
                    m = mod.META
                    m.setdefault("xp", BASE_XP["drill"])
                    m.setdefault("minutes", MINUTES["drill"])
                    m["private"] = False
                    mods[d.id] = mod
                except Exception as e:
                    errors.append("%s: %s: %s" % (p.name, getattr(d, "id", "?"), e))
        except Exception as e:
            errors.append("%s: %s" % (p.name, e))
    _DCAT.update(key=key, mods=mods, errors=errors)
    return mods


def exercises():
    """Everything the runner can set up and check in a workspace: the scenarios and the drills."""
    out = dict(drills())
    out.update(catalog())
    return out


def exercise(sid):
    return catalog().get(sid) or drills().get(sid)


def all_metas():
    """Scenarios, drills and quizzes, for XP, ranks, skills and stage badges."""
    import quizzes   # here, not at the top: quizzes.py imports this module
    out = metas()
    out.update({sid: meta_of(mod) for sid, mod in drills().items()})
    out.update(quizzes.metas())
    return out


def catalog_errors():
    import quizzes
    drills()
    return list(_CAT["errors"]) + list(_DCAT["errors"]) + quizzes.errors()


def values(mod, user, attempt):
    """The student's personal values for one attempt (a remix is a new attempt with new values)."""
    pick = oslab.picker(user, "practice/" + mod.META["id"], str(int(attempt)))
    return mod.values(pick)


def hints_of(mod, v):
    level = mod.META["level"]
    if level == "super":
        return []
    h = getattr(mod, "hints", None) or getattr(mod, "HINTS", [])
    return list(h(v) if callable(h) else h)[:MAX_HINTS.get(level, 3)]


def steps_of(mod, v, attempt=1):
    """The steps of a guided exercise, or [] when it has none. A remix (attempt 2 or more) has no lesson lines: the
    student has read them, so the second time is a test."""
    f = getattr(mod, "steps", None)
    return f(v, remix=int(attempt) > 1) if f else []


def step_progress(steps, results):
    """Where the student is in a guided exercise, from the checks the runner reported (each {id, ok}).

    Returns {"current": index of the first step with a check not passed (== len(steps) when all passed),
    "steps": [{"state": "done" | "current" | "todo", "checks": [{id, ok}]}]}. A step is done when every check it
    decides passed. Checks the runner did not report count as not passed."""
    ok = {r.get("id"): bool(r.get("ok")) for r in results or []}
    rows, current = [], None
    for i, s in enumerate(steps):
        done = all(ok.get(cid, False) for cid in s["checks"])
        if not done and current is None:
            current = i
        rows.append({"state": "done" if done else "todo", "checks": [{"id": c, "ok": ok.get(c, False)} for c in s["checks"]]})
    if current is None:
        current = len(rows)
    else:
        rows[current]["state"] = "current"
    return {"current": current, "steps": rows}


def hidden_picker(key, user, sid, attempt):
    """Super challenges: hidden inputs drawn with a key only root holds, so knowing the term salt does not give them,
    and a new attempt gets new ones."""
    def pick(label, count):
        msg = ("%s|%s|%d|%s" % (user, sid, int(attempt), label)).encode("utf-8")
        return int.from_bytes(hmac.new(key, msg, hashlib.sha256).digest()[:8], "big") % count
    return pick


# ── XP, ranks, badges ─────────────────────────────────────────

def first_clear_xp(base, level, hints, late, fast):
    x = base * HINT_SHARE[max(0, min(3, int(hints)))]
    if hints == 0 and level != "quiz":   # a quiz has no "no hints" bonus (10 XP, or 9 with its hint)
        x += base * NO_HINT_BONUS
    if level == "super" and fast:
        x += base * FAST_BONUS
    if late and level != "super":
        x *= LATE_SHARE
    return int(round(x))


def week_start(now=None):
    d = datetime.fromtimestamp(now or time.time(), PPH)
    monday = (d - timedelta(days=d.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday.timestamp()


def standings(entries, cat_meta, until=None, now=None):
    """Every student's XP, clears and facts for badges, recomputed from the ledger in order."""
    wk = week_start(now)
    out = {}
    for e in sorted(entries, key=lambda e: e.get("ts", 0)):
        if until is not None and e.get("ts", 0) > until:
            continue
        u = out.setdefault(e.get("user"), empty_standing())
        x = 0
        if e.get("kind") == "clear":
            sid = e.get("sid")
            m = cat_meta.get(sid) or {"level": e.get("level"), "xp": e.get("base", 0), "track": e.get("track")}
            level, base = m.get("level"), int(m.get("xp") or 0)
            if sid not in u["cleared"]:
                hints = int(e.get("hints", 0))
                x = first_clear_xp(base, level, hints, bool(e.get("late")), bool(e.get("fast")))
                u["cleared"][sid] = {"hints": hints, "ts": e["ts"], "track": m.get("track"), "level": level}
                if level != "quiz":   # a skill is acquired by a hands-on clear, never by a quiz
                    u["skills"].update(m.get("skills") or [])
                if level == "super":
                    u["supers"].add(sid)
                    u["super_nohint"] = u["super_nohint"] or hints == 0
                    u["clock"] = u["clock"] or bool(e.get("fast"))
                if level == "hard" and hints == 0 and int(e.get("checks", 0)) == 1:
                    u["clean"] = True
            else:
                n = u["remix"].get(sid, 0)
                # a drill or quiz played again (to revise) earns nothing: only scenarios pay for remixes
                x = int(round(base * REMIX_SHARE)) if n < REMIX_MAX and level not in KINDS else 0
                u["remix"][sid] = n + 1
        elif e.get("kind") == "correction":
            x = int(e.get("xp", 0))
            u["corrections"] += x
        u["xp"] += x
        if e.get("ts", 0) >= wk:
            u["week"] += x
        u["last"] = max(u["last"], e.get("ts", 0))
    return out


def rank_of(st):
    xp, supers, nohint = st["xp"], len(st["supers"]), st["super_nohint"]
    best = 0
    for i, (_name, need, sup, nh) in enumerate(RANKS):
        if xp >= need and supers >= sup and (nohint or not nh):
            best = i
    return best


def next_rank(st):
    i = rank_of(st)
    if i + 1 >= len(RANKS):
        return None
    name, need, sup, nh = RANKS[i + 1]
    out = {"name": name, "xp": need, "xp_left": max(0, need - st["xp"])}
    if sup:
        out["supers"] = sup
        out["supers_left"] = max(0, sup - len(st["supers"]))
    if nh:
        out["needs_nohint_super"] = not st["super_nohint"]
    return out


def badges_of(st, cat_meta, author=False):
    cleared = st["cleared"]
    out = []
    for t in TRACKS:
        need = [sid for sid, m in cat_meta.items() if m["track"] == t["id"] and m["level"] in ("easy", "medium", "hard")]
        have = {cat_meta[s]["level"] for s in need}
        ok = {"easy", "medium", "hard"} <= have and all(s in cleared for s in need)
        if need:
            out.append({"id": "track-" + t["id"], "name": t["badge"], "earned": ok,
                        "how": "clear the Easy, Medium and Hard scenarios of %s" % t["title"]})
    tracks = {m["track"] for m in cat_meta.values() if m.get("track")}   # the scenarios' tracks, not the drills
    explorer = bool(tracks) and all(any(c.get("track") == tr for c in cleared.values()) for tr in tracks)
    facts = {"clean-run": st["clean"], "beat-the-clock": st["clock"], "explorer": explorer, "author": bool(author)}
    for bid, name, how in OTHER_BADGES:
        out.append({"id": bid, "name": name, "earned": bool(facts[bid]), "how": how})
    out += stage_badges(st, cat_meta)
    return out


def stage_badges(st, cat_meta):
    """One badge per stage that has exercises (clear every drill and pass every quiz of it), and the Linux
    Journeyman, which needs all six stages to have exercises and all six badges."""
    out, earned = [], []
    for s in STAGES:
        need = [sid for sid, m in cat_meta.items() if m.get("stage") == s["id"]]
        if not need:
            earned.append(False)
            continue
        ok = all(sid in st["cleared"] for sid in need)
        earned.append(ok)
        out.append({"id": "stage-" + s["id"], "name": s["badge"], "earned": ok,
                    "how": "clear every drill and pass every quiz of the stage %s" % s["title"]})
    if out:
        out.append({"id": JOURNEYMAN[0], "name": JOURNEYMAN[1], "earned": all(earned), "how": JOURNEYMAN[2]})
    return out


def skills_summary(st):
    """Skills acquired, of all the skills of the roadmap (from SKILLS, not from what is loaded)."""
    have = sorted(s for s in st["skills"] if s in SKILLS)
    return {"have": len(have), "total": len(SKILLS), "ids": have}


def empty_standing():
    return {"xp": 0, "week": 0, "cleared": {}, "remix": {}, "supers": set(), "super_nohint": False, "clean": False,
            "clock": False, "last": 0, "corrections": 0, "skills": set()}


# ── Storage ───────────────────────────────────────────────────

def var():
    return Path(os.environ.get("ITC_PRACTICE_VAR", "/srv/practice"))


@contextmanager
def locked():
    """One lock for every write (Flask serves requests on threads; a double-clicked Check must not award twice)."""
    var().mkdir(parents=True, exist_ok=True)
    with open(var() / ".lock", "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, type(default)) else default
    except (OSError, ValueError):
        return default


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".%s.%s.tmp" % (path.name, secrets.token_hex(4)))
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
    os.chmod(tmp, 0o640)
    os.replace(tmp, path)


def runs(user):
    return read_json(var() / "runs" / ("%s.json" % user), {})


def save_runs(user, data):
    write_json(var() / "runs" / ("%s.json" % user), data)


_LEDGER = {"key": None, "entries": []}


def ledger():
    path = var() / "ledger.jsonl"
    try:
        st = path.stat()
        key = (st.st_size, st.st_mtime)
    except OSError:
        return []
    if key == _LEDGER["key"]:
        return _LEDGER["entries"]
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
                if isinstance(e, dict):
                    out.append(e)
            except ValueError:
                continue
    _LEDGER.update(key=key, entries=out)
    return out


def append_ledger(entry):
    """Call inside locked()."""
    entry = dict(entry, ts=round(entry.get("ts") or time.time(), 3))
    path = var() / "ledger.jsonl"
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
    with os.fdopen(fd, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def profiles():
    return read_json(var() / "profiles.json", {})


def save_profiles(d):
    write_json(var() / "profiles.json", d)


def clean_nick(text):
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if t == "":
        return ""
    if not NICK_RE.match(t):
        raise ValueError("A nickname is 3 to 20 letters, digits, spaces, - or _.")
    return t


BONUS_DEFAULT = {"per_rank": {}, "cap": 0, "read_at": "", "manual": [], "published": False, "published_at": None}


def bonus_settings():
    d = read_json(var() / "bonus.json", {})
    out = dict(BONUS_DEFAULT)
    out.update({k: d[k] for k in BONUS_DEFAULT if k in d})
    return out


def save_bonus(d):
    write_json(var() / "bonus.json", d)


def read_at_ts(b):
    """End of the day the ranks are read (Phnom Penh), or None for "now"."""
    try:
        day = datetime.strptime(b.get("read_at") or "", "%Y-%m-%d").replace(tzinfo=PPH)
        return (day + timedelta(days=1)).timestamp() - 0.001
    except ValueError:
        return None


def bonus_for(user, entries, cat_meta, b):
    """The bonus on the lab mark: the amount for the rank held on the read date, plus manual bonuses, capped."""
    st = standings(entries, cat_meta, until=read_at_ts(b)).get(user) or empty_standing()
    rank = RANKS[rank_of(st)][0]
    amount = float((b.get("per_rank") or {}).get(rank) or 0)
    amount += sum(float(m.get("amount") or 0) for m in b.get("manual") or [] if m.get("user") == user)
    cap = float(b.get("cap") or 0)
    return {"rank": rank, "amount": round(max(0.0, min(cap, amount)) if cap else 0.0, 2)}


# ── The runner (a root service on a Unix socket) ──────────────

def runner_socket():
    return os.environ.get("ITC_PRACTICE_SOCK", "/run/itc-os-practice/runner.sock")


def runner_call(req, timeout=45):
    """One request to the runner; its JSON answer, or {"error": ...} when it cannot be reached."""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(runner_socket())
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        s.close()
        d = json.loads(buf.decode("utf-8") or "{}")
        return d if isinstance(d, dict) else {"error": "bad answer"}
    except (OSError, ValueError) as e:
        return {"error": "runner: %s" % type(e).__name__, "unavailable": True}
