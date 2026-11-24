"""Paths and names, Easy: Spaces in names (Lab 2)."""
import kit

META = {"id": "paths-easy", "track": "paths", "level": "easy", "title": "Spaces in names",
        "learn": "Quote a name with a space, or the shell splits it into two words."}
META["skills"] = ['quoting', 'copy']   # the roadmap's skills this scenario trains (a clear acquires them)
REPORTS = ("budget 2026.txt", "sales north.txt", "audit notes.txt", "payroll may.txt", "staff list.txt",
           "travel plan.txt", "room booking.txt", "server costs.txt")
DEPTS = ("Finance", "Sales", "Legal", "Audit", "HR", "Support")


def values(pick):
    depts = kit.distinct(pick, "dept", DEPTS, 3)
    chosen = kit.distinct(pick, "rep", REPORTS, 3)
    return {"depts": depts, "orders": [[chosen[i], depts[i]] for i in range(3)], "code": 100 + pick("code", 900)}


def content(v, name):
    return "%s\nreference %d\n" % (name, v["code"])


def fixture(v):
    files = {"reports/" + r: content(v, r) for r in REPORTS}
    files["order.txt"] = "".join('copy "%s" to depts/%s/\n' % (r, d) for r, d in v["orders"])
    return {"dirs": ["depts/" + d for d in v["depts"]], "files": files}


def brief(v):
    return [
        {"p": "Three departments asked for a copy of a report. Each name has a space in it."},
        {"ol": ["Read `order.txt`.",
                "Copy each report named there from `reports/` into the department's folder in `depts/`.",
                "Keep the originals in `reports/`."]},
    ]


def hints(v):
    r, d = v["orders"][0]
    return [
        "A name with a space must be quoted (`\"%s\"`) or have its space escaped (`%s`)." % (r, r.replace(" ", "\\ ")),
        "Without quotes, `cp` sees two names, `%s` and `%s`, and neither exists." % tuple(r.split(" ", 1)),
        "`cp \"reports/%s\" depts/%s/`, then the same for the two other orders." % (r, d),
    ]


def collect(v, hidden):
    return {"tree": True}


def checks(data, v, hidden, info):
    t = kit.Tree.of(data)
    missing = ["depts/%s/%s" % (d, r) for r, d in v["orders"] if t.text("depts/%s/%s" % (d, r)) != content(v, r)]
    out = [kit.ck("copies", "each report is copied into its department's folder", not missing,
                  "not there, or not the same text: %s" % missing[0] if missing else "")]
    originals = [r for r, _d in v["orders"] if t.text("reports/" + r) != content(v, r)]
    out.append(kit.ck("originals", "the originals are still in reports/", not originals,
                      "reports/%s is missing or changed: copy, do not move" % originals[0] if originals else ""))
    halves = {w for r, _d in v["orders"] for w in r.split(" ")}
    split = [p for p in t.entries("depts") if p.rsplit("/", 1)[-1] in halves]
    out.append(kit.ck("split", "no name was split at its space", not split,
                      "found %s: the shell split a name in two; quote it" % split[0] if split else ""))
    return out


def steps(v, remix=False):
    return kit.guided([
        ("Without quotes the shell splits `budget 2026.txt` into two words, and `cp` sees two names. Quote the name (`\"budget 2026.txt\"`) or "
         "escape the space. `cp` copies, and leaves the original where it is.",
         "Read `order.txt`, then copy each report it names from `reports/` into its department's folder in `depts/`. Keep the originals.",
         ["copies", "originals", "split"]),
    ], remix)
