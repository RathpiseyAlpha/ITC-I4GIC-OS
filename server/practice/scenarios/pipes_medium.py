"""Redirection and pipelines, Medium: Count your status (Lab 4)."""
import kit

META = {"id": "pipes-medium", "track": "pipes", "level": "medium", "title": "Count your status",
        "learn": "awk picks a field; a pipe to wc -l counts; grep alone matches anywhere in the line."}
META["skills"] = ['awk', 'redirect']   # the roadmap's skills this scenario trains (a clear acquires them)
STATUSES = (301, 302, 403, 404, 500)
PATHS = ("/", "/index.html", "/login", "/api/items", "/img/logo.png", "/search?q=os", "/docs/lab4.pdf", "/about")


def values(pick):
    return {"status": STATUSES[pick("status", len(STATUSES))], "seed": pick("seed", 2 ** 31), "n": 380 + pick("n", 60)}


def log_lines(v):
    import random
    r = random.Random(v["seed"])
    s = v["status"]
    out = []
    for i in range(v["n"]):
        st = r.choice((200, 200, 200, 200, 301, 302, 403, 404, 500))
        path = r.choice(PATHS)
        size = r.randint(120, 9000)
        if i % 37 == 5:
            size = s            # a size that looks like the status
        if i % 53 == 9:
            path = "/errors/%d.html" % s   # a path with the status in it
        ip = "10.%d.%d.%d" % (r.randint(0, 3), r.randint(0, 255), r.randint(1, 254))
        hh, mm, ss = 8 + i * 9 // v["n"], r.randint(0, 59), r.randint(0, 59)
        out.append('%s - - [23/Nov/2026:%02d:%02d:%02d +0700] "%s %s HTTP/1.1" %d %d "-" "curl/8.5"'
                   % (ip, hh, mm, ss, r.choice(("GET", "GET", "POST")), path, st, size))
    return out


def counts(v):
    lines = log_lines(v)
    exact = sum(1 for ln in lines if ln.split()[8] == str(v["status"]))
    anywhere = sum(1 for ln in lines if str(v["status"]) in ln)
    return exact, anywhere


def fixture(v):
    return {"files": {"access.log": "\n".join(log_lines(v)) + "\n"}}


def brief(v):
    return [
        {"p": "`access.log` is a web server's log, one request per line. The 9th field is the status code."},
        {"ol": ["Count the requests whose status is **%d**." % v["status"],
                "Write that number, and nothing else, in `count.txt`."]},
        {"p": "Careful: %d also appears in some sizes and paths." % v["status"]},
    ]


def hints(v):
    return [
        "`head -3 access.log` shows the format. Count the fields: the status is the 9th, separated by spaces.",
        "`awk '{print $9}' access.log` prints only the status of every line. `wc -l` counts lines.",
        "`awk '$9 == %d' access.log | wc -l > count.txt`" % v["status"],
    ]


def collect(v, hidden):
    return {"tree": True, "texts": ["count.txt", "access.log"]}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    exact, anywhere = counts(v)
    text = t.text("count.txt")
    got = (text or "").strip()
    if text is None:
        why = "there is no count.txt"
    elif not got.isdigit():
        why = "count.txt should hold only a number, not %r" % got[:30]
    elif int(got) == anywhere:
        why = "%s is the number of lines where %d appears anywhere; count only the status field" % (got, v["status"])
    else:
        why = "%s is not the number of requests with status %d" % (got, v["status"])
    return [kit.ck("count", "count.txt holds the number of requests with status %d" % v["status"], got == str(exact), why),
            kit.ck("log", "access.log is unchanged", t.text("access.log") == "\n".join(log_lines(v)) + "\n",
                   "access.log was changed; work on a copy, or only read it")]


def steps(v, remix=False):
    return kit.guided([
        ("`awk '$9 == N'` keeps the lines whose 9th field is N, and `wc -l` counts lines. A plain `grep N` would also match N inside "
         "sizes and paths.",
         "Count the requests whose status is **%d** and write just that number in `count.txt`. Do not change `access.log`." % v["status"],
         ["count", "log"]),
    ], remix)
