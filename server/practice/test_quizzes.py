#!/usr/bin/env python3
"""Tests of the quiz engine (teaching/SKILL-ROADMAP-PLAN.md, build step 2): format, loading, drawing, shuffling, the
hint, grading, the attempt's state (countdown, one hint, the wait after a fail), the ledger line and XP. No runner:

    python3 test_quizzes.py

It defines its own sample quizzes in a temporary folder, so it holds no real question's key. Like test_roadmap.py it
borrows check() and the failure list from test_practice.py (which is git-ignored, so run both from a full copy).
"""
import json
import os
import shutil
import sys
import tempfile
import textwrap
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("OSLAB_TERM_FILE", "/nonexistent/term.conf")

import practice  # noqa: E402
import quizzes  # noqa: E402
import test_practice as tp  # noqa: E402
from test_practice import check  # noqa: E402

SAMPLE = '''
import kit
from quizzes import Quiz, Q

def private_file(pick):
    w = kit.WORDS[pick("w", len(kit.WORDS))]
    return {"q": "Which mode lets only the owner read and write %s.txt?" % w, "right": "600",
            "wrong": ["644", "666", "700", "400"]}

QUIZZES = [
    Quiz("zz-modes", "perms", "Modes sample", "learn", n=5, questions=[
        Q("q-octal", "chmod-octal", [private_file,
                                     {"q": "What does 640 give the group?", "right": "read", "wrong": ["write", "nothing", "run"]}]),
        Q("q-umask", "umask", [{"q": "With umask 077 a new file is", "right": "600", "wrong": ["644", "666", "700"]},
                               {"q": "With umask 027 a new folder is", "right": "750", "wrong": ["755", "777", "700"]}]),
        Q("q-id", "identity", [{"q": "Which command prints your numeric user id?", "right": "id -u", "wrong": ["whoami", "uname -n", "pwd"]}]),
        Q("q-owner", "ownership", [{"q": "Which command changes the owner of a file?", "right": "chown", "wrong": ["chmod", "chgrp", "umask"]}]),
        Q("q-bits", "special-bits", [{"q": "A setuid program runs with the rights of", "right": "its owner", "wrong": ["the caller", "root always", "its group only"]}]),
        Q("q-shared", "shared-dir", [{"q": "Mode 2770 on a folder means new files get", "right": "the folder's group", "wrong": ["the user's group", "root's group", "no group"]}]),
    ]),
    Quiz("zz-small", "perms", "Small sample", "learn", questions=[
        Q("a", "chmod-octal", [{"q": "A?", "right": "yes", "wrong": ["no", "maybe", "never"]}]),
        Q("b", "chmod-symbolic", [{"q": "B?", "right": "yes", "wrong": ["no", "maybe", "never"]}]),
    ]),
]
'''

BAD = {
    "dupe.py": 'from quizzes import Quiz, Q\nQUIZZES = [Quiz("paths-easy", "perms", "t", "l", [Q("a", "umask", [{"q": "q", "right": "r", "wrong": ["a", "b", "c"]}])])]\n',
    "stage.py": 'from quizzes import Quiz, Q\nQUIZZES = [Quiz("zz-st", "perms", "t", "l", [Q("a", "ports", [{"q": "q", "right": "r", "wrong": ["a", "b", "c"]}])])]\n',
    "fewwrong.py": 'from quizzes import Quiz, Q\nQUIZZES = [Quiz("zz-fw", "perms", "t", "l", [Q("a", "umask", [{"q": "q", "right": "r", "wrong": ["a", "b"]}])])]\n',
    "rightinwrong.py": 'from quizzes import Quiz, Q\nQUIZZES = [Quiz("zz-rw", "perms", "t", "l", [Q("a", "umask", [{"q": "q", "right": "r", "wrong": ["a", "b", "r"]}])])]\n',
    "samewrong.py": 'from quizzes import Quiz, Q\nQUIZZES = [Quiz("zz-sw", "perms", "t", "l", [Q("a", "umask", [{"q": "q", "right": "r", "wrong": ["a", "a", "b"]}])])]\n',
    "toomany.py": 'from quizzes import Quiz, Q\nQUIZZES = [Quiz("zz-tm", "perms", "t", "l", [Q("a", "umask", [{"q": "q", "right": "r", "wrong": ["a", "b", "c"]}])], n=3)]\n',
    "novariants.py": 'from quizzes import Quiz, Q\nQUIZZES = [Quiz("zz-nv", "perms", "t", "l", [Q("a", "umask", [])])]\n',
    "dupq.py": 'from quizzes import Quiz, Q\nv = [{"q": "q", "right": "r", "wrong": ["a", "b", "c"]}]\nQUIZZES = [Quiz("zz-dq", "perms", "t", "l", [Q("a", "umask", v), Q("a", "identity", v)])]\n',
    "badcall.py": 'from quizzes import Quiz, Q\ndef f(pick):\n    return {"q": "q", "right": "r", "wrong": ["a", "b", "c"][: 1 + pick("n", 3) - 1]}\nQUIZZES = [Quiz("zz-bc", "perms", "t", "l", [Q("a", "umask", [f])])]\n',
    "noquestions.py": 'from quizzes import Quiz\nQUIZZES = [Quiz("zz-nq", "perms", "t", "l", [])]\n',
    "good.py": 'from quizzes import Quiz, Q\nQUIZZES = [Quiz("zz-good", "perms", "t", "l", [Q("a", "umask", [{"q": "q", "right": "r", "wrong": ["a", "b", "c"]}])])]\n',
}

ME = tp.ME


def all_right(d):
    return {x["qid"]: x["right"] for x in d}


def answers_with(d, n_right):
    """The key for n_right questions, a wrong choice for the rest."""
    out = {}
    for i, x in enumerate(d):
        out[x["qid"]] = x["right"] if i < n_right else next(c["id"] for c in x["choices"] if c["id"] != x["right"])
    return out


def test_catalogue(tmp):
    print("quizzes: catalogue", flush=True)
    good = tmp / "quizzes"
    good.mkdir()
    (good / "sample.py").write_text(textwrap.dedent(SAMPLE))
    os.environ["ITC_PRACTICE_QUIZZES"] = str(good)
    cat = quizzes.catalog()
    check(set(cat) == {"zz-modes", "zz-small"} and not quizzes.errors(), "the sample quizzes load (%s)" % quizzes.errors())
    m = quizzes.metas()["zz-modes"]
    check(m["level"] == "quiz" and m["xp"] == 10 and m["minutes"] == 5 and m["track"] == "" and m["stage"] == "perms"
          and m["skills"] == sorted(["chmod-octal", "umask", "identity", "ownership", "special-bits", "shared-dir"]),
          "a quiz is 10 XP and 5 minutes, level quiz, with the skills of its questions (%s)" % m)
    check("zz-modes" in practice.all_metas() and "zz-modes" not in practice.metas() and practice.exercise("zz-modes") is None,
          "all_metas() has the quiz; metas() and exercise() (the scenarios' map and workspaces) do not")
    check(not [e for e in practice.catalog_errors() if "sample" in e], "practice.catalog_errors() reads the quiz folder too")

    bad = tmp / "badquizzes"
    bad.mkdir()
    for name, text in BAD.items():
        (bad / name).write_text(text)
    os.environ["ITC_PRACTICE_QUIZZES"] = str(bad)
    got = quizzes.catalog()
    errs = quizzes.errors()
    check(set(got) == {"zz-good"}, "only the good quiz of a folder with bad ones loads (%s)" % sorted(got))
    for name, word in (("dupe.py", "duplicate id"), ("stage.py", "not a skill of stage"), ("fewwrong.py", "wrong choices"),
                       ("rightinwrong.py", "all be different"), ("samewrong.py", "all be different"),
                       ("toomany.py", "questions"), ("novariants.py", "no variants"), ("dupq.py", "duplicate question"),
                       ("badcall.py", "wrong choices"), ("noquestions.py", "no questions")):
        check(any(e.startswith(name) and word in e for e in errs), "%s is refused (%s)" % (name, word))
    os.environ["ITC_PRACTICE_QUIZZES"] = str(good)


def test_draw():
    print("quizzes: draw, shuffle, hint, grade", flush=True)
    q = quizzes.catalog()["zz-modes"]
    d1, d1b = quizzes.draw(q, ME, 1), quizzes.draw(q, ME, 1)
    check(d1 == d1b and len(d1) == 5 and len({x["qid"] for x in d1}) == 5, "the same (student, attempt) draws the same 5 distinct questions")
    check(all(len(x["choices"]) == 4 and len({c["text"] for c in x["choices"]}) == 4 and [c["id"] for c in x["choices"]] == list("abcd")
              for x in d1), "every question has four different choices, a to d")
    check(all(sum(1 for c in x["choices"] if c["id"] == x["right"]) == 1 for x in d1), "exactly one right choice")
    drawn = {json.dumps(quizzes.public(quizzes.draw(q, ME, a)), sort_keys=True) for a in range(1, 9)}
    check(len(drawn) >= 7, "a new attempt draws other variants and shuffles again (%d different of 8)" % len(drawn))
    other = json.dumps(quizzes.public(quizzes.draw(q, "someone-else", 1)), sort_keys=True)
    check(other != json.dumps(quizzes.public(d1), sort_keys=True), "another student's draw differs")
    texts = {quizzes.draw(q, u, 1)[i]["text"] for u in ("s%d" % k for k in range(30)) for i in range(5) if "Which mode lets" in quizzes.draw(q, u, 1)[i]["text"]}
    check(len(texts) >= 5, "a question that uses personal values asks with different values for different students (%d)" % len(texts))
    pos = Counter(x["right"] for a in range(1, 401) for x in quizzes.draw(q, ME, a))
    check(len(pos) == 4 and min(pos.values()) > 0.15 * sum(pos.values()), "the right choice sits on a, b, c and d about equally (%s)" % dict(sorted(pos.items())))
    pub = quizzes.public(d1)
    check(all(set(x) == {"n", "qid", "text", "choices"} and all(set(c) == {"id", "text"} for c in x["choices"]) for x in pub),
          "the public draw has only the question and its choices: no key, no skill")
    check('"right"' not in json.dumps(pub) and "skill" not in json.dumps(pub), "no key or skill anywhere in the page's JSON")

    removed = quizzes.hint(d1, 2, ME, "zz-modes", 1)
    x = d1[2]
    left = [c["id"] for c in x["choices"] if c["id"] not in removed]
    check(len(removed) == 2 and x["right"] not in removed and len(left) == 2 and x["right"] in left, "a hint takes away two wrong choices, never the right one")
    check(removed == quizzes.hint(d1, 2, ME, "zz-modes", 1), "the same hint every time for that attempt")

    r = quizzes.grade(d1, all_right(d1))
    check(r["score"] == 5 and r["passed"] and r["pass_mark"] == 4 and r["review"] == [], "5 of 5 passes, nothing to review")
    r = quizzes.grade(d1, answers_with(d1, 4))
    check(r["score"] == 4 and r["passed"] and len(r["review"]) == 1, "4 of 5 passes, one skill to review")
    r = quizzes.grade(d1, answers_with(d1, 3))
    check(r["score"] == 3 and not r["passed"] and len(r["review"]) == 2, "3 of 5 fails, two skills to review")
    r = quizzes.grade(d1, {})
    check(r["score"] == 0 and not r["passed"] and len(r["review"]) == 5, "no answers: 0, every skill to review")
    r = quizzes.grade(d1, {x["qid"]: "z" for x in d1})
    check(r["score"] == 0, "an unknown choice id is wrong")
    r = quizzes.grade(d1, "garbage")
    check(r["score"] == 0 and not r["passed"], "an answer set that is not a dict is wrong, not an error")
    r = quizzes.grade(d1, answers_with(d1, 3))
    check(set(r) == {"score", "total", "pass_mark", "passed", "review"} and all(set(x) == {"skill", "title"} for x in r["review"]),
          "the result holds a score and the skills to review, never a choice id or text")
    small = quizzes.draw(quizzes.catalog()["zz-small"], ME, 1)
    check(len(small) == 2 and quizzes.pass_mark(2) == 2 and quizzes.pass_mark(5) == 4 and quizzes.pass_mark(10) == 8,
          "the pass mark is 80% rounded up (2 of 2, 4 of 5, 8 of 10)")


def test_state():
    print("quizzes: attempts, hint, wait, XP", flush=True)
    q = quizzes.catalog()["zz-modes"]
    meta = quizzes.metas()["zz-modes"]
    run, t = {}, 1_000_000.0
    check(quizzes.begin(run, meta["minutes"], t) is None and run["open"] and run["attempt"] == 1 and run["deadline"] == t + 300,
          "begin: attempt 1, open, a 5-minute countdown")
    first = quizzes.draw(q, ME, run["attempt"])
    check(quizzes.begin(run, 5, t + 10) is None and run["attempt"] == 1 and run["started"] == t, "begin again (a reload): the same attempt and countdown")
    h = quizzes.use_hint(run, first, 1, ME, "zz-modes")
    check(len(h["removed"]) == 2 and run["hints"] == 1, "one hint")
    check(quizzes.use_hint(run, first, 1, ME, "zz-modes") == h and run["hints"] == 1, "asking again for the same question is free")
    check("error" in quizzes.use_hint(run, first, 3, ME, "zz-modes") and run["hints"] == 1, "a second hint on another question is refused")
    check("error" in quizzes.use_hint(run, first, 9, ME, "zz-modes"), "a hint for a question that does not exist is refused")
    res = quizzes.submit(run, first, answers_with(first, 3), t + 100)
    check(not res["passed"] and not run["open"] and run["last"] == "fail" and run["failed_at"] == t + 100, "a fail closes the attempt and starts the wait")
    check("error" not in res and res["late"] is False and res["secs"] == 100.0 and res["attempt"] == 1, "in time, not late, 100 s")
    w = quizzes.begin(run, 5, t + 110)
    check(w and w["error"] == "wait" and 19 < w["retry_s"] < 21, "ten seconds later: wait about 20 more (%s)" % w)
    check(quizzes.state(run, 5, t + 110)["retry_s"] == 20.0 and not quizzes.state(run, 5, t + 110)["open"], "state() shows the wait")
    check("error" in quizzes.submit(run, first, {}, t + 111), "submitting with no open attempt is refused")
    check(quizzes.begin(run, 5, t + 131) is None and run["attempt"] == 2 and run["hints"] == 0 and run["hint"] is None,
          "after 30 s: attempt 2, the hint is back")
    second = quizzes.draw(q, ME, 2)
    check(json.dumps(quizzes.public(second), sort_keys=True) != json.dumps(quizzes.public(first), sort_keys=True), "attempt 2 asks different questions")
    res = quizzes.submit(run, second, all_right(second), t + 131 + 90)
    check(res["passed"] and res["hints"] == 0 and not res["late"] and run["passed"] and run["last"] == "pass" and run["best"] == 5, "a pass")
    e = quizzes.clear_entry(ME, meta, res, t + 221)
    st = practice.standings([e], practice.all_metas())[ME]
    check(st["xp"] == 10 and meta["id"] in st["cleared"] and not st["skills"], "first pass: 10 XP, no skill (a quiz never adds a skill)")

    # a pass with the hint, and a late pass
    run2 = {}
    quizzes.begin(run2, 5, t)
    d = quizzes.draw(q, ME, 1)
    quizzes.use_hint(run2, d, 0, ME, "zz-modes")
    res2 = quizzes.submit(run2, d, all_right(d), t + 60)
    st = practice.standings([quizzes.clear_entry(ME, meta, res2, t + 60)], practice.all_metas())[ME]
    check(res2["hints"] == 1 and st["xp"] == 9, "a pass with the hint: 9 XP")
    run3 = {}
    quizzes.begin(run3, 5, t)
    d = quizzes.draw(q, ME, 1)
    res3 = quizzes.submit(run3, d, all_right(d), t + 301)
    st = practice.standings([quizzes.clear_entry(ME, meta, res3, t + 301)], practice.all_metas())[ME]
    check(res3["late"] and st["xp"] == 5, "a pass after the countdown: half (5 XP)")

    # revising after a pass: no wait, no more XP
    r = run
    check(quizzes.begin(r, 5, t + 300) is None and r["attempt"] == 3, "after a pass the student may play again at once (to revise)")
    d3 = quizzes.draw(q, ME, 3)
    res4 = quizzes.submit(r, d3, all_right(d3), t + 320)
    st = practice.standings([e, quizzes.clear_entry(ME, meta, res4, t + 320)], practice.all_metas())[ME]
    check(res4["passed"] and st["xp"] == 10 and st["remix"].get("zz-modes") == 1, "the second pass earns no XP (10 in all)")
    r["last"] = "pass"
    quizzes.begin(r, 5, t + 330)
    quizzes.submit(r, d3, answers_with(d3, 0), t + 340)
    check(quizzes.begin(r, 5, t + 341)["error"] == "wait", "failing a revision attempt starts the wait too")

    # the stage badge: every drill and quiz of the stage
    metas = {"zz-modes": meta, "dr": {"level": "drill", "xp": 15, "track": "", "stage": "perms", "skills": ["umask"]}}
    only_quiz = practice.standings([e], metas)[ME]
    names = {b["id"]: b["earned"] for b in practice.badges_of(only_quiz, metas)}
    both = practice.standings([e, {"ts": t, "user": ME, "kind": "clear", "sid": "dr", "hints": 0}], metas)[ME]
    names2 = {b["id"]: b["earned"] for b in practice.badges_of(both, metas)}
    check(names["stage-perms"] is False and names2["stage-perms"] is True and names2["journeyman"] is False,
          "the stage badge needs the drill and the quiz; Journeyman still needs the other five stages")


def test_install():
    print("quizzes: install", flush=True)
    src = (HERE.parent / "examroom" / "examctl.py").read_text()
    check('"quizzes"' in src and "private" in src.split('qsrc = ')[1].split("\n")[0], "examctl install copies private/quizzes/*.py")
    check("0o640" in src.split("quiz_files = ")[1].split("quiz_files)")[0], "keys are installed 0640, root:itc-exam, in a 0750 folder")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="quiz-test-"))
    os.environ["ITC_EXAM_ETC"] = str(tmp / "etc")
    (tmp / "etc").mkdir()
    try:
        test_catalogue(tmp)
        test_draw()
        test_state()
        test_install()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d failed" % len(tp.FAILS) if tp.FAILS else "\nall passed")
    for f in tp.FAILS:
        print("  - " + f)
    sys.exit(1 if tp.FAILS else 0)


if __name__ == "__main__":
    main()
