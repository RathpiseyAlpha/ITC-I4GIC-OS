"""Drills for the Linux skill roadmap: short, one-skill exercises (server/practice/drills/*.py).

A drill file holds `DRILLS = [D(...), ...]`. The catalogue turns each drill into an object shaped like a scenario
module (META, values, fixture, brief, hints, collect, checks, and steps when guided), so the runner, the API and the
room use them as they use scenarios. A drill's check judges the data the collector brings back, like a scenario's
(it runs as root, on data, and reads no file).

    D(id, stage, skills, title, learn,
      task=lambda v: "text" or [blocks],     # what to do, with the student's values
      check=lambda t, data, v: ...,          # see below
      values=lambda pick: {...},             # personal values (default: none)
      files=lambda v: {"dirs": [], "files": {}},
      hints=lambda v: [..] or [..],          # one or two; the last gives the command
      collect=lambda v: {...},               # default: the workspace tree
      facts=["kernel", ...],                 # read-only facts the collector brings back (collect.py FACTS)
      checks=[("id", "label"), ...],         # the checks, declared; required when the drill has steps
      steps=lambda v: [S(...), ...],         # a guided drill (stages 1 and 2, and half of 3 and 4)
      goal="what the check verifies",        # the label when check returns (ok, why)
      readonly=False)                        # a drill that only looks at the system

What `check` returns:

  - drill with `checks=` declared: a list of `(id, ok, why)` or a dict `{id: (ok, why)}`. Every declared check is
    always reported, in the declared order, with a stable id: one the function leaves out counts as not reached.
    An id that is not declared is a bug in the drill and fails the check loudly.
  - drill without it: `(ok, why)` (one check, id "done") or a list of `(label, ok, why)` (ids c0, c1, ...). Not for
    guided drills, because their steps name check ids and ids that move with the result would point at the wrong step.

XP and minutes are not set here: practice.py gives every drill the same (BASE_XP, MINUTES), unless `xp=` or
`minutes=` says otherwise. Python 3.8: the development machine and the server run it.
"""
import types

import kit


class S:
    """One step of a guided exercise: a lesson line, the task for this step, the ids of the checks that decide it,
    and optionally a hint for this step (the exercise keeps its cap of two hints for a drill, three for a scenario)."""

    def __init__(self, learn, task, checks, hint=None):
        self.learn, self.task, self.checks, self.hint = learn, task, tuple(checks), hint


def _dummy_pick(label, count):
    return 0


class D:
    def __init__(self, id, stage, skills, title, learn, task, check, values=None, files=None, hints=(), collect=None,
                 facts=None, checks=None, steps=None, goal="", minutes=None, xp=None, readonly=False):
        self.__dict__.update(id=id, stage=stage, skills=list(skills), title=title, learn=learn, task=task, check=check,
                             values_fn=values, files_fn=files, hints_fn=hints, collect_fn=collect, facts_fn=facts,
                             declared=[tuple(c) for c in checks] if checks else [], steps_fn=steps, goal=goal,
                             minutes=minutes, xp=xp, readonly=readonly)
        if steps is not None and not self.declared:
            raise ValueError("%s: a guided drill declares its checks (checks=[(id, label), ...])" % id)

    # -- helpers ------------------------------------------------
    def _v(self, pick=None):
        return self.values_fn(pick or _dummy_pick) if self.values_fn else {}

    def steps_list(self, v):
        s = self.steps_fn(v) if callable(self.steps_fn) else self.steps_fn
        return list(s or [])

    def validate(self):
        """Load-time checks: every step names declared checks, and every declared check belongs to a step."""
        if not self.steps_fn:
            return
        ids = [c[0] for c in self.declared]
        if len(set(ids)) != len(ids):
            raise ValueError("%s: duplicate check ids" % self.id)
        steps = self.steps_list(self._v())
        if not steps:
            raise ValueError("%s: no steps" % self.id)
        used = []
        for i, s in enumerate(steps):
            if not s.checks:
                raise ValueError("%s: step %d decides no check" % (self.id, i + 1))
            for cid in s.checks:
                if cid not in ids:
                    raise ValueError("%s: step %d names the check %r, which is not declared" % (self.id, i + 1, cid))
                used.append(cid)
        if set(used) != set(ids):
            raise ValueError("%s: checks no step decides: %s" % (self.id, sorted(set(ids) - set(used))))

    # -- the scenario-shaped module -----------------------------
    def module(self):
        d = self

        def values(pick):
            return d._v(pick)

        def fixture(v):
            spec = d.files_fn(v) if d.files_fn else {}
            return {"dirs": spec.get("dirs", []), "files": spec.get("files", {})}

        def brief(v):
            t = d.task(v) if callable(d.task) else d.task
            blocks = [{"p": t}] if isinstance(t, str) else list(t)
            if d.readonly:
                blocks.append({"p": "Read-only: look at the system, change nothing outside this folder."})
            return blocks

        def explicit_hints(v):
            h = d.hints_fn(v) if callable(d.hints_fn) else d.hints_fn
            return [x(v) if callable(x) else x for x in (h or [])]   # a list may mix text and functions of v

        def step_hints(v):
            return [(i, s.hint) for i, s in enumerate(d.steps_list(v)) if s.hint]

        def hints(v):
            h = explicit_hints(v)
            return (h if h else [x for _i, x in step_hints(v)])[:2]

        def hint_steps(v):
            """For each hint, the step it belongs to (None when the hint is for the whole exercise)."""
            if explicit_hints(v):
                return [None] * len(hints(v))
            return [i for i, _x in step_hints(v)][:2]

        def steps(v, remix=False):
            out = []
            for s in d.steps_list(v):
                task = s.task(v) if callable(s.task) else s.task
                out.append({"learn": "" if remix else s.learn, "task": task, "checks": list(s.checks)})
            return out

        def collect(v, hidden):
            req = dict(d.collect_fn(v)) if d.collect_fn else {"tree": True}
            if d.facts_fn:
                req["facts"] = list(d.facts_fn(v) if callable(d.facts_fn) else d.facts_fn)
            return req

        def checks(data, v, hidden, info):
            t = kit.Tree.of(data)
            r = d.check(t, data, v)
            if d.declared:
                if isinstance(r, dict):
                    got = {k: (bool(x[0]), x[1] if len(x) > 1 else "") for k, x in r.items()}
                else:
                    got = {x[0]: (bool(x[1]), x[2] if len(x) > 2 else "") for x in r}
                known = {c[0] for c in d.declared}
                if set(got) - known:
                    raise ValueError("%s: the check returned undeclared ids %s" % (d.id, sorted(set(got) - known)))
                out = []
                for cid, label in d.declared:
                    ok, why = got.get(cid, (False, "not reached yet"))
                    out.append(kit.ck(cid, label, ok, why or "not done yet"))
                return out
            if isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], bool):
                return [kit.ck("done", d.goal or d.title, r[0], r[1] or "not done yet")]
            return [kit.ck("c%d" % i, label, ok, why or "not done yet") for i, (label, ok, why) in enumerate(r)]

        meta = {"id": d.id, "track": "", "stage": d.stage, "skills": d.skills, "level": "drill", "title": d.title,
                "learn": d.learn, "readonly": d.readonly}
        if d.xp is not None:
            meta["xp"] = d.xp
        if d.minutes is not None:
            meta["minutes"] = d.minutes
        mod = types.SimpleNamespace(META=meta, values=values, fixture=fixture, brief=brief, hints=hints,
                                    hint_steps=hint_steps, collect=collect, checks=checks, drill=d)
        if d.steps_fn:
            mod.steps = steps
        return mod


# ── helpers for checks ────────────────────────────────────────

def answer(t, name):
    """A one-line answer file, stripped; None when it does not exist."""
    text = t.text(name)
    return None if text is None else text.strip()


def answer_lines(t, name):
    text = t.text(name)
    return None if text is None else [ln.strip() for ln in text.splitlines() if ln.strip()]


def missing(name):
    return "there is no %s yet" % name


def fact(data, name, arg=None):
    """A read-only fact the collector brought back, or None (it could not be read here)."""
    return (data.get("facts") or {}).get(name if arg is None else "%s:%s" % (name, arg))


def word(pick, label):
    return kit.WORDS[pick(label, len(kit.WORDS))]


def num(pick, label, lo, hi):
    return lo + pick(label, hi - lo + 1)
