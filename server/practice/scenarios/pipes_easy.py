"""Redirection and pipelines, Easy: Two streams (Lab 4)."""
import kit

META = {"id": "pipes-easy", "track": "pipes", "level": "easy", "title": "Two streams",
        "learn": "A program writes results to standard output and errors to standard error; > and 2> split them."}
META["skills"] = ['redirect', 'stderr']   # the roadmap's skills this scenario trains (a clear acquires them)


def values(pick):
    w = kit.distinct(pick, "w", kit.WORDS, 4)
    return {"words": w, "n": 10 + pick("n", 80)}


def streams(v):
    w, n = v["words"], v["n"]
    out = ["checked %s: ok" % w[0], "checked %s: %d files" % (w[1], n), "checked %s: ok" % w[3]]
    err = ["inspect: %s: permission denied" % w[2], "inspect: 1 problem found"]
    return out, err


def fixture(v):
    out, err = streams(v)
    script = "#!/usr/bin/env bash\n# checks four folders\n"
    script += "echo %r\necho %r\necho %r >&2\necho %r\necho %r >&2\n" % (out[0], out[1], err[0], out[2], err[1])
    return {"files": {"inspect": {"t": script, "m": 0o750}}}


def brief(v):
    return [
        {"p": "`./inspect` prints its results and its errors to the same screen."},
        {"ol": ["Run `./inspect` once, and look at what it prints.",
                "Run it again so that its results go to `out.txt` and its errors to `err.txt`, with one command."]},
    ]


def hints(v):
    return [
        "Results go to standard output (stream 1), errors to standard error (stream 2).",
        "`>` sends standard output to a file; `2>` sends standard error to a file.",
        "`./inspect > out.txt 2> err.txt`",
    ]


def collect(v, hidden):
    return {"tree": True, "texts": ["out.txt", "err.txt"]}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    out, err = streams(v)
    o, e = t.text("out.txt"), t.text("err.txt")
    res = [kit.ck("out", "out.txt holds the results, and only them", o is not None and kit.lines(o) == out,
                  "there is no out.txt" if o is None else ("out.txt has an error line in it" if any(x in o for x in err)
                                                          else "out.txt is not what ./inspect prints on standard output"))]
    res.append(kit.ck("err", "err.txt holds the errors, and only them", e is not None and kit.lines(e) == err,
                      "there is no err.txt" if e is None else ("err.txt has a result line in it" if any(x in e for x in out)
                                                              else "err.txt is not what ./inspect prints on standard error")))
    return res


def steps(v, remix=False):
    return kit.guided([
        ("A program has two outputs: its results (stream 1) and its error messages (stream 2). `>` sends stream 1 to a file.",
         "Run `./inspect` so that its results go to `out.txt`.", ["out"]),
        ("`2>` sends stream 2, the errors, to a file. Both can be redirected in the same command.",
         "Now run it with one command that sends the results to `out.txt` and the errors to `err.txt`.", ["err"]),
    ], remix)
