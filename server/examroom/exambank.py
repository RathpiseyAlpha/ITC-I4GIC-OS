"""Exam scenario bank: the engine (build step 1 of the instructor's exam bank plan). Standard library only; Python 3.8.

This file holds no exam content. The scenarios are private files in `bank/` (git-ignored, installed root-only); the paper
(`midterm.py`) says which parts there are and what each slot tests (the blueprint).

    PART      a part of the paper: its folder, and its slots with the skill each one tests (the blueprint)
    Scenario  one complete version of a part: story, personal values, starting files, four tasks, their checks
    Bank      every scenario, loaded strictly (any file that fails to load or to validate stops the exam, it is never skipped)
    draw      which scenario each student gets, balanced over the roster, and the draw file that records it with the values

A bank file (`bank/part_a.py` and so on) is

    import exambank as eb
    SCENARIOS = [eb.Scenario(id="A-box", part="A", title=..., skills={"A1": "make", ...}, values=f, fixture=f, tasks=f,
                             check=f, values_line=f, solve=f)]

where, with `v` the student's values for that scenario (JSON data: lists, not tuples):
    values(pick)          -> dict       `pick(label, count)` is the pilot labs' picker (oslab.picker), seeded by the student
    fixture(v)            -> (dirs, {path: text})   relative paths, all inside the part's folder
    tasks(v)              -> [(slot id, text)]      the slots of the blueprint, in order
    check(root, v, kernel)-> [item]                 `item(slot, ok, present, note)`, in the order of the slots; reads files only
    values_line(v)        -> str                    this scenario's line of the student's values.txt
    solve(v)              -> str                    a model solution as shell lines (the tests use it; nothing else does)
"""
import hashlib
import json
import os
import re
import shutil
import stat
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _d in (HERE, HERE.parent):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import common  # noqa: E402
import oslab  # noqa: E402

DRAW_VERSION = 1
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,40}$")
READ_LIMIT = 65536


class BankError(RuntimeError):
    """The bank or a draw is not usable. An exam must stop on it: running the wrong scenario's checks is worse."""


# ── Reading the student's files safely (the checks use these) ─

def read_text(path):
    """Text of a regular file, never following a symbolic link, or None."""
    try:
        fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        return os.read(fd, READ_LIMIT).decode("utf-8", "replace")
    finally:
        os.close(fd)


def lines(text):
    return [line.rstrip("\r") for line in (text or "").split("\n") if line.strip()]


def is_dir(path):
    try:
        return stat.S_ISDIR(os.lstat(str(path)).st_mode)
    except OSError:
        return False


def exists(path):
    try:
        os.lstat(str(path))
        return True
    except OSError:
        return False


def ino(path):
    try:
        st = os.lstat(str(path))
        return st.st_ino if stat.S_ISREG(st.st_mode) else None
    except OSError:
        return None


def nonempty(path):
    try:
        st = os.lstat(str(path))
        return stat.S_ISDIR(st.st_mode) or st.st_size > 0 or stat.S_ISLNK(st.st_mode)
    except OSError:
        return False


def clean_path(text):
    line = next(iter(lines(text)), "").strip()
    if len(line) >= 2 and line[0] == line[-1] and line[0] in "'\"":
        line = line[1:-1]
    return line.replace("\\ ", " ")


def item(slot, ok, present, note="", marks=2):
    """One checked task. "ok" is for the instructor's board; students see only "present" (the expected file exists)."""
    return {"id": slot, "marks": marks, "ok": bool(ok), "present": bool(present), "note": note}


# ── The blueprint, scenarios and the bank ─────────────────────

class Part:
    """A part of the paper: its folder in the student's exam folder, and its slots [(slot id, skill)] in order."""

    def __init__(self, id, folder, slots, marks=2):
        self.id, self.folder, self.slots, self.marks = id, folder, [(s, k) for s, k in slots], int(marks)

    def slot_ids(self):
        return [s for s, _k in self.slots]


class Scenario:
    def __init__(self, id, part, title, skills, values, fixture, tasks, check, values_line, solve=None, story="",
                 minutes=None, nonce=None):
        self.id, self.part, self.title, self.story = id, part, title, story
        self.skills, self.minutes, self.solve = dict(skills), minutes, solve
        self.values, self.fixture, self.tasks, self.check, self.values_line = values, fixture, tasks, check, values_line
        # The picker's nonce. A new scenario leaves it None (its own id, so adding a scenario never changes another one's
        # values). Scenario 1 of each part of the first paper sets "" to give exactly the values that paper always gave.
        self.nonce = id if nonce is None else str(nonce)


def norm(data):
    """Values as the draw file holds them (JSON data), so a computed value and a recorded one are the same thing."""
    return json.loads(json.dumps(data))


def compute_values(scenario, user, namespace):
    return norm(scenario.values(oslab.picker(user, namespace, scenario.nonce)))


def _probe_picks():
    out = [lambda label, count: 0, lambda label, count: count - 1]
    for k in range(6):
        out.append(lambda label, count, k=k: (sum(map(ord, label)) * 7 + k * 13) % count)
    return out


def _safe_rel(path, folder):
    p = str(path)
    parts = p.split("/")
    return (bool(p) and not p.startswith("/") and ".." not in parts and "" not in parts and parts[0] == folder)


def validate(scenario, part):
    """Load-time checks of one scenario against its part's blueprint. Raises ValueError with the reason."""
    s = scenario
    if not ID_RE.match(str(s.id)):
        raise ValueError("bad id")
    if s.part != part.id:
        raise ValueError("part is %r, expected %r" % (s.part, part.id))
    if s.skills != dict(part.slots):
        raise ValueError("skills %s do not follow the blueprint %s" % (s.skills, dict(part.slots)))
    for fn in ("values", "fixture", "tasks", "check", "values_line"):
        if not callable(getattr(s, fn)):
            raise ValueError("%s is missing" % fn)
    for pick in _probe_picks():
        v = norm(s.values(pick))
        if not isinstance(v, dict):
            raise ValueError("values must return a dict")
        tasks = s.tasks(v)
        if [t[0] for t in tasks] != part.slot_ids() or any(not str(t[1]).strip() for t in tasks):
            raise ValueError("tasks must be exactly %s, with a text each" % part.slot_ids())
        dirs, files = s.fixture(v)
        for p in list(dirs) + list(files):
            if not _safe_rel(p, part.folder):
                raise ValueError("starting file %r is not inside %s/" % (p, part.folder))
        got = s.check(Path("/nonexistent-exam-bank"), v, "0.0.0")
        if [i["id"] for i in got] != part.slot_ids() or any(i["marks"] != part.marks for i in got):
            raise ValueError("check must return %s with %d marks each" % (part.slot_ids(), part.marks))
        if not str(s.values_line(v)).strip():
            raise ValueError("values_line is empty")


def bank_dir():
    env = os.environ.get("ITC_EXAM_BANK")
    return Path(env) if env else HERE / "bank"


class Bank:
    def __init__(self, parts, scenarios, digest):
        self.parts = {p.id: p for p in parts}
        self.order = [p.id for p in parts]
        self.scenarios = {}          # part id -> [Scenario], by id
        for sc in sorted(scenarios, key=lambda x: x.id):
            self.scenarios.setdefault(sc.part, []).append(sc)
        self.by_id = {sc.id: sc for sc in scenarios}
        self.hash = digest

    def ids(self, part, disabled=()):
        return [sc.id for sc in self.scenarios.get(part, []) if sc.id not in disabled]


_CACHE = {"key": None, "bank": None}


def _files(directory):
    try:
        return sorted(p for p in Path(directory).glob("*.py") if not p.name.startswith(("_", "test")))
    except OSError:
        return []


def bank_hash(files):
    """Content hash of the bank files (names and bytes, not modification times)."""
    h = hashlib.sha256()
    for p in sorted(files, key=lambda x: x.name):
        h.update(p.name.encode("utf-8") + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def load(parts, directory=None):
    """The bank, loaded strictly: any file that fails to load, any scenario that fails validation, a duplicate id or a part
    without a scenario raises BankError naming every problem. Read again only when a file changed."""
    import importlib.util
    directory = Path(directory) if directory else bank_dir()
    files = _files(directory)
    key = (str(directory), tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in files),
           tuple((p.id, p.folder, tuple(p.slots), p.marks) for p in parts))
    if key == _CACHE["key"]:
        return _CACHE["bank"]
    errors, found = [], []
    if not files:
        errors.append("no scenario files in %s" % directory)
    for p in files:
        try:
            spec = importlib.util.spec_from_file_location("exam_bank_" + p.stem, str(p))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            found += list(mod.SCENARIOS)
        except Exception as e:
            errors.append("%s: %s: %s" % (p.name, type(e).__name__, e))
    by_part = {pt.id: pt for pt in parts}
    ok, seen = [], set()
    for sc in found:
        try:
            if sc.id in seen:
                raise ValueError("duplicate id")
            seen.add(sc.id)
            if sc.part not in by_part:
                raise ValueError("unknown part %r" % sc.part)
            validate(sc, by_part[sc.part])
            ok.append(sc)
        except Exception as e:
            errors.append("%s: %s" % (getattr(sc, "id", "?"), e))
    for pt in parts:
        if not any(sc.part == pt.id for sc in ok):
            errors.append("part %s has no scenario" % pt.id)
    if errors:
        raise BankError("the scenario bank is not usable: " + "; ".join(errors))
    bank = Bank(parts, ok, bank_hash(files))
    _CACHE.update(key=key, bank=bank)
    return bank


# ── The draw ──────────────────────────────────────────────────

def _h(*bits):
    return hashlib.sha256("|".join(str(b) for b in bits).encode("utf-8")).hexdigest()


def deal(users, ids, seed, part):
    """{user: scenario id}: the roster sorted by a hash of (seed, part, user) and the scenarios dealt out in turn, so the
    counts differ by at most one, and the result depends on neither the roster's order nor the Python version."""
    if not ids:
        raise BankError("part %s has no scenario to draw from" % part)
    order = sorted(set(users), key=lambda u: (_h(seed, part, u), u))
    start = int(_h(seed, part, "start")[:8], 16) % len(ids)
    return {u: ids[(start + i) % len(ids)] for i, u in enumerate(order)}


def draw_roster(bank, users, seed, disabled=(), pins=None, mode="balanced"):
    """{user: {part: scenario id}} for the roster. `mode` "balanced" deals each part's scenarios out over the roster (counts
    differ by at most one); "random" is an independent stable pick per student. `disabled` are scenario ids out of play;
    `pins` is {user: {part: scenario id}} and takes that student out of the dealing for that part."""
    pins = pins or {}
    users = sorted(set(users))
    out = {u: {} for u in users}
    for part in bank.order:
        ids = bank.ids(part, disabled)
        pinned = {u: pins[u][part] for u in users if part in (pins.get(u) or {})}
        for u, sid in pinned.items():
            if sid not in bank.by_id or bank.by_id[sid].part != part:
                raise BankError("%s: pinned scenario %r is not a scenario of part %s" % (u, sid, part))
        rest = [u for u in users if u not in pinned]
        if mode == "random":
            for u in rest:
                out[u][part] = pick_one(bank, u, seed, part, disabled)
        else:
            for u, sid in deal(rest, ids, seed, part).items():
                out[u][part] = sid
        for u, sid in pinned.items():
            out[u][part] = sid
    return out


def pick_one(bank, user, seed, part, disabled=()):
    """A stable pick for one student: the "random" mode, and a student who is not on the roster (a late addition)."""
    ids = bank.ids(part, disabled)
    if not ids:
        raise BankError("part %s has no scenario to draw from" % part)
    return ids[int(_h("bank", seed, part, user)[:8], 16) % len(ids)]


def make_draw(bank, user, exam_id, assignment, namespace):
    """The draw file's content: the scenario of each part, and the student's values for each, as they are now."""
    scenarios = {part: assignment[part] for part in bank.order}
    return {"v": DRAW_VERSION, "exam": exam_id, "bank": bank.hash, "scenarios": scenarios,
            "values": {part: compute_values(bank.by_id[sid], user, namespace) for part, sid in scenarios.items()}}


def draw_dir(exam_id):
    return common.var_dir() / str(exam_id) / "draw"


def draw_path(exam_id, user):
    if not common.USER_RE.match(str(user)):
        raise BankError("bad user name")
    return draw_dir(exam_id) / ("%s.json" % user)


def _own(path, group, mode):
    os.chmod(str(path), mode)
    if group and os.geteuid() == 0:
        shutil.chown(str(path), "root", group)


def write_draws(exam_id, draws, group=None):
    """Write every student's draw file at once: into a temporary folder that is then renamed to `draw/`, so a reader never
    sees a half-written draw folder (and `drawn()` is never true with students missing). Refuses when `draw/` exists.
    Run as root, `group` makes the folder 0750 and the files 0640 owned by root:<group> (the API reads, students cannot)."""
    final = draw_dir(exam_id)
    if final.exists():
        raise BankError("%s already has a draw: discard it first, or add the missing students" % exam_id)
    final.parent.mkdir(parents=True, exist_ok=True)
    tmp = final.parent / ("draw.tmp-%s" % os.urandom(4).hex())
    tmp.mkdir(mode=0o750)
    try:
        for user, draw in draws.items():
            path = tmp / ("%s.json" % user)
            if not common.USER_RE.match(str(user)):
                raise BankError("bad user name %r" % user)
            common.write_json_atomic(path, draw, mode=0o640)
            _own(path, group, 0o640)
        _own(tmp, group, 0o750)
        os.rename(str(tmp), str(final))
    except Exception:
        shutil.rmtree(str(tmp), ignore_errors=True)
        raise


def add_draw(exam_id, user, draw, group=None):
    """One more student after the exam has drawn (one atomic file). Refuses to replace an existing draw."""
    path = draw_path(exam_id, user)
    if path.exists():
        raise BankError("%s already has a draw" % user)
    common.write_json_atomic(path, draw, mode=0o640)
    _own(path, group, 0o640)


def discard_draws(exam_id):
    """Remove the draw folder (only while the exam is sealed and has never been opened: the caller checks)."""
    shutil.rmtree(str(draw_dir(exam_id)), ignore_errors=True)
    _DRAWS.clear()


def drawn(exam_id):
    """True once the exam has drawn (the folder holds a draw file): from then on a missing draw is an error, not a guess."""
    try:
        return any(draw_dir(exam_id).glob("*.json"))
    except OSError:
        return False


_DRAWS = {}


def read_draw(exam_id, user, bank):
    """The recorded draw of one student, or None when there is none. A file that is there but wrong raises BankError."""
    path = draw_path(exam_id, user)
    try:
        st = path.stat()
    except OSError:
        return None
    key = (str(path), st.st_mtime_ns, st.st_size)
    hit = _DRAWS.get(str(path))
    if hit and hit[0] == key:
        d = hit[1]
    else:
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise BankError("the draw of %s cannot be read: %s" % (user, e))
        _DRAWS[str(path)] = (key, d)
    if not isinstance(d, dict) or d.get("v") != DRAW_VERSION or not isinstance(d.get("scenarios"), dict) \
            or not isinstance(d.get("values"), dict):
        raise BankError("the draw of %s is not a version %d draw" % (user, DRAW_VERSION))
    for part in bank.order:
        sid = d["scenarios"].get(part)
        if sid not in bank.by_id or bank.by_id[sid].part != part:
            raise BankError("the draw of %s names scenario %r for part %s, which the bank does not have" % (user, sid, part))
        if not isinstance(d["values"].get(part), dict):
            raise BankError("the draw of %s has no values for part %s" % (user, part))
    return d


_ROSTER = {"fn": None}
_PRE = {"key": None, "draw": None}


def set_roster_source(fn):
    """Where the roster comes from before the exam has drawn (the API: its student list; examctl: the roster file), so the
    instructor's preview, "view as student" and the draw `examctl open` writes are all the same balanced deal."""
    _ROSTER["fn"] = fn


def _roster():
    try:
        return sorted(set(_ROSTER["fn"]() or [])) if _ROSTER["fn"] else []
    except Exception:
        return []


def plan_draws(bank, users, exam_id, namespace, settings):
    """{user: draw} for a roster as `examctl open` would write it: `settings` is {"mode", "seed", "disabled", "pins"}."""
    assign = draw_roster(bank, users, settings.get("seed") or exam_id, settings.get("disabled") or (), settings.get("pins"),
                         settings.get("mode") or "balanced")
    return {u: make_draw(bank, u, exam_id, assign[u], namespace) for u in sorted(set(users))}


def resolve(bank, user, exam_id, namespace, settings=None):
    """What a student has: the recorded draw if the exam drew; before that the same draw `examctl open` will write, computed
    over the roster (balanced) and cached; a stable per-student pick only for someone who is not on the roster."""
    d = read_draw(exam_id, user, bank)
    if d:
        return d
    if drawn(exam_id):
        raise BankError("%s has no draw in %s, but the exam has drawn: run examctl draw add" % (user, draw_dir(exam_id)))
    settings = settings or {}
    roster = _roster()
    seed = settings.get("seed") or exam_id
    disabled = tuple(sorted(settings.get("disabled") or ()))
    pins = settings.get("pins") or {}
    mode = settings.get("mode") or "balanced"
    if user in roster:
        key = (bank.hash, tuple(roster), seed, disabled, json.dumps(pins, sort_keys=True), mode, exam_id)
        if _PRE["key"] != key:
            _PRE.update(key=key, draw=draw_roster(bank, roster, seed, disabled, pins, mode))
        assign = _PRE["draw"][user]
    else:
        assign = {part: (pins.get(user, {}).get(part) or pick_one(bank, user, seed, part, disabled)) for part in bank.order}
    return make_draw(bank, user, exam_id, assign, namespace)


# ── Corrections (a regrade: a slot of a scenario is given or ignored, with a reason) ─────

def corrections_path(exam_id):
    return common.var_dir() / str(exam_id) / "corrections.json"


def read_corrections(exam_id):
    """[{"scenario", "slot", "mode": "give"|"ignore", "reason", "by", "at"}], [] when there are none."""
    d = common.read_json(corrections_path(exam_id), []) or []
    return [c for c in d if isinstance(c, dict) and c.get("mode") in ("give", "ignore") and c.get("scenario") and c.get("slot")]


def write_corrections(exam_id, items, group=None):
    path = corrections_path(exam_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    common.write_json_atomic(path, items, mode=0o640)
    _own(path, group, 0o640)


def bank_changed(draw, bank):
    """True when the bank is not the one the draw was made with (the draw's recorded scenario and values still hold)."""
    return draw.get("bank") != bank.hash

