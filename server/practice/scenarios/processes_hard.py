"""Files and processes, Hard: Runaway job (Lab 1, Weeks 2 to 3)."""
import kit

META = {"id": "processes-hard", "track": "processes", "level": "hard", "title": "Runaway job",
        "learn": "Read a process tree; a parent that restarts its child must be stopped first."}
META["skills"] = ['ps', 'signals', 'pstree']   # the roadmap's skills this scenario trains (a clear acquires them)


def values(pick):
    w = kit.WORDS[pick("w", len(kit.WORDS))]
    return {"word": w, "parent": "nightly-%s.sh" % w, "writer": "%s-writer.sh" % w}


def fixture(v):
    start = ('#!/usr/bin/env bash\n# Starts the night shift in the background, away from this terminal.\n'
             'cd "$(dirname "$0")"\nsetsid nohup bash bin/%s >/dev/null 2>&1 < /dev/null &\necho "night shift started"\n'
             % v["parent"])
    parent = ('#!/usr/bin/env bash\n# keeps the writer running: when it stops, start it again\ncd "$(dirname "$0")/.."\n'
              'while true; do\n    bash bin/%s\n    sleep 1\ndone\n' % v["writer"])
    writer = ('#!/usr/bin/env bash\ncd "$(dirname "$0")/.."\nmkdir -p status\n'
              'while true; do date +%%s.%%N > status/heartbeat.txt; sleep 1; done\n')
    return {"files": {"start-night-shift": {"t": start, "m": 0o750}, "bin/" + v["parent"]: {"t": parent, "m": 0o750},
                      "bin/" + v["writer"]: {"t": writer, "m": 0o750}}}


def brief(v):
    return [
        {"p": "The night shift is a job that writes `status/heartbeat.txt` every second. It should stop in the "
              "morning, but it never does."},
        {"ol": ["Start it: `./start-night-shift`. Once is enough; it keeps running when you close the terminal.",
                "Find the process that writes the file, and the process that starts it again when it stops.",
                "Stop the job for good: nothing of it may still run, and `status/heartbeat.txt` must stop changing.",
                "Write in `found.txt` two lines: the name of the script that restarts the writer, then the name of "
                "the writer script. Only the file names."]},
    ]


def hints(v):
    return [
        "`ps -ef --forest`, or `ps -o pid,ppid,args -u $USER --forest`, shows which process started which.",
        "If you stop only the writer, the script above it starts a new writer a second later. Stop that one first.",
        "`pkill -f %s`, then `pkill -f %s`; after that `ps -ef | grep %s` shows nothing of it." % (v["parent"], v["writer"], v["word"]),
    ]


def collect(v, hidden):
    return {"tree": True, "procs": True, "texts": ["found.txt"],
            "again": {"after": 2.5, "paths": ["status/heartbeat.txt"]}}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    hb = t.get("status/heartbeat.txt")
    out = [kit.ck("started", "the night shift was started", hb is not None,
                  "status/heartbeat.txt does not exist yet: start the job with ./start-night-shift")]
    again = data.get("again") or {}
    procs = (data.get("procs") or []) + (again.get("procs") or [])
    left = [p for p in procs if p.get("state") != "Z" and
            (kit.procs_matching([p], v["parent"]) or kit.procs_matching([p], v["writer"]))]
    names = sorted({v["parent"] if kit.procs_matching([p], v["parent"]) else v["writer"] for p in left})
    out.append(kit.ck("stopped", "nothing of the job is still running", hb is not None and not left,
                      ("still running: %s" % " and ".join(names)) if left else "start the job first"))
    later = (again.get("stat") or {}).get("status/heartbeat.txt")
    quiet = hb is not None and later is not None and abs(later[0] - hb["mt"]) < 0.001
    out.append(kit.ck("quiet", "status/heartbeat.txt stopped changing", quiet,
                      "status/heartbeat.txt changed during the check: something still writes it" if hb else "start the job first"))
    got = [ln.strip().rsplit("/", 1)[-1] for ln in kit.lines(t.text("found.txt"))]
    out.append(kit.ck("found", "found.txt names the restarting script, then the writer", got == [v["parent"], v["writer"]],
                      "there is no found.txt" if t.text("found.txt") is None else
                      ("found.txt should have 2 lines" if len(got) != 2 else "those are not the two scripts, in that order")))
    return out
