"""Files and processes, Medium: Who is running? (Lab 1)."""
import os

import kit

META = {"id": "processes-medium", "track": "processes", "level": "medium", "title": "Who is running?",
        "learn": "Background jobs, PID and PPID, ps and kill."}
META["skills"] = ['jobs', 'ps', 'signals']   # the roadmap's skills this scenario trains (a clear acquires them)


def values(pick):
    n = 3 + pick("n", 3)
    base = 7100 + 10 * pick("base", 80)
    secs = [base + 11 * i + 1 for i in range(n)]
    return {"secs": secs, "stop": secs[pick("stop", n)]}


def fixture(v):
    return {"files": {"sleeps.txt": "\n".join(str(s) for s in v["secs"]) + "\n"}}


def brief(v):
    return [
        {"p": "Every number in `sleeps.txt` is a job: a `sleep` of that many seconds."},
        {"ol": ["Start one `sleep` in the background for each number in `sleeps.txt`, for example `sleep %d &`." % v["secs"][0],
                "Stop the one that sleeps **%d** seconds." % v["stop"],
                "Write in `running.txt` one line for each of your sleeps that is still running: its PID, a space, "
                "and the PID of its parent (PPID).",
                "Leave the others running until the check passes."]},
    ]


def hints(v):
    return [
        "`sleep %d &` starts one and gives you the prompt back. `jobs -l` lists your jobs with their PIDs." % v["secs"][0],
        "`kill PID` stops one process. `ps -o pid,ppid,args` shows the PID and the parent's PID of your processes.",
        "`ps -o pid=,ppid=,args= -C sleep` lists every sleep; keep only yours with `grep`, and only the first two "
        "columns with `awk '{print $1, $2}'`, into `running.txt`.",
    ]


def collect(v, hidden):
    return {"tree": True, "procs": True, "texts": ["running.txt"]}


def sleeps_of(procs, secs):
    return [p for p in procs if len(p.get("args") or []) == 2 and os.path.basename(p["args"][0]) == "sleep"
            and p["args"][1] == str(secs) and p.get("state") != "Z"]


def checks(data, v, hidden, info):
    procs = data.get("procs") or []
    keep = [s for s in v["secs"] if s != v["stop"]]
    gone = [s for s in keep if not sleeps_of(procs, s)]
    extra = [s for s in keep if len(sleeps_of(procs, s)) > 1]
    why = ("not running: %s" % ", ".join("sleep %d" % s for s in gone)) if gone else \
        ("running more than once: %s; stop the extra copies" % ", ".join("sleep %d" % s for s in extra))
    out = [kit.ck("running", "each sleep you keep runs exactly once", not gone and not extra, why)]
    out.append(kit.ck("stopped", "the sleep of %d seconds is stopped" % v["stop"], not sleeps_of(procs, v["stop"]),
                      "sleep %d is still running" % v["stop"]))
    want = {(p["pid"], p["ppid"]) for s in keep for p in sleeps_of(procs, s)}
    text = kit.Tree.of(data).text("running.txt")
    got, bad = set(), []
    for ln in kit.lines(text):
        parts = ln.split()
        try:
            got.add((int(parts[0]), int(parts[1])))
        except (ValueError, IndexError):
            bad.append(ln)
    if text is None:
        why = "there is no running.txt yet"
    elif bad:
        why = "this line is not two numbers: %r" % bad[0][:40]
    elif {p for p, _ in got} - {p for p, _ in want}:
        why = "PID %d in running.txt is not one of the sleeps you keep" % sorted({p for p, _ in got} - {p for p, _ in want})[0]
    elif got - want:
        pid = sorted(got - want)[0][0]
        why = "the PPID written for PID %d is not its parent" % pid
    else:
        why = "running.txt has %d line(s), but %d of your sleeps run" % (len(got), len(want))
    out.append(kit.ck("listed", "running.txt lists the PID and PPID of each running sleep", text is not None and not bad and got == want and want, why))
    return out


def steps(v, remix=False):
    return kit.guided([
        ("`sleep N &` starts one in the background. `jobs -l` or `ps` shows their PIDs, and `kill PID` stops one.",
         "Start one `sleep` in the background for each number in `sleeps.txt`, then stop the one that sleeps **%d** seconds." % v["stop"],
         ["running", "stopped"]),
        ("`ps -o pid,ppid,args` shows the PID of each process and the PID of its parent (PPID).",
         "Write one line in `running.txt` for each of your sleeps that is still running: its PID, a space, and its PPID.", ["listed"]),
    ], remix)
