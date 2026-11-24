"""Quizzes for the Linux skill roadmap: a short set of multiple-choice questions, no shell (build step 2 of
teaching/SKILL-ROADMAP-PLAN.md). Standard library only; Python 3.8.

A quiz file (server/practice/private/quizzes/*.py, git-ignored: it holds the keys) is

    QUIZZES = [Quiz(id, stage, title, learn, questions=[Q(id, skill, variants=[...]), ...], n=5)]

A variant is a dict `{"q": text, "right": text, "wrong": [text, ...]}` (three or more wrong ones; three are drawn)
or a function `f(pick) -> that dict`, which can use the student's personal values like a scenario's `values(pick)`.
The quiz asks `n` of its questions (all of them by default), each in one of its variants.

How a quiz runs (the API calls these; none of them reads a file the student can reach):

  - `draw(quiz, user, attempt)`: the questions of one attempt, with the key. Drawn again from (user, attempt) every
    time, so nothing is stored and a reload shows the same questions in the same order. A new attempt draws other
    variants and shuffles the choices again.
  - `public(draw)`: what the page gets: the question and its four choices (a to d), never the key or the skill.
  - `hint(draw, i)`: the ids of two wrong choices to take away from question i (one hint per quiz).
  - `grade(draw, answers)`: the score, whether it passed (4 of 5), and the skills to review. It never says which
    choice was right, and never marks one question as it goes, so the key cannot be learned by trying choices.
  - `begin`, `use_hint`, `submit`, `state` keep the attempt in a run record (a dict the API stores): the countdown, the
    one hint, and the 30-second wait after a fail. `clear_entry` is the ledger line of a pass; the ledger gives XP on
    the first pass only, and a quiz never adds a skill (practice.standings).
"""
import importlib.util
import math
import os
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _d in (HERE, HERE.parent):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import kit  # noqa: E402
import oslab  # noqa: E402
import practice  # noqa: E402

PASS_SHARE = 0.8        # 4 of 5
WAIT_S = 30             # after a failed attempt, before the next one
LETTERS = "abcd"
WRONG_SHOWN = 3         # a question has the right choice and three wrong ones
MAX_HINTS = 1


class Q:
    """One question of a quiz: the skill it tests and its variants."""

    def __init__(self, id, skill, variants):
        self.id, self.skill, self.variants = id, skill, list(variants)


class Quiz:
    def __init__(self, id, stage, title, learn, questions, n=None, minutes=None, xp=None):
        self.id, self.stage, self.title, self.learn = id, stage, title, learn
        self.questions = list(questions)
        self.n = len(self.questions) if n is None else int(n)
        self.minutes, self.xp = minutes, xp

    def skills(self):
        return sorted({q.skill for q in self.questions})


# ── building a question from a variant ────────────────────────

def build(variant, pick):
    """A variant as {"q", "right", "wrong": [three]}; `pick(label, count)` draws the personal values and which wrong
    choices are shown."""
    v = variant(pick) if callable(variant) else variant
    wrong = list(v["wrong"])
    if len(wrong) > WRONG_SHOWN:
        wrong = kit.distinct(pick, "wrong", wrong, WRONG_SHOWN)
    return {"q": str(v["q"]), "right": str(v["right"]), "wrong": [str(w) for w in wrong]}


def _check_variant(quiz_id, qid, variant, pick):
    v = variant(pick) if callable(variant) else variant
    if not isinstance(v, dict) or not str(v.get("q", "")).strip() or not str(v.get("right", "")).strip():
        raise ValueError("%s/%s: a variant needs a question and a right choice" % (quiz_id, qid))
    wrong = [str(w) for w in v.get("wrong", [])]
    if len(wrong) < WRONG_SHOWN or any(not w.strip() for w in wrong):
        raise ValueError("%s/%s: a variant needs at least %d wrong choices" % (quiz_id, qid, WRONG_SHOWN))
    if len(set(wrong)) != len(wrong) or str(v["right"]) in wrong:
        raise ValueError("%s/%s: the choices of a variant must all be different" % (quiz_id, qid))


def _probe_picks():
    """Several different pickers, so a variant that builds from personal values is tried on more than one."""
    out = [lambda label, count: 0, lambda label, count: count - 1]
    for k in range(6):
        out.append(lambda label, count, k=k: (sum(map(ord, label)) * 7 + k * 13) % count)
    return out


def validate(q):
    """Load-time checks of one quiz."""
    if not practice.SCENARIO_RE.match(q.id):
        raise ValueError("bad id")
    if q.stage not in practice.STAGE_IDS:
        raise ValueError("unknown stage %r" % q.stage)
    if not q.questions:
        raise ValueError("no questions")
    if not 1 <= q.n <= len(q.questions):
        raise ValueError("n is %d, but there are %d questions" % (q.n, len(q.questions)))
    seen = set()
    for question in q.questions:
        if question.id in seen or not practice.SCENARIO_RE.match(question.id):
            raise ValueError("bad or duplicate question id %r" % question.id)
        seen.add(question.id)
        sk = practice.SKILLS.get(question.skill)
        if not sk or sk["stage"] != q.stage:
            raise ValueError("%s: skill %r is not a skill of stage %s" % (question.id, question.skill, q.stage))
        if not question.variants:
            raise ValueError("%s: no variants" % question.id)
        for variant in question.variants:
            for pick in _probe_picks():
                _check_variant(q.id, question.id, variant, pick)


# ── the catalogue ─────────────────────────────────────────────

def quiz_dirs():
    env = os.environ.get("ITC_PRACTICE_QUIZZES")
    if env:
        return [Path(x) for x in env.split(os.pathsep) if x]
    return [HERE / "private" / "quizzes"]


_CAT = {"key": None, "quizzes": {}, "errors": []}


def catalog():
    """Quiz id -> Quiz, read again when a file changes. A bad quiz is left out and named in errors()."""
    files = []
    for d in quiz_dirs():
        try:
            files += sorted(p for p in d.glob("*.py") if not p.name.startswith(("_", "test")))
        except OSError:
            continue
    taken = set(practice.catalog()) | set(practice.drills())
    key = (practice._CAT["key"], practice._DCAT["key"]) + tuple((str(p), p.stat().st_mtime) for p in files)
    if key == _CAT["key"]:
        return _CAT["quizzes"]
    out, errors = {}, []
    for p in files:
        try:
            spec = importlib.util.spec_from_file_location("practice_quiz_" + p.stem, str(p))
            fm = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fm)
            for q in fm.QUIZZES:
                try:
                    validate(q)
                    if q.id in out or q.id in taken:
                        raise ValueError("duplicate id")
                    out[q.id] = q
                except Exception as e:
                    errors.append("%s: %s: %s" % (p.name, getattr(q, "id", "?"), e))
        except Exception as e:
            errors.append("%s: %s" % (p.name, e))
    _CAT.update(key=key, quizzes=out, errors=errors)
    return out


def errors():
    catalog()
    return list(_CAT["errors"])


def meta_of(q):
    """The quiz as the other exercises' meta (practice.meta_of): level "quiz", no track, 10 XP and 5 minutes unless
    the quiz says otherwise."""
    return practice.meta_of(types.SimpleNamespace(META={
        "id": q.id, "track": "", "stage": q.stage, "skills": q.skills(), "level": "quiz", "title": q.title,
        "learn": q.learn, "private": True, "xp": q.xp if q.xp is not None else practice.BASE_XP["quiz"],
        "minutes": q.minutes if q.minutes is not None else practice.MINUTES["quiz"]}))


def metas():
    return {qid: meta_of(q) for qid, q in catalog().items()}


# ── drawing, hint and grade ───────────────────────────────────

def picker(user, quiz_id, attempt):
    return oslab.picker(user, "practice/quiz/" + quiz_id, str(int(attempt)))


def pass_mark(total):
    return int(math.ceil(PASS_SHARE * total - 1e-9))


def draw(quiz, user, attempt):
    """The questions of one attempt, with the key: [{"qid", "skill", "text", "choices": [{"id", "text"}], "right": id}].
    The same (user, attempt) always gives the same draw."""
    pick = picker(user, quiz.id, attempt)
    chosen = kit.distinct(pick, "question", quiz.questions, quiz.n)
    out = []
    for q in chosen:
        sub = (lambda label, count, qid=q.id: pick("%s/%s" % (qid, label), count))
        variant = q.variants[sub("variant", len(q.variants))]
        b = build(variant, sub)
        items = [("right", b["right"])] + [("wrong", w) for w in b["wrong"]]
        order = kit.distinct(sub, "order", items, len(items))
        choices = [{"id": LETTERS[i], "text": text} for i, (_kind, text) in enumerate(order)]
        right = next(LETTERS[i] for i, (kind, _t) in enumerate(order) if kind == "right")
        out.append({"qid": q.id, "skill": q.skill, "text": b["q"], "choices": choices, "right": right})
    return out


def public(d):
    """What the page gets: no key, no skill."""
    return [{"n": i + 1, "qid": x["qid"], "text": x["text"], "choices": [dict(c) for c in x["choices"]]}
            for i, x in enumerate(d)]


def hint(d, i, user="", quiz_id="", attempt=1):
    """The ids of two wrong choices of question i to take away (the same two every time for that attempt)."""
    x = d[i]
    wrong = [c["id"] for c in x["choices"] if c["id"] != x["right"]]
    pick = picker(user, quiz_id, attempt)
    keep = kit.distinct(pick, "hint/%s" % x["qid"], wrong, 1)[0]
    return [w for w in wrong if w != keep]


def grade(d, answers):
    """answers: {qid: choice id}. Returns {"score", "total", "pass_mark", "passed", "review": [{"skill", "title"}]}.
    A missing, unknown or wrong answer counts as wrong; the right choice is never revealed."""
    answers = answers if isinstance(answers, dict) else {}
    score, wrong_skills = 0, []
    for x in d:
        if answers.get(x["qid"]) == x["right"]:
            score += 1
        elif x["skill"] not in wrong_skills:
            wrong_skills.append(x["skill"])
    need = pass_mark(len(d))
    return {"score": score, "total": len(d), "pass_mark": need, "passed": score >= need,
            "review": [{"skill": s, "title": practice.SKILLS[s]["title"]} for s in wrong_skills]}


# ── one student's attempts (a run record the API stores) ──────

def begin(run, minutes, now):
    """Start an attempt, or continue the open one. Returns None, or {"error": "wait", "retry_s": n} when the last
    attempt failed less than WAIT_S ago. A student who passed may start again to revise (no XP)."""
    if run.get("open"):
        return None
    if run.get("last") == "fail" and now - float(run.get("failed_at", 0)) < WAIT_S:
        return {"error": "wait", "retry_s": round(WAIT_S - (now - float(run["failed_at"])), 1)}
    run.update(attempt=int(run.get("attempt", 0)) + 1, open=True, started=now, deadline=now + float(minutes) * 60,
               hint=None, hints=0)
    return None


def use_hint(run, d, i, user, quiz_id):
    """One hint per quiz: take two wrong choices away from question i. Asking again for the same question gives the
    same answer at no cost. Returns {"removed": [ids]} or {"error": ...}."""
    if not run.get("open"):
        return {"error": "no attempt is open"}
    if not 0 <= i < len(d):
        return {"error": "no such question"}
    h = run.get("hint")
    if h:
        if h["q"] != i:
            return {"error": "one hint per quiz (used on question %d)" % (h["q"] + 1)}
        return {"removed": list(h["removed"])}
    removed = hint(d, i, user, quiz_id, run["attempt"])
    run["hint"] = {"q": i, "removed": removed}
    run["hints"] = 1
    return {"removed": removed}


def submit(run, d, answers, now):
    """Mark an open attempt and close it. A fail starts the wait. A pass sets run["passed"]; whether it earns XP is
    the ledger's rule (first pass only)."""
    if not run.get("open"):
        return {"error": "no attempt is open"}
    res = grade(d, answers)
    res.update(attempt=int(run["attempt"]), hints=int(run.get("hints", 0)), late=now > float(run["deadline"]),
               secs=round(now - float(run["started"]), 1))
    run["open"] = False
    if res["passed"]:
        run.update(passed=True, last="pass", best=max(int(run.get("best", 0)), res["score"]))
    else:
        run.update(last="fail", failed_at=now, best=max(int(run.get("best", 0)), res["score"]))
    return res


def state(run, minutes, now):
    """What the page shows about the attempt."""
    wait = 0.0
    if not run.get("open") and run.get("last") == "fail":
        wait = max(0.0, WAIT_S - (now - float(run.get("failed_at", 0))))
    return {"open": bool(run.get("open")), "attempt": int(run.get("attempt", 0)), "passed": bool(run.get("passed")),
            "retry_s": round(wait, 1), "hint": (run.get("hint") or {}).get("q"),
            "left_s": round(max(0.0, float(run["deadline"]) - now), 1) if run.get("open") else None,
            "minutes": minutes, "best": int(run.get("best", 0))}


def clear_entry(user, meta, res, now):
    """The ledger line of a pass (same fields as a scenario's). The ledger counts it as the first clear or not."""
    return {"user": user, "kind": "clear", "sid": meta["id"], "hints": int(res["hints"]), "late": bool(res["late"]),
            "fast": False, "level": "quiz", "base": int(meta["xp"]), "track": "", "ts": now,
            "attempt": int(res["attempt"]), "score": int(res["score"])}
