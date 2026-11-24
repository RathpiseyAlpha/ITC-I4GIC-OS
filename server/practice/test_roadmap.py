#!/usr/bin/env python3
"""Tests of the Linux skill roadmap's engine (teaching/SKILL-ROADMAP-PLAN.md, build step 1): the drill format, the
catalogue, steps, the read-only facts, XP, skills and stage badges. Run in WSL or on the server's Linux (Python 3.8):

    python3 test_roadmap.py          # all
    python3 test_roadmap.py rules    # no runner

It defines its own sample drills in a temporary folder, so it holds no real drill's answer and is safe in git.
The development runner runs as your own account and uses ~/practice/zz-*.
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("OSLAB_TERM_FILE", "/nonexistent/term.conf")

import practice  # noqa: E402
import test_practice as tp  # noqa: E402  (check(), DevRunner, sh(), ws_path(), FAILS, USED)
from test_practice import check  # noqa: E402

ME = tp.ME

SAMPLE = '''
from drillkit import D, S, answer, fact

def guided(t, data, v):
    out = [("dir", t.is_dir("box"), "there is no folder box yet")]
    if t.is_dir("box"):                      # a check that is not reached is still reported, with its id
        out.append(("file", t.is_file("box/a.txt"), "there is no box/a.txt yet"))
    return out

def shapes(t, data, v):
    f = lambda n: fact(data, n)
    acc = f("account") or {}
    own = f("owner:/etc/passwd") or {}
    rows = [
        ("kernel", isinstance(f("kernel"), str) and f("kernel") != "", "kernel"),
        ("cpus", isinstance(f("cpus"), int) and f("cpus") >= 1, "cpus"),
        ("mem", isinstance(f("memtotal_kib"), int) and f("memtotal_kib") > 0, "memtotal_kib"),
        ("osrel", isinstance(f("osrelease"), dict), "osrelease"),
        ("pid1", isinstance(f("pid1"), str) and f("pid1") != "", "pid1"),
        ("ports", isinstance(f("ports"), list) and all(isinstance(p, int) for p in f("ports")), "ports"),
        ("account", acc.get("uid") == %(uid)d and acc.get("name") == %(me)r, "account"),
        ("owner", own.get("user") == "root" and isinstance(own.get("mode"), int), "owner"),
        ("mount", isinstance(f("mount:~"), str) and f("mount:~").startswith("/"), "mount"),
        ("package", f("package:/usr/bin/ls") is None or isinstance(f("package:/usr/bin/ls"), str), "package"),
        ("denied", f("owner:/root/.ssh/id_rsa") is None and "owner:/root/.ssh/id_rsa" in data["facts"], "a path off the list"),
    ]
    k = answer(t, "k.txt")
    rows.append(("answer", k is not None and k == f("kernel"), "k.txt is not the kernel release"))
    return rows

DRILLS = [
    D("zz-guided", "shell", ["mkdir", "touch"], "Guided sample", "learn",
      task="Make the folder `box` and the empty file `box/a.txt`.",
      checks=[("dir", "the folder box exists"), ("file", "box/a.txt exists")],
      steps=[S("A folder holds files.", "Make `box`.", ["dir"], hint="mkdir box"),
             S("touch makes an empty file.", "Make `box/a.txt`.", ["file"], hint="touch box/a.txt")],
      check=guided),
    D("zz-plain", "shell", ["navigate"], "Plain sample", "learn", task="Write `ok` in ok.txt.",
      check=lambda t, data, v: (answer(t, "ok.txt") == "ok", "ok.txt does not say ok"), goal="ok.txt says ok"),
    D("zz-facts", "insight", ["os-info", "env"], "Facts sample", "learn", task="Write the kernel release in k.txt.",
      readonly=True,
      facts=["kernel", "cpus", "memtotal_kib", "osrelease", "pid1", "ports", "account", "owner:/etc/passwd", "mount:~",
             "package:/usr/bin/ls", "owner:/root/.ssh/id_rsa"],
      checks=[(c, c) for c in ("kernel", "cpus", "mem", "osrel", "pid1", "ports", "account", "owner", "mount",
                                "package", "denied", "answer")],
      check=shapes),
]
''' % {"uid": os.getuid(), "me": ME}

BAD = {
    "dupe.py": ('from drillkit import D\nDRILLS = [D("paths-easy", "shell", ["navigate"], "t", "l", task="x",\n'
                '  check=lambda t, d, v: (True, ""))]\n'),
    "wrongstage.py": ('from drillkit import D\nDRILLS = [D("zz-ws", "shell", ["ports"], "t", "l", task="x",\n'
                      '  check=lambda t, d, v: (True, ""))]\n'),
    "nocheck.py": ('from drillkit import D, S\nDRILLS = [D("zz-nc", "shell", ["navigate"], "t", "l", task="x",\n'
                   '  steps=[S("a", "b", ["x"])], check=lambda t, d, v: (True, ""))]\n'),
    "badstep.py": ('from drillkit import D, S\nDRILLS = [D("zz-bs", "shell", ["navigate"], "t", "l", task="x",\n'
                   '  checks=[("a", "A")], steps=[S("l", "t", ["nope"])], check=lambda t, d, v: [("a", True, "")])]\n'),
    "orphan.py": ('from drillkit import D, S\nDRILLS = [D("zz-or", "shell", ["navigate"], "t", "l", task="x",\n'
                  '  checks=[("a", "A"), ("b", "B")], steps=[S("l", "t", ["a"])],\n'
                  '  check=lambda t, d, v: [("a", True, ""), ("b", True, "")])]\n'),
    "noskill.py": ('from drillkit import D\nDRILLS = [D("zz-nk", "shell", [], "t", "l", task="x",\n'
                   '  check=lambda t, d, v: (True, ""))]\n'),
    "badid.py": ('from drillkit import D\nDRILLS = [D("Bad Id", "shell", ["navigate"], "t", "l", task="x",\n'
                 '  check=lambda t, d, v: (True, ""))]\n'),
    "undeclared.py": ('from drillkit import D\nDRILLS = [D("zz-ud", "shell", ["navigate"], "t", "l", task="x",\n'
                      '  checks=[("a", "A")], check=lambda t, d, v: [("zzz", True, "")])]\n'),
    "good.py": ('from drillkit import D\nDRILLS = [D("zz-good", "shell", ["navigate"], "t", "l", task="x",\n'
                '  check=lambda t, d, v: (True, ""))]\n'),
}


def test_rules():
    print("roadmap rules", flush=True)
    rows = {s["id"]: sum(1 for x in practice.SKILLS.values() if x["stage"] == s["id"]) for s in practice.STAGES}
    check(len(practice.SKILLS) == 57 and list(rows.values()) == [12, 12, 8, 8, 10, 7],
          "57 skills in 6 stages: 12, 12, 8, 8, 10, 7 (%s)" % list(rows.values()))
    check(all(x["stage"] in practice.STAGE_IDS for x in practice.SKILLS.values()), "every skill belongs to a stage")
    check(practice.LEVELS == ("easy", "medium", "hard", "super") and set(practice.LEVEL_NAME) == set(practice.LEVELS)
          and "" not in practice.TRACK_IDS, "the scenarios' LEVELS, LEVEL_NAME and TRACK_IDS did not change")
    f = practice.first_clear_xp
    check([f(15, "drill", h, False, False) for h in (0, 1, 2)] == [16, 14, 10],
          "a drill: 16 with no hints (15 + 10%), 14 with 1 hint, 10 with 2")
    check(f(15, "drill", 0, True, False) == 8, "a drill cleared after its countdown: half")
    check([f(10, "quiz", h, False, False) for h in (0, 1)] == [10, 9] and f(10, "quiz", 0, True, False) == 5,
          "a quiz: 10, 9 with its hint (no bonus for no hints), half when late")

    meta = {"d1": {"level": "drill", "xp": 15, "track": "", "stage": "shell", "skills": ["mkdir"]},
            "d2": {"level": "drill", "xp": 15, "track": "", "stage": "shell", "skills": ["touch"]},
            "q1": {"level": "quiz", "xp": 10, "track": "", "stage": "shell", "skills": ["mkdir", "touch", "copy"]},
            "s1": {"level": "easy", "xp": 50, "track": "paths", "skills": ["quoting", "copy"]},
            "s2": {"level": "easy", "xp": 50, "track": "links"}}
    t0 = time.time() - 600
    led = [{"ts": t0, "user": "u", "kind": "clear", "sid": "q1", "hints": 0},
           {"ts": t0 + 1, "user": "u", "kind": "clear", "sid": "d1", "hints": 0},
           {"ts": t0 + 2, "user": "u", "kind": "clear", "sid": "d1", "attempt": 2},
           {"ts": t0 + 3, "user": "u", "kind": "clear", "sid": "q1", "attempt": 2},
           {"ts": t0 + 4, "user": "u", "kind": "clear", "sid": "s1", "hints": 1},
           {"ts": t0 + 5, "user": "u", "kind": "clear", "sid": "s1", "attempt": 2}]
    st = practice.standings(led, meta)["u"]
    check(st["xp"] == 10 + 16 + 0 + 0 + 45 + 5, "XP: quiz 10, drill 16, no XP for the drill or quiz again, scenario 45, its remix 5 (%d)" % st["xp"])
    check(st["skills"] == {"mkdir", "quoting", "copy"}, "skills come from drills and scenarios, never from a quiz (%s)" % sorted(st["skills"]))
    check(practice.skills_summary(st) == {"have": 3, "total": 57, "ids": ["copy", "mkdir", "quoting"]}, "the count is 'of 57', from SKILLS")
    quiz_only = practice.standings([{"ts": t0, "user": "q", "kind": "clear", "sid": "q1", "hints": 0}], meta)["q"]
    check(not quiz_only["skills"] and quiz_only["xp"] == 10, "a quiz clear alone adds no skill")

    names = {b["id"]: b["earned"] for b in practice.badges_of(st, meta)}
    check("stage-shell" in names and not names["stage-shell"] and "stage-text" not in names and "journeyman" in names
          and not names["journeyman"], "a stage badge exists only for a stage that has exercises; no Journeyman yet")
    done = practice.standings([{"ts": t0 + i, "user": "w", "kind": "clear", "sid": s, "hints": 0}
                               for i, s in enumerate(("d1", "d2", "q1"))], meta)["w"]
    names = {b["id"]: b["earned"] for b in practice.badges_of(done, meta)}
    check(names["stage-shell"] and not names["journeyman"],
          "the stage badge needs every drill and quiz of the stage; Journeyman waits for the other five stages")
    full, led3 = {}, []
    for i, s in enumerate(practice.STAGES):
        full["x-" + s["id"]] = {"level": "drill", "xp": 15, "track": "", "stage": s["id"], "skills": []}
        led3.append({"ts": t0 + i, "user": "j", "kind": "clear", "sid": "x-" + s["id"], "hints": 0})
    names = {b["id"]: b["earned"] for b in practice.badges_of(practice.standings(led3, full)["j"], full)}
    check(names["journeyman"] and all(names["stage-" + s] for s in practice.STAGE_IDS), "all six stage badges earn the Linux Journeyman")
    check(not any(b["id"].startswith(("stage-", "journeyman")) for b in practice.badges_of(st, {"s1": meta["s1"]})),
          "no stage badge and no Journeyman while no stage has an exercise")
    ex = {b["id"]: b["earned"] for b in practice.badges_of(practice.standings(
        [{"ts": t0, "user": "e", "kind": "clear", "sid": "d1", "hints": 0}], meta)["e"], meta)}
    check(not ex["explorer"], "drills do not count as a track for Explorer")
    ex2 = {b["id"]: b["earned"] for b in practice.badges_of(practice.standings(
        [{"ts": t0, "user": "e", "kind": s, "sid": s2, "hints": 0} for s, s2 in (("clear", "s1"), ("clear", "s2"))], meta)["e"], meta)}
    check(ex2["explorer"], "Explorer: one scenario in every track, whatever drills are loaded")

    steps = [{"learn": "a", "task": "t", "checks": ["x"]}, {"learn": "b", "task": "u", "checks": ["y", "z"]}]
    p = practice.step_progress(steps, [{"id": "x", "ok": False}, {"id": "y", "ok": True}])
    check(p["current"] == 0 and p["steps"][0]["state"] == "current" and p["steps"][1]["state"] == "todo", "step 1 is current until its check passes")
    p = practice.step_progress(steps, [{"id": "x", "ok": True}, {"id": "y", "ok": True}, {"id": "z", "ok": False}])
    check(p["current"] == 1 and p["steps"][0]["state"] == "done" and p["steps"][1]["state"] == "current", "step 2 needs both its checks")
    p = practice.step_progress(steps, [{"id": c, "ok": True} for c in "xyz"])
    check(p["current"] == 2 and all(r["state"] == "done" for r in p["steps"]), "all steps done")
    check(practice.step_progress(steps, [])["current"] == 0, "a check the runner did not report counts as not passed")


def test_catalogue(tmp):
    print("roadmap catalogue", flush=True)
    d = tmp / "drills"
    d.mkdir()
    (d / "sample.py").write_text(textwrap.dedent(SAMPLE))
    os.environ["ITC_PRACTICE_DRILLS"] = str(d)
    mods = practice.drills()
    check(set(mods) == {"zz-guided", "zz-plain", "zz-facts"} and not practice.catalog_errors(),
          "the drills load (%s)" % practice.catalog_errors())
    check(not any(k in practice.metas() for k in mods) and all(k in practice.all_metas() for k in mods),
          "metas() is the scenarios only (the API's map); all_metas() adds the drills")
    check(practice.exercise("zz-plain") is mods["zz-plain"] and practice.exercise("paths-easy") is not None
          and practice.exercise("nope") is None, "exercise() finds a scenario or a drill")
    m = practice.all_metas()["zz-guided"]
    check(m["level"] == "drill" and m["xp"] == 15 and m["minutes"] == 5 and m["stage"] == "shell" and m["track"] == ""
          and m["skills"] == ["mkdir", "touch"], "a drill gets 15 XP and 5 minutes from practice.py, not from the drill (%s)" % m)
    mod = mods["zz-guided"]
    v = practice.values(mod, ME, 1)
    check(practice.hints_of(mod, v) == ["mkdir box", "touch box/a.txt"], "hints come from the steps, at most 2")
    check(mod.hint_steps(v) == [0, 1], "each such hint says which step it belongs to")
    s1, s2 = practice.steps_of(mod, v, 1), practice.steps_of(mod, v, 2)
    check(len(s1) == 2 and s1[0]["learn"] and not any(s["learn"] for s in s2) and s2[0]["task"] == s1[0]["task"],
          "a first attempt has the lesson lines; a remix has the same steps without them")
    check(practice.steps_of(mods["zz-plain"], {}, 1) == [], "an unguided drill has no steps")
    check(len(practice.hints_of(mods["zz-facts"], {})) == 0, "a drill without hints has none")
    check("Read-only" in str(mods["zz-facts"].brief({})), "a read-only drill says so in its brief")
    check(mods["zz-facts"].collect({}, None)["facts"][0] == "kernel" and mods["zz-plain"].collect({}, None) == {"tree": True},
          "collect() asks for the facts a drill names, and for the tree by default")

    bad = tmp / "bad"
    bad.mkdir()
    for name, text in BAD.items():
        (bad / name).write_text(text)
    os.environ["ITC_PRACTICE_DRILLS"] = str(bad)
    got = practice.drills()
    # undeclared.py is well formed: its bug shows only when the check runs (tested below)
    check(set(got) == {"zz-good", "zz-ud"}, "only the well-formed drills of a folder with bad ones load (%s)" % sorted(got))
    for name, word in (("dupe.py", "duplicate"), ("wrongstage.py", "not a skill of stage"), ("nocheck.py", "declares its checks"),
                       ("badstep.py", "not declared"), ("orphan.py", "no step decides"), ("noskill.py", "no skill"),
                       ("badid.py", "bad id")):
        check(any(e.startswith(name) and word in e for e in practice.catalog_errors()), "%s is refused (%s)" % (name, word))
    import drillkit
    ns = {"D": drillkit.D}
    exec(BAD["undeclared.py"].replace("from drillkit import D\n", ""), ns)   # loads fine; the check is the bug
    try:
        ns["DRILLS"][0].module().checks({}, {}, None, {})
        loud = False
    except ValueError as e:
        loud = "undeclared" in str(e)
    check(loud, "a check that returns an id the drill did not declare fails loudly, not silently")
    os.environ["ITC_PRACTICE_DRILLS"] = str(d)
    check(not [e for e in practice.catalog_errors() if "sample.py" in e], "back to the sample folder: no errors")


def test_runner(tmp):
    print("roadmap runner (development runner)", flush=True)
    r = tp.DevRunner(tmp)
    try:
        ping = r.call(op="ping")
        check(ping.get("ok"), "the runner answers a ping")
        # a guided drill: the check ids are the same on a fresh workspace and on a solved one
        sid = "zz-guided"
        tp.USED.add(sid)
        mod = practice.exercise(sid)
        v = practice.values(mod, ME, 1)
        steps = practice.steps_of(mod, v, 1)
        s = r.call(op="setup", user=ME, sid=sid, attempt=1)
        check(s.get("ok"), "a drill's workspace is set up (%s)" % s.get("error", ""))
        c0 = r.call(op="check", user=ME, sid=sid, attempt=1, info=s.get("info"))
        ids0 = [x["id"] for x in c0.get("checks", [])]
        check(ids0 == ["dir", "file"] and not c0.get("ok") and all(x["why"] for x in c0["checks"]),
              "fresh: both declared checks, in order, each with a reason (%s)" % ids0)
        check(practice.step_progress(steps, c0["checks"])["current"] == 0, "fresh: the student is on step 1")
        tp.sh(sid, "mkdir box")
        c1 = r.call(op="check", user=ME, sid=sid, attempt=1, info=s.get("info"))
        check(practice.step_progress(steps, c1["checks"])["current"] == 1 and [x["id"] for x in c1["checks"]] == ids0,
              "after the first step: on step 2, the same ids")
        tp.sh(sid, "touch box/a.txt")
        c2 = r.call(op="check", user=ME, sid=sid, attempt=1, info=s.get("info"))
        check(c2.get("ok") and [x["id"] for x in c2["checks"]] == ids0 and practice.step_progress(steps, c2["checks"])["current"] == 2,
              "solved: passes, the same ids, all steps done")

        sid = "zz-plain"
        tp.USED.add(sid)
        s = r.call(op="setup", user=ME, sid=sid, attempt=1)
        c = r.call(op="check", user=ME, sid=sid, attempt=1, info=s.get("info"))
        check([x["id"] for x in c.get("checks", [])] == ["done"] and not c.get("ok"), "an unguided drill is one check, id 'done'")
        tp.sh(sid, "echo ok > ok.txt")
        check(r.call(op="check", user=ME, sid=sid, attempt=1, info=s.get("info")).get("ok"), "and passes when right")

        # the read-only facts, through the collector that runs as the student
        sid = "zz-facts"
        tp.USED.add(sid)
        s = r.call(op="setup", user=ME, sid=sid, attempt=1)
        c = r.call(op="check", user=ME, sid=sid, attempt=1, info=s.get("info"))
        got = {x["id"]: x for x in c.get("checks", [])}
        shapes = [k for k in got if k != "answer"]
        check(c.get("checks") and all(got[k]["ok"] for k in shapes),
              "every fact has the right shape (%s)" % [(k, got[k]["why"]) for k in shapes if not got[k]["ok"]])
        check(not got["answer"]["ok"], "the answer is not there yet")
        tp.sh(sid, "uname -r > k.txt")
        c = r.call(op="check", user=ME, sid=sid, attempt=1, info=s.get("info"))
        check(c.get("ok"), "the kernel release from `uname -r` matches the fact")
    finally:
        r.stop()


def test_collector(tmp):
    print("roadmap collector (direct)", flush=True)
    import collect
    f = collect.facts(["kernel", "bogus", "owner:/etc/shadow", "owner:/home/nobody/x", "mount:~", "mount:/etc/x", "package:/etc/passwd"])
    check("bogus" not in f and f.get("kernel") and f.get("owner:/home/nobody/x") is None and f.get("mount:/etc/x") is None,
          "an unknown fact is skipped; a path off the list gives nothing")
    own = f.get("owner:/etc/shadow") or {}
    check(own.get("user") == "root" and isinstance(own.get("mode"), int) and own.get("setuid") is False, "owner: user, mode, setuid flag")
    check(f.get("package:/etc/passwd") in (None, "base-passwd"), "package of a file that is on the list (%s)" % f.get("package:/etc/passwd"))
    if shutil.which("dpkg-query"):   # /usr/bin/ls is /bin/ls to dpkg on a system where /bin and /usr/bin are not merged
        check(collect.fact_package("/usr/bin/ls") == "coreutils" and collect.fact_package("/usr/bin/tar") == "tar",
              "the owning package of /usr/bin/ls and /usr/bin/tar (dpkg-query, both path forms tried)")
    ls_owner = collect.fact_owner("/usr/bin/passwd") or {}
    check(ls_owner == {} or ls_owner.get("setuid") in (True, False), "the setuid flag is a boolean")

    w = tmp / "ws"
    w.mkdir()
    (w / "docs").mkdir()
    (w / "docs" / "a.txt").write_text("a")
    with tarfile.open(str(w / "b.tar.gz"), "w:gz") as tf:
        tf.add(str(w / "docs"), arcname="docs")
    (w / "plain.tar.gz").write_text("not an archive")
    (w / "link.tar.gz").symlink_to(w / "b.tar.gz")
    t = collect.tar_listing("b.tar.gz", w)
    check(t["ok"] and t["gzip"] and sorted(t["names"]) == ["docs", "docs/a.txt"], "a .tar.gz is listed by name (%s)" % t)
    check(not (w / "docs" / "docs").exists() and sorted(p.name for p in w.iterdir()) == ["b.tar.gz", "docs", "link.tar.gz", "plain.tar.gz"],
          "listing extracts nothing")
    check(not collect.tar_listing("plain.tar.gz", w)["ok"], "a file that is not gzip is not listed")
    check(not collect.tar_listing("link.tar.gz", w)["ok"], "a symbolic link is not followed")
    check(not collect.tar_listing("none.tar.gz", w)["ok"], "a missing archive is reported")

    class Zeros:
        def __init__(self, n):
            self.left = n

        def read(self, n=-1):
            n = self.left if n is None or n < 0 else min(n, self.left)
            self.left -= n
            return b"\0" * n

    with gzip.open(str(w / "bomb.tar.gz"), "wb") as g:
        with tarfile.open(fileobj=g, mode="w|") as tf:
            ti = tarfile.TarInfo("big")
            ti.size = collect.MAX_TAR_BYTES + 50_000_000
            tf.addfile(ti, Zeros(ti.size))
    t0 = time.time()
    t = collect.tar_listing("bomb.tar.gz", w)
    check(not t["ok"] and t.get("error") and time.time() - t0 < 20, "a gzip bomb stops at the byte limit (%s, %.1fs)" % (t.get("error"), time.time() - t0))

    nice = subprocess.Popen(["nice", "-n", "10", "sleep", "60"])
    ign = subprocess.Popen(["bash", "-c", "trap '' TERM; sleep 60 & wait"])
    time.sleep(0.6)
    try:
        procs = {p["pid"]: p for p in collect.procs()}
        check(procs.get(nice.pid, {}).get("nice") == 10, "a process reports its niceness (%s)" % procs.get(nice.pid, {}).get("nice"))
        sig = procs.get(ign.pid, {}).get("sigign")
        check(sig is not None and (sig >> 14) & 1 == 1, "a process reports the signals it ignores (TERM is bit 14)")
        check(((procs.get(nice.pid, {}).get("sigign") or 0) >> 14) & 1 == 0, "and one that does not ignore TERM does not")
    finally:
        for p in (nice, ign):
            p.kill()
        subprocess.run(["pkill", "-f", "^sleep 60"], capture_output=True)


def test_sources():
    print("roadmap install", flush=True)
    src = (HERE.parent / "examroom" / "examctl.py").read_text()
    check("drillkit.py" in src and '"drills"' in src, "examctl install copies drillkit.py and drills/")
    check(not (HERE / "drills").exists() or all(p.name.startswith("_") or p.suffix == ".py" for p in (HERE / "drills").iterdir() if p.is_file()),
          "drills/ holds only .py files")
    run_src = (HERE / "runner.py").read_text()
    check('"runuser", "-u"' not in run_src and "[RUNUSER, " in run_src and '"/usr/sbin:/sbin' in run_src,
          "the runner starts the collector with runuser by its full path (it lives in /usr/sbin, outside the clean PATH)")
    sys.path.insert(0, str(HERE))
    import runner
    check(os.path.isabs(runner.RUNUSER) and ("/sbin/" in runner.RUNUSER or not os.path.exists("/usr/sbin/runuser")),
          "RUNUSER is an absolute path (%s)" % runner.RUNUSER)


def main():
    which = set(sys.argv[1:]) or {"rules", "catalogue", "runner", "collector"}
    tmp = Path(tempfile.mkdtemp(prefix="roadmap-test-"))
    os.environ["ITC_EXAM_ETC"] = str(tmp / "etc")
    (tmp / "etc").mkdir()
    try:
        if "rules" in which:
            test_rules()
        if which & {"catalogue", "runner"}:
            test_catalogue(tmp)
        if "runner" in which:
            test_runner(tmp)
        if "collector" in which:
            test_collector(tmp)
            test_sources()
    finally:
        for sid in tp.USED:
            shutil.rmtree(tp.ws_path(sid), ignore_errors=True)
        try:
            (tp.HOME / "practice").rmdir()
        except OSError:
            pass
        shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d failed" % len(tp.FAILS) if tp.FAILS else "\nall passed")
    for f in tp.FAILS:
        print("  - " + f)
    sys.exit(1 if tp.FAILS else 0)


if __name__ == "__main__":
    main()
